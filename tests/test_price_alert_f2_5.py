"""RED contract for F2.5 price-increase email — the idempotency table and the
lying-table gate (AC-PRICE-1, AC-PRICE-2, AC-PRICE-7).

Spec: ``docs/plans/price-alert-spec.md`` (DDL section, idempotency key,
"Ordering — a `sent` row must never be a lie", AC table rows 1 / 2 / 7).
The table, the two methods and the ``if sent:`` write do NOT exist yet, so all
three tests are RED against the current tree.

Three properties this file depends on, all verified in the working tree:

1. THE SENT ROW MUST NOT BE A LIE (``subscription_alerts.py:722``). The row
   and the ``price_emails_sent`` counter are written **only** under ``if
   sent:``. A ``False`` from either silent gate must leave ``COUNT(*) == 0``.
   Asserting only the counter would pass even if the row were written
   unconditionally, so every gate case asserts the row count too.
2. THE CONTROL ARM IS NOT OPTIONAL. A test that only proves "0 counted" is
   vacuous: a scheduler that never attempts any send also counts 0. Each gate
   case is therefore paired with an ``smtp.example.com`` case whose stubbed
   sender returns ``True`` and which MUST reach ``price_emails_sent == 1``
   and write exactly one row. The zero in the gate case is only meaningful
   next to the one in the control case.
3. THE SENDER IS A MODULE GLOBAL. ``daily_scheduler`` calls the bare name
   ``send_email_notification(...)`` (``subscription_alerts.py:719``), so
   ``monkeypatch.setattr`` on the module attribute intercepts the call. The
   *real* function is captured by reference at import time
   (``_REAL_SEND``) so the gate arm bypasses the patch instead of racing it.

An owner member is seeded through the ``app.product_api.service`` singleton
because the trigger resolves the recipient from ``list_members`` (Decision B)
and AC-12 makes 0 owners mean "send nothing" — without a seeded owner the
control arm could not distinguish a real send from a skipped one.

Tolerance is confined to FIXTURE CLEANUP. ``clean_alert_table`` swallows
``no such table`` so the missing table is reported as a FAILED assertion
instead of an ERROR during setup, but the ``_alert_row_count`` used by the
assertions stays strict: it propagates ``sqlite3.OperationalError`` rather
than reporting 0, because every expected count here is 0 and a "return 0 when
absent" helper would make the table's non-existence indistinguishable from a
correctly empty table — the test would go green against a tree that never
created it. A table-less tree must stay RED (002, 003-host-arm, and any 0-row
arm), and a broken COUNT must never read as a pass.

Anti-brittleness: every assertion is on a counter or a row count. No test
reads source text, searches for a marker comment, or compares a string by
distance, so refactoring the message body cannot break them.
"""

from __future__ import annotations

import sqlite3
from typing import Any

import pytest

import app.subscription_alerts as alerts
from app.product_api import Actor
from app.product_api import service as product_service_singleton
from app.product_service import ProductService

# Captured before any monkeypatching: the genuine two-gate implementation.
_REAL_SEND = alerts.send_email_notification

# AC-6 / AC-7 shared input, copied literally from the spec table.
PRICE_HIKE_SUB: dict[str, Any] = {
    "merchant": "Netflix",
    "amount": 19.99,
    "baseline": [15.99],
    "email_alert_enabled": True,
}

# A config the real sender accepts: resolvable host, every field present.
# ``to_addr`` is None on purpose — Decision B lets the trigger override it
# with the household owner, and no gate depends on it.
CFG_OK: dict[str, Any] = {
    "host": "smtp.example.com",
    "port": 587,
    "user": "u",
    "password": "p",
    "from_addr": "u@x.io",
    "to_addr": None,
}

# AC-7 second gate case: "localhost" carries no "." or ":" so the host
# regex gate at subscription_alerts.py:508-512 rejects it. The gate is
# checked BEFORE the RECEIPTLENS_SMTP_ENABLED opt-in (:515-518), so this
# case returns False in any environment.
CFG_BAD_HOST: dict[str, Any] = dict(CFG_OK, host="localhost")

TENANT = "demo"
OWNER_EMAIL = "ac7-owner@example.com"


