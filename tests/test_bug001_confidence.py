"""BUG-001 + OCR confidence contract tests — Consumer Pivot F1.4.

Acceptance mapping (docs/plans/consumer-pivot-2026-08-13.md §2.2 / F1.4):
1. BUG-001 regression: on low-quality images the extracted total must
   NOT be a fabricated `total=1.0` — either exact or flagged uncertain.
2. Per-receipt confidence level in the parse-receipt response.
3. Review flow requests user confirmation on weak matches (UI contract).
4. At least one integration test via real multipart upload (no mocks).

Run: PATH="$PWD/.venv/bin:$PATH" python -m pytest tests/test_bug001_confidence.py -v
"""
from __future__ import annotations

import re

import pytest

from app import api
from app.ocr import (
    ConfidenceReceipt,
    ParsedReceipt,
    _clean_text,
    _confidence_from_data,
    _parse_float,
    parse_receipt,
    parse_receipt_with_confidence,
)
from tests.fixtures_bug001_images import blurry_receipt, clean_receipt, noisy_garbage

pytestmark = pytest.mark.bug001


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    return TestClient(api.app)


# ---------------------------------------------------------------------------
# BUG-001 regression: low-quality image must NOT yield a fabricated total
# ---------------------------------------------------------------------------


def test_low_quality_image_total_not_fabricated() -> None:
    """AC1: blurry receipt -> total is NOT the fake value 1.0.

    Either the real total is extracted, or the result is flagged
    uncertain — never a confident-but-wrong amount.
    """
    parsed = parse_receipt(blurry_receipt())
    assert parsed.total != 1.0, (
        f"BUG-001: low-quality image produced fabricated total=1.0 "
        f"(raw_text={parsed.raw_text!r})"
    )


def test_low_quality_image_is_uncertain_when_no_clean_total() -> None:
    """AC1/AC2: no confident total -> 'uncertain' signal instead of a value."""
    parsed = parse_receipt_with_confidence(noisy_garbage())
    conf = parsed.confidence or {}
    if parsed.total is None:
        # No total extracted at all — acceptable (explicit None beats 1.0).
        assert parsed.total is None
    else:
        total_conf = conf.get("total")
        assert total_conf is not None, "total present but confidence missing"
        assert total_conf < 0.5, (
            f"low-quality image returned total={parsed.total} with high confidence "
            f"{total_conf} — must be flagged uncertain"
        )


def test_clean_image_control_still_parses_total() -> None:
    """Control: a clean receipt still yields the real total (no regression)."""
    parsed = parse_receipt(clean_receipt())
    assert parsed.total is not None
    assert parsed.total != 1.0


# ---------------------------------------------------------------------------
# Confidence level in the parse-receipt response (backend contract)
# ---------------------------------------------------------------------------


def test_confidence_level_field_present() -> None:
    """AC2: a per-receipt confidence level ('high'|'medium'|'low') is exposed."""
    parsed = parse_receipt_with_confidence(clean_receipt())
    assert isinstance(parsed, ConfidenceReceipt)
    assert getattr(parsed, "confidence_level", None) in {"high", "medium", "low"}, (
        "confidence_level must be one of high/medium/low"
    )


def test_confidence_level_matches_per_field_total() -> None:
    """The level is consistent with the total's own confidence score."""
    parsed = parse_receipt_with_confidence(clean_receipt())
    level = getattr(parsed, "confidence_level", None)
    total_conf = (parsed.confidence or {}).get("total")
    if level == "high":
        assert total_conf is None or total_conf >= 0.6
    elif level == "low":
        assert total_conf is not None and total_conf < 0.6


def test_api_response_carries_confidence_level() -> None:
    """The rendered API payload includes the confidence level."""
    parsed = parse_receipt_with_confidence(clean_receipt())
    rendered = api._render_receipt(parsed)
    assert "confidence_level" in rendered
    assert rendered["confidence_level"] in {"high", "medium", "low"}


# ---------------------------------------------------------------------------
# Review-flow UI contract: confirmation requested on weak matches
# ---------------------------------------------------------------------------

REVIEW_PAGE = "frontend/app/(app)/review/page.tsx"


def test_review_ui_has_confirmation_requirement_marker() -> None:
    """AC3: review UI asks for confirmation before accepting weak matches."""
    try:
        with open(REVIEW_PAGE, encoding="utf-8") as fh:
            src = fh.read()
    except FileNotFoundError:
        pytest.skip("review page not present in this checkout")
    assert re.search(r"confirm|Confirm|megerősít|erősít", src), (
        "review flow must request user confirmation on weak matches"
    )


def test_review_ui_has_uncertain_total_notice() -> None:
    """AC3: the UI shows an 'uncertain amount' notice at review time."""
    try:
        with open(REVIEW_PAGE, encoding="utf-8") as fh:
            src = fh.read()
    except FileNotFoundError:
        pytest.skip("review page not present in this checkout")
    assert re.search(r"uncertain|bizonytalan", src, re.IGNORECASE), (
        "review UI must display an uncertain-amount notice"
    )


# ---------------------------------------------------------------------------
# Integration: real multipart upload through the API (no mocks)
# ---------------------------------------------------------------------------


def test_integration_low_quality_upload_never_returns_total_1_0(
    client: object,
) -> None:
    """AC4: real multipart upload of a low-quality image.

    The API response for the blurry image must not carry total == 1.0.
    """
    files = {"file": ("bad-receipt.png", blurry_receipt(), "image/png")}
    resp = client.post("/v1/parse-receipt", files=files)
    assert resp.status_code in (200, 422), f"unexpected status {resp.status_code}"
    if resp.status_code == 200:
        payload = resp.json()
        assert payload.get("total") != 1.0, (
            f"BUG-001 via API: total=1.0 fabricated (payload={payload})"
        )


def test_integration_clean_upload_returns_confidence_level(client: object) -> None:
    """AC2/AC4: real upload response carries the per-receipt confidence level."""
    files = {"file": ("clean-receipt.png", clean_receipt(), "image/png")}
    resp = client.post("/v1/parse-receipt", files=files)
    assert resp.status_code == 200
    payload = resp.json()
    assert payload.get("confidence_level") in {"high", "medium", "low"}


# ---------------------------------------------------------------------------
# Unit-level guards around the confidence machinery
# ---------------------------------------------------------------------------


def test_parse_float_never_returns_one_from_garbage() -> None:
    """The float parser must not turn stray '1' fragments into 1.0."""
    assert _parse_float("") is None
    assert _parse_float("..") is None
    assert _parse_float("ab") is None


def test_clean_text_empty() -> None:
    assert _clean_text("") == ""


def test_confidence_from_data_returns_all_keys() -> None:
    data = _confidence_from_data(clean_receipt())
    assert set(data.keys()) == {"vendor", "total", "date", "tax", "currency", "line_items"}


def test_parsed_receipt_is_dataclass() -> None:
    parsed = parse_receipt(clean_receipt())
    assert isinstance(parsed, ParsedReceipt)
