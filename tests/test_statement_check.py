"""A bank statement is checked against receipts without being stored, in the layouts banks really use."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.ocr import ConfidenceReceipt
from app.statement_check import (
    MAX_BYTES,
    Line,
    StatementError,
    match,
    parse_amount,
    parse_date,
    parse_statement,
)

client = TestClient(app)

HUNGARIAN = (
    "Számlaszám;12345678-12345678\n"
    "Könyvelés dátuma;Partner neve;Közlemény;Összeg;Pénznem\n"
    "2026.10.05.;KISBOLT KFT;kártyás vásárlás;-3 267,00;HUF\n"
    "2026.10.06.;Fizetés;munkabér;450 000,00;HUF\n"
    "2026.10.07.;TESCO;kártyás vásárlás;-12 990,50;HUF\n"
).encode("cp1250")

ENGLISH_ALL_POSITIVE = "Date,Description,Amount\n2026-10-05,Corner shop,8.15\n2026-10-06,Cafe,\"1,250.00\"\n"
DEBIT_CREDIT = "Dátum;Megnevezés;Terhelés;Jóváírás\n05/10/2026;Bolt;3267;\n06/10/2026;Fizetés;;450000\n"


def _receipt(rid="r1", total=3267.0, day="2026-10-05", currency="HUF", candidate=None, vendor="Kisbolt"):
    return {"receipt_id": rid, "vendor": vendor, "date": day, "total": total, "total_candidate": candidate,
            "currency": currency, "version": 1}


@pytest.mark.parametrize(("text", "expected"), [
    ("-3 267,00", -3267.0), ("1.234,56", 1234.56), ("1,234.56", 1234.56), ("4,400", 4400.0),
    ("12,5", 12.5), ("(450,00)", -450.0), ("−4 400 Ft", -4400.0), ("8.15", 8.15), ("3 267", 3267.0),
])
@pytest.mark.test_id("TEST-RL-V02-246")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-49")
def test_amounts_are_read_in_either_number_style(text, expected) -> None:
    assert parse_amount(text) == pytest.approx(expected)


@pytest.mark.test_id("TEST-RL-V02-247")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-49")
def test_text_that_is_not_an_amount_is_not_guessed() -> None:
    assert parse_amount("") is None and parse_amount("n/a") is None


@pytest.mark.parametrize(("text", "expected"), [
    ("2026.10.05.", date(2026, 10, 5)), ("2026. 10. 05.", date(2026, 10, 5)), ("2026-10-05", date(2026, 10, 5)),
    ("05/10/2026", date(2026, 10, 5)), ("31.12.2026", date(2026, 12, 31)), ("2026-10-05T10:00:00", date(2026, 10, 5)),
])
@pytest.mark.test_id("TEST-RL-V02-248")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-49")
def test_dates_are_read_in_the_formats_banks_write(text, expected) -> None:
    assert parse_date(text) == expected


@pytest.mark.test_id("TEST-RL-V02-249")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-49")
def test_an_impossible_date_is_refused() -> None:
    assert parse_date("2026.13.45.") is None and parse_date("soon") is None


@pytest.mark.test_id("TEST-RL-V02-250")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-50")
def test_a_hungarian_export_is_read_and_only_spending_is_kept() -> None:
    parsed = parse_statement(HUNGARIAN)
    assert [(x.date.isoformat(), x.amount, x.currency) for x in parsed["lines"]] == [
        ("2026-10-05", 3267.0, "HUF"), ("2026-10-07", 12990.5, "HUF")]
    assert "partner" not in parsed["lines"][0].description and "KISBOLT" in parsed["lines"][0].description
    assert parsed["direction"] == "negative_is_spending"
    assert parsed["delimiter"] == ";"


@pytest.mark.test_id("TEST-RL-V02-251")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-50")
def test_a_card_export_with_only_positive_amounts_is_all_spending_and_says_so() -> None:
    parsed = parse_statement(ENGLISH_ALL_POSITIVE.encode())
    assert [x.amount for x in parsed["lines"]] == [8.15, 1250.0]
    assert parsed["direction"] == "all_positive_is_spending"


@pytest.mark.test_id("TEST-RL-V02-252")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-50")
def test_separate_debit_and_credit_columns_keep_the_debits_only() -> None:
    parsed = parse_statement(DEBIT_CREDIT.encode())
    assert [(x.date.isoformat(), x.amount) for x in parsed["lines"]] == [("2026-10-05", 3267.0)]


@pytest.mark.test_id("TEST-RL-V02-253")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-50")
@pytest.mark.parametrize("raw", [b"", b"hello\nworld\n", b"Date,Amount\nsoon,lots\n"])
def test_a_file_that_is_not_a_statement_is_refused_with_a_reason(raw) -> None:
    with pytest.raises(StatementError):
        parse_statement(raw)


@pytest.mark.test_id("TEST-RL-V02-254")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-50")
def test_an_oversized_file_is_refused() -> None:
    with pytest.raises(StatementError, match="larger than 1 MB"):
        parse_statement(b"x" * (MAX_BYTES + 1))


def _line(day=5, amount=3267.0, currency=None):
    return Line(row=2, date=date(2026, 10, day), amount=amount, description="shop", currency=currency)


@pytest.mark.test_id("TEST-RL-V02-255")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-51")
def test_a_line_matches_the_receipt_with_the_same_amount_and_a_close_date() -> None:
    result = match([_line(7)], [_receipt()])
    assert [(m["receipt"]["receipt_id"], m["confirmed"]) for m in result["matched"]] == [("r1", True)]


@pytest.mark.test_id("TEST-RL-V02-256")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-51")
def test_dates_further_apart_than_the_window_do_not_match() -> None:
    result = match([_line(20)], [_receipt()])
    assert result["matched"] == [] and len(result["unmatched_lines"]) == 1


@pytest.mark.test_id("TEST-RL-V02-257")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-51")
def test_each_receipt_is_used_once_and_the_closest_date_wins() -> None:
    lines = [_line(5), _line(6)]
    receipts = [_receipt("far", day="2026-10-08"), _receipt("near", day="2026-10-06")]
    result = match(lines, receipts)
    assert {m["line"].date.day: m["receipt"]["receipt_id"] for m in result["matched"]} == {5: "near", 6: "far"}


@pytest.mark.test_id("TEST-RL-V02-258")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-51")
def test_an_unconfirmed_receipt_matches_on_what_ocr_read_and_is_marked_unconfirmed() -> None:
    result = match([_line()], [_receipt(total=None, candidate=3267.0)])
    assert [m["confirmed"] for m in result["matched"]] == [False]


@pytest.mark.test_id("TEST-RL-V02-259")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-51")
def test_a_different_currency_is_not_a_match() -> None:
    assert match([_line(currency="EUR")], [_receipt(currency="HUF")])["matched"] == []
    assert len(match([_line(currency=None)], [_receipt(currency="HUF")])["matched"]) == 1


@pytest.mark.test_id("TEST-RL-V02-260")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-52")
def test_a_close_but_different_amount_is_offered_as_a_possible_misread() -> None:
    result = match([_line(amount=3627.0)], [_receipt(total=3267.0)])
    assert result["matched"] == [] and result["unmatched_lines"] == []
    assert [(s["line"].amount, s["receipt_amount"]) for s in result["suggestions"]] == [(3627.0, 3267.0)]


@pytest.mark.test_id("TEST-RL-V02-261")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-52")
def test_receipts_outside_the_statement_period_are_not_reported_as_missing_from_it() -> None:
    receipts = [_receipt("inside", total=500.0, day="2026-10-06"), _receipt("outside", total=500.0, day="2026-06-01")]
    result = match([_line(5, 3267.0)], receipts)
    assert [r["receipt_id"] for r in result["unmatched_receipts"]] == ["inside"]
    assert result["suggestions"] == []


def _upload(tenant: str, total, candidate=None, day="2026-10-05", currency="HUF") -> str:
    parsed = ConfidenceReceipt(merchant="Kisbolt", date=day, items=[], total=total, tax=None, currency=currency,
                               raw_text="", confidence={"merchant": 0.9, "total": 0.9},
                               currency_source="marker", total_candidate=candidate)
    with patch("app.product_api.parse_receipt_with_confidence", return_value=parsed):
        created = client.post("/product/receipts/upload", headers={"X-Tenant-ID": tenant, "X-Role": "admin"},
                              files={"file": ("r.png", b"image", "image/png")})
    assert created.status_code == 201
    return created.json()["receipt_id"]


def _check(tenant: str, content: bytes):
    return client.post("/product/statement-check", headers={"X-Tenant-ID": tenant, "X-Role": "admin"},
                       files={"file": ("statement.csv", content, "text/csv")})


@pytest.mark.test_id("TEST-RL-V02-262")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-53")
def test_the_api_matches_a_statement_to_the_households_receipts() -> None:
    rid = _upload("stmt-1", 3267.0)
    body = _check("stmt-1", HUNGARIAN).json()
    assert body["counts"] == {"lines": 2, "matched": 1, "unmatched_lines": 1, "unmatched_receipts": 0, "suggestions": 0}
    assert body["matched"][0]["receipt"]["receipt_id"] == rid
    assert body["unmatched_lines"][0]["amount"] == 12990.5
    assert body["assumptions"] == {"direction": "negative_is_spending", "skipped_rows": 0, "date_order": "day_first"}


@pytest.mark.test_id("TEST-RL-V02-263")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-53")
def test_the_api_reports_an_unconfirmed_receipt_with_its_version_so_it_can_be_confirmed() -> None:
    rid = _upload("stmt-2", None, candidate=3267.0)
    matched = _check("stmt-2", HUNGARIAN).json()["matched"]
    assert [(m["receipt"]["receipt_id"], m["confirmed"], m["receipt"]["version"]) for m in matched] == [(rid, False, 1)]


@pytest.mark.test_id("TEST-RL-V02-264")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-54")
def test_another_households_receipts_are_never_matched() -> None:
    _upload("stmt-3", 3267.0)
    body = _check("stmt-4", HUNGARIAN).json()
    assert body["counts"]["matched"] == 0 and body["counts"]["unmatched_lines"] == 2


@pytest.mark.test_id("TEST-RL-V02-265")
@pytest.mark.requirements("FEAT-RL-V02-REQ-065")
@pytest.mark.scenario("AC-RL-V02-54")
def test_the_api_explains_why_a_file_was_refused_and_stores_nothing() -> None:
    response = _check("stmt-5", b"this is not a statement")
    assert response.status_code == 422
    assert "date and amount" in response.json()["detail"]
    assert client.get("/product/review-items", headers={"X-Tenant-ID": "stmt-5", "X-Role": "admin"}).json()["items"] == []
