"""TDD acceptance coverage for day-to-day workflow improvements."""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.product_service import Actor, ProductConflict, ProductService

client = TestClient(app)
HEADERS = {"X-Tenant-ID": "workflow-tdd", "X-Role": "admin"}


def parsed(confidence: float = 0.4):
    return SimpleNamespace(
        merchant="Daily Shop",
        date="2026-08-01",
        total=20.0,
        tax=1.5,
        currency="CHF",
        items=[SimpleNamespace(name="Paper", price=20.0)],
        confidence={
            "vendor": confidence,
            "date": confidence,
            "total": confidence,
            "tax": confidence,
            "currency": confidence,
        },
    )


def test_atomic_workspace_update_commits_fields_line_items_and_metadata_together():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "reviewer")
    receipt_id = service.create_receipt(actor, parsed(), "daily.png")["receipt_id"]

    result = service.update_receipt_workspace(
        actor,
        receipt_id,
        expected_version=1,
        fields={"vendor": "Daily Shop AG", "total": 24.5},
        line_items=[{"name": "Paper", "quantity": 1, "unit_price": 24.5, "amount": 24.5}],
        metadata={"tags": ["office"], "project": "Launch", "cost_center": "FIN"},
        complete=True,
    )

    assert result["version"] == 2
    assert result["status"] == "completed"
    assert result["receipt"]["vendor"] == "Daily Shop AG"
    assert result["receipt"]["line_items"][0]["amount"] == 24.5
    assert result["metadata"] == {"tags": ["office"], "project": "Launch", "cost_center": "FIN"}


def test_atomic_workspace_update_rolls_back_everything_on_invalid_line_item():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "reviewer")
    receipt_id = service.create_receipt(actor, parsed(), "daily.png")["receipt_id"]

    with pytest.raises(ValueError, match="line item"):
        service.update_receipt_workspace(
            actor,
            receipt_id,
            expected_version=1,
            fields={"vendor": "Should Not Persist"},
            line_items=[{"name": "", "quantity": 1, "unit_price": 5, "amount": 5}],
            metadata={"tags": ["bad"], "project": "Bad", "cost_center": "BAD"},
            complete=True,
        )

    item = service.search_receipts(actor)["items"][0]
    assert item["version"] == 1
    assert item["receipt"]["vendor"] == "Daily Shop"
    assert item["metadata"] == {"tags": [], "project": None, "cost_center": None}


def test_atomic_workspace_update_rejects_stale_version():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "reviewer")
    receipt_id = service.create_receipt(actor, parsed(), "daily.png")["receipt_id"]
    with pytest.raises(ProductConflict):
        service.update_receipt_workspace(
            actor, receipt_id, expected_version=99,
            fields={"total": 22}, line_items=None, metadata=None, complete=False,
        )


def test_work_queue_prioritizes_failures_and_explains_required_action():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "admin")
    first = service.create_receipt(actor, parsed(), "review.png")
    second = service.create_receipt(actor, parsed(), "failed.png")
    with service._db:
        service._db.execute(
            "UPDATE jobs SET status='failed', error='OCR timeout' WHERE job_id=?",
            (second["job_id"],),
        )

    queue = service.work_queue(actor)

    assert queue["total"] >= 2
    assert queue["items"][0]["type"] == "failed_job"
    assert queue["items"][0]["priority"] < queue["items"][1]["priority"]
    assert all(item["reason"] and item["action_url"] for item in queue["items"])
    assert any(item["type"] == "review" and item["receipt_id"] == first["receipt_id"] for item in queue["items"])


def test_work_queue_endpoint_and_atomic_workspace_endpoint_are_available(monkeypatch):
    from app import product_api

    service = ProductService(":memory:")
    monkeypatch.setattr(product_api, "service", service)
    monkeypatch.setattr(product_api.accounting, "service", service)
    monkeypatch.setattr(product_api.accounting, "db", service._db)
    monkeypatch.setattr(product_api.advanced, "service", service)
    monkeypatch.setattr(product_api.advanced, "db", service._db)

    actor = Actor("workflow-tdd", "admin")
    receipt_id = service.create_receipt(actor, parsed(), "daily.png")["receipt_id"]

    queue = client.get("/product/work-queue", headers=HEADERS)
    assert queue.status_code == 200
    assert queue.json()["items"][0]["type"] == "review"

    updated = client.patch(
        f"/product/receipts/{receipt_id}/workspace",
        headers={**HEADERS, "If-Match": "1", "Idempotency-Key": "daily-update-1"},
        json={
            "fields": {"total": 25.0},
            "line_items": [{"name": "Paper", "quantity": 1, "unit_price": 25, "amount": 25}],
            "metadata": {"tags": ["office"], "project": "Launch", "cost_center": "FIN"},
            "action": "complete",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["version"] == 2
    assert client.get("/product/work-queue", headers=HEADERS).json()["total"] == 0
