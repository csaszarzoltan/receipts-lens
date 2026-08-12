"""SEC-005: per-tenant + per-IP rate limiting (429 + Retry-After).

The security test report (2026-08-12, SEC-005) found no rate limiting on the
OCR-heavy and inbound-ingestion endpoints:

- POST /product/receipts/upload  — expensive OCR (2x Tesseract in AI mode), DoS
- POST /product/inbound-emails  — any tenant can spam (even with headers)
- POST /v1/parse-receipt*        — unauthenticated OCR entrypoints
- POST /api/v1/receipts          — same OCR cost via the /api/v1 namespace

Expected behaviour (per the ticket): a per-tenant + per-IP rate limit, HTTP 429
with a Retry-After header, and the limits documented in docs/api.md.

The limiter lives in app/rate_limits.py as a Starlette middleware with an
in-process fixed-window counter. Tests configure small limits through the
module-level ``set_limits`` helper so the 429 path is deterministic; the
production defaults are env-tunable and deliberately generous.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import api
from app import rate_limits as rl
from app.ocr import ConfidenceReceipt, ReceiptItem

client = TestClient(api.app)
AUTH = {"X-Tenant-ID": "rate-team-a", "X-Role": "admin"}
# TestClient reports a fixed client IP; ASGI tests report None -> "unknown".
TEST_IP = "testclient"


def _receipt() -> ConfidenceReceipt:
    return ConfidenceReceipt(
        merchant="Rate Shop",
        date="2026-08-01",
        items=[ReceiptItem(name="Coffee", price=5.5)],
        total=5.5,
        tax=0.5,
        currency="USD",
        raw_text="RATE SHOP",
        confidence={"merchant": 0.9, "total": 0.95},
    )


@pytest.fixture(autouse=True)
def _fresh_limiter():
    rl.reset()
    yield
    rl.reset()
    rl.set_limits(None)  # restore env/default limits for later tests


def _upload():
    with patch("app.product_api.parse_receipt_with_confidence", return_value=_receipt()):
        return client.post(
            "/product/receipts/upload",
            headers=AUTH,
            files={"file": ("r.png", b"image", "image/png")},
        )


def _inbound():
    return client.post(
        "/product/inbound-emails",
        headers=AUTH,
        json={"sender": "billing@example.com", "subject": "Nyugta", "attachments": []},
    )


# ---------------------------------------------------------------------------
# Upload endpoint (OCR DoS vector)
# ---------------------------------------------------------------------------


def test_upload_exceeding_limit_returns_429_with_retry_after() -> None:
    rl.set_limits({"POST /product/receipts/upload": (2, 60)})
    assert _upload().status_code == 201
    assert _upload().status_code == 201
    limited = _upload()
    assert limited.status_code == 429
    body = limited.json()
    assert "rate limit" in body["detail"].lower()
    retry_after = limited.headers.get("Retry-After")
    assert retry_after is not None
    assert retry_after.isdigit() and int(retry_after) >= 1
    assert limited.headers.get("X-RateLimit-Remaining") == "0"


def test_upload_success_carries_remaining_header() -> None:
    rl.set_limits({"POST /product/receipts/upload": (2, 60)})
    resp = _upload()
    assert resp.status_code == 201
    assert resp.headers.get("X-RateLimit-Remaining") == "1"


def test_upload_retry_after_matches_window_boundary() -> None:
    rl.set_limits({"POST /product/receipts/upload": (1, 60)})
    _upload()
    limited = _upload()
    assert limited.status_code == 429
    # Fixed window: retry_after <= remaining window seconds.
    assert 1 <= int(limited.headers["Retry-After"]) <= 60


def test_upload_limit_resets_across_tenants() -> None:
    """Per-tenant isolation: a different tenant is NOT limited by tenant A's quota."""
    rl.set_limits({"POST /product/receipts/upload": (2, 60)})
    _upload()
    _upload()
    assert _upload().status_code == 429  # tenant A exhausted
    with patch("app.product_api.parse_receipt_with_confidence", return_value=_receipt()):
        other = client.post(
            "/product/receipts/upload",
            headers={"X-Tenant-ID": "rate-team-b", "X-Role": "admin"},
            files={"file": ("r.png", b"image", "image/png")},
        )
    assert other.status_code == 201  # tenant B unaffected


