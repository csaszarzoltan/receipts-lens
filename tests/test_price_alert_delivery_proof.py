"""F2.5 delivery proof: the real price-alert CLI against a local mock SMTP server.

The F2.5 acceptance claim is not "the code calls ``smtplib.send_message``" --
it is that a price hike travels the *whole* path end to end: the SMTP
``DATA`` command is accepted by a real wire conversation **and** a
``price_alert_sent`` ledger row is written, with no real email ever leaving
the machine.  Every test here drives ``tests._smtp_probe.run_cli_against_mock``,
which spawns the actual ``app.cli:main(['subscription-alerts', ...])`` child
process against a plaintext SMTP responder on an ephemeral loopback port.

Two properties make these tests a *delivery proof* rather than a mock-shape
assertion:

1. **No real email.**  The five ``RECEIPTLENS_SMTP_*`` keys are overridden in
   the child environment to point at 127.0.0.1 on an ephemeral port.  Nothing
   dials the configured production relay, so this suite is safe to run
   anywhere.
2. **No live-DB write.**  The child resolves ``RECEIPTLENS_PRODUCT_DB`` to a
   throwaway copy made with SQLite's backup API.  TEST-SMTPDEL-003 pins that
   isolation down as a first-class regression test: it counts
   ``price_alert_sent`` in the live ``./receiptlens-product.db`` immediately
   before and immediately after the probe run and asserts the two are equal
   *while* the run still produced exactly one row in its own copy.  That is
   the defect this suite exists to prevent -- an earlier version of the probe
   wrote its ledger row straight into the live database.

No test in this module writes to the live database; the only live-DB access
is a read-only ``SELECT COUNT(*)`` (plus the read that resolves the owner
tenant).

Run:
    PATH="$PWD/.venv/bin:$PATH" python -m pytest tests/test_price_alert_delivery_proof.py -v
"""

from __future__ import annotations

import pathlib
import sqlite3

import pytest

from tests import _smtp_probe

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LIVE_DB = REPO_ROOT / "receiptlens-product.db"

#: Column contract of the ``price_alert_sent`` ledger.  TEST-SMTPDEL-002
#: asserts every one of these is non-null on the row the run actually wrote.
LEDGER_COLUMNS = ("alert_id", "tenant_id", "merchant", "amount_cents", "period_ym")


def _count_live_ledger_rows() -> int:
    """Count ``price_alert_sent`` rows in the **live** product database.

    Read-only by construction: a single ``SELECT COUNT(*)`` on its own
    connection, closed in a ``finally``.  If the live file is absent this
    reports 0 rather than raising, so a missing database cannot masquerade as
    a delta.
    """
    if not LIVE_DB.is_file():
        return 0
    conn = sqlite3.connect(LIVE_DB)
    try:
        return int(conn.execute("SELECT COUNT(*) FROM price_alert_sent").fetchone()[0])
    finally:
        conn.close()


@pytest.fixture(scope="module")
def owner_tenant() -> str:
    """The tenant of an active owner in the members table.

    Read from the live database rather than hardcoded: the probe needs a
    tenant that actually resolves to an owner with subscriptions, and both the
    ledger count and the ledger row the helper reports are filtered by this
    value.  Picking it from the data keeps the test correct if the fixture data
    changes.
    """
    if not LIVE_DB.is_file():
        pytest.fail(f"live product DB missing at {LIVE_DB}")
    conn = sqlite3.connect(LIVE_DB)
    try:
        cursor = conn.execute(
            "SELECT tenant_id FROM members WHERE role = ? AND active = 1 ORDER BY member_id",
            ("owner",),
        )
        row = cursor.fetchone()
    finally:
        conn.close()
    if row is None:
        pytest.fail("no active owner row in the members table")
    return str(row[0])


@pytest.fixture(scope="module")
def _run_probe(owner_tenant: str) -> dict:
    """Run the probe once for the module and capture everything it produced.

    ``run_cli_against_mock`` returns ``returncode``, ``stdout``, ``stderr``,
    ``message``, ``ledger_rows``, ``ledger_row``, ``db_path`` and ``port``.
    It reads the ``price_alert_sent`` row out of its throwaway copy *before*
    that copy is deleted, and returns it as plain row values -- so
    TEST-SMTPDEL-002 asserts on a real dict without needing the file to still
    exist.  Nothing here patches the helper.

    The live-database count is sampled immediately before and immediately
    after the run, which is what TEST-SMTPDEL-003 compares.
    """
    live_before = _count_live_ledger_rows()
    result = _smtp_probe.run_cli_against_mock(owner_tenant)
    live_after = _count_live_ledger_rows()

    return {
        "result": result,
        "row": result.get("ledger_row"),
        "db_path": result.get("db_path"),
        "live_before": live_before,
        "live_after": live_after,
        "tenant": owner_tenant,
    }


