"""F2.5 claim release paths: a stranded claim must never suppress forever.

The claim-before-send fix (app/subscription_alerts.py:913-931) closes the
concurrency hole that TEST-PRICECONC-001 documents: the INSERT into
``price_alert_sent`` is now the mutual-exclusion token for the SMTP call, so a
losing run never mails the household a second time.  That fix opens a second,
quieter hole, and this module is the regression net for it.

Once a run **wins** the claim, every path that does not end in a delivered
email owes the household a *release* (app/product_service.py:351,
``release_price_alert_sent``).  A claim that is taken and never released is
indistinguishable, from the outside, from a claim that a *delivered* alert
owns -- the row is the same row -- so every subsequent run suppresses the
alert forever and the household is never told about the hike.  The failure is
silent, permanent, and grows with time; nothing in the run summary shows it,
because a suppressed alert is a legitimate outcome (AC-PRICE-14).

There are exactly three non-delivery paths out of a won claim, plus the
exception variant of the first:

* **P1** ``_resolve_price_alert_recipient`` returns ``None`` -- no active
  owner, so there is no addressee.  The alert was never owed to anyone, so
  this is NOT a failure (``price_alerts_failed`` must stay 0) but the claim
  still has to go.
* **P2** ``send_email_notification`` returns ``False`` -- the hike is real and
  the household was not told.  One failure, and the claim goes.
* **P3** ``send_email_notification`` raises ``OSError`` -- the same, one
  failure, claim released.
* **P4** recipient resolution itself raises ``sqlite3.OperationalError``
  (a locked database).  This one is the easiest to get wrong, because the
  resolution call reads the same SQLite file that holds the claim: hoist it
  out of the try/except and every later run suppresses the alert forever.

Ordering, measured rather than assumed: ``_claim_price_alert_sent`` runs at
app/subscription_alerts.py:916 and ``_resolve_price_alert_recipient`` at :945,
so the claim is acquired *before* the recipient is resolved and *before* the
send.  All four paths above therefore win a real claim row and must release
it; none of them bails out ahead of the claim.  Each test asserts the claim
was won (:func:`_assert_released`) so a future refactor that moves resolution
above the claim cannot pass vacuously.

How these tests are built, and why:

* **Only the transport and the resolver are patched.**  ``_claim_price_alert_sent``,
  ``_release_price_alert_sent`` and the ``ProductService`` ledger are **real**,
  so what is under test is the production release ordering and a real DELETE
  against a real file.  The two ledger calls are only *wrapped*, to observe
  them -- the wrappers call straight through to the originals, so a test
  cannot pass by suppressing the release it is meant to prove.
* **The truth is read at the level that owns it.**  The module-level
  ``_release_price_alert_sent`` is annotated ``-> None`` and discards the
  store's return value (app/subscription_alerts.py:730-736), so it cannot
  report whether anything was deleted.  Whether a row really went is answered
  by ``ProductService.release_price_alert_sent``, which returns ``rowcount >
  0`` -- and by ``claim_price_alert_sent``, which proves the claim existed at
  all.  Asserting on the discarded ``None`` is what made an earlier draft of
  this module unpassable rather than merely weak.
* **The negative assertion alone would prove nothing.**  "no ledger row" is
  equally true of a run that never claimed.  So each test asserts
  the claim was won, the release was called for *this* alert key and the real
  store confirms it dropped a row, **and** then runs a second time with the
  fault removed and asserts the alert is actually delivered -- one ledger
  row, ``price_emails_sent == 1``.  That second run is the assertion that
  matters: a leaked claim shows up there as a permanent suppression, and no
  amount of counting would have caught it.
* **The schema is the production one.**  The table comes from
  ``ProductService._create_schema`` rather than being hand-copied, and the
  owner member is seeded so ``_resolve_price_alert_recipient`` resolves an
  addressee in the "delivers" halves of the tests.
* **The live database is never written.**  The store points at a temp file
  created by ``ProductService`` itself, and every test asserts the resolved
  path is not ``./receiptlens-product.db`` *and* that the live ledger count
  is unchanged across the run.

No SMTP and no sockets: ``send_email_notification`` is replaced by a local
fake throughout, so this suite is safe to run anywhere.

Run:
    python -m pytest tests/test_price_alert_release_paths.py -o addopts= -q -p no:randomly
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
TENANT = "hh-test-rel-001"
OWNER_EMAIL = "owner@hh-test-rel-001.invalid"
MERCHANT = "NetStream"

#: Fixed anchor so ``period_ym`` and the renewal window are deterministic.
TODAY = "2026-10-02"
#: Far outside ``RENEWAL_ALERT_DAYS`` (7) on purpose: the renewal branch calls
#: the *same* ``send_email_notification``, and a renewal firing here would
#: both pollute the send counts and trip the raise/false fakes for the wrong
#: reason.  The send fakes here are the price-hike path only.
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
    "from_addr": "probe@hh-test-rel-001.invalid",
    # Deliberately NOT the owner's address: daily_scheduler must override it
    # (AC-PRICE-10), and a test that leaked a real to_addr here would be a
    # PII problem rather than a correctness one.
    "to_addr": "operator@example.invalid",
}

#: (tenant, merchant, amount_cents, period_ym) -- the F2.5 idempotency key.
ALERT_KEY = (TENANT, MERCHANT, 1599, RENEWAL_DATE[:7])

#: The subject every successful price-hike delivery is expected to carry.
ALERT_SUBJECT = "Price Increase: {}".format(MERCHANT)

#: Guards only the per-store construction, so a fixture teardown can never
#: race a ``CREATE TABLE IF NOT EXISTS`` script.  It is not held across a run
#: and masks nothing: the release paths under test are single-run.
_STORE_INIT_LOCK = threading.Lock()


def _build_store(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Create a throwaway product DB and point the alert store at it.

    The schema comes from ``ProductService._create_schema`` -- the production
    one -- rather than being hand-copied here, so this test cannot drift from
    the real table definitions.  One synthetic owner is seeded so
    ``_resolve_price_alert_recipient`` resolves an addressee by default;
    TEST-REL-001 deactivates it on purpose.
    """
    db_path = tmp_path / "release-paths-product.db"

    seeder = ProductService(str(db_path))
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute(
                "INSERT INTO members VALUES(?,?,?,?,1)",
                ("m-rel-001", TENANT, OWNER_EMAIL, "owner"),
            )
            conn.execute("DELETE FROM price_alert_sent")
            conn.commit()
        finally:
            conn.close()
    finally:
        seeder._db.close()

    resolved = str(db_path.resolve())
    assert os.path.realpath(resolved) != os.path.realpath(LIVE_DB), (
        "test DB resolved to the live product database: {}".format(resolved)
    )

    # The alert store is the ``ProductService`` singleton resolved at
    # subscription_alerts.py:679.  Each thread gets its own instance on the
    # same file, mirroring the concurrency suite; these tests run in the main
    # thread, but the per-thread shape is kept so a future threaded variant
    # cannot accidentally share one connection object.
    local = threading.local()

    def _price_alert_store() -> ProductService:
        store = getattr(local, "store", None)
        if store is None:
            with _STORE_INIT_LOCK:
                store = ProductService(resolved)
            local.store = store
        return store

    monkeypatch.setattr(subscription_alerts, "_price_alert_store", _price_alert_store)
    # Belt and braces: anything that resolves the module-level singleton
    # instead (e.g. ``from app.product_api import Actor`` importing
    # app.product_api) must still not reach the live database.
    monkeypatch.setenv("RECEIPTLENS_PRODUCT_DB", resolved)
    return resolved


