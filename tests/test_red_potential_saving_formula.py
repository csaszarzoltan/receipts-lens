"""RED contract for the ``potential_saving`` formula — AC-PS-1 .. AC-PS-5.

Spec: ``docs/plans/potential-saving-formula-spec.md`` section 1 (formula) and
section 4 (acceptance criteria). The formula is DECIDED:

    potential_saving = round(sum(
        max(0.0, mean(late[c]) - mean(early[c]))
        for c in categories
        if len(early[c]) >= 2 and len(late[c]) >= 2), 2)

Three properties the implementation MUST honour, all exercised below:

1. PER LINE ITEM (``app/savings.py:66-68`` shape). A receipt whose
   ``line_items`` are ``[{name, price, category}, ...]`` contributes
   ``price`` to THAT ONE category. A receipt with NO line items contributes
   its payload ``total`` to ``"Uncategorized"``. The whole receipt total is
   NEVER added to every category the receipt touches. Pinned by the
   two-category block in TEST-SAVPS-001 (per-line 60.0 vs whole-total 0.0).
2. HALF SPLIT. ``date_from``/``date_to`` come from ``_period_bounds("90d")``,
   so the window spans 90 days and the midpoint is ``today - 45``. Every
   fixture below straddles the midpoint on purpose, and ``_assert_half_split``
   proves it from the STORED payloads using the spec's own exact predicate: a
   fixture that only populates one half trips the ``count >= 2`` guard and
   silently yields 0.0 for the wrong reason, making the test vacuously green.
3. LITERAL assertions. Each test asserts the exact ``potential_saving`` value
   from the spec (never ``> 0``), so a formula that merely returns "something
   positive" cannot pass.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.api
from app.product_api import Actor
from app.product_service import ProductService
from app.reports import receipt_store

HEADERS = {"X-Role": "admin"}

# ``app/savings.py:_period_bounds("90d")`` -> window [today-90, today], span 90,
# midpoint today-45. Every value below is checked against the exact predicate
# ``2 * (d - date_from).days < span`` in _assert_half_split, never by hand.
EARLY_6 = (80, 70, 60, 55, 50, 48)  # 6 dates, all > 45
LATE_6 = (40, 35, 30, 25, 20, 15)  # 6 dates, all <= 45


def _date_ago(days: int) -> str:
    return (datetime.now(UTC).date() - timedelta(days=days)).isoformat()


def _item(name: str, price: float, category: str | None) -> SimpleNamespace:
    """One line item. ``category=None`` is a REAL uncategorized line item."""
    return SimpleNamespace(name=name, price=price, category=category)


def _parsed(merchant: str, total: float, date: str, items: list[Any]) -> SimpleNamespace:
    """Parsed-receipt stand-in carrying real categories (spec section 1).

    ``items=[]`` produces a payload with ``line_items == []`` — the ONLY shape
    that may fall back to the receipt total under ``"Uncategorized"``.
    """
    return SimpleNamespace(
        merchant=merchant,
        date=date,
        total=total,
        tax=0.0,
        currency="USD",
        items=items,
        confidence={
            "vendor": 0.95,
            "date": 0.95,
            "total": 0.95,
            "tax": 0.95,
            "currency": 0.95,
        },
    )


def _seed(
    service: ProductService,
    tenant: str,
    merchant: str,
    total: float,
    date: str,
    items: list[Any],
) -> str:
    actor = Actor(tenant, "admin")
    return service.create_receipt(actor, _parsed(merchant, total, date, items), f"{merchant}.png")[
        "receipt_id"
    ]


def _seed_single_category(
    service: ProductService,
    tenant: str,
    category: str,
    total: float,
    days_ago: int,
    tag: str = "S",
) -> str:
    """One receipt, ONE line item priced at ``total`` in ``category``.

    The line price equals the receipt total on purpose: for a single-category
    receipt the per-line rule and the whole-total rule are indistinguishable,
    and AC-PS-1..3/5 are about the half split. The per-line rule is pinned
    separately by the two-category block in TEST-SAVPS-001.
    """
    merchant = f"{tag}-{days_ago}d-{total:g}"
    return _seed(
        service,
        tenant,
        merchant,
        total,
        _date_ago(days_ago),
        [_item(f"{merchant}-line", total, category)],
    )


def _isolated_client(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, ProductService]:
    """Fresh SQLite product store + cleared in-memory store (no cross-test bleed)."""
    service = ProductService(":memory:")
    monkeypatch.setattr("app.api.service", service)
    monkeypatch.setattr("app.product_api.service", service)
    with receipt_store._lock:
        receipt_store._data.clear()
        receipt_store._tenants.clear()
    return TestClient(app.api.app), service


def _stored_payloads(service: ProductService, tenant: str) -> list[dict[str, Any]]:
    rows = service._db.execute(
        "SELECT payload FROM receipts WHERE tenant_id=?", (tenant,)
    ).fetchall()
    return [json.loads(row["payload"]) for row in rows]


def _assert_half_split(
    service: ProductService,
    tenant: str,
    expected_rows: int,
    expected_categories: set[str],
    expected_early: int,
    expected_late: int,
) -> None:
    """Precondition, read back from SQLite: the fixture is what the spec assumes.

    Guards against a VACUOUS green. Without this, a silent seed failure — or a
    window that put every receipt in one half — is indistinguishable from a
    correct ``0.0``: both trip the ``count >= 2`` guard and return 0.0. The
    per-half counts are the whole point of each fixture (spec section 1 note on
    the 45-day midpoint), so they are asserted, not assumed.
    """
    payloads = _stored_payloads(service, tenant)
    assert len(payloads) == expected_rows, f"fixture did not persist: {payloads}"

    categories = {
        str(item.get("category") or "Uncategorized")
        for p in payloads
        for item in p["line_items"]
    }
    assert categories == expected_categories, f"categories lost on write path: {categories}"

    today = datetime.now(UTC).date()
    date_from, date_to = today - timedelta(days=90), today
    span = (date_to - date_from).days
    early = late = 0
    for payload in payloads:
        day = datetime.fromisoformat(str(payload["date"])).date()
        assert date_from <= day <= date_to, f"receipt outside the 90d window: {day}"
        # Spec section 1, verbatim: is_early(d) = 2 * (d - date_from).days < span
        if 2 * (day - date_from).days < span:
            early += 1
        else:
            late += 1
    assert early == expected_early, f"expected {expected_early} early receipts, got {early}"
    assert late == expected_late, f"expected {expected_late} late receipts, got {late}"


def _get(client: TestClient, tenant: str, period: str = "90d") -> dict[str, Any]:
    response = client.get(
        f"/api/v1/analytics/savings-summary?period={period}",
        headers={**HEADERS, "X-Tenant-ID": tenant},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.test_id("TEST-SAVPS-001")
@pytest.mark.requirements("REQ-F2-2")
@pytest.mark.scenario("AC-PS-1")
def test_potential_saving_equal_means_across_halves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-PS-1 — 12 receipts @ 20.0, 6 early / 6 late -> literal 0.0.

    Also pins the per-line-item contribution rule on a second tenant, because
    the single-category fixture cannot tell it apart from whole-total.
    """
    client, service = _isolated_client(monkeypatch)

    tenant = "ps-equal"
    for days_ago in EARLY_6:  # 6 EARLY receipts @ 20.0
        _seed_single_category(service, tenant, "Groceries", 20.0, days_ago, "E")
    for days_ago in LATE_6:  # 6 LATE receipts @ 20.0
        _seed_single_category(service, tenant, "Groceries", 20.0, days_ago, "L")
    _assert_half_split(service, tenant, 12, {"Groceries"}, 6, 6)

    body = _get(client, tenant)

    # mean(late) 20.0 - mean(early) 20.0 -> max(0.0, 0.0) -> 0.0. Counts 6/6 clear the guard.
    assert body["potential_saving"] == 0.0
    # A whole-window "sum(total - avg)" formula yields 220.0 here.
    assert body["potential_saving"] != 220.0
    assert body["total_spent"] == 240.0

    # --- per-line-item rule: 80/20 and 20/80 splits of the SAME 100.00 receipts.
    # per-line (correct): Food mean 20 - 80 -> clamp 0 ; Fuel mean 80 - 20 -> 60  => 60.0
    # whole-total (wrong): both means 100 - 100 -> 0.0
    lines_tenant = "ps-lines"
    for days_ago in (80, 70):  # EARLY: 100.00 = 80 Food + 20 Fuel
        _seed(
            service,
            lines_tenant,
            f"MixE-{days_ago}d",
            100.0,
            _date_ago(days_ago),
            [_item("big-food", 80.0, "Food"), _item("small-fuel", 20.0, "Fuel")],
        )
    for days_ago in (40, 30):  # LATE: 100.00 = 20 Food + 80 Fuel
        _seed(
            service,
            lines_tenant,
            f"MixL-{days_ago}d",
            100.0,
            _date_ago(days_ago),
            [_item("small-food", 20.0, "Food"), _item("big-fuel", 80.0, "Fuel")],
        )
    _assert_half_split(service, lines_tenant, 4, {"Food", "Fuel"}, 2, 2)

    lines_body = _get(client, lines_tenant)

    assert lines_body["potential_saving"] == 60.0
    assert lines_body["potential_saving"] != 0.0  # whole-total rule would give 0.0
    # avg_by_category is the WHOLE-window mean per spec section 3, unchanged: 50.0 each.
    assert lines_body["avg_by_category"] == {"Food": 50.0, "Fuel": 50.0}


