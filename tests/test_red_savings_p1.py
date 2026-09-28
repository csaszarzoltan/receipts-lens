"""RED contract for F2.2 savings summary — P1.

GET /api/v1/analytics/savings-summary?period=90d — auth, tenant izolacio,
ures allapot, per-category clamped delta es top_candidates cap/sort.
Endpoint docs/plans/savings-summary-spec.md szerint mukodik.

Minta: tests/test_red_recurring_p0_contract.py — TestClient + dev header
(X-Tenant-ID / X-Role) + nyugta-bevitel ProductService-en keresztul
es receipt_store-en keresztul (SpendingAnalytics).

``potential_saving`` a DECIDED felezes formula szerint mukodik
(docs/plans/potential-saving-formula-spec.md section 1):
``sum(max(0.0, mean(late[c]) - mean(early[c])))`` azokon a kategoriakon,
ahol mindket felben legalabb 2 rekord van. A 90d ablak kozeppontja
``today - 45``, ezert a puszta ``_date_ago(5|10|20)`` fixture-ek egyetlen
felbe esnek es a guard 0.0-t ad — TEST-SAVINGS-P1-004 ezert CELESZULATUL
mindket felre populal.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.api
from app.product_api import Actor
from app.product_service import ProductService
from app.recurring import RecurringAnalytics


def _parsed(merchant: str, total: float, date: str, category: str) -> SimpleNamespace:
    return SimpleNamespace(
        merchant=merchant,
        date=date,
        total=total,
        tax=0.0,
        currency="USD",
        items=[SimpleNamespace(name=merchant, price=total, category=category)],
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
    category: str,
) -> str:
    actor = Actor(tenant, "admin")
    return service.create_receipt(
        actor, _parsed(merchant, total, date, category), f"{merchant}.png"
    )["receipt_id"]


def _isolated_client(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, ProductService]:
    service = ProductService(":memory:")
    monkeypatch.setattr("app.api.service", service)
    monkeypatch.setattr("app.product_api.service", service)
    return TestClient(app.api.app), service


def _date_ago(days: int) -> str:
    return (datetime.now(UTC).date() - timedelta(days=days)).isoformat()


def _stored_payloads(service: ProductService, tenant: str) -> list[dict[str, Any]]:
    rows = service._db.execute(
        "SELECT payload FROM receipts WHERE tenant_id=?", (tenant,)
    ).fetchall()
    return [json.loads(row["payload"]) for row in rows]


def _half_split(service: ProductService, tenant: str) -> tuple[int, int]:
    """(early, late) receipt counts per the spec's exact predicate.

    spec section 1 verbatim: ``is_early(d) = 2 * (d - date_from).days < span``.
    Used as a precondition so a fixture that never straddles the midpoint fails
    loudly instead of returning 0.0 via the count>=2 guard (vacuous green).
    """
    today = datetime.now(UTC).date()
    date_from, date_to = today - timedelta(days=90), today
    span = (date_to - date_from).days
    early = late = 0
    for payload in _stored_payloads(service, tenant):
        day = date.fromisoformat(str(payload["date"]))
        if 2 * (day - date_from).days < span:
            early += 1
        else:
            late += 1
    return early, late


def _assert_half_split(
    service: ProductService, tenant: str, expected_rows: int, expected_early: int, expected_late: int
) -> None:
    payloads = _stored_payloads(service, tenant)
    assert len(payloads) == expected_rows, f"fixture did not persist: {payloads}"
    early, late = _half_split(service, tenant)
    assert (early, late) == (expected_early, expected_late), (
        f"fixture does not straddle the midpoint: early={early} late={late}"
    )


def _body(client: TestClient, tenant: str) -> dict[str, Any]:
    response = client.get(
        "/api/v1/analytics/savings-summary?period=90d",
        headers={"X-Tenant-ID": tenant, "X-Role": "admin"},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.test_id("TEST-SAVINGS-P1-001")
@pytest.mark.requirements("REQ-F2-2")
@pytest.mark.scenario("AC-P1-1")
def test_savings_requires_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _ = _isolated_client(monkeypatch)
    response = client.get("/api/v1/analytics/savings-summary?period=90d")
    assert response.status_code == 401


@pytest.mark.test_id("TEST-SAVINGS-P1-002")
@pytest.mark.requirements("REQ-F2-2")
@pytest.mark.scenario("AC-P1-2")
def test_savings_isolates_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    client, service = _isolated_client(monkeypatch)
    tenant_a = "savings-tenant-a"
    tenant_b = "savings-tenant-b"
    _seed(service, tenant_a, "OfficeMart", 100.0, _date_ago(10), "Office")
    _seed(service, tenant_b, "LunchBox", 200.0, _date_ago(10), "Meals")

    headers_a = {"X-Tenant-ID": tenant_a, "X-Role": "admin"}
    response = client.get("/api/v1/analytics/savings-summary?period=90d", headers=headers_a)
    assert response.status_code == 200
    body = response.json()
    assert body["currency"] == "USD"
    avg_by_cat: dict = body.get("avg_by_category", {})
    assert "Office" in avg_by_cat
    assert "Meals" not in avg_by_cat
    # total_spent must reflect only A's receipts, not B's
    assert body.get("total_spent") == 100.0 or body.get("total_spent") == 100
    assert body.get("total_spent") != 300.0
    # B's data does not leak via any numeric field
    assert body.get("total_spent") != 200.0


@pytest.mark.test_id("TEST-SAVINGS-P1-003")
@pytest.mark.requirements("REQ-F2-2")
@pytest.mark.scenario("AC-P1-3")
def test_savings_empty_household(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _ = _isolated_client(monkeypatch)
    headers = {"X-Tenant-ID": "savings-empty", "X-Role": "admin"}
    response = client.get("/api/v1/analytics/savings-summary?period=90d", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body.get("period") == "90d"
    assert body.get("potential_saving") == 0 or body.get("potential_saving") == 0.0
    assert body.get("total_spent") == 0 or body.get("total_spent") == 0.0
    assert body.get("avg_by_category") == {}
    assert body.get("top_candidates") == []
    assert body.get("currency") == "USD"


@pytest.mark.test_id("TEST-SAVINGS-P1-004")
@pytest.mark.requirements("REQ-F2-2")
@pytest.mark.scenario("AC-P1-4")
def test_savings_clamped_per_category_delta(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-P1-4 — a category whose late mean did not rise contributes literal 0.0.

    The per-category term is ``max(0.0, mean(late[c]) - mean(early[c]))`` and the
    clamp is applied PER CATEGORY, BEFORE the sum (spec section 1). The fixture
    straddles the 45-day midpoint so the 0.0 is a real clamp, not a guard trip.
    """
    client, service = _isolated_client(monkeypatch)
    tenant = "savings-clamp"
    # Groceries: EARLY 10 + 30 => mean 20.0 ; LATE 40 + 40 => mean 40.0 -> +20.0
    _seed(service, tenant, "GroceryE1", 10.0, _date_ago(60), "Groceries")
    _seed(service, tenant, "GroceryE2", 30.0, _date_ago(50), "Groceries")
    _seed(service, tenant, "GroceryL1", 40.0, _date_ago(40), "Groceries")
    _seed(service, tenant, "GroceryL2", 40.0, _date_ago(30), "Groceries")
    # Utilities: flat 5.0 on both sides => mean(late) 5.0 - mean(early) 5.0 = 0.0
    _seed(service, tenant, "UtilityE1", 5.0, _date_ago(70), "Utilities")
    _seed(service, tenant, "UtilityE2", 5.0, _date_ago(55), "Utilities")
    _seed(service, tenant, "UtilityL1", 5.0, _date_ago(35), "Utilities")
    _seed(service, tenant, "UtilityL2", 5.0, _date_ago(25), "Utilities")
    _assert_half_split(service, tenant, 8, 4, 4)

    # Hard-coded contract (NOT re-derived from the same store the endpoint reads,
    # which would be self-fulfilling). Groceries total 120 / count 4 -> avg 30,
    # Utilities total 20 / count 4 -> avg 5.
    # potential_saving is a BARE LITERAL, never re-derived from the formula
    # under test: Groceries early mean 20.0 -> late mean 40.0 = +20.0, and
    # Utilities flat 5.0 -> 5.0 is clamped to 0.0, so the sum is 20.0.
    expected_avg = {"Groceries": 30.0, "Utilities": 5.0}
    expected_total = 140.0

    body = _body(client, tenant)
    assert body.get("avg_by_category") == expected_avg
    assert body.get("total_spent") == expected_total
    assert body["potential_saving"] == 20.0, body

    # --- per-category isolation: Utilities ALONE must contribute 0.0, not be
    # masked by Groceries' 20.0 in the sum.
    util_only = "savings-clamp-utilities"
    for merchant, amount, days_ago in (
        ("SoloUtilE1", 5.0, 70),
        ("SoloUtilE2", 5.0, 55),
        ("SoloUtilL1", 5.0, 35),
        ("SoloUtilL2", 5.0, 25),
    ):
        _seed(service, util_only, merchant, amount, _date_ago(days_ago), "Utilities")
    _assert_half_split(service, util_only, 4, 2, 2)
    util_body = _body(client, util_only)
    assert util_body["avg_by_category"] == {"Utilities": 5.0}
    assert util_body["total_spent"] == 20.0
    assert util_body["potential_saving"] == 0.0

    # --- and Groceries ALONE contributes exactly its own 20.0.
    grocery_only = "savings-clamp-groceries"
    for merchant, amount, days_ago in (
        ("SoloGrocE1", 10.0, 60),
        ("SoloGrocE2", 30.0, 50),
        ("SoloGrocL1", 40.0, 40),
        ("SoloGrocL2", 40.0, 30),
    ):
        _seed(service, grocery_only, merchant, amount, _date_ago(days_ago), "Groceries")
    _assert_half_split(service, grocery_only, 4, 2, 2)
    grocery_body = _body(client, grocery_only)
    assert grocery_body["avg_by_category"] == {"Groceries": 30.0}
    assert grocery_body["total_spent"] == 120.0
    assert grocery_body["potential_saving"] == 20.0
    # The clamp must never leak a negative: Utilities' -0.0 term is 0.0, and a
    # whole-window sum(total - avg) formula would give 120 - 30 = 90.0 here.
    assert grocery_body["potential_saving"] != 90.0
    assert grocery_body["potential_saving"] >= 0.0


