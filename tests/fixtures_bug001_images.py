"""Reproduction fixture for BUG-001: low-quality receipt images.

These images simulate the real-world scenario reported from live testing:
a blurry / low-contrast photo of a receipt where Tesseract misreads
garbage characters. The critical regression: `parse_receipt` must NOT
return a fabricated `total=1.0` for such images.
"""
from __future__ import annotations

import io

from PIL import Image, ImageDraw, ImageFilter


def _render(text: str, *, size=(700, 380), bg=(255, 255, 255), fg=(0, 0, 0)) -> bytes:
    img = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(img)
    draw.multiline_text((24, 24), text, fill=fg)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def blurry_receipt() -> bytes:
    """Low-quality: heavy Gaussian blur + low contrast (gray on gray)."""
    base = _render(
        "MART STORE\n"
        "12 Main Street\n"
        "2026-08-01\n"
        "\n"
        "Milk 1.29\n"
        "Bread 2.49\n"
        "TOTAL 3.78",
        fg=(120, 120, 120),
        bg=(235, 235, 235),
    )
    img = Image.open(io.BytesIO(base)).filter(ImageFilter.GaussianBlur(radius=4))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def noisy_garbage() -> bytes:
    """Extremely poor quality: effectively unreadable noise.

    Tesseract will produce sparse garbage tokens; the parser must not
    hallucinate a total from stray digit-like fragments.
    """
    img = Image.new("RGB", (500, 300), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    for i in range(80):
        x = (i * 37) % 460 + 10
        y = (i * 53) % 260 + 10
        draw.text((x, y), "#?!%&~", fill=(140, 140, 140))
    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def clean_receipt() -> bytes:
    """High-quality baseline receipt (control case)."""
    return _render(
        "MART STORE\n"
        "12 Main Street\n"
        "2026-08-01\n"
        "\n"
        "Milk 1.29\n"
        "Bread 2.49\n"
        "TOTAL 3.78"
    )
