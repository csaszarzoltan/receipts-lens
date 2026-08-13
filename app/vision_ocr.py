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
"""
from __future__ import annotations

import base64
import json
import os
from typing import Any

import httpx

from app.ocr import (
    ConfidenceReceipt,
    ParsedReceipt,
    ReceiptItem,
    _confidence_level,
    parse_receipt_with_confidence,
)

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

# The JSON-schema extraction prompt sent with the receipt image. The model is
# asked to return ONLY this object shape; anything else is treated as a
# non-JSON response and triggers the Tesseract fallback.
_EXTRACTION_PROMPT = (
    "Extract structured receipt data from this receipt image.\n"
    "Respond with ONLY a JSON object matching this exact schema:\n"
    '{"merchant": string|null, "date": string|null, "total": number|null, '
    '"tax": number|null, "currency": string|null, '
    '"line_items": [{"name": string, "price": number}]}\n'
    "Rules:\n"
    "- merchant: store/merchant name as printed on the receipt.\n"
    "- date: normalized to YYYY-MM-DD (null if unreadable).\n"
    "- total: the grand total paid (null if unreadable).\n"
    "- tax: the tax/VAT amount (null if not shown).\n"
    "- currency: ISO 4217 code (USD, EUR, CHF, HUF, ...) — prefer the symbol "
    "or code printed on the receipt.\n"
    "- line_items: purchased items with their prices; empty array if none.\n"
    "- Return valid JSON only: no markdown fences, no commentary, no trailing text."
)

_CONFIDENCE_KEYS: tuple[str, ...] = ("vendor", "total", "date", "tax", "currency", "line_items")


def _env_flag(name: str) -> bool:
    """Parse a boolean environment flag (1/true/yes/on => True)."""
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _is_transient(exc: Exception) -> bool:
    """True when *exc* is a transient network failure worth one retry.

    Timeouts and connection errors (``httpx.TransportError``) are always
    transient; HTTP errors only when the server reported a 5xx.
    """
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return False


def _to_float(value: Any) -> float | None:
    """Coerce *value* to float, returning None for unparseable input."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sniff_media_type(image_bytes: bytes) -> str:
    """Best-effort image MIME sniff from magic bytes (defaults to PNG)."""
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


def _confidence_from_json(data: dict) -> dict[str, float | None]:
    """Derive per-field confidence from the vision JSON payload.

    Mirrors the Tesseract confidence keys (vendor/total/date/tax/currency/
    line_items). A field the model actually extracted scores 1.0, a missing
    field 0.0 — the API contract only requires the keys to exist.
    """
    items = data.get("line_items")
    return {
        "vendor": 1.0 if data.get("merchant") else 0.0,
        "total": 1.0 if _to_float(data.get("total")) is not None else 0.0,
        "date": 1.0 if data.get("date") else 0.0,
        "tax": 1.0 if _to_float(data.get("tax")) is not None else 0.0,
        "currency": 1.0 if data.get("currency") else 0.0,
        "line_items": 1.0 if isinstance(items, list) and items else 0.0,
    }


def _tesseract_fallback(image_bytes: bytes, *, lang: str | None = None) -> ConfidenceReceipt:
    """Run the classic Tesseract pipeline and mark the result's source."""
    result = parse_receipt_with_confidence(image_bytes, lang=lang)
    result.confidence = dict(result.confidence or {})
    result.confidence["source"] = SOURCE_TESSERACT
    return result


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

    def _call_with_retry(self, image_bytes: bytes, *, lang: str | None = None) -> dict:
        """Call the vision endpoint, retrying exactly once on transient failure.

        A transient failure (timeout / connection error / HTTP 5xx) triggers
        a single retry; a second failure propagates so the caller can fall
        back to Tesseract. Non-transient failures (4xx, non-JSON body)
        propagate immediately.
        """
        try:
            return self._call_vision(image_bytes, lang=lang)
        except Exception as exc:
            if not _is_transient(exc):
                raise
            return self._call_vision(image_bytes, lang=lang)

    def parse(self, image_bytes: bytes, *, lang: str | None = None) -> ParsedReceipt:
        """Extract structured receipt data via the vision LLM.

        Calls ``_call_vision`` with retry-once on transient failures
        (timeout / connection error / HTTP 5xx), then converts the JSON
        payload with ``_parse_vision_json``.
        """
        data = self._call_with_retry(image_bytes, lang=lang)
        return self._parse_vision_json(data)

    def parse_with_confidence(self, image_bytes: bytes, *, lang: str | None = None) -> ConfidenceReceipt:
        """Extract structured receipt data + per-field confidence via vision LLM."""
        data = self._call_with_retry(image_bytes, lang=lang)
        parsed = self._parse_vision_json(data)
        confidence = _confidence_from_json(data)
        return ConfidenceReceipt(
            merchant=parsed.merchant,
            date=parsed.date,
            items=parsed.items,
            total=parsed.total,
            tax=parsed.tax,
            currency=parsed.currency,
            raw_text=parsed.raw_text,
            confidence=confidence,
            confidence_level=_confidence_level(confidence),
        )

    def _call_vision(self, image_bytes: bytes, *, lang: str | None = None) -> dict:
        """POST the base64-encoded image to the vision endpoint.

        Returns the parsed JSON body as a dict. Raises ``httpx.TimeoutException``
        / ``httpx.HTTPStatusError`` / ``json.JSONDecodeError`` on failure so the
        caller can retry once and then fall back to Tesseract.
        """
        if not image_bytes:
            raise ValueError("image_bytes must not be empty")

        media_type = _sniff_media_type(image_bytes)
        data_url = f"data:{media_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"

        prompt = _EXTRACTION_PROMPT
        if lang:
            prompt = f"The receipt is written in language code '{lang}'. {prompt}"

        body = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            "temperature": 0.0,
            "max_tokens": 600,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(
                f"{self._base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content) if isinstance(content, str) else content
        if not isinstance(parsed, dict):
            raise TypeError("Vision model response is not a JSON object")
        return parsed

    def _parse_vision_json(self, data: dict) -> ParsedReceipt:
        """Convert the vision JSON payload into a ParsedReceipt."""
        raw_items = data.get("line_items")
        items: list[ReceiptItem] = []
        if isinstance(raw_items, list):
            for entry in raw_items:
                if not isinstance(entry, dict):
                    continue
                name = str(entry.get("name") or "").strip()
                price = _to_float(entry.get("price"))
                if not name or price is None:
                    continue
                items.append(ReceiptItem(name=name, price=price))

        return ParsedReceipt(
            merchant=data.get("merchant") or None,
            date=data.get("date") or None,
            items=items,
            total=_to_float(data.get("total")),
            tax=_to_float(data.get("tax")),
            currency=data.get("currency") or None,
            raw_text=json.dumps(data, ensure_ascii=False, sort_keys=True),
        )


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
    provider = provider or VisionOcrProvider()
    if not provider.available:
        return _tesseract_fallback(image_bytes, lang=lang)
    try:
        result = provider.parse_with_confidence(image_bytes, lang=lang)
    except Exception:  # noqa: BLE001 - any vision failure falls back to Tesseract (contract AC3)
        return _tesseract_fallback(image_bytes, lang=lang)
    result.confidence = dict(result.confidence or {})
    result.confidence["source"] = SOURCE_VISION
    return result
