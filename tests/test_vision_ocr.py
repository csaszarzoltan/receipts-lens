"""Pre-development interface + behavioral tests for the LLM-vision OCR path.

Covers the new AI Vision OCR extraction feature (spec t_44105a69):
``app/vision_ocr.py`` — VisionOcrProvider + parse_receipt_with_vision with
automatic Tesseract fallback.

Layout (follows repo pre-tester conventions):
  * Interface tests  — imports, signatures, type hints, config-plumbing
    defaults. These MUST pass immediately (stub exists with the contract).
  * Behavioral tests — real acceptance-criteria assertions. They fail with
    NotImplementedError until the developer implements the vision path.

Run with:
    .venv/bin/python -m pytest tests/test_vision_ocr.py -v
"""
from __future__ import annotations

import inspect
import io
from typing import get_type_hints

import httpx
import pytest
from PIL import Image

from app import vision_ocr
from app.ocr import ConfidenceReceipt, ParsedReceipt, ReceiptItem
from app.vision_ocr import (
    SOURCE_TESSERACT,
    SOURCE_VISION,
    VisionOcrProvider,
    parse_receipt_with_vision,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _blank_png() -> bytes:
    """A tiny valid PNG that Tesseract can process (empty text)."""
    buf = io.BytesIO()
    Image.new("RGB", (200, 100), color="white").save(buf, format="PNG")
    return buf.getvalue()


BLANK_PNG = _blank_png()

# Canned vision-LLM JSON payload (the JSON-schema extraction contract).
VISION_JSON = {
    "merchant": "STARBUCKS COFFEE",
    "date": "2026-08-01",
    "total": 12.34,
    "currency": "USD",
    "tax": 1.11,
    "line_items": [
        {"name": "Caffe Latte", "price": 6.17},
        {"name": "Butter Croissant", "price": 6.17},
    ],
}


@pytest.fixture
def provider() -> VisionOcrProvider:
    return VisionOcrProvider()


@pytest.fixture
def available_provider() -> VisionOcrProvider:
    """Enabled + API key -> the vision path may run."""
    return VisionOcrProvider(api_key="test-key", enabled=True)


def _conf_source(result: ConfidenceReceipt) -> str | None:
    """Read the source marker from a ConfidenceReceipt's confidence dict."""
    source = (result.confidence or {}).get("source")
    return source if isinstance(source, str) else None


# ===========================================================================
# INTERFACE TESTS — must pass immediately
# ===========================================================================


class TestVisionOcrInterface:
    """Module surface: imports, signatures, type hints, config plumbing."""

    def test_module_importable(self) -> None:
        assert vision_ocr is not None

    def test_vision_ocr_provider_importable(self) -> None:
        assert VisionOcrProvider is not None
        assert callable(VisionOcrProvider)

    def test_parse_receipt_with_vision_importable(self) -> None:
        assert callable(parse_receipt_with_vision)

    def test_source_constants(self) -> None:
        assert SOURCE_VISION == "vision"
        assert SOURCE_TESSERACT == "tesseract"

    def test_parse_receipt_with_vision_signature(self) -> None:
        sig = inspect.signature(parse_receipt_with_vision)
        params = list(sig.parameters)
        assert "image_bytes" in params, f"missing image_bytes: {params}"
        assert "lang" in params, f"missing lang: {params}"
        assert "provider" in params, f"missing provider: {params}"
        hints = get_type_hints(parse_receipt_with_vision)
        assert hints.get("image_bytes") is bytes

    def test_parse_receipt_with_vision_returns_confidence_receipt(self) -> None:
        hints = get_type_hints(parse_receipt_with_vision)
        ret = hints.get("return")
        assert ret is ConfidenceReceipt or ret == "ConfidenceReceipt", (
            f"return hint is {ret!r}, expected ConfidenceReceipt"
        )

    def test_provider_init_signature(self) -> None:
        sig = inspect.signature(VisionOcrProvider.__init__)
        params = sig.parameters
        for name in ("api_key", "base_url", "model", "timeout", "enabled"):
            assert name in params, f"__init__ missing {name} param"
        assert params["api_key"].default is None
        assert params["enabled"].default is None

    def test_provider_parse_signature(self) -> None:
        sig = inspect.signature(VisionOcrProvider.parse)
        params = list(sig.parameters)
        assert "image_bytes" in params
        assert "lang" in params
        hints = get_type_hints(VisionOcrProvider.parse)
        assert hints.get("image_bytes") is bytes
        assert hints.get("return") is ParsedReceipt

    def test_provider_parse_with_confidence_signature(self) -> None:
        sig = inspect.signature(VisionOcrProvider.parse_with_confidence)
        params = list(sig.parameters)
        assert "image_bytes" in params
        assert "lang" in params
        hints = get_type_hints(VisionOcrProvider.parse_with_confidence)
        assert hints.get("return") is ConfidenceReceipt

    def test_provider_has_call_vision_seam(self) -> None:
        """_call_vision is the documented HTTP seam (returns the JSON dict)."""
        assert callable(VisionOcrProvider._call_vision)
        hints = get_type_hints(VisionOcrProvider._call_vision)
        assert hints.get("image_bytes") is bytes
        assert hints.get("return") is dict

    def test_provider_has_parse_vision_json_seam(self) -> None:
        """_parse_vision_json maps the vision JSON payload to ParsedReceipt."""
        assert callable(VisionOcrProvider._parse_vision_json)
        hints = get_type_hints(VisionOcrProvider._parse_vision_json)
        assert hints.get("data") is dict
        assert hints.get("return") is ParsedReceipt

    def test_provider_has_enabled_and_available_properties(self) -> None:
        assert isinstance(vision_ocr.VisionOcrProvider.enabled, property)
        assert isinstance(vision_ocr.VisionOcrProvider.available, property)

    def test_provider_disabled_by_default(self, monkeypatch) -> None:
        """Cost guard: vision path is OFF unless explicitly enabled."""
        for key in (vision_ocr.ENV_ENABLED, vision_ocr.ENV_API_KEY, vision_ocr.ENV_BASE_URL,
                    vision_ocr.ENV_MODEL, vision_ocr.ENV_TIMEOUT):
            monkeypatch.delenv(key, raising=False)
        p = VisionOcrProvider()
        assert p.enabled is False
        assert p.available is False

    def test_provider_enabled_flag_turns_on(self, monkeypatch) -> None:
        monkeypatch.setenv(vision_ocr.ENV_ENABLED, "1")
        monkeypatch.setenv(vision_ocr.ENV_API_KEY, "env-key")
        p = VisionOcrProvider()
        assert p.enabled is True
        assert p.available is True

    def test_provider_enabled_without_key_not_available(self, monkeypatch) -> None:
        monkeypatch.setenv(vision_ocr.ENV_ENABLED, "1")
        monkeypatch.delenv(vision_ocr.ENV_API_KEY, raising=False)
        p = VisionOcrProvider()
        assert p.enabled is True
        assert p.available is False

    def test_provider_reads_categorizer_env_plumbing(self, monkeypatch) -> None:
        """Reuses LLM_API_KEY / LLM_BASE_URL / LLM_MODEL like app/categorizer.py."""
        monkeypatch.setenv(vision_ocr.ENV_MODEL, "gpt-4o")
        monkeypatch.setenv(vision_ocr.ENV_BASE_URL, "https://example.com/v1")
        p = VisionOcrProvider()
        assert p._model == "gpt-4o"
        assert p._base_url == "https://example.com/v1"

    def test_provider_explicit_args_beat_env(self, monkeypatch) -> None:
        monkeypatch.setenv(vision_ocr.ENV_MODEL, "env-model")
        p = VisionOcrProvider(model="explicit-model")
        assert p._model == "explicit-model"


# ===========================================================================
# BEHAVIORAL TESTS — fail with NotImplementedError until implemented
# ===========================================================================


class TestVisionOcrBehavioral:
    """Real acceptance criteria for the vision path + fallback chain."""

    def test_successful_vision_call_returns_structured_receipt(
        self, available_provider: VisionOcrProvider, monkeypatch
    ) -> None:
        """AC2: vision success returns ParsedReceipt with structured fields."""
        monkeypatch.setattr(available_provider, "_call_vision", lambda *a, **k: VISION_JSON)
        result = available_provider.parse(BLANK_PNG)
        assert isinstance(result, ParsedReceipt)
        assert result.merchant == "STARBUCKS COFFEE"
        assert result.date == "2026-08-01"
        assert result.total == 12.34
        assert result.currency == "USD"
        assert result.tax == 1.11
        assert isinstance(result.raw_text, str)
        names = {item.name for item in result.items}
        assert "Caffe Latte" in names and "Butter Croissant" in names
        latte = next(i for i in result.items if i.name == "Caffe Latte")
        assert isinstance(latte, ReceiptItem)
        assert latte.price == 6.17

    def test_vision_confidence_receipt_shape(
        self, available_provider: VisionOcrProvider, monkeypatch
    ) -> None:
        """AC2: confidence variant returns ConfidenceReceipt (same shape as Tesseract)."""
        monkeypatch.setattr(available_provider, "_call_vision", lambda *a, **k: VISION_JSON)
        result = available_provider.parse_with_confidence(BLANK_PNG)
        assert isinstance(result, ConfidenceReceipt)
        assert isinstance(result.confidence, dict)
        for key in ("vendor", "total", "date", "tax", "currency", "line_items"):
            assert key in result.confidence, f"confidence missing {key}"

    def test_parse_receipt_with_vision_returns_confidence_receipt(
        self, available_provider: VisionOcrProvider, monkeypatch
    ) -> None:
        """AC2: module function returns the SAME ConfidenceReceipt shape as Tesseract."""
        monkeypatch.setattr(available_provider, "_call_vision", lambda *a, **k: VISION_JSON)
        result = parse_receipt_with_vision(BLANK_PNG, provider=available_provider)
        assert isinstance(result, ConfidenceReceipt)
        assert result.merchant == "STARBUCKS COFFEE"
        assert isinstance(result.items, list)

    def test_vision_success_marks_source_vision(
        self, available_provider: VisionOcrProvider, monkeypatch
    ) -> None:
        """AC3: successful vision call marks source='vision'."""
        monkeypatch.setattr(available_provider, "_call_vision", lambda *a, **k: VISION_JSON)
        result = parse_receipt_with_vision(BLANK_PNG, provider=available_provider)
        assert _conf_source(result) == SOURCE_VISION

    def test_no_api_key_falls_back_to_tesseract(self, provider: VisionOcrProvider) -> None:
        """AC3: no API key -> Tesseract path, source='tesseract'."""
        result = parse_receipt_with_vision(BLANK_PNG, provider=provider)
        assert isinstance(result, ConfidenceReceipt)
        assert _conf_source(result) == SOURCE_TESSERACT

    def test_disabled_flag_falls_back_to_tesseract(
        self, available_provider: VisionOcrProvider, monkeypatch
    ) -> None:
        """AC4: explicit config flag off disables the vision path entirely."""
        monkeypatch.setattr(available_provider, "_enabled", False)
        result = parse_receipt_with_vision(BLANK_PNG, provider=available_provider)
        assert isinstance(result, ConfidenceReceipt)
        assert _conf_source(result) == SOURCE_TESSERACT

    def test_timeout_falls_back_to_tesseract(
        self, available_provider: VisionOcrProvider, monkeypatch
    ) -> None:
        """AC3: timeout -> Tesseract fallback with source marker."""
        def _boom(*a, **k):
            raise httpx.TimeoutException("vision timed out")
        monkeypatch.setattr(available_provider, "_call_vision", _boom)
        result = parse_receipt_with_vision(BLANK_PNG, provider=available_provider)
        assert isinstance(result, ConfidenceReceipt)
        assert _conf_source(result) == SOURCE_TESSERACT

    def test_api_error_falls_back_to_tesseract(
        self, available_provider: VisionOcrProvider, monkeypatch
    ) -> None:
        """AC3: HTTP API error -> Tesseract fallback with source marker."""
        def _boom(*a, **k):
            raise httpx.HTTPStatusError(
                "500 from vision API", request=httpx.Request("POST", "http://x"),
                response=httpx.Response(500, request=httpx.Request("POST", "http://x")),
            )
        monkeypatch.setattr(available_provider, "_call_vision", _boom)
        result = parse_receipt_with_vision(BLANK_PNG, provider=available_provider)
        assert isinstance(result, ConfidenceReceipt)
        assert _conf_source(result) == SOURCE_TESSERACT

    def test_non_json_response_falls_back_to_tesseract(
        self, available_provider: VisionOcrProvider, monkeypatch
    ) -> None:
        """AC3: non-JSON response -> Tesseract fallback with source marker."""
        def _boom(*a, **k):
            raise ValueError("Invalid JSON")
        monkeypatch.setattr(available_provider, "_call_vision", _boom)
        result = parse_receipt_with_vision(BLANK_PNG, provider=available_provider)
        assert isinstance(result, ConfidenceReceipt)
        assert _conf_source(result) == SOURCE_TESSERACT

    def test_retries_once_on_transient_failure(
        self, available_provider: VisionOcrProvider, monkeypatch
    ) -> None:
        """AC4: retry-once on transient failure, then success on 2nd attempt."""
        calls: list[str] = []

        def _flaky(*a, **k):
            calls.append("call")
            if len(calls) == 1:
                raise httpx.TimeoutException("transient")
            return VISION_JSON

        monkeypatch.setattr(available_provider, "_call_vision", _flaky)
        result = available_provider.parse(BLANK_PNG)
        assert len(calls) == 2, f"expected exactly one retry, got {len(calls)} calls"
        assert isinstance(result, ParsedReceipt)
        assert result.merchant == "STARBUCKS COFFEE"

    def test_retry_only_once_then_falls_back(
        self, available_provider: VisionOcrProvider, monkeypatch
    ) -> None:
        """AC4: persistent transient failure -> retried once, then Tesseract fallback."""
        calls: list[str] = []

        def _always_boom(*a, **k):
            calls.append("call")
            raise httpx.TimeoutException("always transient")

        monkeypatch.setattr(available_provider, "_call_vision", _always_boom)
        result = parse_receipt_with_vision(BLANK_PNG, provider=available_provider)
        assert len(calls) == 2, f"expected exactly one retry, got {len(calls)} calls"
        assert isinstance(result, ConfidenceReceipt)
        assert _conf_source(result) == SOURCE_TESSERACT

    def test_vision_path_skipped_when_provider_unavailable(
        self, provider: VisionOcrProvider, monkeypatch
    ) -> None:
        """AC4: unavailable provider -> vision _call_vision never invoked."""
        calls: list[str] = []

        def _spy(*a, **k):
            calls.append("call")
            return VISION_JSON

        monkeypatch.setattr(provider, "_call_vision", _spy)
        result = parse_receipt_with_vision(BLANK_PNG, provider=provider)
        assert calls == [], "vision call must not run when provider is unavailable"
        assert _conf_source(result) == SOURCE_TESSERACT
