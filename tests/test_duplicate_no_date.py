"""Duplicate candidates must still be found when a receipt has no date (I7).

Real case: two TESCO EXPRESS receipts with total 4786.0 and date NULL were
not offered as a duplicate pair.
"""
from types import SimpleNamespace

import pytest

from app.advanced_workspace import AdvancedWorkspace
from app.product_service import Actor, ProductService


def parsed_without_date(vendor, total):
    return SimpleNamespace(
        merchant=vendor, date=None, total=total, tax=0.0, currency="HUF",
        items=[SimpleNamespace(name="Item", price=total)],
        confidence={k: .95 for k in ("vendor", "date", "total", "tax", "currency", "line_items")},
    )


@pytest.fixture
def bundle():
    service = ProductService(":memory:")
    advanced = AdvancedWorkspace(service)
    actor = Actor("tenant-a", "admin")
    return service, advanced, actor


def test_pair_with_equal_vendor_and_total_and_no_date_is_a_candidate(bundle):
    service, advanced, actor = bundle
    first = service.create_receipt(actor, parsed_without_date("TESCO EXPRESS", 4786.0), "a.png")["receipt_id"]
    second = service.create_receipt(actor, parsed_without_date("TESCO EXPRESS", 4786.0), "b.png")["receipt_id"]
    candidates = advanced.duplicates(actor)
    assert len(candidates) == 1
    assert {candidates[0]["left_id"], candidates[0]["right_id"]} == {first, second}
    assert candidates[0]["evidence"] == {"vendor": True, "total": True, "date": False}
    assert candidates[0]["confidence"] == 0.67


def test_pair_with_different_total_and_no_date_is_not_a_candidate(bundle):
    service, advanced, actor = bundle
    service.create_receipt(actor, parsed_without_date("TESCO EXPRESS", 4786.0), "a.png")
    service.create_receipt(actor, parsed_without_date("TESCO EXPRESS", 1200.0), "b.png")
    assert advanced.duplicates(actor) == []


def test_ocr_path_groups_pair_with_no_date():
    from app.ocr import _group_duplicates

    receipts = [
        {"vendor": "TESCO EXPRESS", "total": 4786.0, "date": None},
        {"vendor": "TESCO EXPRESS", "total": 4786.0, "date": None},
    ]
    result = _group_duplicates(receipts)
    assert len(result.duplicate_groups) == 1
    assert result.duplicate_groups[0].indices == [0, 1]


def test_category_suggestion_is_offered_and_never_written_to_the_other_receipt():
    from app.product_service import ProductService as _PS

    service = _PS(":memory:")
    actor = Actor("tenant-a", "admin")
    first = service.create_receipt(actor, parsed_without_date("Tesco", 10.0), "a.png")["receipt_id"]
    second = service.create_receipt(actor, parsed_without_date("TESCO", 20.0), "b.png")["receipt_id"]
    first_version = service.get_receipt(actor, first)["version"]
    service.update_receipt_workspace(actor, first, first_version, {"category": "Groceries"}, None, None, True)

    before = service.get_receipt(actor, second)
    assert before["suggested_category"] == "Groceries"
    assert before["receipt"].get("category") is None
    assert before["receipt"].get("category_source") != "user"

    after = service.get_receipt(actor, second)
    assert after["receipt"] == before["receipt"]
