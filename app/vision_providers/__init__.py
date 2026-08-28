"""Vision provider package — OpenAI + Gemini adapters over the shared VisionOcrProvider."""

from app.vision_ocr import VisionOcrProvider, parse_receipt_with_vision

__all__ = ["VisionOcrProvider", "parse_receipt_with_vision"]
