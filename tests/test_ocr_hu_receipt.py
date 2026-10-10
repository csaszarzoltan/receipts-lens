"""Hungarian (HUF, whole-unit) receipts through the full parse pipeline.

Found by an end-to-end run: a date line ("2024.03.05") looked like a cents
amount and switched off the space-grouping rule; "Osszesen" (OCR without the
accent) was neither a total nor excluded from line items; and "Ft" was not
recognised, so the currency fell back to USD.
"""

from __future__ import annotations

import pytest

from app import ocr

HU_TEXT = "BOLT KFT\n2024.03.05\nCoffee 3 500 Ft\nTea 900 Ft\nOsszesen 4 400 Ft"


@pytest.fixture
def hu_receipt(monkeypatch):
    monkeypatch.setattr(ocr, "extract_text", lambda image_bytes, lang="eng": HU_TEXT)
    return ocr.parse_receipt(b"unused")


@pytest.mark.test_id("TEST-RL-V02-156")
@pytest.mark.requirements("FEAT-RL-V02-REQ-059")
@pytest.mark.scenario("AC-RL-V02-40")
def test_date_line_does_not_count_as_cents(hu_receipt):
    assert [(i.name, i.price) for i in hu_receipt.items] == [
        ("Coffee", 3500.0),
        ("Tea", 900.0),
    ]


@pytest.mark.test_id("TEST-RL-V02-157")
@pytest.mark.requirements("FEAT-RL-V02-REQ-059")
@pytest.mark.scenario("AC-RL-V02-40")
def test_total_is_recognised_without_accent(hu_receipt):
    assert hu_receipt.total == 4400.0


@pytest.mark.test_id("TEST-RL-V02-158")
@pytest.mark.requirements("FEAT-RL-V02-REQ-059")
@pytest.mark.scenario("AC-RL-V02-40")
def test_total_line_is_not_a_line_item(hu_receipt):
    assert "Osszesen 4" not in [i.name for i in hu_receipt.items]


@pytest.mark.test_id("TEST-RL-V02-159")
@pytest.mark.requirements("FEAT-RL-V02-REQ-059")
@pytest.mark.scenario("AC-RL-V02-40")
def test_ft_suffix_gives_huf_currency(hu_receipt):
    assert hu_receipt.currency == "HUF"


@pytest.mark.test_id("TEST-RL-V02-160")
@pytest.mark.requirements("FEAT-RL-V02-REQ-059")
@pytest.mark.scenario("AC-RL-V02-40")
def test_date_is_iso(hu_receipt):
    assert hu_receipt.date == "2024-03-05"


@pytest.mark.test_id("TEST-RL-V02-161")
@pytest.mark.requirements("FEAT-RL-V02-REQ-059")
@pytest.mark.scenario("AC-RL-V02-40")
def test_total_keyword_matches_without_accent():
    """Asserts the keyword itself, not the last-number fallback in parse_receipt."""
    captured = ocr._find_first(ocr._TOTAL_RE, "Osszesen 4 400 Ft")
    assert ocr._parse_float(captured) == 4400.0
