"""RED contract for F2.1 recurring spend — P0 (weekly).

GET /api/v1/analytics/recurring?period=90d — auth, tenant izolacio,
ures allapot es heti ismetlodes. Az endpoint MOST NEM letezik,
ezert mind a 4 teszt RED (varhatoan FAIL).

Minta: tests/test_unprotected_routes.py — TestClient + dev header
(X-Tenant-ID / X-Role) + nyugta-bevitel ProductService-en keresztul.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.api
from app.product_api import Actor
from app.product_service import ProductService


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
    return TestClient(app.api.app), service


@pytest.mark.test_id("TEST-RECUR-P0-001")
@pytest.mark.requirements("REQ-F2-1")
@pytest.mark.scenario("AC-F2-1")
def test_recurring_requires_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _ = _isolated_client(monkeypatch)
    response = client.get("/api/v1/analytics/recurring?period=90d")
    assert response.status_code == 401


@pytest.mark.test_id("TEST-RECUR-P0-002")
@pytest.mark.requirements("REQ-F2-1")
@pytest.mark.scenario("AC-F2-1")
def test_recurring_isolates_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    client, service = _isolated_client(monkeypatch)
    _seed(service, "recur-tenant-a", "Tesco", 10.0, "2026-09-10")
    _seed(service, "recur-tenant-b", "Lidl", 20.0, "2026-09-11")

    headers_a = {"X-Tenant-ID": "recur-tenant-a", "X-Role": "admin"}
    response = client.get("/api/v1/analytics/recurring?period=90d", headers=headers_a)
    assert response.status_code == 200
    body = response.json()
    merchants = [item["merchant"] for item in body.get("items", [])]
    assert "Tesco" in merchants
    assert "Lidl" not in merchants


@pytest.mark.test_id("TEST-RECUR-P0-003")
@pytest.mark.requirements("REQ-F2-1")
@pytest.mark.scenario("AC-F2-1")
def test_recurring_empty_household(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _ = _isolated_client(monkeypatch)
    headers = {"X-Tenant-ID": "recur-empty", "X-Role": "admin"}
    response = client.get("/api/v1/analytics/recurring?period=90d", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"items": []} or response.json().get("items") == []


@pytest.mark.test_id("TEST-RECUR-P0-004")
@pytest.mark.requirements("REQ-F2-1")
@pytest.mark.scenario("AC-F2-1")
def test_recurring_detects_weekly_merchant(monkeypatch: pytest.MonkeyPatch) -> None:
    client, service = _isolated_client(monkeypatch)
    tenant = "recur-weekly"
    for day in ("2026-09-01", "2026-09-08", "2026-09-15", "2026-09-22"):
        _seed(service, tenant, "Tesco", 10.0, day)

    headers = {"X-Tenant-ID": tenant, "X-Role": "admin"}
    response = client.get("/api/v1/analytics/recurring?period=90d", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["items"], "weekly merchant not detected"
    first = body["items"][0]
    assert first["merchant"] == "Tesco"
    assert first["occurrences"] >= 3
    assert first["frequency"] == "weekly"
