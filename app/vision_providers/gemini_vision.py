"""Gemini Vision adapter — thin wrapper over VisionOcrProvider (ADR-005)."""

from __future__ import annotations

import os

from app.vision_ocr import VisionOcrProvider

__all__ = ["GeminiVisionProvider"]


class GeminiVisionProvider(VisionOcrProvider):
    """Gemini-compatible vision provider (gemini-1.5-flash default).

    Wraps VisionOcrProvider with Gemini defaults so ADR-005's
    app/vision_providers/gemini_vision.py contract is fulfilled:

        from app.vision_providers.gemini_vision import GeminiVisionProvider
        p = GeminiVisionProvider()  # reads GEMINI_API_KEY / GEMINI_BASE_URL

    When GEMINI_API_KEY is set it is used; otherwise falls back to
    LLM_API_KEY (so one key can serve both adapters in dev).
    No extra dependency — httpx already present.
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
        super().__init__(
            api_key=api_key or os.getenv("GEMINI_API_KEY") or None,
            base_url=base_url or os.getenv("GEMINI_BASE_URL") or "https://generativelanguage.googleapis.com/v1",
            model=model or os.getenv("GEMINI_MODEL") or "gemini-1.5-flash",
            timeout=timeout,
            enabled=enabled,
        )
