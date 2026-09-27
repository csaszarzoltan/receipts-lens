"""RED tests for C3 pilot (AC1-3) — expect new behavior, FAIL before impl.

Target Files: app/preprocessing.py, app/ocr.py, frontend/components/ConfidenceBadge.tsx

Covers External Dogfood Pilot §6 AC1-3:
  AC1 [happy]    low-DPI synthetic -> confidence_level==low + total is None (GIGO gated) + HU warning + 8-12px border
  AC2 [recovery] threshold param + DPI-aware upscale to ~300 DPI (not fixed 1.5x) + sauvola branch
  AC3 [negative] 3000px cap before LANCZOS + GIGO gated on confidence_level
"""
from __future__ import annotations

import io
import inspect
import pathlib

from PIL import Image

from app.preprocessing import preprocess_image
import app.ocr as ocr_module
import app.preprocessing as pre_module

HU_WARNING = "Ellenőrzés szükséges — összeg bizonytalan"
RETRY_HINT = "Próbálja újra jobb megvilágítással / nagyobb felbontással"


def _make_low_dpi_bytes(w: int = 320, h: int = 200) -> bytes:
    """Synthetic low-DPI receipt-like image (short edge < 1000, no DPI meta)."""
    img = Image.new("RGB", (w, h), color="white")
    for x in range(w):
        for y in range(0, 8):
            img.putpixel((x, y), (240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_large_bytes(w: int = 4000, h: int = 2800) -> bytes:
    img = Image.new("RGB", (w, h), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# --- AC1: low-DPI flagged + GIGO gated + HU badge + border -----------------------

def test_ac1_low_dpi_flagged_gigo_and_hu_warning():
    """AC1 [happy] — low-DPI synthetic must be flagged low, total None, badge HU + border."""
    low_bytes = _make_low_dpi_bytes(320, 200)
    # Use deskew=False for deterministic sizing (deskew adds rotation/expand jitter)
    out = preprocess_image(low_bytes, deskew=False)
    # Current code does fixed 1.5x without border: 320x200 -> 480x300.
    # Spec requires 8-12px white border before _adaptive_threshold (so +16-24px per axis).
    # With deskew=False this is deterministic and RED before border impl.
    assert out.width >= 480 + 16, f"AC1 RED: expected 8-12px border (width >= {480+16}), got {out.width}"
    assert out.height >= 300 + 16, f"AC1 RED: expected 8-12px border (height >= {300+16}), got {out.height}"

    # OCR on low-DPI must gate GIGO: confidence_level low and total None
    result = ocr_module.parse_receipt_with_confidence(low_bytes)
    assert result.confidence_level == "low", (
        f"AC1 RED: expected confidence_level=='low' for low-DPI, got {result.confidence_level!r}"
    )
    assert result.total is None, (
        f"AC1 RED: GIGO not gated — low confidence should yield total is None, got {result.total!r}"
    )

    # Badge must render HU warning verbatim + retry hint when low
    badge_path = pathlib.Path(__file__).parent.parent / "frontend" / "components" / "ConfidenceBadge.tsx"
    text = badge_path.read_text(encoding="utf-8")
    assert HU_WARNING in text, f"AC1 RED: HU warning {HU_WARNING!r} missing from ConfidenceBadge.tsx"
    assert RETRY_HINT in text, f"AC1 RED: retry hint {RETRY_HINT!r} missing from ConfidenceBadge.tsx"


# --- AC2: threshold param + DPI-aware upscale to ~300 DPI ------------------------

def test_ac2_preprocess_threshold_and_dpi_upscale():
    """AC2 [recovery] — preprocess must expose threshold param and upscale to ~300 DPI."""
    sig = inspect.signature(pre_module.preprocess_image)
    assert "threshold" in sig.parameters, (
        f"AC2 RED: preprocess_image missing 'threshold' param, got {list(sig.parameters)}"
    )
    param = sig.parameters["threshold"]
    assert param.default == "auto", f"AC2 RED: threshold default should be 'auto', got {param.default!r}"

    # Upscale should target ~300 DPI (short edge ~1000px) with factor min(2.0, target/current),
    # not fixed 1.5x. Use deskew=False for deterministic measurement.
    small_bytes = _make_low_dpi_bytes(200, 100)
    out = preprocess_image(small_bytes, deskew=False)
    # Fixed 1.5x would be 300x150. Spec: min(2.0, target_edge/current_edge) so 200->400.
    assert out.width >= 380, f"AC2 RED: expected DPI-aware upscale ~2.0x (width >=380), got {out.width}"
    assert out.height >= 190, f"AC2 RED: expected DPI-aware upscale, got height {out.height}"

    src = inspect.getsource(pre_module.preprocess_image)
    assert "sauvola" in src.lower(), "AC2 RED: preprocess_image missing sauvola branch"
    assert "otsu" in src.lower(), "AC2 RED: missing otsu handling"


# --- AC3: 3000px cap before LANCZOS + GIGO gated -------------------------------

def test_ac3_3000px_cap_and_gigo_gated():
    """AC3 [negative] — 4000px image capped at 3000px before LANCZOS and GIGO gated."""
    pre_src = pathlib.Path(inspect.getfile(pre_module)).read_text(encoding="utf-8")
    # Exclude comment-only mentions: strip lines starting with '#'
    code_lines = [l for l in pre_src.splitlines() if not l.lstrip().startswith("#")]
    code_only = "\n".join(code_lines)
    assert "3000" in code_only, "AC3 RED: 3000px cap not found in app/preprocessing.py code (not comment)"
    assert "LANCZOS" in code_only, "AC3 RED: LANCZOS not found in preprocessing"
    # 3000 must be a runtime guard (assignment/comparison/min), not just a string literal in a comment
    import re as _re
    has_guard = bool(_re.search(r"(?:=\s*3000|>\s*3000|min\(.*3000|max\(.*3000|3000\s*\))", code_only))
    assert has_guard, "AC3 RED: 3000 runtime guard (e.g. min(…,3000) / =3000 / >3000) missing in preprocessing code"

    # Functional: 4000px wide image longest edge must be <=3000 after preprocess
    large_bytes = _make_large_bytes(4000, 2800)
    out = preprocess_image(large_bytes, deskew=False)
    longest = max(out.width, out.height)
    assert longest <= 3000, f"AC3 RED: longest edge {longest} exceeds 3000 cap"

    # GIGO at ocr.py ~456 total_score=1.0 if t_a==t_b must be gated by confidence_level low
    ocr_src = pathlib.Path(inspect.getfile(ocr_module)).read_text(encoding="utf-8")
    idx_conf = ocr_src.find("confidence_level")
    idx_score = ocr_src.find("total_score = 1.0")
    gated = idx_conf != -1 and idx_score != -1 and abs(idx_conf - idx_score) < 800
    assert gated, "AC3 RED: GIGO total_score not gated by confidence_level (ocr.py ~line 456)"