@pytest.fixture
def seeded_owner():
    """Seed exactly one active owner into the service singleton's ``members``.

    Yields the singleton. The row is removed again on teardown so the
    global ``app.product_api.service`` is not left mutated for other tests.
    """
    actor = Actor(TENANT, "owner")
    product_service_singleton.add_member(actor, OWNER_EMAIL, "owner")
    try:
        yield product_service_singleton
    finally:
        product_service_singleton._db.execute(
            "DELETE FROM members WHERE tenant_id=? AND email=?", (TENANT, OWNER_EMAIL)
        )
        product_service_singleton._db.commit()


@pytest.fixture
def clean_alert_table(seeded_owner):
    """Empty ``price_alert_sent`` before and after each test.

    The table is created by this feature alone, so a full wipe is a
    legitimate isolation move and lets the gate case assert a literal
    ``COUNT(*) == 0`` without depending on test execution order.

    The table does not exist yet — that is the RED this file encodes. The
    wipe therefore tolerates "no such table" rather than raising, so a
    missing table surfaces as a FAILED assertion in the test body instead of
    an ERROR during setup. A setup ERROR would hide the assertion that
    actually matters (that a failed send writes no row) behind a fixture
    crash, and the implementer would never get to see it. Only this
    "no such table" case is swallowed; any other OperationalError re-raises.
    """
    db = seeded_owner._db

    def _wipe() -> None:
        try:
            db.execute("DELETE FROM price_alert_sent")
        except sqlite3.OperationalError as exc:
            if "no such table" not in str(exc):
                raise
        db.commit()

    _wipe()
    yield seeded_owner
    _wipe()


def _alert_row_count(service: ProductService) -> int:
    """Number of rows in the idempotency table.

    Strict on purpose: if the table was never created this raises
    ``sqlite3.OperationalError`` and the test FAILS. Reporting 0 instead
    would be a false pass — every expected count in this file is 0 or 1, and
    0 is exactly what a table-less tree must never be able to claim.
    """
    return service._db.execute("SELECT COUNT(*) FROM price_alert_sent").fetchone()[0]


@pytest.mark.test_id("TEST-PRICEALERT-001")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-PRICE-1")
def test_price_alert_idempotency_key_records_exactly_once():
    """AC-1: the (tenant, merchant, cents, month) key writes one row, ever.

    The first ``record_price_alert_sent`` must report success and flip
    ``has_price_alert_sent`` to True; the second must report False and
    leave the table at exactly one row. The UNIQUE constraint is the only
    thing that can make the repeat a no-op, so the final COUNT is the
    assertion that actually pins the constraint down.
    """
    svc = ProductService(":memory:")

    assert svc.has_price_alert_sent("demo", "Netflix", 1999, "2026-08") is False
    assert svc.record_price_alert_sent("demo", "Netflix", 1999, "2026-08") is True
    assert svc.has_price_alert_sent("demo", "Netflix", 1999, "2026-08") is True
    assert svc.record_price_alert_sent("demo", "Netflix", 1999, "2026-08") is False

    n = svc._db.execute("SELECT COUNT(*) FROM price_alert_sent").fetchone()[0]
    assert n == 1


@pytest.mark.test_id("TEST-PRICEALERT-002")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-PRICE-2")
def test_price_alert_table_creation_is_idempotent_across_instances(tmp_path):
    """AC-2: re-opening one file-backed DB must not re-run the DDL.

    There is no Alembic in this repo, so the inline ``executescript`` uses
    ``CREATE TABLE IF NOT EXISTS``. Constructing a second ProductService over
    the same file must be a silent no-op; a plain CREATE would raise
    ``sqlite3.OperationalError: table price_alert_sent already exists`` here.
    """
    db_path = tmp_path / "price_alert.db"

    first = ProductService(str(db_path))
    assert _alert_row_count(first) == 0

    second = ProductService(str(db_path))
    assert _alert_row_count(second) == 0

    # A third open guards the same property from the other direction: the
    # schema is still intact and still empty after repeated reopen.
    third = ProductService(str(db_path))
    assert _alert_row_count(third) == 0

    for svc in (first, second, third):
        svc._db.close()


