"""POST /product/receipts/upload tells the caller when the same file was uploaded before (I10)."""
from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api import app
from app.ocr import ConfidenceReceipt

client = TestClient(app)


def _post(tenant: str, content: bytes) -> dict:
    parsed = ConfidenceReceipt(
        merchant="Shop", date="2026-10-01", items=[], total=None, tax=None, currency="CHF",
        raw_text="", confidence={"merchant": 0.9, "total": 0.0}, currency_source="marker",
    )
    with patch("app.product_api.parse_receipt_with_confidence", return_value=parsed):
        response = client.post("/product/receipts/upload",
                               headers={"X-Tenant-ID": tenant, "X-Role": "admin"},
                               files={"file": ("r.png", content, "image/png")})
    assert response.status_code == 201, response.text
    return response.json()


def test_second_upload_of_identical_bytes_returns_duplicate_of():
    first = _post("same-file-a", b"image-bytes")
    second = _post("same-file-a", b"image-bytes")
    assert first["duplicate_of"] is None
    assert second["duplicate_of"] == first["receipt_id"]


def test_different_bytes_and_other_tenants_get_no_match():
    _post("same-file-b", b"image-bytes")
    assert _post("same-file-b", b"other-bytes")["duplicate_of"] is None
    assert _post("same-file-c", b"image-bytes")["duplicate_of"] is None
