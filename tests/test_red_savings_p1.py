"""RED contract for F2.2 savings summary — P1.

GET /api/v1/analytics/savings-summary?period=90d — auth, tenant izolacio,
ures allapot, per-category clamped delta es top_candidates cap/sort.
Endpoint docs/plans/savings-summary-spec.md szerint mukodik.

Minta: tests/test_red_recurring_p0_contract.py — TestClient + dev header
(X-Tenant-ID / X-Role) + nyugta-bevitel ProductService-en keresztul
es receipt_store-en keresztul (SpendingAnalytics).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.api
from app.analytics import spending_analytics
from app.ocr import ConfidenceReceipt, ReceiptItem
from app.product_api import Actor
from app.product_service import ProductService
from app.recurring import RecurringAnalytics
from app.reports import receipt_store
from app.savings import _period_bounds


def _parsed(merchant: str, total: float, date: str) -> SimpleNamespace:
    return SimpleNamespace(
        merchant=merchant,
        date=date,
        total=total,
        tax=0.0,
        currency="USD",
        items=[SimpleNamespace(name=merchant, price=total)],
        confidence={
            "vendor": 0.95,
            "date": 0.95,
            "total": 0.95,
            "tax": 0.95,
            "currency": 0.95,
        },
    )


def _seed(service: ProductService, tenant: str, merchant: str, total: float, date: str) -> str:
    actor = Actor(tenant, "admin")
    return service.create_receipt(actor, _parsed(merchant, total, date), f"{merchant}.png")[
        "receipt_id"
    ]


def _isolated_client(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, ProductService]:
    service = ProductService(":memory:")
    monkeypatch.setattr("app.api.service", service)
    monkeypatch.setattr("app.product_api.service", service)
    with receipt_store._lock:
        receipt_store._data.clear()
        receipt_store._tenants.clear()
    return TestClient(app.api.app), service


def _date_ago(days: int) -> str:
    return (datetime.now(UTC).date() - timedelta(days=days)).isoformat()


def _store_receipt(
    tenant: str,
    merchant: str,
    date: str,
    items: list[tuple[str, float, str]],
) -> str:
    receipt = ConfidenceReceipt(
        merchant=merchant,
        date=date,
        items=[ReceiptItem(name=n, price=p, category=c) for n, p, c in items],
        total=sum(p for _, p, _ in items),
        tax=0.0,
        currency="USD",
        raw_text="",
        confidence={},
    )
    return receipt_store.store(receipt, tenant_id=tenant)


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
    client, _ = _isolated_client(monkeypatch)
    tenant_a = "savings-tenant-a"
    tenant_b = "savings-tenant-b"
    _store_receipt(tenant_a, "OfficeMart", _date_ago(10), [("Desk", 100.0, "Office")])
    _store_receipt(tenant_b, "LunchBox", _date_ago(10), [("Lunch", 200.0, "Meals")])

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
    client, service = _isolated_client(monkeypatch)
    tenant = "savings-clamp"
    # Groceries: 10 + 30 => total 40 avg 20 delta 20 (winner)
    # Utilities: 5 => total 5 avg 5 delta 0 (loser, contributes 0)
    _store_receipt(tenant, "GroceryA", _date_ago(20), [("Milk", 10.0, "Groceries")])
    _store_receipt(tenant, "GroceryB", _date_ago(10), [("Milk", 30.0, "Groceries")])
    _store_receipt(tenant, "UtilityC", _date_ago(5), [("Cable", 5.0, "Utilities")])

    # Expected values sourced from SpendingAnalytics.by_category (not re-derived)
    date_from, date_to = _period_bounds("90d")
    cat = spending_analytics.by_category(date_from, date_to, tenant_id=tenant)
    groups = cat.get("groups", [])
    expected_avg = {g["key"]: g["avg"] for g in groups}
    expected_total = float(cat.get("total_spent", 0.0))
    expected_potential = round(sum(max(0.0, float(g["total"]) - float(g["avg"])) for g in groups), 2)

    # winner / loser logic explicitly: loser contributes 0
    groceries_total = next((g["total"] for g in groups if g["key"] == "Groceries"), 0)
    groceries_avg = next((g["avg"] for g in groups if g["key"] == "Groceries"), 0)
    utilities_total = next((g["total"] for g in groups if g["key"] == "Utilities"), 0)
    utilities_avg = next((g["avg"] for g in groups if g["key"] == "Utilities"), 0)
    assert groceries_total > groceries_avg
    assert utilities_total == utilities_avg  # loser delta 0, clamped
    assert expected_potential == round(max(0.0, float(groceries_total - groceries_avg)), 2)

    _ = service  # product store not needed for category delta; silence linter
    headers = {"X-Tenant-ID": tenant, "X-Role": "admin"}
    response = client.get("/api/v1/analytics/savings-summary?period=90d", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body.get("avg_by_category") == expected_avg
    assert body.get("total_spent") == expected_total
    assert body.get("potential_saving") == expected_potential


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
            _seed(service, tenant, merchant, amount, d)

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