@pytest.mark.parametrize(
    ("config", "use_real_sender", "expected_price_emails_sent", "expected_rows"),
    [
        pytest.param(
            CFG_OK,
            False,
            1,
            1,
            id="control-working-smtp-writes-the-row",
        ),
        pytest.param(
            CFG_BAD_HOST,
            True,
            0,
            0,
            id="host-gate-must-not-write-a-row",
        ),
    ],
)
@pytest.mark.test_id("TEST-PRICEALERT-003")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-PRICE-7")
def test_price_alert_row_is_never_written_when_the_send_fails(
    monkeypatch,
    clean_alert_table,
    config,
    use_real_sender,
    expected_price_emails_sent,
    expected_rows,
):
    """AC-7: a ``sent`` row must never be a lie.

    The control arm stubs the sender to return True and demands exactly one
    counted send and one written row — it proves the pipeline is live, so
    the zero in the gate arm is a real suppression and not a dead code path.
    The gate arm hands the config to the REAL ``send_email_notification``,
    which rejects ``host="localhost"`` at subscription_alerts.py:508-512
    before any socket is opened, and demands a counted send of 0 **and** an
    empty table.
    """
    sent_calls: list[tuple[str, str]] = []

    def _stub(subject: str, body: str, *, smtp_config: dict[str, Any] | None = None) -> bool:
        sent_calls.append((subject, body))
        return True

    if use_real_sender:
        # Bypass the patch entirely by calling the captured original.
        assert _REAL_SEND("subject", "body", smtp_config=config) is False
    else:
        monkeypatch.setattr(alerts, "send_email_notification", _stub)

    # The opt-in env gate is irrelevant to the host case (it is checked
    # first) but removing it keeps the control arm honest in a CI image
    # where somebody exported it.
    monkeypatch.delenv("RECEIPTLENS_SMTP_ENABLED", raising=False)

    result = alerts.daily_scheduler(
        smtp_config=config,
        today="2026-08-15",
        subscriptions=[dict(PRICE_HIKE_SUB)],
        tenant=TENANT,
    )

    assert result["subscriptions_checked"] == 1
    # The sub carries no renewal_date, so only the price branch may fire.
    assert result["renewal_emails_sent"] == 0
    assert result["price_emails_sent"] == expected_price_emails_sent
    # The table's absence is itself a failure here: a table-less tree must
    # not be able to satisfy ``expected_rows == 0`` by never existing.
    assert _alert_row_count(clean_alert_table) == expected_rows

    if use_real_sender:
        # The scheduler must have *attempted* the send and been refused;
        # a zero because the branch never ran would not test the gate.
        assert len(sent_calls) == 0
    else:
        assert len(sent_calls) == 1
        assert sent_calls[0][0] == "Price Increase: Netflix"


# ---------------------------------------------------------------------------
# AC-PRICE-6 / AC-PRICE-8 — the LIVE arm and the SUPPRESSION it makes real.
# ---------------------------------------------------------------------------

# The AC-6/AC-8 input. Identical to PRICE_HIKE_SUB plus an explicit
# ``renewal_date``, because the idempotency key's ``period_ym`` is derived
# from the renewal date when one is present (subscription_alerts.py:761) and
# only falls back to the anchor when it is not. Pinning the date pins the key
# to "2026-08" and makes a second run the *same* key, which is exactly the
# re-run AC-8 asks to suppress. A separate constant rather than a mutation of
# PRICE_HIKE_SUB: 003 depends on that dict having NO renewal_date so the
# renewal branch stays inert, and sharing one mutable object would couple them.
#
# 2026-08-14 is weeks in the past relative to the real ``today`` the scheduler
# falls back to, so ``0 <= days_until <= RENEWAL_ALERT_DAYS`` is False forever
# and the renewal branch can never fire — asserted, not assumed, in both tests.
PRICE_HIKE_SUB_RENEWAL: dict[str, Any] = {
    "merchant": "Netflix",
    "amount": 19.99,
    "baseline": [15.99],
    "email_alert_enabled": True,
    "renewal_date": "2026-08-14",
}


