"""TTL expiry-on-conflict for the ``price_alert_sent`` claim.

Shipped code states the hazard plainly (app/product_service.py:319-326): a
claim that is never followed by a successful send is PERMANENT --
``notified_at`` is written at claim time and read nowhere, so a process
killed between the claim INSERT and the send blocks that
(tenant, merchant, amount, period) alert forever.

This module is the gate for the fix: a claim older than
``PRICE_ALERT_CLAIM_TTL_SECONDS`` no longer suppresses the alert. The next
claim for the same key succeeds again (lazy expiry-on-conflict, no reaper),
and ``daily_scheduler`` re-sends instead of counting
``price_alerts_suppressed``.

How these tests are built, and why:

* **Only the transport is patched.** ``claim_price_alert_sent``,
  ``has_price_alert_sent`` and the ``ProductService`` ledger are **real**,
  so what is under test is the production age comparison against a real
  row. The stranded claim is simulated with a SQL ``UPDATE`` of
  ``notified_at`` -- exactly what a dead run leaves behind: a row whose
  timestamp is older than the TTL.
* **The mutex half is asserted, not assumed.** TEST-RL-V02-059 proves a
  fresh claim still returns ``False`` on immediate re-claim: expiry must
  permit re-delivery without breaking the mutual exclusion the
  concurrency suite guards.
* **The consumer line is driven, not the sampler alone.**
  TEST-RL-V02-060 seeds a TTL-expired claim row and runs the real
  ``daily_scheduler`` (app/subscription_alerts.py:948 claim site) with a
  stubbed send, asserting the email goes out. A store-only gate would
  prove the INSERT and leave the suppress-vs-send branch untested.
* **The live database is never written.** Store-level tests use
  ``:memory:``; the scheduler test points the alert store at a temp file
  and asserts the live ledger count is unchanged.

No SMTP and no sockets: ``send_email_notification`` is replaced by a local
fake throughout, so this suite is safe to run anywhere.

Run:
    python -m pytest tests/test_price_alert_ttl.py -q -p no:randomly
"""

import copy
import os
import pathlib
import sqlite3
import threading
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

import app.subscription_alerts as subscription_alerts
from app.product_service import (
    PRICE_ALERT_CLAIM_TTL_SECONDS,
    ProductService,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LIVE_DB = REPO_ROOT / "receiptlens-product.db"

#: Synthetic household. Never the real tenant.
TENANT = "hh-test-ttl-001"
OWNER_EMAIL = "owner@hh-test-ttl-001.invalid"
MERCHANT = "NetStream"

TODAY = "2026-10-02"
#: Far outside ``RENEWAL_ALERT_DAYS`` (7): the renewal branch calls the same
#: ``send_email_notification``, and a renewal firing here would pollute the
#: send counts.
RENEWAL_DATE = "2027-06-01"

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
    "from_addr": "probe@hh-test-ttl-001.invalid",
    "to_addr": "operator@example.invalid",
}

#: (tenant, merchant, amount_cents, period_ym) -- the F2.5 idempotency key.
ALERT_KEY = (TENANT, MERCHANT, 1599, RENEWAL_DATE[:7])

ALERT_SUBJECT = "Price Increase: {}".format(MERCHANT)

_STORE_INIT_LOCK = threading.Lock()


def _backdate(store: ProductService, age: timedelta) -> str:
    """Age the claim row for ``ALERT_KEY`` by *age*; returns the stamp.

    A direct UPDATE on purpose: this is exactly what a stranded claim looks
    like on disk -- a row whose ``notified_at`` predates the TTL -- with no
    fixture shortcut. ``rowcount`` is checked so a silently-vacuous UPDATE
    cannot turn the expiry tests into tests of nothing.
    """
    stamp = (datetime.now(UTC) - age).isoformat()
    with store._lock, store._db:
        cur = store._db.execute(
            "UPDATE price_alert_sent SET notified_at=? "
            "WHERE tenant_id=? AND merchant=? AND amount_cents=? AND period_ym=?",
            (stamp, *ALERT_KEY),
        )
    assert cur.rowcount == 1, (
        "expected to age exactly the claimed row for {}, updated {}".format(
            ALERT_KEY, cur.rowcount
        )
    )
    return stamp


