"""A file uploaded twice is an exact duplicate whatever OCR read (I10), and a missing total is not a blind spot (I12)."""
from types import SimpleNamespace

import pytest

from app.advanced_workspace import AdvancedWorkspace
from app.product_service import Actor, ProductService

CONF = {k: .95 for k in ("vendor", "date", "total", "tax", "currency", "line_items")}


def parsed(vendor="COOP", total=None, date="2026-08-13", candidate=2026.0):
    return SimpleNamespace(merchant=vendor, date=date, total=total, total_candidate=candidate, tax=0.0,
                           currency="CHF", items=[], confidence=CONF)


@pytest.fixture
def bundle():
    service = ProductService(":memory:")
    return service, AdvancedWorkspace(service), Actor("tenant-a", "admin"), Actor("tenant-b", "admin")


def add(service, advanced, actor, content, **kw):
    rid = service.create_receipt(actor, parsed(**kw), "a.jpg")["receipt_id"]
    advanced.store_asset(actor.tenant_id, rid, content, "image/jpeg", "a.jpg")
    return rid


def test_find_same_file_returns_the_earliest_receipt_with_identical_bytes(bundle):
    service, advanced, a, _ = bundle
    first = add(service, advanced, a, b"bytes-1")
    assert advanced.find_same_file("tenant-a", b"bytes-1") == first
    assert advanced.find_same_file("tenant-a", b"bytes-2") is None


def test_same_bytes_with_null_totals_is_listed_as_same_file(bundle):
    service, advanced, a, _ = bundle
    first = add(service, advanced, a, b"x")
    second = add(service, advanced, a, b"x", vendor="Other", date=None, candidate=None)
    pairs = advanced.duplicates(a)
    assert len(pairs) == 1 and pairs[0]["reason"] == "same_file" and pairs[0]["confidence"] == 1.0
    assert {pairs[0]["left_id"], pairs[0]["right_id"]} == {first, second}


def test_other_tenant_gets_no_match(bundle):
    service, advanced, a, b = bundle
    add(service, advanced, a, b"x")
    assert advanced.find_same_file("tenant-b", b"x") is None
    add(service, advanced, b, b"x")
    assert advanced.duplicates(b) == [] and advanced.duplicates(a) == []


def test_dismissed_same_file_pair_stays_dismissed(bundle):
    service, advanced, a, _ = bundle
    first = add(service, advanced, a, b"x")
    second = add(service, advanced, a, b"x")
    advanced.decide_duplicate("tenant-a", first, second, "different")
    assert advanced.duplicates(a) == []


def test_different_files_with_different_data_are_not_a_pair(bundle):
    service, advanced, a, _ = bundle
    add(service, advanced, a, b"x", vendor="COOP", candidate=10.0)
    add(service, advanced, a, b"y", vendor="MIGROS", candidate=20.0)
    assert advanced.duplicates(a) == []


def test_missing_total_pair_with_equal_vendor_date_and_candidate_is_a_candidate(bundle):
    service, advanced, a, _ = bundle
    add(service, advanced, a, b"photo-1")
    add(service, advanced, a, b"photo-2")
    pairs = advanced.duplicates(a)
    assert len(pairs) == 1 and pairs[0]["reason"] == "candidate_total"


def test_missing_total_pair_with_different_candidate_is_not_a_candidate(bundle):
    service, advanced, a, _ = bundle
    add(service, advanced, a, b"photo-1", candidate=2026.0)
    add(service, advanced, a, b"photo-2", candidate=99.0)
    assert advanced.duplicates(a) == []


def test_missing_total_pair_without_a_date_is_not_a_candidate(bundle):
    service, advanced, a, _ = bundle
    add(service, advanced, a, b"photo-1", date=None)
    add(service, advanced, a, b"photo-2", date=None)
    assert advanced.duplicates(a) == []
