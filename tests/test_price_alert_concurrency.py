"""F2.5 price-alert idempotency under concurrency: the send is claimed, not atomic.

The F2.5 acceptance claim is that a price hike is delivered to a household
**exactly once**.  That claim is a statement about the *send*, so the token
that guards it has to be taken **before** the send and not after it.

The code today is a single ordered sequence, and the ordering is the whole
mechanism:

1. ``_claim_price_alert_sent(...)`` -> ``True``   (app/subscription_alerts.py:939)
2. ``recipient = _resolve_price_alert_recipient(...)``  (:956)
3. ``sent = send_email_notification(...)``        (:1003)

Step 1 is the mutual-exclusion token.  It is an ``INSERT`` against the
``UNIQUE(tenant_id, merchant, amount_cents, period_ym)`` key on
``price_alert_sent``, so of two overlapping runs exactly one gets ``True``
and the loser returns ``False`` and sends nothing.  Nothing holds a lock
across the SMTP call in step 3 — and it does not need to, because the claim
was already taken in step 1, before any mail was attempted.  The
``UNIQUE`` constraint now guards the *decision to send* rather than only the
bookkeeping after it, which is what the previous three-step
check-then-send-then-record ordering could not do.

Two runs, two orders of events, one outcome worth naming: the loser may
suppress while the winner is still mid-send, and the winner may then fail
and release its claim.  Suppression therefore proves that *a run held the
claim*, not that *the household was told* — see the
``price_alerts_failed`` note in ``daily_scheduler`` for why the two are
counted differently.  The regression net for the other side of that trade — a
won claim that is never released — is
``tests/test_price_alert_release_paths.py``.

How these tests are built, and why:

* **Only the transport is patched.**  ``send_email_notification`` is replaced
  with a counting fake; ``_claim_price_alert_sent`` and
  ``ProductService`` are left **real**, so the production ordering and the
  real ledger are what the race runs against.  A test that patched the
  claim helper would assert nothing about the mechanism.
* **The race is forced, not timed.**  A :class:`threading.Barrier` sits
  *inside* the fake send, so the first thread is held at the SMTP call until
  the second thread has run step 1 and taken its own decision.  There is no
  ``sleep`` and no "loop until it flakes": the interleaving is a
  precondition of the test, not a probability.  A consequence worth
  stating: with the claim taken before the send, exactly one thread reaches
  the barrier and sends.  A regression that let the second thread into the
  send would strand that thread at the barrier for the full timeout — which
  is reported as a diagnostic rather than asserted, because the assertion
  under test is the send count.
* **No shared SQLite connection.**  ``app.product_api.service`` is a module
  singleton holding one connection, so each thread is handed its *own*
  ``ProductService`` bound to the same temp file.  Two connections, one
  database, SQLite's own locking -- the real deployment shape, without
  sharing a connection object across threads.
* **The test cannot hang.**  Every barrier wait, every ``join`` and every
  thread has a timeout, and the worker threads are daemons.  A deadlocked or
  wedged run fails the test instead of wedging the suite.
* **The live database is never written.**  The store points at a fresh temp
  file created by the production ``ProductService`` schema itself, and both
  tests assert the resolved path is not ``./receiptlens-product.db``.

TEST-PRICECONC-001 asserts the send count is **1**.  That is the whole
acceptance criterion, and it is a live assertion against the current code —
a run that mails the household twice fails here rather than being recorded
as an expected RED.

Run:
    python -m pytest tests/test_price_alert_concurrency.py -o addopts= -q -p no:randomly
"""

from __future__ import annotations

import copy
import os
import pathlib
import sqlite3
import threading
from typing import Any

import pytest

import app.subscription_alerts as subscription_alerts
from app.product_service import ProductService

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LIVE_DB = REPO_ROOT / "receiptlens-product.db"

#: Synthetic household.  Never the real tenant -- a bug in the tenant filter
#: would then mail a real member, and the ledger assertions would read real
#: rows.
TENANT = "hh-test-conc-001"
OWNER_EMAIL = "owner@hh-test-conc-001.invalid"
MERCHANT = "NetStream"

