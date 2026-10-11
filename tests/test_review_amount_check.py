"""Review must offer an amount to confirm and say whether the lines support it."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.ocr import ConfidenceReceipt, ReceiptItem
from app.product_service import line_sum_check

client = TestClient(app)


def _headers(tenant: str, role: str = "admin") -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-Role": role}


def _legacy_upload(tenant: str, items: list[ReceiptItem] | None = None) -> str:
    """Upload a receipt the way old data looks: no total and no candidate saved."""
    parsed = ConfidenceReceipt(
        merchant=None, date="2026-10-01", items=items or [], total=None, tax=None,
        currency="HUF", raw_text="", confidence={"merchant": 0.1, "total": 0.1},
        total_candidate=None,
    )
    with patch("app.product_api.parse_receipt_with_confidence", return_value=parsed):
        created = client.post(
            "/product/receipts/upload", headers=_headers(tenant),
            files={"file": ("receipt.png", b"image", "image/png")},
        )
    assert created.status_code == 201
    return created.json()["receipt_id"]


def _review(tenant: str, receipt_id: str) -> dict:
    items = client.get("/product/review-items", headers=_headers(tenant)).json()["items"]
    return next(i for i in items if i["receipt_id"] == receipt_id)


@pytest.mark.test_id("TEST-RL-V02-219")
@pytest.mark.requirements("FEAT-RL-V02-REQ-062")
@pytest.mark.scenario("AC-RL-V02-43")
def test_lines_that_add_up_to_the_amount_match() -> None:
    payload = {"total": 1000.0, "line_items": [{"price": 600.0}, {"price": 400.0}]}
    assert line_sum_check(payload) == {"line_sum": 1000.0, "lines_match": True}


@pytest.mark.test_id("TEST-RL-V02-220")
@pytest.mark.requirements("FEAT-RL-V02-REQ-062")
@pytest.mark.scenario("AC-RL-V02-43")
def test_lines_may_add_up_to_the_amount_before_tax() -> None:
    payload = {"total": 1270.0, "tax": 270.0, "line_items": [{"price": 600.0}, {"price": 400.0}]}
    assert line_sum_check(payload)["lines_match"] is True


@pytest.mark.test_id("TEST-RL-V02-221")
@pytest.mark.requirements("FEAT-RL-V02-REQ-062")
@pytest.mark.scenario("AC-RL-V02-43")
def test_lines_that_do_not_add_up_are_reported_with_their_sum() -> None:
    payload = {"total": 1500.0, "line_items": [{"price": 600.0}, {"price": 400.0}]}
    assert line_sum_check(payload) == {"line_sum": 1000.0, "lines_match": False}


@pytest.mark.test_id("TEST-RL-V02-222")
@pytest.mark.requirements("FEAT-RL-V02-REQ-062")
@pytest.mark.scenario("AC-RL-V02-43")
def test_nothing_to_compare_is_unknown_not_a_mismatch() -> None:
    assert line_sum_check({"total": 1000.0, "line_items": []}) == {"line_sum": None, "lines_match": None}
    assert line_sum_check({"total": None, "line_items": [{"price": 5.0}]}) == {"line_sum": 5.0, "lines_match": None}
    assert line_sum_check({"line_items": [{"name": "unpriced", "price": None}]})["lines_match"] is None


@pytest.mark.test_id("TEST-RL-V02-223")
@pytest.mark.requirements("FEAT-RL-V02-REQ-062")
@pytest.mark.scenario("AC-RL-V02-43")
def test_the_ocr_candidate_is_what_the_lines_are_compared_with() -> None:
    payload = {"total": None, "total_candidate": 1000.0, "line_items": [{"price": 1000.0}]}
    assert line_sum_check(payload)["lines_match"] is True


@pytest.mark.test_id("TEST-RL-V02-224")
@pytest.mark.requirements("FEAT-RL-V02-REQ-062")
@pytest.mark.scenario("AC-RL-V02-43")
def test_review_items_carry_the_check() -> None:
    receipt_id = _legacy_upload("amount-check-1", [ReceiptItem(name="Bread", price=420.0)])
    assert _review("amount-check-1", receipt_id)["checks"] == {"line_sum": 420.0, "lines_match": None}


@pytest.mark.test_id("TEST-RL-V02-225")
@pytest.mark.requirements("FEAT-RL-V02-REQ-062")
@pytest.mark.scenario("AC-RL-V02-44")
def test_reread_offers_the_amount_without_confirming_it() -> None:
    receipt_id = _legacy_upload("amount-reread-1", [ReceiptItem(name="Bread", price=420.0)])
    assert _review("amount-reread-1", receipt_id)["receipt"]["total_candidate"] is None

    with patch("app.product_api.parse_receipt", return_value=SimpleNamespace(total=420.0)):
        result = client.post("/product/review-items/reread", headers=_headers("amount-reread-1"))
    assert result.json() == {"updated": 1, "failed": 0, "remaining": 0}

    item = _review("amount-reread-1", receipt_id)
    assert item["receipt"]["total"] is None, "the user still has to confirm the amount"
    assert item["receipt"]["total_candidate"] == 420.0
    assert item["checks"] == {"line_sum": 420.0, "lines_match": True}


@pytest.mark.test_id("TEST-RL-V02-226")
@pytest.mark.requirements("FEAT-RL-V02-REQ-062")
@pytest.mark.scenario("AC-RL-V02-44")
def test_a_receipt_read_once_is_not_read_again_even_when_nothing_was_found() -> None:
    _legacy_upload("amount-reread-2")
    with patch("app.product_api.parse_receipt", return_value=SimpleNamespace(total=None)) as reader:
        first = client.post("/product/review-items/reread", headers=_headers("amount-reread-2")).json()
        second = client.post("/product/review-items/reread", headers=_headers("amount-reread-2")).json()
    assert first["updated"] == 1
    assert second == {"updated": 0, "failed": 0, "remaining": 0}
    assert reader.call_count == 1


@pytest.mark.test_id("TEST-RL-V02-227")
@pytest.mark.requirements("FEAT-RL-V02-REQ-062")
@pytest.mark.scenario("AC-RL-V02-44")
def test_reread_works_in_batches_and_reports_what_is_left() -> None:
    for _ in range(3):
        _legacy_upload("amount-reread-3")
    with patch("app.product_api.parse_receipt", return_value=SimpleNamespace(total=9.0)):
        first = client.post("/product/review-items/reread?limit=2", headers=_headers("amount-reread-3")).json()
        second = client.post("/product/review-items/reread?limit=2", headers=_headers("amount-reread-3")).json()
    assert first == {"updated": 2, "failed": 0, "remaining": 1}
    assert second == {"updated": 1, "failed": 0, "remaining": 0}


@pytest.mark.test_id("TEST-RL-V02-228")
@pytest.mark.requirements("FEAT-RL-V02-REQ-062")
@pytest.mark.scenario("AC-RL-V02-44")
def test_a_failing_image_does_not_stop_the_batch_and_is_retried_later() -> None:
    _legacy_upload("amount-reread-4")
    _legacy_upload("amount-reread-4")
    calls = iter([RuntimeError("tesseract failed"), SimpleNamespace(total=5.0)])

    def reader(_content: bytes):
        value = next(calls)
        if isinstance(value, Exception):
            raise value
        return value

    with patch("app.product_api.parse_receipt", side_effect=reader):
        result = client.post("/product/review-items/reread", headers=_headers("amount-reread-4")).json()
    assert result == {"updated": 1, "failed": 1, "remaining": 1}


@pytest.mark.test_id("TEST-RL-V02-229")
@pytest.mark.requirements("FEAT-RL-V02-REQ-062")
@pytest.mark.scenario("AC-RL-V02-44")
def test_reread_stays_inside_the_callers_household_and_needs_write_access() -> None:
    mine = _legacy_upload("amount-reread-5")
    theirs = _legacy_upload("amount-reread-6")
    with patch("app.product_api.parse_receipt", return_value=SimpleNamespace(total=7.0)):
        denied = client.post("/product/review-items/reread", headers=_headers("amount-reread-5", "view_only"))
        assert denied.status_code == 403
        client.post("/product/review-items/reread", headers=_headers("amount-reread-5"))
    assert _review("amount-reread-5", mine)["receipt"]["total_candidate"] == 7.0
    assert _review("amount-reread-6", theirs)["receipt"]["total_candidate"] is None
