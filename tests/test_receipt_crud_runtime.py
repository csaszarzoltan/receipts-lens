"""Runtime acceptance tests for the public receipt CRUD endpoints."""
from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api import app
from app.ocr import ConfidenceReceipt, ReceiptItem
from app.reports import ReceiptStore


def _receipt() -> ConfidenceReceipt:
    return ConfidenceReceipt(
        merchant="Test Shop",
        date="2026-07-29",
        items=[ReceiptItem(name="Coffee", price=5.5)],
        total=5.5,
        tax=0.5,
        currency="USD",
        raw_text="TEST SHOP",
        confidence={"merchant": 0.9, "total": 0.95},
    )


def test_store_list_all_and_get_are_thread_safe_contract() -> None:
    store = ReceiptStore()
    receipt_id = store.store(_receipt())
    assert store.get(receipt_id) is not None
    assert store.list_all() == [(receipt_id, store.get(receipt_id))]


def test_receipt_routes_create_list_and_get() -> None:
    client = TestClient(app)
    headers = {"X-Tenant-ID": "crud", "X-Role": "admin"}
    with patch("app.api.fetch_image_bytes", return_value=b"image"), patch(
        "app.api.parse_receipt_with_confidence", return_value=_receipt()
    ):
        created = client.post(
            "/api/v1/receipts", headers=headers, json={"image_url": "https://example.com/r.png"}
        )
    assert created.status_code == 201
    receipt_id = created.json()["receipt_id"]

    listed = client.get("/api/v1/receipts", headers=headers)
    assert listed.status_code == 200
    assert any(item["receipt_id"] == receipt_id for item in listed.json()["receipts"])

    fetched = client.get(f"/api/v1/receipts/{receipt_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["vendor"] == "Test Shop"


def test_get_unknown_receipt_returns_404() -> None:
    headers = {"X-Tenant-ID": "crud", "X-Role": "admin"}
    response = TestClient(app).get("/api/v1/receipts/missing", headers=headers)
    assert response.status_code == 404