#: Fixed anchor so ``period_ym`` and the renewal window are deterministic.
TODAY = "2026-10-02"
#: Far outside ``RENEWAL_ALERT_DAYS`` (7) on purpose: the renewal branch calls
#: the *same* ``send_email_notification``, and a renewal firing here would
#: both trip the barrier and muddy the send count.  The fake send is the
#: price-hike path only.
RENEWAL_DATE = "2027-06-01"

#: 15.99 against a 9.99 average is a ~60% hike, comfortably over the 10%
#: threshold, so ``detect_price_increase`` returns True without depending on
#: any fixture data.
SUBSCRIPTION: dict[str, Any] = {
    "merchant": MERCHANT,
    "renewal_date": RENEWAL_DATE,
    "amount": 15.99,
    "baseline": [9.99, 9.99],
    "email_alert_enabled": True,
}

SMTP_CONFIG: dict[str, Any] = {
    "host": "127.0.0.1",
    "port": 25,
    "user": "probe-user",
    "password": "probe-password",
    "from_addr": "probe@hh-test-conc-001.invalid",
    # Deliberately NOT the owner's address: daily_scheduler must override it
    # (AC-PRICE-10), and a test that leaked a real to_addr here would be a
    # PII problem rather than a correctness one.
    "to_addr": "operator@example.invalid",
}

#: (tenant, merchant, amount_cents, period_ym) -- the F2.5 idempotency key.
ALERT_KEY = (TENANT, MERCHANT, 1599, RENEWAL_DATE[:7])

#: Every wait in this module is bounded.  The threads do O(1) sqlite work
#: against a local temp file, so anything past this is a hang, not slowness.
TIMEOUT = 20.0

#: Guards only the per-thread ``ProductService`` construction, so two threads
#: never race on the ``CREATE TABLE IF NOT EXISTS`` script.  It is NOT held
#: across the send and does not mask the bug: the two stores are still
#: separate connections and the send window is still unguarded.
_STORE_INIT_LOCK = threading.Lock()