@pytest.mark.test_id("TEST-PRICEALERT-004")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-PRICE-6")
def test_price_alert_live_send_counts_one_and_claims_the_key_once(
    monkeypatch,
    clean_alert_table,
    seeded_owner,
):
    """AC-6: a price hike that really is sent counts once and writes one row.

    This is the CONTROL ARM the whole file leans on. It stubs the sender to
    return ``True`` and demands that the pipeline actually move: one counted
    send, exactly one intercepted call, exactly one idempotency row. Only a
    tree that really reaches the send and really claims the key can satisfy
    this — which is what makes the zeros in 003 and 005 mean "suppressed"
    rather than "dead code path".

    The recipient assertion is Decision B: the config handed in carries
    ``to_addr=None``, and the trigger must resolve the household's active
    owner from the service singleton (``seeded_owner``) and put it in the
    config the sender is called with. The expected value is the address the
    existing ``seeded_owner`` fixture seeded — ``OWNER_EMAIL`` — read from
    this module rather than re-typed, so the fixture and the expectation
    cannot drift apart.
    """
    calls: list[tuple[str, str, dict[str, Any]]] = []

    def _stub(
        subject: str, body: str, *, smtp_config: dict[str, Any] | None = None
    ) -> bool:
        calls.append((subject, body, dict(smtp_config or {})))
        return True

    monkeypatch.setattr(alerts, "send_email_notification", _stub)

    result = alerts.daily_scheduler(
        smtp_config=dict(CFG_OK),
        subscriptions=[dict(PRICE_HIKE_SUB_RENEWAL)],
        tenant=TENANT,
    )

    assert result["subscriptions_checked"] == 1
    # The renewal branch stays inert for this input, so every send counted
    # here is the price branch. If this ever trips, the control arm is no
    # longer proving what 003/005 need it to prove.
    assert result["renewal_emails_sent"] == 0
    assert result["price_emails_sent"] == 1

    # The send was attempted exactly once, with this merchant's subject.
    assert len(calls) == 1
    assert calls[0][0] == "Price Increase: Netflix"
    # Decision B: the owner wins over the caller's ``to_addr=None``.
    assert calls[0][2]["to_addr"] == OWNER_EMAIL

    # One row, and it is the row the AC names: the amount in cents and the
    # billing month the renewal date pins. A row written for a different
    # merchant/month would be a claim that never suppresses the real re-run.
    assert _alert_row_count(seeded_owner) == 1
    row = seeded_owner._db.execute(
        "SELECT amount_cents, period_ym FROM price_alert_sent"
    ).fetchone()
    assert (row[0], row[1]) == (1999, "2026-08")


@pytest.mark.test_id("TEST-PRICEALERT-005")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-PRICE-8")
def test_price_alert_second_identical_run_is_suppressed(
    monkeypatch,
    clean_alert_table,
    seeded_owner,
):
    """AC-8: re-running the identical hike sends nothing and claims nothing.

    ORDER IS THE POINT. Run 1 must reach the sender and write its row BEFORE
    run 2's zero is read, otherwise a scheduler that never attempts any send
    would satisfy every assertion below just as happily as a correct one. The
    mid-test ``_alert_row_count == 1`` is the hinge: it proves run 1 really
    claimed the key, so run 2's ``0`` can only come from the gate.

    The final count of 1 is the anti-double-send claim: two rows would mean
    the second run mailed the household twice, which is the exact harm the
    idempotency table exists to prevent.
    """
    calls: list[tuple[str, str, dict[str, Any]]] = []

    def _stub(
        subject: str, body: str, *, smtp_config: dict[str, Any] | None = None
    ) -> bool:
        calls.append((subject, body, dict(smtp_config or {})))
        return True

    monkeypatch.setattr(alerts, "send_email_notification", _stub)

    run1 = alerts.daily_scheduler(
        smtp_config=dict(CFG_OK),
        subscriptions=[dict(PRICE_HIKE_SUB_RENEWAL)],
        tenant=TENANT,
    )

    # Control arm: run 1 is live before anything is suppressed.
    assert run1["price_emails_sent"] == 1
    assert len(calls) == 1
    assert _alert_row_count(seeded_owner) == 1

    # Identical arguments, so an identical (tenant, merchant, cents, month).
    run2 = alerts.daily_scheduler(
        smtp_config=dict(CFG_OK),
        subscriptions=[dict(PRICE_HIKE_SUB_RENEWAL)],
        tenant=TENANT,
    )

    assert run2["price_emails_sent"] == 0
    assert run2["price_alerts_suppressed"] == 1
    # Exactly one, not two: the second run mailed nobody.
    assert _alert_row_count(seeded_owner) == 1
    # The stub was not called a second time — the gate stopped the run
    # before the sender, it did not merely decline to count the send.
    assert len(calls) == 1