def _build_store(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Throwaway product DB with a seeded owner; point the alert store at it."""
    db_path = tmp_path / "ttl-product.db"

    seeder = ProductService(str(db_path))
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute(
                "INSERT INTO members VALUES(?,?,?,?,1)",
                ("m-ttl-001", TENANT, OWNER_EMAIL, "owner"),
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

    local = threading.local()

    def _price_alert_store() -> ProductService:
        store = getattr(local, "store", None)
        if store is None:
            with _STORE_INIT_LOCK:
                store = ProductService(resolved)
            local.store = store
        return store

    monkeypatch.setattr(subscription_alerts, "_price_alert_store", _price_alert_store)
    monkeypatch.setenv("RECEIPTLENS_PRODUCT_DB", resolved)
    return resolved


def _count_live_ledger_rows() -> int:
    if not LIVE_DB.is_file():
        return 0
    conn = sqlite3.connect(LIVE_DB)
    try:
        return int(conn.execute("SELECT COUNT(*) FROM price_alert_sent").fetchone()[0])
    finally:
        conn.close()


@pytest.fixture
def store_db(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> str:
    return _build_store(tmp_path, monkeypatch)


# ---------------------------------------------------------------------------
# TEST-RL-V02-058 -- an expired claim can be re-claimed (expiry permits)
# ---------------------------------------------------------------------------


@pytest.mark.test_id("TEST-RL-V02-058")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-F25-11: a price_alert_sent claim older than PRICE_ALERT_CLAIM_TTL_SECONDS no longer suppresses: claim -> backdate notified_at past the TTL via SQL UPDATE -> claim_price_alert_sent for the same key returns True again. The UPDATE simulates the stranded claim a run killed between INSERT and send leaves behind.")
def test_expired_claim_can_be_reclaimed() -> None:
    store = ProductService(":memory:")
    try:
        assert store.claim_price_alert_sent(*ALERT_KEY) is True
        _backdate(store, timedelta(seconds=PRICE_ALERT_CLAIM_TTL_SECONDS + 3600))
        assert store.claim_price_alert_sent(*ALERT_KEY) is True, (
            "a claim older than PRICE_ALERT_CLAIM_TTL_SECONDS ({!r}s) must be "
            "re-claimable -- otherwise a stranded claim suppresses the alert "
            "forever".format(PRICE_ALERT_CLAIM_TTL_SECONDS)
        )
    finally:
        store._db.close()


# ---------------------------------------------------------------------------
# TEST-RL-V02-059 -- a fresh claim still suppresses (mutex holds in TTL)
# ---------------------------------------------------------------------------


@pytest.mark.test_id("TEST-RL-V02-059")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-F25-12: a fresh price_alert_sent claim still returns False on immediate re-claim -- expiry must not break the mutual exclusion the concurrency suite guards. Anti-regression half of the TTL gate.")
def test_fresh_claim_still_suppresses() -> None:
    store = ProductService(":memory:")
    try:
        assert store.claim_price_alert_sent(*ALERT_KEY) is True
        assert store.claim_price_alert_sent(*ALERT_KEY) is False, (
            "a fresh claim inside the TTL must still win the mutex -- "
            "expiry that re-arms immediately would double-send"
        )
        assert store.has_price_alert_sent(*ALERT_KEY) is True, (
            "a fresh claim must still read as sent on the existence check"
        )
    finally:
        store._db.close()


# ---------------------------------------------------------------------------
# TEST-RL-V02-060 -- the stranded claim is re-sent by daily_scheduler (AC2)
# ---------------------------------------------------------------------------


@pytest.mark.test_id("TEST-RL-V02-060")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-F25-13: a TTL-expired claim row does not suppress the next daily_scheduler run: with the send stubbed to succeed, the price-hike email goes out (price_emails_sent == 1, price_alerts_suppressed == 0 for the key). Drives the consumer line at app/subscription_alerts.py:948 -- a store-only gate would prove the sampler, not the send.")
def test_stranded_claim_is_resent_by_daily_scheduler(
    store_db: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    live_before = _count_live_ledger_rows()
    sent_subjects: list = []

    def _fake_send(
        subject: str, body: str, *, smtp_config: dict[str, Any] | None = None
    ) -> bool:
        sent_subjects.append(subject)
        return True

    monkeypatch.setattr(subscription_alerts, "send_email_notification", _fake_send)

    # Seed the stranded claim: a won claim row aged past the TTL, exactly
    # what a run killed between INSERT and send leaves behind.
    store = subscription_alerts._price_alert_store()
    assert store.claim_price_alert_sent(*ALERT_KEY) is True
    conn = sqlite3.connect(store_db)
    try:
        stamp = (datetime.now(UTC) - timedelta(
            seconds=PRICE_ALERT_CLAIM_TTL_SECONDS + 3600
        )).isoformat()
        cur = conn.execute(
            "UPDATE price_alert_sent SET notified_at=? "
            "WHERE tenant_id=? AND merchant=? AND amount_cents=? AND period_ym=?",
            (stamp, *ALERT_KEY),
        )
        conn.commit()
        assert cur.rowcount == 1
    finally:
        conn.close()

    summary = subscription_alerts.daily_scheduler(
        smtp_config=copy.deepcopy(SMTP_CONFIG),
        today=TODAY,
        subscriptions=[copy.deepcopy(SUBSCRIPTION)],
        tenant=TENANT,
    )

    assert summary["price_emails_sent"] == 1, (
        "the stranded (TTL-expired) claim suppressed the alert instead of "
        "re-sending it: {}".format(summary)
    )
    assert summary["price_alerts_suppressed"] == 0, (
        "the expired claim counted as a suppression: {}".format(summary)
    )
    assert summary["price_alerts_failed"] == 0, (
        "a healthy transport must not report a failure: {}".format(summary)
    )
    assert sent_subjects == [ALERT_SUBJECT], (
        "expected exactly one delivered alert {!r}, got {!r}".format(
            ALERT_SUBJECT, sent_subjects
        )
    )
    assert _count_live_ledger_rows() == live_before, (
        "the run touched the live product database"
    )