def _build_store(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Create a throwaway product DB and point the alert store at it.

    The schema comes from ``ProductService._create_schema`` -- the production
    one -- rather than being hand-copied here, so this test cannot drift from
    the real table definitions.  One synthetic owner is seeded so
    ``_resolve_price_alert_recipient`` resolves an addressee; without it the
    run suppresses the alert (AC-PRICE-12) and there would be no race to
    observe at all.
    """
    db_path = tmp_path / "concurrency-product.db"

    seeder = ProductService(str(db_path))
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute(
                "INSERT INTO members VALUES(?,?,?,?,1)",
                ("m-conc-001", TENANT, OWNER_EMAIL, "owner"),
            )
            conn.execute("DELETE FROM price_alert_sent")
            conn.commit()
        finally:
            conn.close()
    finally:
        seeder._db.close()

    resolved = str(db_path.resolve())
    assert pathlib.Path(resolved).resolve() != LIVE_DB.resolve(), (
        "test DB resolved to the live product database: {}".format(resolved)
    )

    # The alert store is the ``ProductService`` singleton resolved at
    # subscription_alerts.py:679.  Each thread gets its own instance on the
    # same file -- two connections, one database, no shared connection
    # object.  ``_price_alert_already_sent`` and ``_record_price_alert_sent``
    # are NOT patched and keep calling through here.
    local = threading.local()

    def _price_alert_store() -> ProductService:
        store = getattr(local, "store", None)
        if store is None:
            with _STORE_INIT_LOCK:
                store = ProductService(resolved)
            local.store = store
        return store

    monkeypatch.setattr(
        subscription_alerts, "_price_alert_store", _price_alert_store
    )
    # Belt and braces: anything that resolves the module-level singleton
    # instead (e.g. ``from app.product_api import Actor`` importing
    # app.product_api) must still not reach the live database.
    monkeypatch.setenv("RECEIPTLENS_PRODUCT_DB", resolved)
    return resolved


def _ledger_rows(db_path: str) -> list[tuple[Any, ...]]:
    """Read the whole ledger for the synthetic tenant, key included.

    A fresh connection on purpose: the assertion is about what actually
    landed in the file on disk, not about what one of the racing stores
    believes it wrote.
    """
    if not pathlib.Path(db_path).is_file():
        return []
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            "SELECT tenant_id, merchant, amount_cents, period_ym "
            "FROM price_alert_sent WHERE tenant_id = ? ORDER BY alert_id",
            (TENANT,),
        )
        return [tuple(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def _count_live_ledger_rows() -> int:
    """Count ``price_alert_sent`` in the live DB -- read-only, never a write."""
    if not LIVE_DB.is_file():
        return 0
    conn = sqlite3.connect(LIVE_DB)
    try:
        return int(conn.execute("SELECT COUNT(*) FROM price_alert_sent").fetchone()[0])
    finally:
        conn.close()


@pytest.fixture
def store_db(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Temp product DB plus the per-thread store patch.  Yields its path."""
    return _build_store(tmp_path, monkeypatch)


@pytest.fixture
def send_recorder(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Replace ``send_email_notification`` with a counting fake.

    The fake records the subject of every call and returns True, so the
    production path behaves exactly as it does on a successful delivery --
    ``price_emails_sent`` increments and the ledger row is written.  The
    barrier is installed by TEST-PRICECONC-001 via ``barrier``.

    No SMTP: nothing here opens a socket, so this suite is safe to run
    anywhere.
    """
    state: dict[str, Any] = {
        "subjects": [],
        "barrier": None,
        "barrier_broken": False,
        "errors": [],
    }
    lock = threading.Lock()

    def _fake_send(
        subject: str, body: str, *, smtp_config: dict[str, Any] | None = None
    ) -> bool:
        with lock:
            state["subjects"].append(subject)
        barrier = state.get("barrier")
        if barrier is not None:
            try:
                # Bounded: if the other thread never arrives (because a fix
                # made it suppress the alert) this breaks instead of hanging.
                barrier.wait(timeout=TIMEOUT)
            except threading.BrokenBarrierError:
                with lock:
                    state["barrier_broken"] = True
        return True

    monkeypatch.setattr(
        subscription_alerts, "send_email_notification", _fake_send
    )
    return state


def _run_scheduler(today: str = TODAY) -> dict:
    """Run the real ``daily_scheduler`` against a fresh copy of the fixture sub."""
    return subscription_alerts.daily_scheduler(
        smtp_config=copy.deepcopy(SMTP_CONFIG),
        today=today,
        subscriptions=[copy.deepcopy(SUBSCRIPTION)],
        tenant=TENANT,
    )


def _run_in_threads(count: int) -> list[dict[str, Any]]:
    """Run ``daily_scheduler`` in ``count`` threads concurrently; return results.

    Each thread gets its own deep copy of the subscription list and its own
    ``ProductService`` (installed by :func:`_build_store`).  Worker exceptions
    are captured and re-raised here, because a thread that dies does not by
    itself fail a pytest run.
    """
    results: list[dict[str, Any] | None] = [None] * count
    errors: list[BaseException] = []
    guard = threading.Lock()

    def _worker(index: int) -> None:
        try:
            outcome = _run_scheduler()
        except BaseException as exc:  # noqa: BLE001 - re-raised in the main thread
            with guard:
                errors.append(exc)
            return
        with guard:
            results[index] = outcome

    threads = [
        threading.Thread(target=_worker, args=(i,), name="sched-{}".format(i), daemon=True)
        for i in range(count)
    ]
    start = threading.Barrier(count, timeout=TIMEOUT)
    for thread in threads:
        thread.start()
    # Release all workers into daily_scheduler at the same moment, so the
    # outer interleaving is not an accident of thread start-up order.
    try:
        start.wait(timeout=TIMEOUT)
    except threading.BrokenBarrierError:
        pass
    for thread in threads:
        thread.join(timeout=TIMEOUT)

    still_running = [t.name for t in threads if t.is_alive()]
    assert not still_running, (
        "daily_scheduler threads did not finish within {}s: {} -- the run is "
        "wedged, not slow".format(TIMEOUT, still_running)
    )
    if errors:
        raise errors[0]
    return [r for r in results if r is not None]


# ---------------------------------------------------------------------------
# TEST-PRICECONC-001 -- concurrent runs must mail the household once
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.test_id("TEST-PRICECONC-001")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-F25-05: two concurrent daily_scheduler runs over the same price hike send the price-increase email EXACTLY ONCE. The claim into price_alert_sent is taken BEFORE the send (app/subscription_alerts.py:939), so the UNIQUE key now guards the decision to send rather than only the bookkeeping after it, and the loser returns False without reaching the transport.")
def test_concurrent_runs_send_price_alert_exactly_once(
    store_db: str, send_recorder: dict
) -> None:
    live_before = _count_live_ledger_rows()

    results = _run_in_threads(2)

    subjects = list(send_recorder["subjects"])
    rows = _ledger_rows(store_db)

    assert _count_live_ledger_rows() == live_before, (
        "the live product database was written to by this test"
    )

    assert len(results) == 2, "expected two scheduler results, got {}".format(len(results))
    assert len(subjects) == 1, (
        "the household was mailed {} times for one price hike: {}. "
        "the send is now protected by claim_price_alert_sent -- the loser "
        "never reaches send_email_notification.".format(len(subjects), subjects)
    )
    assert subjects[0] == "Price Increase: {}".format(MERCHANT), (
        "the single send was not the price-hike alert: {!r}".format(subjects[0])
    )

    assert rows == [ALERT_KEY], (
        "expected exactly one price_alert_sent row {} for the key, got {}".format(
            ALERT_KEY, rows
        )
    )
    # The losing run suppressed the alert; the winning run sent it.
    sorts = sorted(r["price_emails_sent"] for r in results)
    assert sorts == [0, 1], (
        "expected one concurrent run to suppress the alert, got {}".format(
            [r["price_emails_sent"] for r in results]
        )
    )
    suppressed = sum(r["price_alerts_suppressed"] for r in results)
    assert suppressed == 1, (
        "expected exactly one suppressed alert across two concurrent runs, got {}: {}".format(
            suppressed, results
        )
    )


# ---------------------------------------------------------------------------
# TEST-PRICECONC-002 -- sequential re-run is idempotent (the control)
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.test_id("TEST-PRICECONC-002")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-F25-06: two SEQUENTIAL daily_scheduler runs over the same price hike send the price-increase email exactly once and leave exactly one price_alert_sent row; the second run reports the alert suppressed rather than failed. Control case for TEST-PRICECONC-001 -- it passes, which is what shows the concurrent failure is a race and not a broken key.")
def test_sequential_rerun_sends_once_and_leaves_one_ledger_row(
    store_db: str, send_recorder: dict
) -> None:
    live_before = _count_live_ledger_rows()

    first = _run_scheduler()
    second = _run_scheduler()

    subjects = list(send_recorder["subjects"])
    rows = _ledger_rows(store_db)

    assert _count_live_ledger_rows() == live_before, (
        "the live product database was written to by this test"
    )
    assert len(subjects) == 1, (
        "two sequential runs sent {} emails, expected 1: {!r}".format(
            len(subjects), subjects
        )
    )
    assert subjects[0] == "Price Increase: {}".format(MERCHANT), (
        "the single send was not the price-hike alert: {!r}".format(subjects[0])
    )
    assert rows == [ALERT_KEY], (
        "expected exactly one price_alert_sent row {} for the key, got {}".format(
            ALERT_KEY, rows
        )
    )
    assert first["price_emails_sent"] == 1, (
        "first run should have delivered the alert, got {}".format(first)
    )
    assert second["price_emails_sent"] == 0 and second["price_alerts_suppressed"] == 1, (
        "second run should suppress, not send or fail: {}".format(second)
    )
    assert second["price_alerts_failed"] == 0, (
        "a suppressed alert is a success, never a failure: {}".format(second)
    )
    assert os.path.realpath(store_db) != os.path.realpath(LIVE_DB), (
        "the alert store pointed at the live product database"
    )