@pytest.mark.test_id("TEST-PRICEALERT-006")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-PRICE-4")
def test_one_builder_imports_without_a_cycle():
    """AC-4: one builder, and importing it must not create a cycle.

    subscriptions_api module-level-imports subscription_alerts, so
    the builder lives in subscription_alerts and the API projects it.
    Both imports must succeed in one process, in this order.
    """
    from app.subscription_alerts import build_subscriptions
    import app.subscriptions_api

    assert callable(build_subscriptions)
    assert callable(app.subscriptions_api._build_subscriptions)


@pytest.mark.test_id("TEST-PRICEALERT-007")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-PRICE-13")
def test_cli_exposes_the_subscription_alerts_subcommand(capsys):
    """AC-13: the trigger has a caller.

    ``daily_scheduler`` is otherwise orphaned — nothing in ``app/`` invokes it
    in production, so the price-hike path is only reachable from a test. This
    test pins the CLI entry point that makes the feature callable.

    Convention taken from ``app/cli.py`` rather than assumed: ``main()``
    RETURNS AN EXIT CODE, it never returns help text or a tuple, and it
    catches argparse's ``SystemExit`` itself (cli.py:43-45). So ``--help``
    comes back as ``rc == 0`` with the help body on stdout, and an unknown
    subcommand comes back as ``rc == 2`` with "invalid choice" on stderr —
    hence ``capsys`` instead of inspecting the return value's contents.

    Both arms are behavioural: the first reads the root help listing, the
    second actually dispatches the subcommand. No source-text search, so
    renaming a private helper or re-indenting the parser cannot break it.
    """
    from app.cli import main

    # Arm 1: the subcommand is advertised in the root help listing.
    rc = main(["--help"])
    out = capsys.readouterr()
    assert rc == 0, f"--help should exit 0, got {rc}; stderr={out.err!r}"
    assert "subscription-alerts" in out.out, (
        "app/cli.py does not expose a 'subscription-alerts' subcommand, so "
        f"daily_scheduler has no production caller. Root help was:\n{out.out}"
    )

    # Arm 2: the advertised name is really wired to a subparser. An
    # unimplemented name makes argparse write "invalid choice" to stderr and
    # exit 2; main() converts that SystemExit into a 2 return value.
    rc2 = main(["subscription-alerts", "--help"])
    out2 = capsys.readouterr()
    assert "invalid choice" not in out2.err, (
        "'subscription-alerts' is not a registered subcommand: "
        f"{out2.err.strip()!r}"
    )
    assert rc2 == 0, f"'subscription-alerts --help' should exit 0, got {rc2}"
    assert "subscription-alerts" in out2.out


# ---------------------------------------------------------------------------
# AC-PRICE-9 — THE KEY RE-ARMS. Merchant alone is not the key.
# ---------------------------------------------------------------------------


