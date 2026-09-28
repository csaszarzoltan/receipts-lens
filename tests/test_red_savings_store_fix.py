"""RED contract for D1.1 — savings-summary reads the wrong store.

``GET /api/v1/analytics/savings-summary`` currently reads the global in-memory
``receipt_store`` (app/savings.py:57 -> app/analytics.py:122) which no /api/v1
write path ever populates. Receipts created via the real write path
(``ProductService.create_receipt`` -> SQLite) are invisible, so tenants that own
receipts see ``total_spent == 0.0`` / ``avg_by_category == {}``.

These tests seed through ``service.create_receipt`` — the production write path —
and assert the literal contract from docs/plans/defect-p1-1-savings-zero-spec.md
section 3. They MUST be RED until app/savings.py is migrated to
``_tenant_receipt_payloads`` (app/consumer_dashboard.py:61).

Unlike tests/test_red_savings_p1.py:30-45, ``_parsed`` here attaches ``category``
to every line item, so seeded receipts land in their real category instead of
``Uncategorized``.
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


def _date_ago(days: int) -> str:
    return (datetime.now(UTC).date() - timedelta(days=days)).isoformat()


def _parsed(merchant: str, total: float, date: str, category: str) -> SimpleNamespace:
    """Parsed-receipt stand-in that CARRIES a category (spec section 4 hazard).

    tests/test_red_savings_p1.py:30-45 omits ``category``; product_service then
    emits ``getattr(i, "category", None) -> None`` and everything collapses into
    ``Uncategorized``.
    """
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
    return service.create_receipt(actor, _parsed(merchant, total, date, category), f"{merchant}.png")[
        "receipt_id"
    ]


def _isolated_client(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, ProductService]:
    """Fresh SQLite product store + cleared in-memory store (no cross-test bleed)."""
    service = ProductService(":memory:")
    monkeypatch.setattr("app.api.service", service)
    monkeypatch.setattr("app.product_api.service", service)
    with receipt_store._lock:
        receipt_store._data.clear()
        receipt_store._tenants.clear()
    return TestClient(app.api.app), service


def _seed_sav_fix(service: ProductService) -> None:
    """SPEC section 3 fixture — tenant ``sav-fix``.

    In the 90d window: A1 10.0/"A" (20d), A2 30.0/"A" (10d), B1 5.0/"B" (5d).
    Out of window: "Old" 999.0/"A" (200d) — must NOT count.

    Distinct merchants keep the RecurringAnalytics half quiet so a failure on the
    category half cannot be masked by top_candidates noise.
    """
    _seed(service, "sav-fix", "ShopA1", 10.0, _date_ago(20), "A")
    _seed(service, "sav-fix", "ShopA2", 30.0, _date_ago(10), "A")
    _seed(service, "sav-fix", "ShopB1", 5.0, _date_ago(5), "B")
    _seed(service, "sav-fix", "ShopOld", 999.0, _date_ago(200), "A")


def _stored_payloads(service: ProductService, tenant: str) -> list[dict[str, Any]]:
    rows = service._db.execute(
        "SELECT payload FROM receipts WHERE tenant_id=?", (tenant,)
    ).fetchall()
    return [json.loads(row["payload"]) for row in rows]


def _numeric_values(node: Any) -> list[float]:
    """Every int/float in a JSON body (bools excluded) — for leak assertions."""
    found: list[float] = []
    if isinstance(node, bool):
        return found
    if isinstance(node, (int, float)):
        return [float(node)]
    if isinstance(node, dict):
        for value in node.values():
            found.extend(_numeric_values(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_numeric_values(item))
    return found


def _assert_fixture_landed(service: ProductService, tenant: str, expected_rows: int) -> None:
    """Precondition: the receipts really are in SQLite with real categories.

    Without this a silent seed failure would be indistinguishable from D1.1.
    """
    payloads = _stored_payloads(service, tenant)
    assert len(payloads) == expected_rows, f"fixture did not persist: {payloads}"
    categories = {item["category"] for p in payloads for item in p["line_items"]}
    assert "Uncategorized" not in categories, f"category lost on write path: {categories}"


def _get(client: TestClient, tenant: str, period: str = "90d") -> dict[str, Any]:
    response = client.get(
        f"/api/v1/analytics/savings-summary?period={period}",
        headers={**HEADERS, "X-Tenant-ID": tenant},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.test_id("TEST-SAVD1-001")
@pytest.mark.requirements("REQ-F2-2")
@pytest.mark.scenario("AC-D1-1")
def test_savings_reads_product_store_categories(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-D1-1 — seeded receipts surface with real categories, 90d window respected."""
    client, service = _isolated_client(monkeypatch)
    _seed_sav_fix(service)
    _assert_fixture_landed(service, "sav-fix", 4)

    body = _get(client, "sav-fix")

    # 10 + 30 + 5 = 45.0 — the 200-day-old 999.0 receipt is outside the 90d window.
    assert body["total_spent"] == 45.0
    assert body["total_spent"] != 1044.0
    assert body["avg_by_category"] == {"A": 20.0, "B": 5.0}
    assert "Uncategorized" not in body["avg_by_category"]


