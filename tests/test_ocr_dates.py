"""Receipt dates without a "Date:" label, and ISO normalization.

Many receipts print the date as a bare line ("2024-03-05", "05.03.2024").
The labelled-only pattern missed those, so the date came back empty.
"""

from __future__ import annotations

import pytest

from app import ocr


@pytest.mark.parametrize(
    ("text", "raw"),
    [
        ("ACME\n2024-03-05\nMilk 1.20", "2024-03-05"),
        ("ACME\n05.03.2024\nMilk 1.20", "05.03.2024"),
        ("ACME\nDate: 05/03/2024\nMilk 1.20", "05/03/2024"),
    ],
)
@pytest.mark.test_id("TEST-RL-V02-162")
@pytest.mark.requirements("FEAT-RL-V02-REQ-059")
@pytest.mark.scenario("AC-RL-V02-40")
def test_extract_date_finds_labelled_and_bare_dates(text, raw):
    assert ocr._extract_date_raw(text) == raw


@pytest.mark.parametrize(
    ("raw", "iso"),
    [
        ("2024-03-05", "2024-03-05"),
        ("2024/03/05", "2024-03-05"),
        ("05.03.2024", "2024-03-05"),
        ("05/03/2024", "2024-03-05"),
    ],
)
@pytest.mark.test_id("TEST-RL-V02-163")
@pytest.mark.requirements("FEAT-RL-V02-REQ-059")
@pytest.mark.scenario("AC-RL-V02-40")
def test_normalize_date_returns_iso(raw, iso):
    assert ocr._normalize_date(raw) == iso


@pytest.mark.test_id("TEST-RL-V02-164")
@pytest.mark.requirements("FEAT-RL-V02-REQ-059")
@pytest.mark.scenario("AC-RL-V02-40")
def test_parse_receipt_reports_bare_date(monkeypatch):
    monkeypatch.setattr(
        ocr, "extract_text", lambda image_bytes, lang="eng": "ACME\n2024-03-05\nTOTAL 3.70"
    )
    parsed = ocr.parse_receipt(b"unused")
    assert parsed.date == "2024-03-05"
