"""The OCR total is withheld by the BUG-001 gate, but not discarded.

When the confidence gate hides ``total`` (typically because the merchant could
not be read), the value OCR read is kept as ``total_candidate``. The review
screen shows it and the user confirms it; nothing is saved as a total unless
the user does so.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app import ocr
from app.product_service import Actor, ProductService

TEXT = "NEWSHOP\n2024-03-09\nPen 1.20\nPaper 3.00\nTOTAL 4.20"


@pytest.fixture
def low_vendor(monkeypatch):
    monkeypatch.setattr(ocr, "extract_text", lambda image_bytes, lang="eng": TEXT)
    monkeypatch.setattr(
        ocr, "_confidence_from_data",
        lambda image_bytes: {"vendor": 0.0, "total": 0.88, "date": 0.88, "tax": 0.0,
                             "currency": 0.88, "line_items": 0.88},
    )


@pytest.mark.test_id("TEST-RL-V02-192")
@pytest.mark.requirements("FEAT-RL-V02-REQ-062")
@pytest.mark.scenario("AC-RL-V02-43")
def test_gated_total_is_withheld_but_kept_as_candidate(low_vendor):
    parsed = ocr.parse_receipt_with_confidence(b"unused")
    assert parsed.total is None
    assert parsed.total_candidate == 4.2


@pytest.mark.test_id("TEST-RL-V02-193")
@pytest.mark.requirements("FEAT-RL-V02-REQ-062")
@pytest.mark.scenario("AC-RL-V02-43")
def test_candidate_is_stored_on_the_receipt_and_total_stays_empty():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "admin")
    parsed = SimpleNamespace(
        merchant=None, date="2024-03-09", total=None, total_candidate=4.2, tax=None,
        currency="USD", currency_source="marker", items=[],
        confidence={"vendor": 0.0, "total": 0.88},
    )
    rid = service.create_receipt(actor, parsed, "x.png")["receipt_id"]
    payload = service.get_receipt(actor, rid)["receipt"]
    assert payload["total"] is None
    assert payload["total_candidate"] == 4.2


@pytest.mark.test_id("TEST-RL-V02-194")
@pytest.mark.requirements("FEAT-RL-V02-REQ-062")
@pytest.mark.scenario("AC-RL-V02-43")
def test_confirming_the_candidate_saves_it_as_total():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "admin")
    parsed = SimpleNamespace(
        merchant=None, date="2024-03-09", total=None, total_candidate=4.2, tax=None,
        currency="USD", currency_source="marker", items=[],
        confidence={"vendor": 0.0, "total": 0.88},
    )
    rid = service.create_receipt(actor, parsed, "x.png")["receipt_id"]
    out = service.correct(actor, rid, {"total": 4.2}, expected_version=1, complete=True)
    assert out["receipt"]["total"] == 4.2
    assert out["status"] == "completed"
