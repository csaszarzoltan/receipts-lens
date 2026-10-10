"""Thousands grouping without decimals must not be read as a small amount.

Receipts that print whole-unit totals (``TOTAL 1,234``, ``Összesen 1.250 Ft``)
used to be parsed as ``1.23`` / ``1.25`` / ``1.0``: a silent understatement.
"""

from __future__ import annotations

import pytest

from app import ocr


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1,000", 1000.0),
        ("1,234", 1234.0),
        ("1.250", 1250.0),
        ("1,000,000", 1000000.0),
        ("1.000.000", 1000000.0),
        # Decimal forms must keep working.
        ("12,50", 12.5),
        ("12.50", 12.5),
        ("1.234,56", 1234.56),
        ("1,234.56", 1234.56),
        ("$12.50", 12.5),
        ("42", 42.0),
    ],
)
@pytest.mark.test_id("TEST-RL-V02-146")
@pytest.mark.requirements("FEAT-RL-V02-REQ-058")
@pytest.mark.scenario("AC-RL-V02-39")
def test_parse_float_handles_thousands_grouping(raw, expected):
    assert ocr._parse_float(raw) == expected


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("TOTAL 1,234", 1234.0),
        ("Grand total: 1,000", 1000.0),
        ("TOTAL 1,234.50", 1234.5),
    ],
)
@pytest.mark.test_id("TEST-RL-V02-147")
@pytest.mark.requirements("FEAT-RL-V02-REQ-058")
@pytest.mark.scenario("AC-RL-V02-39")
def test_total_regex_captures_whole_thousands_amount(line, expected):
    """The amount regex must capture the full grouped number, not a prefix."""
    captured = ocr._find_first(ocr._TOTAL_RE, line)
    assert ocr._parse_float(captured) == expected


@pytest.mark.test_id("TEST-RL-V02-148")
@pytest.mark.requirements("FEAT-RL-V02-REQ-058")
@pytest.mark.scenario("AC-RL-V02-39")
def test_line_item_with_thousands_price_is_not_truncated():
    items = ocr._parse_line_items("Laptop bag 1,250")
    assert [(i.name, i.price) for i in items] == [("Laptop bag", 1250.0)]


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("Összesen 1.250", 1250.0),
        ("Összesen: 1.250,50", 1250.5),
        ("Végösszeg 4.200", 4200.0),
        ("Végösszeg 4 200", 4200.0),
        ("Összesen 1 250,50", 1250.5),
        ("TOTAL 1 234 567", 1234567.0),
        ("Fizetendő 2\u00a0500", 2500.0),
        ("Fizetendő 2.500", 2500.0),
    ],
)
@pytest.mark.test_id("TEST-RL-V02-149")
@pytest.mark.requirements("FEAT-RL-V02-REQ-058")
@pytest.mark.scenario("AC-RL-V02-39")
def test_total_regex_recognises_hungarian_total_labels(line, expected):
    captured = ocr._find_first(ocr._TOTAL_RE, line)
    assert ocr._parse_float(captured) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("12,50", 12.5),
        ("1.250,50", 1250.5),
        ("1 250,50", 1250.5),
    ],
)
@pytest.mark.test_id("TEST-RL-V02-150")
@pytest.mark.requirements("FEAT-RL-V02-REQ-058")
@pytest.mark.scenario("AC-RL-V02-39")
def test_locale_parser_uses_comma_decimal_for_hungarian(raw, expected):
    assert ocr._parse_float_locale(raw, "hun") == expected


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("Laptop bag 1 250", 1250.0),
        ("Desk lamp 12 500", 12500.0),
        ("Monitor 1\u00a0299", 1299.0),
    ],
)
@pytest.mark.test_id("TEST-RL-V02-151")
@pytest.mark.requirements("FEAT-RL-V02-REQ-058")
@pytest.mark.scenario("AC-RL-V02-39")
def test_line_item_with_space_grouped_price(line, expected):
    items = ocr._parse_line_items(line)
    assert [i.price for i in items] == [expected]


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("Desk lamp 12 500 Ft", 12500.0),
        ("Tea 900 Ft", 900.0),
        ("Milk 1.20 EUR", 1.2),
        ("Bread $2.50", 2.5),
        ("Coffee 3.50 €", 3.5),
        ("Refund -5.00 EUR", -5.0),
    ],
)
@pytest.mark.test_id("TEST-RL-V02-152")
@pytest.mark.requirements("FEAT-RL-V02-REQ-058")
@pytest.mark.scenario("AC-RL-V02-39")
def test_line_item_with_currency_affix_is_kept(line, expected):
    items = ocr._parse_line_items(line)
    assert [i.price for i in items] == [expected]


@pytest.mark.test_id("TEST-RL-V02-153")
@pytest.mark.requirements("FEAT-RL-V02-REQ-058")
@pytest.mark.scenario("AC-RL-V02-39")
def test_space_is_quantity_separator_on_receipts_with_cents():
    """On a cents-style receipt a space is never a thousands separator in a
    line item: "Coffee 3 500" is quantity 3 and price 500, not 3500."""
    items = ocr._parse_line_items("Milk 1.20\nCoffee 3 500")
    assert [(i.name, i.price) for i in items] == [("Milk", 1.2), ("Coffee 3", 500.0)]


@pytest.mark.test_id("TEST-RL-V02-154")
@pytest.mark.requirements("FEAT-RL-V02-REQ-058")
@pytest.mark.scenario("AC-RL-V02-39")
def test_space_is_thousands_separator_on_whole_unit_receipts():
    """A receipt without any cents amount (e.g. HUF) keeps space grouping."""
    items = ocr._parse_line_items("Coffee 3 500\nTea 900")
    assert [(i.name, i.price) for i in items] == [("Coffee", 3500.0), ("Tea", 900.0)]


@pytest.mark.test_id("TEST-RL-V02-155")
@pytest.mark.requirements("FEAT-RL-V02-REQ-058")
@pytest.mark.scenario("AC-RL-V02-39")
def test_total_with_space_grouping_on_cents_receipt_is_unambiguous():
    """Totals are anchored by their keyword, so grouping is always applied."""
    captured = ocr._find_first(ocr._TOTAL_RE, "Milk 1.20\nTOTAL 1 234.56")
    assert ocr._parse_float(captured) == 1234.56
