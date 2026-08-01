"""Acceptance tests for early export-readiness visibility and recovery."""
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import app
from app.product_service import Actor, ProductService

client = TestClient(app)
HEADERS = {"X-Tenant-ID": "readiness-team", "X-Role": "admin"}


def parsed(confidence: float = 0.95):
    return SimpleNamespace(
        merchant="Ready Shop", date="2026-08-01", total=42.0, tax=3.0,
        currency="CHF", items=[SimpleNamespace(name="Paper", price=42.0)],
        confidence={key: confidence for key in ("vendor", "date", "total", "tax", "currency")},
    )


def test_receipt_list_exposes_blocked_readiness_and_reasons():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "admin")
    service.create_receipt(actor, parsed(), "ready.png")

    item = service.search_receipts(actor)["items"][0]

    assert item["readiness"]["state"] == "blocked"
    assert item["readiness"]["blocker_count"] == 1
    assert item["readiness"]["issues"][0]["code"] == "missing_cost_center"
    assert item["readiness"]["issues"][0]["field"] == "cost_center"


def test_setting_cost_center_makes_complete_receipt_exportable():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "admin")
    receipt_id = service.create_receipt(actor, parsed(), "ready.png")["receipt_id"]

    service.set_metadata(actor, receipt_id, ["office"], "Launch", "FIN")
    item = service.search_receipts(actor)["items"][0]

    assert item["readiness"] == {"state": "exportable", "blocker_count": 0, "warning_count": 0, "issues": []}


def test_work_queue_includes_export_blocker_after_review_is_complete():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "admin")
    receipt_id = service.create_receipt(actor, parsed(), "ready.png")["receipt_id"]

    queue = service.work_queue(actor)

    blocker = next(item for item in queue["items"] if item["type"] == "export_blocker")
    assert blocker["receipt_id"] == receipt_id
    assert blocker["priority"] == 25
    assert blocker["action_url"] == f"#receipts?receipt={receipt_id}&field=cost_center"
    assert queue["counts"]["export_blocker"] == 1


def test_readiness_is_available_through_receipt_api(monkeypatch):
    from app import product_api

    service = ProductService(":memory:")
    monkeypatch.setattr(product_api, "service", service)
    actor = Actor("readiness-team", "admin")
    service.create_receipt(actor, parsed(), "ready.png")

    response = client.get("/product/receipts?limit=10", headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["items"][0]["readiness"]["state"] == "blocked"


def test_workspace_shows_readiness_column_and_filter_contract():
    html = client.get("/workspace").text
    js = client.get("/assets/workspace.js").text

    assert 'id="readinessFilter"' in html
    assert "Könyvelési állapot" in html
    assert "readinessBadge" in js
    assert "exportable" in js and "blocked" in js


def test_readiness_filter_returns_only_requested_state():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "admin")
    blocked_id = service.create_receipt(actor, parsed(), "blocked.png")["receipt_id"]
    exportable_id = service.create_receipt(actor, parsed(), "exportable.png")["receipt_id"]
    service.set_metadata(actor, exportable_id, [], None, "FIN")

    blocked = service.search_receipts(actor, readiness="blocked")
    exportable = service.search_receipts(actor, readiness="exportable")

    assert [item["receipt_id"] for item in blocked["items"]] == [blocked_id]
    assert [item["receipt_id"] for item in exportable["items"]] == [exportable_id]