@pytest.mark.test_id("TEST-SAVPS-002")
@pytest.mark.requirements("REQ-F2-2")
@pytest.mark.scenario("AC-PS-2")
def test_potential_saving_late_minus_early_is_literal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-PS-2 — early @ 20.0 (3) / late @ 40.0 (3) -> literal 20.0, not "> 0"."""
    client, service = _isolated_client(monkeypatch)
    tenant = "ps-rise"
    for days_ago in (80, 70, 60):  # 3 EARLY receipts @ 20.0
        _seed_single_category(service, tenant, "Groceries", 20.0, days_ago, "E")
    for days_ago in (40, 30, 20):  # 3 LATE receipts @ 40.0
        _seed_single_category(service, tenant, "Groceries", 40.0, days_ago, "L")
    _assert_half_split(service, tenant, 6, {"Groceries"}, 3, 3)

    body = _get(client, tenant)

    # mean(late) 40.0 - mean(early) 20.0 -> 20.0. Both halves clear count>=2.
    assert body["potential_saving"] == 20.0
    # A whole-window formula would give 180 - 30 = 150.0.
    assert body["potential_saving"] != 150.0
    assert body["total_spent"] == 180.0


@pytest.mark.test_id("TEST-SAVPS-003")
@pytest.mark.requirements("REQ-F2-2")
@pytest.mark.scenario("AC-PS-3")
def test_potential_saving_single_receipt_hits_count_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-PS-3 — ONE receipt @ 250.0 -> literal 0.0 via the count>=2 guard, not 125.0."""
    client, service = _isolated_client(monkeypatch)
    tenant = "ps-single"
    _seed_single_category(service, tenant, "Electronics", 250.0, 10, "Solo")
    _assert_half_split(service, tenant, 1, {"Electronics"}, 0, 1)

    body = _get(client, tenant)

    # Only the LATE half is populated -> len(early) == 0 < 2 -> guard -> 0.0.
    assert body["potential_saving"] == 0.0
    assert body["potential_saving"] != 125.0
    # The receipt is genuinely visible, so 0.0 is the guard and not an empty read.
    assert body["avg_by_category"] == {"Electronics": 250.0}
    assert body["total_spent"] == 250.0