@pytest.mark.test_id("TEST-SAVINGS-P1-005")
@pytest.mark.requirements("REQ-F2-2")
@pytest.mark.scenario("AC-P1-5")
def test_savings_top_candidates_cap_and_sort(monkeypatch: pytest.MonkeyPatch) -> None:
    client, service = _isolated_client(monkeypatch)
    tenant = "savings-top"
    empty_tenant = "savings-top-empty"

    # 3 recurring merchants, each 3 occurrences weekly, delta_pct > 0
    # Alpha 10,10,20 => avg 13.33 last 20 pot 6.67
    # Beta  10,10,15 => avg 11.67 last 15 pot 3.33
    # Gamma 10,10,12 => avg 10.67 last 12 pot 1.33
    merchants = [
        ("AlphaMart", [10.0, 10.0, 20.0]),
        ("BetaShop", [10.0, 10.0, 15.0]),
        ("GammaStore", [10.0, 10.0, 12.0]),
    ]
    dates = [_date_ago(21), _date_ago(14), _date_ago(7)]
    for merchant, amounts in merchants:
        for amount, d in zip(amounts, dates, strict=True):
            _seed(service, tenant, merchant, amount, d, "Shopping")

    # Non-empty household: top_candidates <=2, DESC by potential_saving
    headers = {"X-Tenant-ID": tenant, "X-Role": "admin"}
    response = client.get("/api/v1/analytics/savings-summary?period=90d", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body.get("currency") == "USD"
    top = body.get("top_candidates", [])
    assert isinstance(top, list)
    assert len(top) <= 2
    assert len(top) == 2, "expected cap 2 when 3 qualifying merchants exist"
    for entry in top:
        assert "merchant" in entry
        assert "potential_saving" in entry
        assert "delta_pct" in entry
        assert entry["potential_saving"] > 0
        assert entry["delta_pct"] > 0
    # ordered DESC by potential_saving
    assert top[0]["potential_saving"] >= top[1]["potential_saving"]

    # Cross-check ordering matches RecurringAnalytics-derived expectation
    actor = Actor(tenant, "admin")
    recurring = RecurringAnalytics().for_actor(actor, service)
    expected: list[dict] = []
    for item in recurring:
        delta = float(item.get("delta_pct", 0) or 0)
        if delta <= 0:
            continue
        pot = round(max(0.0, float(item.get("last_amount", 0)) - float(item.get("avg_amount", 0))), 2)
        if pot <= 0:
            continue
        expected.append(
            {"merchant": item.get("merchant"), "potential_saving": pot, "delta_pct": item.get("delta_pct")}
        )
    expected.sort(key=lambda x: x["potential_saving"], reverse=True)
    expected = expected[:2]
    # Compare sorted pots and merchants (allow float tolerance)
    assert [e["merchant"] for e in expected] == [t["merchant"] for t in top]
    for e, t in zip(expected, top, strict=True):
        assert e["potential_saving"] == t["potential_saving"]
        assert e["delta_pct"] == t["delta_pct"]

    # Empty household: top_candidates == [], currency still USD
    headers_empty = {"X-Tenant-ID": empty_tenant, "X-Role": "admin"}
    resp_empty = client.get("/api/v1/analytics/savings-summary?period=90d", headers=headers_empty)
    assert resp_empty.status_code == 200
    body_empty = resp_empty.json()
    assert body_empty.get("top_candidates") == []
    assert body_empty.get("currency") == "USD"