@pytest.mark.test_id("TEST-PRICEALERT-008")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-PRICE-9")
def test_same_merchant_second_hike_rearms_the_key(
    monkeypatch,
    clean_alert_table,
    seeded_owner,
):
    """AC-9: a second, different hike from the SAME merchant must alert again.

    THE GAP THIS FILE HAS UNTIL NOW. Every other test drives one
    (merchant, amount_cents, period_ym) triple and then repeats THAT triple, so
    a key of ``merchant`` alone — or of ``merchant`` + ``period_ym``, or of
    ``merchant`` + ``amount_cents`` — would satisfy all of them green. The
    suppression in 003/005 is only ever the "same key again" case; nothing
    until now asked whether a *genuinely different* alert for a merchant the
    household has already been told about still goes out. That is the
    headline case in the spec's key definition ("merchant alone is wrong: a
    merchant can hike twice … and merchant-only would suppress the second,
    real alert forever") and it was unverified.

    THREE RUNS, and each one is load-bearing:

    * RUN 1 sends 19.99 and claims (1999, "2026-08"). The control arm —
      without it, a scheduler that never sends anything would satisfy every
      later zero.
    * RUN 2 is the same merchant hiking AGAIN three months later at a
      different price. ``price_emails_sent == 1`` here is THE assertion a
      merchant-only key fails: it has already been told about Netflix, so it
      suppresses a real, new alert. ``price_alerts_suppressed == 0`` says the
      same thing from the other side — the run was not even considered a
      repeat. The two rows are compared AS A LIST, not by COUNT: a table
      holding two rows for the wrong months would pass a count-only check.
    * RUN 3 replays run 2 verbatim and must suppress. A key that never
      re-arms (a per-merchant "alerted once, forever" flag) is the opposite
      failure and only RUN 3 can see it.

    The rows are read with ``ORDER BY alert_id`` so the list is the claim
    order, not SQLite's whim, and the two rows being present *and distinct*
    is the property a merchant-only key cannot fake.

    The owner is seeded by the shared ``seeded_owner`` fixture, exactly as the
    AC-6 control arm (004) does: one active owner in the service singleton,
    removed again on teardown. Nothing is asserted about
    ``renewal_emails_sent`` — each ``renewal_date`` is already past its
    ``today``, but the price branch owns this test either way. Nothing here
    reads source text, and ``detect_price_increase`` is never recomputed: each
    run hands the scheduler a real sub whose baseline genuinely is lower.
    """

    def _stub(
        subject: str, body: str, *, smtp_config: dict[str, Any] | None = None
    ) -> bool:
        return True

    monkeypatch.setattr(alerts, "send_email_notification", _stub)

    def _claimed_keys() -> list[tuple[int, str]]:
        """Every ``(amount_cents, period_ym)`` the table claims, in claim order."""
        return [
            (row[0], row[1])
            for row in seeded_owner._db.execute(
                "SELECT amount_cents, period_ym FROM price_alert_sent ORDER BY alert_id"
            )
        ]

    # --- RUN 1: the first hike, 19.99 billed in 2026-08. ---
    run1 = alerts.daily_scheduler(
        smtp_config=dict(CFG_OK),
        tenant=TENANT,
        today="2026-08-25",
        subscriptions=[
            {
                "merchant": "Netflix",
                "amount": 19.99,
                "baseline": [15.99],
                "renewal_date": "2026-08-20",
                "email_alert_enabled": True,
            }
        ],
    )

    assert run1["price_emails_sent"] == 1
    assert _claimed_keys() == [(1999, "2026-08")]

    # --- RUN 2: same merchant, hikes AGAIN, 29.99 billed in 2026-11. ---
    # A merchant-only (or merchant+month-only) key has already been told about
    # Netflix and suppresses this — the real, new alert the household has
    # never seen.
    run2 = alerts.daily_scheduler(
        smtp_config=dict(CFG_OK),
        tenant=TENANT,
        today="2026-11-25",
        subscriptions=[
            {
                "merchant": "Netflix",
                "amount": 29.99,
                "baseline": [19.99],
                "renewal_date": "2026-11-20",
                "email_alert_enabled": True,
            }
        ],
    )

    assert run2["price_emails_sent"] == 1, (
        "the second, different hike from an already-alerted merchant was "
        "suppressed — the idempotency key is wider than "
        "(tenant, merchant, amount_cents, period_ym)"
    )
    assert run2["price_alerts_suppressed"] == 0
    # The whole list, not a count: both claims must exist and be distinct.
    assert _claimed_keys() == [(1999, "2026-08"), (2999, "2026-11")]

    # --- RUN 3: replay RUN 2 verbatim — now it MUST suppress. ---
    run3 = alerts.daily_scheduler(
        smtp_config=dict(CFG_OK),
        tenant=TENANT,
        today="2026-11-25",
        subscriptions=[
            {
                "merchant": "Netflix",
                "amount": 29.99,
                "baseline": [19.99],
                "renewal_date": "2026-11-20",
                "email_alert_enabled": True,
            }
        ],
    )

    assert run3["price_emails_sent"] == 0
    assert run3["price_alerts_suppressed"] == 1
    assert _claimed_keys() == [(1999, "2026-08"), (2999, "2026-11")]