@pytest.mark.test_id("TEST-SAVD1-002")
@pytest.mark.requirements("REQ-F2-2")
@pytest.mark.scenario("AC-D1-2")
def test_savings_potential_saving_literal_arithmetic(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-D1-2 — potential_saving is the literal 20.0, not merely "> 0"."""
    client, service = _isolated_client(monkeypatch)
    _seed_sav_fix(service)
    _assert_fixture_landed(service, "sav-fix", 4)

    body = _get(client, "sav-fix")

    # A: total 40, count 2, avg 20 -> delta 20 (winner)
    # B: total 5,  count 1, avg  5 -> delta  0 (clamp, contributes nothing)
    expected = round(max(0.0, 40.0 - 20.0) + max(0.0, 5.0 - 5.0), 2)
    assert expected == 20.0
    assert body["potential_saving"] == expected
    assert body["potential_saving"] > 0


@pytest.mark.test_id("TEST-SAVD1-003")
@pytest.mark.requirements("REQ-F2-2")
@pytest.mark.scenario("AC-D1-3")
def test_savings_isolates_tenants_across_stores(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-D1-3 — no cross-tenant leak through the migrated category reader."""
    client, service = _isolated_client(monkeypatch)
    _seed_sav_fix(service)
    _seed(service, "sav-other", "Bistro", 200.0, _date_ago(3), "Meals")
    _assert_fixture_landed(service, "sav-fix", 4)
    _assert_fixture_landed(service, "sav-other", 1)

    body_fix = _get(client, "sav-fix")
    assert body_fix["total_spent"] == 45.0
    assert "Meals" not in body_fix["avg_by_category"]
    assert 200.0 not in _numeric_values(body_fix), "sav-other amount leaked into sav-fix body"

    body_other = _get(client, "sav-other")
    assert body_other["total_spent"] == 200.0
    assert "Meals" in body_other["avg_by_category"]
    assert body_other["avg_by_category"]["Meals"] == 200.0


@pytest.mark.test_id("TEST-SAVD1-004")
@pytest.mark.requirements("REQ-F2-2")
@pytest.mark.scenario("AC-D1-4")
def test_savings_empty_tenant_payload_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-D1-4 — zero-receipt tenant keeps the exact 6-key payload (regression guard)."""
    client, service = _isolated_client(monkeypatch)
    assert _stored_payloads(service, "sav-empty") == []

    body = _get(client, "sav-empty")

    assert body == {
        "period": "90d",
        "potential_saving": 0,
        "total_spent": 0,
        "avg_by_category": {},
        "currency": "USD",
        "top_candidates": [],
    }
