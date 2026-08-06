"""Pre-development interface + behavioral tests for the AI-mode API flow.

Covers acceptance criterion #6 of the AI Vision OCR feature (spec
t_44105a69): the ``/v1/parse-receipt`` endpoint, when called in AI mode
(``ai_scan=true`` form field), exposes a ``source`` field ("vision" |
"tesseract") and optionally ``ai_result`` + ``tesseract_result`` payloads
carrying the same receipt/confidence shape as the Tesseract path.

Layout (follows repo pre-tester conventions):
  * Interface tests  — route registration, endpoint signature, response
    render shape. These MUST pass immediately.
  * Behavioral tests — the AI-mode contract. They fail during RED (the API
    does not yet accept ``ai_scan`` / does not expose ``source``) and pass
    once the developer wires the vision path.

Run with:
    .venv/bin/python -m pytest tests/test_api_vision.py -v
"""
from __future__ import annotations

import io
from unittest.mock import patch

import pytest
from PIL import Image
from starlette.testclient import TestClient

from app import api, vision_ocr
from app.ocr import ConfidenceReceipt
from app.vision_ocr import SOURCE_TESSERACT, SOURCE_VISION

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _blank_png() -> bytes:
    """A tiny valid PNG that Tesseract can process (empty text)."""
    buf = io.BytesIO()
    Image.new("RGB", (200, 100), color="white").save(buf, format="PNG")
    return buf.getvalue()


BLANK_PNG = _blank_png()

RECEIPT_SHAPE_KEYS = ("vendor", "total", "date", "tax", "currency", "line_items", "confidence")


@pytest.fixture
def client() -> TestClient:
    return TestClient(api.app)


def _upload(client: TestClient, *, ai_scan: bool = False) -> dict:
    data = {"ai_scan": "true"} if ai_scan else {}
    resp = client.post(
        "/v1/parse-receipt",
        files={"file": ("receipt.png", BLANK_PNG, "image/png")},
        data=data,
    )
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}: {resp.text}"
    return resp.json()


def _vision_receipt(source: str = SOURCE_VISION) -> ConfidenceReceipt:
    """Canned vision-path result: STARBUCKS receipt with source marker."""
    return ConfidenceReceipt(
        merchant="STARBUCKS COFFEE",
        date="2026-08-01",
        items=[],  # type: ignore[arg-type]
        total=12.34,
        tax=1.11,
        currency="USD",
        raw_text='{"merchant": "STARBUCKS COFFEE"}',
        confidence={
            "vendor": 0.99,
            "total": 0.98,
            "date": 0.97,
            "tax": 0.9,
            "currency": 0.95,
            "line_items": 0.0,
            "source": source,
        },  # type: ignore[arg-type]  # source marker is a str by contract
    )


# ===========================================================================
# INTERFACE TESTS — must pass immediately
# ===========================================================================


class TestApiVisionInterface:
    """Existing API surface the AI-mode flow builds on."""

    def test_api_importable(self) -> None:
        assert api is not None

    def test_parse_receipt_route_registered(self) -> None:
        paths = {getattr(r, "path", None) for r in api.app.routes}
        assert "/v1/parse-receipt" in paths

    def test_parse_receipt_endpoint_signature(self) -> None:
        import inspect

        sig = inspect.signature(api.parse_receipt_endpoint)
        params = list(sig.parameters)
        assert "file" in params, f"parse_receipt_endpoint missing file param: {params}"

    def test_vision_ocr_wiring_surface(self) -> None:
        """The API flow builds on the vision_ocr module contract."""
        assert callable(vision_ocr.parse_receipt_with_vision)
        assert vision_ocr.SOURCE_VISION == "vision"
        assert vision_ocr.SOURCE_TESSERACT == "tesseract"

    def test_regular_flow_render_shape(self, client: TestClient) -> None:
        """Non-AI flow keeps the existing receipt shape (no breaking change)."""
        data = _upload(client)
        for key in RECEIPT_SHAPE_KEYS:
            assert key in data, f"regular response missing {key}"
        # The regular flow must NOT leak AI-mode fields.
        assert "source" not in data
        assert "ai_result" not in data
        assert "tesseract_result" not in data


# ===========================================================================
# BEHAVIORAL TESTS — RED until the AI-mode flow is implemented
# ===========================================================================


class TestApiVisionBehavioral:
    """AI-mode upload contract: source + ai_result/tesseract_result."""

    def test_ai_mode_response_has_source(self, client: TestClient, monkeypatch) -> None:
        """AC6: AI-mode response exposes a top-level source field."""
        monkeypatch.delenv(vision_ocr.ENV_ENABLED, raising=False)
        monkeypatch.delenv(vision_ocr.ENV_API_KEY, raising=False)
        data = _upload(client, ai_scan=True)
        assert "source" in data, "AI-mode response missing source field"
        assert data["source"] in (SOURCE_VISION, SOURCE_TESSERACT)

    def test_ai_mode_fallback_marks_tesseract_source(
        self, client: TestClient, monkeypatch
    ) -> None:
        """AC6: no vision config -> source='tesseract' + tesseract_result."""
        monkeypatch.delenv(vision_ocr.ENV_ENABLED, raising=False)
        monkeypatch.delenv(vision_ocr.ENV_API_KEY, raising=False)
        data = _upload(client, ai_scan=True)
        assert data["source"] == SOURCE_TESSERACT
        assert "tesseract_result" in data, "fallback must expose tesseract_result"
        for key in RECEIPT_SHAPE_KEYS:
            assert key in data["tesseract_result"], (
                f"tesseract_result missing {key}"
            )

    def test_ai_mode_vision_success_exposes_ai_result(
        self, client: TestClient, monkeypatch
    ) -> None:
        """AC6: vision success -> source='vision' + ai_result with AI data."""
        monkeypatch.setenv(vision_ocr.ENV_ENABLED, "1")
        monkeypatch.setenv(vision_ocr.ENV_API_KEY, "test-key")
        canned = _vision_receipt(SOURCE_VISION)
        with (
            patch.object(api, "parse_receipt_with_vision", return_value=canned, create=True),
            patch.object(vision_ocr, "parse_receipt_with_vision", return_value=canned),
        ):
            data = _upload(client, ai_scan=True)
        assert data["source"] == SOURCE_VISION
        assert "ai_result" in data, "vision success must expose ai_result"
        assert data["ai_result"]["vendor"] == "STARBUCKS COFFEE"
        assert data["ai_result"]["total"] == 12.34
        assert data["ai_result"]["currency"] == "USD"
        for key in RECEIPT_SHAPE_KEYS:
            assert key in data["ai_result"], f"ai_result missing {key}"

    def test_ai_mode_vision_failure_falls_back(
        self, client: TestClient, monkeypatch
    ) -> None:
        """AC6: vision failure -> source='tesseract' (friendly fallback)."""
        monkeypatch.setenv(vision_ocr.ENV_ENABLED, "1")
        monkeypatch.setenv(vision_ocr.ENV_API_KEY, "test-key")

        def _boom(*a, **k):
            raise TimeoutError("vision unavailable")

        with (
            patch.object(api, "parse_receipt_with_vision", side_effect=_boom, create=True),
            patch.object(vision_ocr, "parse_receipt_with_vision", side_effect=_boom),
        ):
            data = _upload(client, ai_scan=True)
        assert data["source"] == SOURCE_TESSERACT