def _set_owner_active(db_path: str, active: bool) -> None:
    """Flip the synthetic owner's ``active`` flag on the temp DB.

    A separate connection on purpose: the assertion is about what a *later*
    reader of the file sees, not about what a cached store connection
    believes.  ``rowcount`` is checked so a silently-vacuous UPDATE cannot
    turn TEST-REL-001 into a test of nothing.
    """
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "UPDATE members SET active = ? WHERE tenant_id = ?",
            (1 if active else 0, TENANT),
        )
        conn.commit()
        assert cur.rowcount == 1, (
            "expected to update exactly the seeded owner row, updated {} "
            "(members rows for {}: {})".format(
                cur.rowcount,
                TENANT,
                conn.execute(
                    "SELECT COUNT(*) FROM members WHERE tenant_id = ?", (TENANT,)
                ).fetchone()[0],
            )
        )
    finally:
        conn.close()


def _ledger_rows(db_path: str) -> list[tuple[Any, ...]]:
    """Read the whole ledger for the synthetic tenant, key included.

    A fresh connection on purpose: the assertion is about what actually
    landed in the file on disk, not about what the run's store believes it
    wrote.
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


def _run_scheduler(today: str = TODAY) -> dict:
    """Run the real ``daily_scheduler`` against a fresh copy of the fixture sub."""
    return subscription_alerts.daily_scheduler(
        smtp_config=copy.deepcopy(SMTP_CONFIG),
        today=today,
        subscriptions=[copy.deepcopy(SUBSCRIPTION)],
        tenant=TENANT,
    )


@pytest.fixture
def store_db(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Temp product DB plus the per-thread store patch.  Yields its path."""
    return _build_store(tmp_path, monkeypatch)


