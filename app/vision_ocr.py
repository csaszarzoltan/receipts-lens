"""LLM-vision receipt extraction with automatic Tesseract fallback.

Implements the AI Vision OCR path (spec t_44105a69): the receipt image is
sent as base64 to an OpenAI-compatible vision-capable LLM and the model
returns structured receipt JSON. When the vision path is unavailable or
fails, extraction falls back to the Tesseract pipeline (``app.ocr``).

Contract notes (pinned by tests/test_vision_ocr.py + tests/test_api_vision.py):

* ``parse_receipt_with_vision`` returns the SAME ``ConfidenceReceipt`` shape
  as ``ocr.parse_receipt_with_confidence``; the producing path is marked via
  ``result.confidence["source"]`` == ``SOURCE_VISION`` / ``SOURCE_TESSERACT``.
* The API AI-mode flow (``ai_scan=true`` form field on ``/v1/parse-receipt``)
  exposes a top-level ``source`` field plus ``ai_result`` / ``tesseract_result``
  payloads carrying the same receipt/confidence shape as the Tesseract path.
* Config plumbing mirrors app/categorizer.py (``LLM_API_KEY`` / ``LLM_BASE_URL`` /
  ``LLM_MODEL``) plus ``VISION_OCR_ENABLED`` (cost guard, default OFF) and
  ``VISION_OCR_TIMEOUT`` (seconds).

This module is a pre-development stub: the public extraction methods raise
``NotImplementedError`` until the developer implements the vision path.
"""
from __future__ import annotations

import os

from app.ocr import ConfidenceReceipt, ParsedReceipt

# ---------------------------------------------------------------------------
# Contract constants (values pinned by the frontend AI-scan contract)
# ---------------------------------------------------------------------------

SOURCE_VISION = "vision"
SOURCE_TESSERACT = "tesseract"

# ---------------------------------------------------------------------------
# Config plumbing (mirrors app/categorizer.py conventions)
# ---------------------------------------------------------------------------

ENV_API_KEY = "LLM_API_KEY"
ENV_BASE_URL = "LLM_BASE_URL"
ENV_MODEL = "LLM_MODEL"
ENV_ENABLED = "VISION_OCR_ENABLED"
ENV_TIMEOUT = "VISION_OCR_TIMEOUT"

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_TIMEOUT = 30.0


def _env_flag(name: str) -> bool:
    """Parse a boolean environment flag (1/true/yes/on => True)."""
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


class VisionOcrProvider:
    """Provider that sends receipt images to a vision-capable LLM.

    The vision path is only used when explicitly enabled (cost guard):
    ``enabled`` reflects the ``VISION_OCR_ENABLED`` config flag and
    ``available`` additionally requires an API key. On any call failure the
    caller (``parse_receipt_with_vision``) falls back to Tesseract.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        enabled: bool | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else os.environ.get(ENV_API_KEY, "")
        self._base_url = base_url or os.environ.get(ENV_BASE_URL, DEFAULT_BASE_URL)
        self._model = model or os.environ.get(ENV_MODEL, DEFAULT_MODEL)
        self._timeout = float(timeout if timeout is not None else os.environ.get(ENV_TIMEOUT, DEFAULT_TIMEOUT))
        self._enabled = enabled if enabled is not None else _env_flag(ENV_ENABLED)

    @property
    def enabled(self) -> bool:
        """True when the vision path is explicitly enabled (cost guard)."""
        return self._enabled

    @property
    def available(self) -> bool:
        """True when the vision path is enabled AND an API key is configured."""
        return self._enabled and bool(self._api_key)

    def parse(self, image_bytes: bytes, *, lang: str | None = None) -> ParsedReceipt:
        """Extract structured receipt data via the vision LLM.

        Calls ``_call_vision`` with retry-once on transient failures
        (timeout / connection error / HTTP 5xx), then converts the JSON
        payload with ``_parse_vision_json``.
        """
        raise NotImplementedError("VisionOcrProvider.parse is not implemented yet")

    def parse_with_confidence(self, image_bytes: bytes, *, lang: str | None = None) -> ConfidenceReceipt:
        """Extract structured receipt data + per-field confidence via vision LLM."""
        raise NotImplementedError("VisionOcrProvider.parse_with_confidence is not implemented yet")

    def _call_vision(self, image_bytes: bytes, *, lang: str | None = None) -> dict:
        """POST the base64-encoded image to the vision endpoint.

        Returns the parsed JSON body as a dict. Raises ``httpx.TimeoutException``
        / ``httpx.HTTPStatusError`` / ``json.JSONDecodeError`` on failure so the
        caller can retry once and then fall back to Tesseract.
        """
        raise NotImplementedError("VisionOcrProvider._call_vision is not implemented yet")

    def _parse_vision_json(self, data: dict) -> ParsedReceipt:
        """Convert the vision JSON payload into a ParsedReceipt."""
        raise NotImplementedError("VisionOcrProvider._parse_vision_json is not implemented yet")


def parse_receipt_with_vision(
    image_bytes: bytes,
    *,
    lang: str | None = None,
    provider: VisionOcrProvider | None = None,
) -> ConfidenceReceipt:
    """Vision-first receipt extraction with automatic Tesseract fallback.

    Fallback chain (spec acceptance criteria #3):

    1. provider disabled (config flag off) or no API key -> Tesseract
    2. vision call succeeds -> vision result
    3. timeout / API error / non-JSON response -> Tesseract (after one retry)

    Returns a ``ConfidenceReceipt`` whose ``confidence`` dict carries a
    ``"source"`` key: ``SOURCE_VISION`` when the vision path produced the
    result, ``SOURCE_TESSERACT`` when it fell back. The Tesseract fallback
    reuses ``ocr.parse_receipt_with_confidence`` so both shapes stay
    identical to the existing API responses (no breaking changes).
    """
    raise NotImplementedError("parse_receipt_with_vision is not implemented yet")
