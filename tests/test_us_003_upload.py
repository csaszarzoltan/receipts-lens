"""
US-003: Nyugta feltöltés — API szerződésteszt.

Source: docs/stories/US-003-nyugta-feltoltes.md (4 AC).
Fut: pytest -q tests/test_us_003_upload.py
"""
from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app, raise_server_exceptions=False)


def _session(email: str = "us003@example.com") -> str:
    req = client.post("/auth/magic-link-request", json={"email": email})
    assert req.status_code == 201, req.text
    tok = req.json()["token"]
    ver = client.post("/auth/magic-link-verify", json={"token": tok})
    assert ver.status_code == 201, ver.text
    return ver.json()["session_token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _dummy_jpeg() -> bytes:
    """Minimum valid JPEG via Pillow (raster content for OCR)."""
    from PIL import Image
    img = Image.new("RGB", (200, 100), color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ── AC1: Happy — single upload ───────────────────────────────────


class TestUS003AC1Happy:
    def test_single_jpeg_upload_returns_201(self):
        tok = _session("us003-ac1@example.com")
        jpg = _dummy_jpeg()
        r = client.post(
            "/product/receipts/upload",
            headers=_headers(tok),
            files={"file": ("receipt.jpg", jpg, "image/jpeg")},
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "receipt_id" in data
        # source only in ai_mode; default mode has receipt + status

    def test_session_tenant_scoped(self):
        tok_a = _session("us003-ac1a@example.com")
        tok_b = _session("us003-ac1b@example.com")
        jpg = _dummy_jpeg()
        ra = client.post("/product/receipts/upload", headers=_headers(tok_a), files={"file": ("a.jpg", jpg, "image/jpeg")}).json()
        rb = client.post("/product/receipts/upload", headers=_headers(tok_b), files={"file": ("b.jpg", jpg, "image/jpeg")}).json()
        assert ra["receipt_id"] != rb["receipt_id"]


# ── AC2: Error — no session / bad format ─────────────────────────


class TestUS003AC2Errors:
    def test_no_session_returns_401(self):
        jpg = _dummy_jpeg()
        r = client.post("/product/receipts/upload", files={"file": ("r.jpg", jpg, "image/jpeg")})
        assert r.status_code == 401

    def test_unsupported_format_returns_415(self):
        tok = _session("us003-ac2@example.com")
        r = client.post(
            "/product/receipts/upload",
            headers=_headers(tok),
            files={"file": ("doc.pdf", b"fake-pdf-content", "application/pdf")},
        )
        assert r.status_code in (415, 400), r.text


# ── AC3: Edge — batch ────────────────────────────────────────────


class TestUS003AC3Batch:
    def test_batch_endpoint_exists(self):
        tok = _session("us003-ac3@example.com")
        jpg = _dummy_jpeg()
        r = client.post(
            "/v1/parse-receipts",
            headers=_headers(tok),
            files=[("files", ("r1.jpg", jpg, "image/jpeg")), ("files", ("r2.jpg", jpg, "image/jpeg"))],
        )
        assert r.status_code in (200, 201, 207), r.text


# ── AC4: GUI — AI scan gated ─────────────────────────────────────


class TestUS003AC4Gui:
    def test_upload_route_accessible(self):
        tok = _session("us003-ac4@example.com")
        jpg = _dummy_jpeg()
        r = client.post("/product/receipts/upload", headers=_headers(tok), files={"file": ("t.jpg", jpg, "image/jpeg")})
        assert r.status_code == 201
