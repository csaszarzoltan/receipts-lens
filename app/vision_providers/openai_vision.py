"""OpenAI Vision adapter — thin wrapper over VisionOcrProvider (ADR-005)."""

from __future__ import annotations

from app.vision_ocr import VisionOcrProvider

__all__ = ["OpenAIVisionProvider"]


class OpenAIVisionProvider(VisionOcrProvider):
    """OpenAI-compatible vision provider (gpt-4o default).

    Inherits all behaviour from VisionOcrProvider; this subclass exists so
    ADR-005's app/vision_providers/openai_vision.py contract is fulfilled
    and callers can import the provider by name:

        from app.vision_providers.openai_vision import OpenAIVisionProvider
        p = OpenAIVisionProvider()

    Configuration: LLM_API_KEY / LLM_BASE_URL / LLM_MODEL / VISION_OCR_ENABLED
    (mirrors app/vision_ocr.py). No extra dependency.
    """

