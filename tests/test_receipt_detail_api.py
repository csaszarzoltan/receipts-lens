"""Regression tests for GET /product/receipts/{receipt_id} (detail-page fix F1).

The ReceiptLens receipt detail page used to fetch the first 200 receipts via
search and find the target client-side, which broke for any receipt beyond
that cap (pagination pages 5+, deep links). These tests pin the direct
single-receipt endpoint that replaced the workaround.
"""
from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import app
from app.product_service import Actor, ProductService

client = TestClient(app)
HEADERS = {"X-Tenant-ID": "detail-team", "X-Role": "admin"}


def parsed(confidence: float = 0.95) -> SimpleNamespace:
    return SimpleNamespace(
        merchant="Detail Shop", date="2026-08-01", total=42.0, tax=3.0,
        currency="CHF", items=[SimpleNamespace(name="Paper", price=42.0)],
        confidence={key: confidence
                    for key in ("vendor", "date", "total", "tax", "currency")},
    )


def test_get_receipt_returns_single_item(monkeypatch) -> None:
    service = ProductService(":memory:")
    monkeypatch.setattr("app.product_api.service", service)
    actor = Actor("detail-team", "admin")
    receipt_id = service.create_receipt(actor, parsed(), "detail.png")["receipt_id"]

    response = client.get(f"/product/receipts/{receipt_id}", headers=HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["receipt_id"] == receipt_id
    assert body["receipt"]["vendor"] == "Detail Shop"
    assert body["status"] in {"needs_review", "completed"}
    assert body["version"] == 1
    assert body["metadata"] == {"tags": [], "project": None, "cost_center": None}
    assert "readiness" in body


def test_get_receipt_404_when_missing(monkeypatch) -> None:
    service = ProductService(":memory:")
    monkeypatch.setattr("app.product_api.service", service)

    response = client.get("/product/receipts/does-not-exist", headers=HEADERS)

    assert response.status_code == 404


def test_get_receipt_is_tenant_isolated(monkeypatch) -> None:
    service = ProductService(":memory:")
    monkeypatch.setattr("app.product_api.service", service)
    actor_a = Actor("tenant-a", "admin")
    receipt_id = service.create_receipt(actor_a, parsed(), "a.png")["receipt_id"]

    response = client.get(
        f"/product/receipts/{receipt_id}",
        headers={"X-Tenant-ID": "tenant-b", "X-Role": "admin"},
    )

    assert response.status_code == 404


def test_get_receipt_reaches_receipts_beyond_first_200(monkeypatch) -> None:
    """Regression: a receipt outside the search limit=200 cap is still reachable."""
    service = ProductService(":memory:")
    monkeypatch.setattr("app.product_api.service", service)
    actor = Actor("detail-team", "admin")
    ids = [service.create_receipt(actor, parsed(), f"{i}.png")["receipt_id"]
           for i in range(205)]

    search = service.search_receipts(actor, limit=200)
    assert len(search["items"]) == 200
    visible = {item["receipt_id"] for item in search["items"]}
    beyond = next(rid for rid in ids if rid not in visible)
    assert beyond not in visible  # exactly the failing case for the old workaround

    response = client.get(f"/product/receipts/{beyond}", headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["receipt_id"] == beyond
