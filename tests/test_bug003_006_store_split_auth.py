"""Regression tests for BUG-003 / BUG-006 (test report 2026-08-11).

BUG-003: /api/v1/receipts and /product/* used two different stores — a receipt
         uploaded through one namespace was invisible (404) in the other.
         Expected: both namespaces read/write the same product store.
BUG-006: /api/v1/receipts answered 200 without auth headers and accepted
         unknown roles.  Expected: missing header -> 401, unknown role -> 403
         (matching /product/* behaviour).
"""
from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api import app
from app.ocr import ConfidenceReceipt, ReceiptItem
from app.product_api import service

client = TestClient(app)
AUTH = {"X-Tenant-ID": "bug003", "X-Role": "admin"}


def _receipt() -> ConfidenceReceipt:
    return ConfidenceReceipt(
        merchant="Shared Shop",
        date="2026-08-01",
        items=[ReceiptItem(name="Coffee", price=5.5)],
        total=5.5,
        tax=0.5,
        currency="USD",
        raw_text="SHARED SHOP",
        confidence={"merchant": 0.9, "total": 0.95},
    )


def test_bug003_upload_via_product_is_listed_via_api_v1() -> None:
    """A receipt uploaded through /product/* must appear in /api/v1/receipts."""
    with patch("app.product_api.parse_receipt_with_confidence", return_value=_receipt()):
        created = client.post(
            "/product/receipts/upload",
            headers=AUTH,
            files={"file": ("r.png", b"image", "image/png")},
        )
    assert created.status_code == 201
    receipt_id = created.json()["receipt_id"]

    listed = client.get("/api/v1/receipts", headers=AUTH).json()["receipts"]
    ids = [item["receipt_id"] for item in listed]
    assert receipt_id in ids, "upload via /product/* missing from /api/v1/receipts"

    fetched = client.get(f"/api/v1/receipts/{receipt_id}", headers=AUTH)
    assert fetched.status_code == 200
    assert fetched.json()["vendor"] == "Shared Shop"


def test_bug003_upload_via_api_v1_is_listed_via_product() -> None:
    """A receipt created through /api/v1/receipts must appear in /product/receipts."""
    with patch("app.api.fetch_image_bytes", return_value=b"image"), patch(
        "app.api.parse_receipt_with_confidence", return_value=_receipt()
    ):
        created = client.post("/api/v1/receipts", headers=AUTH, json={"image_url": "https://example.com/r.png"})
    assert created.status_code == 201
    receipt_id = created.json()["receipt_id"]

    search = client.get("/product/receipts", headers=AUTH).json()
    assert any(item["receipt_id"] == receipt_id for item in search["items"]), (
        "upload via /api/v1/receipts missing from /product/receipts"
    )


def test_bug006_missing_tenant_header_returns_401() -> None:
    assert client.get("/api/v1/receipts").status_code == 401
    assert client.get("/api/v1/receipts/some-id").status_code == 401
    with patch("app.api.fetch_image_bytes", return_value=b"image"), patch(
        "app.api.parse_receipt_with_confidence", return_value=_receipt()
    ):
        resp = client.post("/api/v1/receipts", json={"image_url": "https://example.com/r.png"})
    assert resp.status_code == 401


def test_bug006_unknown_role_returns_403() -> None:
    headers = {"X-Tenant-ID": "bug003", "X-Role": "superuser"}
    assert client.get("/api/v1/receipts", headers=headers).status_code == 403
    assert client.get("/api/v1/receipts/some-id", headers=headers).status_code == 403