@pytest.mark.test_id("TEST-SAVPS-004")
@pytest.mark.requirements("REQ-F2-2")
@pytest.mark.scenario("AC-PS-4")
def test_potential_saving_empty_tenant_six_key_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-PS-4 — empty tenant -> the exact 6-key all-zero payload, HTTP 200."""
    client, service = _isolated_client(monkeypatch)
    assert _stored_payloads(service, "ps-empty") == []

    body = _get(client, "ps-empty")

    # Full-dict equality: the new formula must NOT add a 7th key (spec section 3).
    assert body == {
        "period": "90d",
        "potential_saving": 0,
        "total_spent": 0,
        "avg_by_category": {},
        "currency": "USD",
        "top_candidates": [],
    }
    assert body["potential_saving"] == 0


@pytest.mark.test_id("TEST-SAVPS-005")
@pytest.mark.requirements("REQ-F2-2")
@pytest.mark.scenario("AC-PS-5")
def test_potential_saving_decrease_is_clamped_to_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-PS-5 — early @ 40.0 (2) / late @ 20.0 (2) -> literal 0.0, never negative."""
    client, service = _isolated_client(monkeypatch)
    tenant = "ps-fall"
    for days_ago in (80, 70):  # 2 EARLY receipts @ 40.0
        _seed_single_category(service, tenant, "Utilities", 40.0, days_ago, "E")
    for days_ago in (40, 30):  # 2 LATE receipts @ 20.0
        _seed_single_category(service, tenant, "Utilities", 20.0, days_ago, "L")
    _assert_half_split(service, tenant, 4, {"Utilities"}, 2, 2)

    body = _get(client, tenant)

    # mean(late) 20.0 - mean(early) 40.0 = -20.0 -> max(0.0, ...) -> 0.0.
    assert body["potential_saving"] == 0.0
    assert body["potential_saving"] >= 0
    # A whole-window formula would give 120 - 30 = 90.0.
    assert body["potential_saving"] != 90.0
    assert body["total_spent"] == 120.0