@pytest.fixture
def send_recorder(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Replace ``send_email_notification`` with a counting fake that succeeds.

    This is the *healthy* transport: it returns True, so the production path
    behaves exactly as on a real delivery -- ``price_emails_sent`` increments
    and the ledger row is written.  A test that needs the transport to fail
    re-patches it over the top via :func:`_patch_send`.

    No SMTP: nothing here opens a socket, so this suite is safe to run
    anywhere.
    """
    state: dict[str, Any] = {"subjects": []}

    def _fake_send(
        subject: str, body: str, *, smtp_config: dict[str, Any] | None = None
    ) -> bool:
        state["subjects"].append(subject)
        return True

    _patch_send(monkeypatch, _fake_send)
    return state


@pytest.fixture
def release_recorder(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Observe the claim/release pair at both levels of the ledger boundary.

    Three recorders, each at the level that actually owns the fact:

    * ``calls`` -- module-level ``_release_price_alert_sent`` invocations.
      Proves the *production ordering* reaches the release on this path.  Its
      return value is deliberately NOT recorded as evidence: the function is
      annotated ``-> None`` and throws the store's answer away
      (app/subscription_alerts.py:730-736).
    * ``claims`` -- ``(key, won)`` from the real
      ``ProductService.claim_price_alert_sent``.  ``won`` is False on a lost
      race, so ``(key, True)`` is positive proof that a claim row genuinely
      existed and the release below has something real to delete.
    * ``releases`` -- ``(key, deleted)`` from the real
      ``ProductService.release_price_alert_sent``, whose return is
      ``rowcount > 0``.  ``deleted`` is True only when the DELETE actually
      dropped a row.

    All three wrappers call straight through to the originals and return their
    result unchanged, so a test cannot pass by suppressing the release it is
    meant to prove.
    """
    state: dict[str, Any] = {"calls": [], "claims": [], "releases": []}
    real_module_release = subscription_alerts._release_price_alert_sent
    real_service_claim = ProductService.claim_price_alert_sent
    real_service_release = ProductService.release_price_alert_sent

    def _recording_module_release(
        tenant: str, merchant: str, amount_cents: int, period_ym: str
    ) -> Any:
        result = real_module_release(tenant, merchant, amount_cents, period_ym)
        state["calls"].append((tenant, merchant, amount_cents, period_ym))
        return result

    def _recording_claim(
        self: ProductService, tenant: str, merchant: str, amount_cents: int, period_ym: str
    ) -> bool:
        result = real_service_claim(self, tenant, merchant, amount_cents, period_ym)
        state["claims"].append(((tenant, merchant, amount_cents, period_ym), result))
        return result

    def _recording_release(
        self: ProductService, tenant: str, merchant: str, amount_cents: int, period_ym: str
    ) -> bool:
        result = real_service_release(self, tenant, merchant, amount_cents, period_ym)
        state["releases"].append(((tenant, merchant, amount_cents, period_ym), result))
        return result

    monkeypatch.setattr(
        subscription_alerts, "_release_price_alert_sent", _recording_module_release
    )
    monkeypatch.setattr(ProductService, "claim_price_alert_sent", _recording_claim)
    monkeypatch.setattr(ProductService, "release_price_alert_sent", _recording_release)
    return state


def _patch_send(monkeypatch: pytest.MonkeyPatch, fake: Any) -> None:
    """Install ``fake`` as ``subscription_alerts.send_email_notification``."""
    monkeypatch.setattr(subscription_alerts, "send_email_notification", fake)


def _assert_not_live(store_db: str) -> None:
    """Fail loudly if the alert store ever resolved to the live product DB."""
    assert os.path.realpath(store_db) != os.path.realpath(LIVE_DB), (
        "the alert store pointed at the live product database: {}".format(store_db)
    )


def _assert_claimed(release_recorder: dict) -> None:
    """The run won the claim for exactly this alert key before anything else.

    This is what makes the release assertions non-vacuous.  A run that never
    claimed records no claim here, and no release test downstream can be
    satisfied by a run that skipped the ledger entirely.  It also pins the
    ordering requirement itself (claim at :916, resolve at :945): a refactor
    that hoisted recipient resolution above the claim would drop this entry
    on the P1/P4 paths and fail.
    """
    assert release_recorder["claims"] == [(ALERT_KEY, True)], (
        "expected the run to win the claim {} exactly once, got {} -- without "
        "a won claim there is nothing to release, and this run's release "
        "assertions would be vacuous".format(ALERT_KEY, release_recorder["claims"])
    )


def _assert_released(release_recorder: dict) -> None:
    """Exactly one release, for exactly this alert key, and it deleted a row.

    ``ProductService.release_price_alert_sent`` returns ``rowcount > 0``, so
    ``True`` means a real DELETE removed the claim row and ``False`` means
    there was nothing there -- which, after :func:`_assert_claimed` has proven
    the row existed, can only mean the production code released the wrong key.
    """
    _assert_claimed(release_recorder)
    assert release_recorder["calls"] == [ALERT_KEY], (
        "expected exactly one _release_price_alert_sent call for {}, got {}".format(
            ALERT_KEY, release_recorder["calls"]
        )
    )
    assert release_recorder["releases"] == [(ALERT_KEY, True)], (
        "the release did not delete the claim row (ProductService."
        "release_price_alert_sent returned {} for {}) -- the claim taken by "
        "this run is stranded and every later run suppresses the alert "
        "forever".format(release_recorder["releases"], ALERT_KEY)
    )


def _assert_delivered(summary: dict, rows: list[tuple[Any, ...]], subjects: list) -> None:
    """A second run with the fault gone must actually mail the household."""
    assert summary["price_emails_sent"] == 1, (
        "the second run did not deliver the alert -- price_emails_sent={} "
        "(summary={}). A claim left behind by the first run suppresses every "
        "later run forever.".format(summary["price_emails_sent"], summary)
    )
    assert summary["price_alerts_suppressed"] == 0, (
        "the second run suppressed the alert instead of sending it -- the "
        "claim from the first run was never released: {}".format(summary)
    )
    assert summary["price_alerts_failed"] == 0, (
        "the second run reported a failure on a healthy transport: {}".format(summary)
    )
    assert rows == [ALERT_KEY], (
        "expected exactly one price_alert_sent row {} for the key, got {}".format(
            ALERT_KEY, rows
        )
    )
    assert subjects == [ALERT_SUBJECT], (
        "expected exactly one delivered alert {!r}, got {!r}".format(
            ALERT_SUBJECT, subjects
        )
    )


# ---------------------------------------------------------------------------
# TEST-REL-001 -- P1: no active owner releases the claim, and is not a failure
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.test_id("TEST-REL-001")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-F25-07: P1 -- a won claim with no active owner to address (recipient resolution returns None) is released rather than stranded: price_emails_sent, price_alerts_suppressed and price_alerts_failed all stay 0, send_email_notification is never called, no price_alert_sent row is left behind, and once an owner exists again the next run delivers the alert with one ledger row. The claim is taken before the recipient is resolved (app/subscription_alerts.py:916 vs :945), so the resolution None path releases a real row; a claim that is not released here would suppress the hike forever.")
def test_no_active_owner_releases_claim_and_is_not_a_failure(
    store_db: str, send_recorder: dict, release_recorder: dict
) -> None:
    live_before = _count_live_ledger_rows()
    _assert_not_live(store_db)

    # P1 -- there is no addressee, so the alert is not owed to anyone.
    _set_owner_active(store_db, False)

    first = _run_scheduler()
    rows_after_first = _ledger_rows(store_db)

    assert _count_live_ledger_rows() == live_before, (
        "the live product database was written to by this test"
    )
    assert first["price_emails_sent"] == 0, (
        "nothing may be sent when there is no active owner: {}".format(first)
    )
    assert first["price_alerts_suppressed"] == 0, (
        "no other run holds this alert, so nothing was suppressed: {}".format(first)
    )
    assert first["price_alerts_failed"] == 0, (
        "a no-owner resolution is a deliberate no-op, never a failure: {}".format(first)
    )
    assert send_recorder["subjects"] == [], (
        "send_email_notification was called with no active owner: {!r}".format(
            send_recorder["subjects"]
        )
    )
    # The claim was won *before* the recipient resolved to None, so it is a
    # real row that a real DELETE has to drop -- this is the assertion an
    # earlier draft of this test wrongly replaced with a bare no-op check.
    _assert_released(release_recorder)
    assert rows_after_first == [], (
        "the claim was stranded after a None recipient: {}".format(rows_after_first)
    )

    # The assertion that makes this real: an owner exists again, and the
    # alert is delivered.  A leaked claim shows up here as a suppression.
    _set_owner_active(store_db, True)
    second = _run_scheduler()

    _assert_delivered(second, _ledger_rows(store_db), send_recorder["subjects"])


# ---------------------------------------------------------------------------
# TEST-REL-002 -- P2: a refused send releases the claim
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.test_id("TEST-REL-002")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-F25-08: P2 -- when send_email_notification returns False after the claim was won, price_alerts_failed is 1 and no price_alert_sent row is left behind; the very next run with a working transport delivers the alert and writes one ledger row. Proves the claim was released rather than merely absent.")
def test_refused_send_releases_claim_and_next_run_delivers(
    store_db: str,
    send_recorder: dict,
    release_recorder: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    live_before = _count_live_ledger_rows()
    _assert_not_live(store_db)

    # P2 -- the transport refuses.  The claim must not survive this.
    attempted: list[str] = []

    def _refusing_send(
        subject: str, body: str, *, smtp_config: dict[str, Any] | None = None
    ) -> bool:
        attempted.append(subject)
        return False

    _patch_send(monkeypatch, _refusing_send)

    first = _run_scheduler()
    rows_after_first = _ledger_rows(store_db)

    assert _count_live_ledger_rows() == live_before, (
        "the live product database was written to by this test"
    )
    assert first["price_alerts_failed"] == 1, (
        "a real hike that reached nobody is exactly one failure, got {}".format(
            first["price_alerts_failed"]
        )
    )
    assert first["price_emails_sent"] == 0, (
        "a refused send must not count as delivered: {}".format(first)
    )
    assert first["price_alerts_suppressed"] == 0, (
        "no other run holds this alert: {}".format(first)
    )
    assert attempted == [ALERT_SUBJECT], (
        "the refused send was not the price-hike alert: {!r}".format(attempted)
    )
    _assert_released(release_recorder)
    assert rows_after_first == [], (
        "a refused send left a claim row behind, which would suppress the "
        "hike forever: {}".format(rows_after_first)
    )

    # Fault removed: the next run must deliver.  This is the assertion that
    # distinguishes "released" from "never claimed".
    _patch_send(
        monkeypatch,
        lambda subject, body, *, smtp_config=None: send_recorder["subjects"].append(
            subject
        )
        or True,
    )

    second = _run_scheduler()

    _assert_delivered(second, _ledger_rows(store_db), send_recorder["subjects"])


# ---------------------------------------------------------------------------
# TEST-REL-003 -- P3: a raising send releases the claim
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.test_id("TEST-REL-003")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-F25-09: P3 -- when send_email_notification raises OSError after the claim was won, price_alerts_failed is 1 and no price_alert_sent row is left behind; the very next run with a working transport delivers the alert and writes one ledger row. An exception escaping the send path without a release is the same permanent suppression as a refused send.")
def test_raising_send_releases_claim_and_next_run_delivers(
    store_db: str,
    send_recorder: dict,
    release_recorder: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    live_before = _count_live_ledger_rows()
    _assert_not_live(store_db)

    # P3 -- the transport blows up mid-send.
    attempted: list[str] = []

    def _raising_send(
        subject: str, body: str, *, smtp_config: dict[str, Any] | None = None
    ) -> bool:
        attempted.append(subject)
        raise OSError("probe: transport failed")

    _patch_send(monkeypatch, _raising_send)

    first = _run_scheduler()
    rows_after_first = _ledger_rows(store_db)

    assert _count_live_ledger_rows() == live_before, (
        "the live product database was written to by this test"
    )
    assert first["price_alerts_failed"] == 1, (
        "a raised send is exactly one failure, got {}".format(
            first["price_alerts_failed"]
        )
    )
    assert first["price_emails_sent"] == 0, (
        "a raising send must not count as delivered: {}".format(first)
    )
    assert first["price_alerts_suppressed"] == 0, (
        "no other run holds this alert: {}".format(first)
    )
    assert attempted == [ALERT_SUBJECT], (
        "the raising send was not the price-hike alert: {!r}".format(attempted)
    )
    _assert_released(release_recorder)
    assert rows_after_first == [], (
        "an OSError from the send left a claim row behind, which would "
        "suppress the hike forever: {}".format(rows_after_first)
    )

    # Fault removed: the next run delivers.
    _patch_send(
        monkeypatch,
        lambda subject, body, *, smtp_config=None: send_recorder["subjects"].append(
            subject
        )
        or True,
    )

    second = _run_scheduler()

    _assert_delivered(second, _ledger_rows(store_db), send_recorder["subjects"])


# ---------------------------------------------------------------------------
# TEST-REL-004 -- P4: an exception during recipient resolution releases
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.test_id("TEST-REL-004")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-F25-10: P4 -- a sqlite3.OperationalError raised by _resolve_price_alert_recipient (a locked database) after the claim was won is caught: price_alerts_failed is 1, no price_alert_sent row is left behind, and the next run with the fault removed resolves the owner and delivers the alert with one ledger row. Recipient resolution reads the same SQLite file that holds the claim, so hoisting it out of the release scope strands every later run.")
def test_resolution_exception_releases_claim_and_next_run_delivers(
    store_db: str,
    send_recorder: dict,
    release_recorder: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    live_before = _count_live_ledger_rows()
    _assert_not_live(store_db)

    # P4 -- the resolution read raises instead of returning an address.  The
    # patch is scoped to exactly one call, so the second run exercises the
    # real resolver with no further action from the test.
    real_resolve = subscription_alerts._resolve_price_alert_recipient
    resolver_calls: list[str] = []

    def _flaky_resolve(tenant: str) -> str | None:
        resolver_calls.append(tenant)
        if len(resolver_calls) == 1:
            raise sqlite3.OperationalError("probe: database is locked")
        return real_resolve(tenant)

    monkeypatch.setattr(
        subscription_alerts, "_resolve_price_alert_recipient", _flaky_resolve
    )

    first = _run_scheduler()
    rows_after_first = _ledger_rows(store_db)

    assert _count_live_ledger_rows() == live_before, (
        "the live product database was written to by this test"
    )
    assert first["price_alerts_failed"] == 1, (
        "an undeliverable hike behind a resolution exception is one failure, "
        "got {}".format(first["price_alerts_failed"])
    )
    assert first["price_emails_sent"] == 0, (
        "nothing was delivered, so nothing may count as sent: {}".format(first)
    )
    assert first["price_alerts_suppressed"] == 0, (
        "no other run holds this alert: {}".format(first)
    )
    assert resolver_calls == [TENANT], (
        "the price-hike path must resolve a recipient exactly once per run: "
        "{!r}".format(resolver_calls)
    )
    _assert_released(release_recorder)
    assert rows_after_first == [], (
        "the claim was stranded when recipient resolution raised, which would "
        "suppress the hike forever: {}".format(rows_after_first)
    )

    # The patch now delegates to the real resolver; the next run delivers.
    second = _run_scheduler()

    assert len(resolver_calls) == 2, (
        "the second run did not reach recipient resolution -- it suppressed "
        "the alert because the first run stranded its claim: {!r}".format(
            resolver_calls
        )
    )
    _assert_delivered(second, _ledger_rows(store_db), send_recorder["subjects"])