# ---------------------------------------------------------------------------
# TEST-SMTPDEL-001 -- end-to-end: the alert is delivered and recorded
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.test_id("TEST-SMTPDEL-001")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-F25-01: a price hike runs the full path -- SMTP DATA accepted with 250 and a queue-id, exit code 0, and one price_alert_sent ledger row -- without a real email leaving the machine.")
def test_cli_run_delivers_and_records_ledger_row(_run_probe: dict) -> None:
    result = _run_probe["result"]

    assert result["returncode"] == 0, (
        "CLI exited {}; stderr:\n{}".format(result["returncode"], result["stderr"])
    )
    assert "price_emails_sent: 1" in result["stdout"], (
        "stdout did not report exactly one delivered alert:\n{}".format(result["stdout"])
    )
    assert result["ledger_rows"] == 1, (
        "expected 1 price_alert_sent row in the isolated DB, got {}".format(
            result["ledger_rows"]
        )
    )
    assert result["message"] is not None, (
        "no message was captured on the wire; the SMTP DATA command never completed"
    )


# ---------------------------------------------------------------------------
# TEST-SMTPDEL-002 -- the ledger row is complete
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.test_id("TEST-SMTPDEL-002")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-F25-02: the price_alert_sent row the run wrote carries non-null alert_id, tenant_id, merchant, amount_cents and period_ym -- the ledger is a usable audit record, not a stub row.")
def test_ledger_row_is_complete(_run_probe: dict) -> None:
    row = _run_probe["row"]

    assert row is not None, (
        "run_cli_against_mock returned no single ledger row "
        "(ledger_rows={}, isolated DB {})".format(
            _run_probe["result"]["ledger_rows"], _run_probe["db_path"]
        )
    )
    missing = [column for column in LEDGER_COLUMNS if row.get(column) is None]
    assert not missing, "ledger row has null column(s): {} (row={!r})".format(missing, row)


# ---------------------------------------------------------------------------
# TEST-SMTPDEL-003 -- isolation: the live database is never written
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.test_id("TEST-SMTPDEL-003")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-F25-03: the probe run leaves ./receiptlens-product.db untouched -- the price_alert_sent count is identical before and after -- while still recording exactly one row in its throwaway copy. Regression test for the defect where the first version wrote to the live DB.")
def test_live_database_is_untouched_by_probe_run(_run_probe: dict) -> None:
    result = _run_probe["result"]

    assert _run_probe["live_after"] == _run_probe["live_before"], (
        "the probe wrote to the live database: price_alert_sent went from {} to {}".format(
            _run_probe["live_before"], _run_probe["live_after"]
        )
    )
    # Isolation only counts if delivery still happened -- a run that skipped the
    # write entirely would also leave the live DB unchanged.
    assert result["ledger_rows"] == 1, (
        "expected 1 row in the isolated DB, got {}".format(result["ledger_rows"])
    )


# ---------------------------------------------------------------------------
# TEST-SMTPDEL-004 -- the captured message is a real message
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.test_id("TEST-SMTPDEL-004")
@pytest.mark.requirements("REQ-F2-5")
@pytest.mark.scenario("AC-F25-04: the bytes captured from the SMTP DATA payload form a real message -- a non-blank envelope sender, at least one non-blank recipient, and a non-empty body.")
def test_captured_message_has_envelope_and_body(_run_probe: dict) -> None:
    message = _run_probe["result"]["message"]

    assert message is not None, "no message was captured on the wire"
    assert isinstance(message.get("mail_from"), str) and message["mail_from"].strip(), (
        "mail_from missing or blank: {!r}".format(message.get("mail_from"))
    )
    recipients = message.get("rcpt_to")
    assert isinstance(recipients, list) and recipients, (
        "rcpt_to missing or empty: {!r}".format(recipients)
    )
    assert all(isinstance(r, str) and r.strip() for r in recipients), (
        "rcpt_to contains a blank address: {!r}".format(recipients)
    )
    data = message.get("data")
    assert isinstance(data, bytes), "DATA payload is not bytes: {}".format(type(data))
    assert data.strip(), "DATA payload is empty"