def test_upload_quota_is_per_ip_within_same_tenant() -> None:
    """Same tenant, different client IP -> separate counters."""
    rl.set_limits({"POST /product/receipts/upload": (2, 60)})
    _upload()
    _upload()
    assert _upload().status_code == 429
    # Force a different IP via X-Forwarded-For is NOT honoured (client.host is
    # authoritative); instead assert the key includes the real client IP by
    # exercising the limiter directly.
    ok, _ = rl._check("POST /product/receipts/upload", "rate-team-a", "10.0.0.9")
    assert ok is True


# ---------------------------------------------------------------------------
# Inbound emails endpoint (spam flood vector)
# ---------------------------------------------------------------------------


def test_inbound_emails_exceeding_limit_returns_429_with_retry_after() -> None:
    rl.set_limits({"POST /product/inbound-emails": (2, 60)})
    assert _inbound().status_code == 201
    assert _inbound().status_code == 201
    limited = _inbound()
    assert limited.status_code == 429
    assert int(limited.headers["Retry-After"]) >= 1
    assert "rate limit" in limited.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Unauthenticated OCR endpoints (per-IP keying)
# ---------------------------------------------------------------------------


def test_parse_receipt_exceeding_limit_returns_429() -> None:
    rl.set_limits({"POST /v1/parse-receipt": (2, 60)})
    payload = {"image_url": "https://example.com/r.png"}
    for _ in range(2):
        resp = client.post("/v1/parse-receipt", data=payload)
        assert resp.status_code in (200, 400, 422)  # fetch/OCR result irrelevant
    limited = client.post("/v1/parse-receipt", data=payload)
    assert limited.status_code == 429
    assert "Retry-After" in limited.headers
    assert limited.headers["X-RateLimit-Remaining"] == "0"


def test_unauthenticated_endpoint_keyed_by_ip() -> None:
    """No tenant header -> the client IP is the key (per-IP limit)."""
    rl.set_limits({"POST /v1/parse-receipt": (2, 60)})
    ok, _ = rl._check("POST /v1/parse-receipt", "", TEST_IP)
    assert ok is True
    ok, _ = rl._check("POST /v1/parse-receipt", "", TEST_IP)
    assert ok is True
    ok, retry_after = rl._check("POST /v1/parse-receipt", "", TEST_IP)
    assert ok is False and retry_after >= 1
    # A different IP is not limited
    ok, _ = rl._check("POST /v1/parse-receipt", "", "10.0.0.9")
    assert ok is True


# ---------------------------------------------------------------------------
# Exemptions
# ---------------------------------------------------------------------------


def test_health_and_readiness_never_limited() -> None:
    rl.set_limits({"POST /v1/parse-receipt": (2, 60)})
    for _ in range(5):
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 200


def test_unlisted_route_not_limited() -> None:
    rl.set_limits({"POST /product/receipts/upload": (2, 60)})
    for _ in range(10):
        resp = client.get("/product/jobs", headers=AUTH)
        assert resp.status_code == 200


def test_options_preflight_not_limited() -> None:
    rl.set_limits({"POST /product/receipts/upload": (2, 60)})
    for _ in range(5):
        resp = client.options("/product/receipts/upload", headers=AUTH)
        assert resp.status_code in (200, 405)


# ---------------------------------------------------------------------------
# Limiter unit behaviour
# ---------------------------------------------------------------------------


def test_fixed_window_rolls_over() -> None:
    """A new window bucket resets the counter (injectable clock)."""
    clock = {"t": 1000.0}
    rl.set_limits({"POST /v1/parse-receipt": (1, 60)})
    original = rl._time
    rl._time = lambda: clock["t"]
    try:
        ok, _ = rl._check("POST /v1/parse-receipt", "", TEST_IP)
        assert ok is True
        ok, _ = rl._check("POST /v1/parse-receipt", "", TEST_IP)
        assert ok is False
        clock["t"] = 1061.0  # next window
        ok, _ = rl._check("POST /v1/parse-receipt", "", TEST_IP)
        assert ok is True
    finally:
        rl._time = original


def test_default_limits_cover_ticket_endpoints() -> None:
    """The production defaults must include the SEC-005 attack surface."""
    for route in (
        "POST /product/receipts/upload",
        "POST /product/inbound-emails",
        "POST /v1/parse-receipt",
        "POST /v1/parse-receipt/async",
        "POST /v1/parse-receipts",
        "POST /v1/parse-receipts/async",
        "POST /api/v1/receipts",
        "POST /api/v1/receipts/batch",
    ):
        assert route in rl._limits, f"missing default limit for {route}"
        limit, window = rl._limits[route]
        assert limit >= 10 and window >= 10
