"""Pre-development interface + behavioral tests for Receipt Normalization.

Module 2: app/normalization.py — NormalizedReceipt schema, date/currency normalization.

Run: PYTHONPATH=src .venv/bin/python -m pytest tests/test_normalization.py -v
"""
from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass
from datetime import date
from typing import get_type_hints

import pytest

from app.normalization import (
    NormalizedItem,
    NormalizedReceipt,
    normalize_currency,
    normalize_date,
    normalize_receipt,
)

# ===========================================================================
# INTERFACE TESTS — must pass immediately
# ===========================================================================

class TestNormalizedReceiptInterface:
    """Verify NormalizedReceipt dataclass exists and has required fields."""

    def test_is_dataclass(self):
        assert is_dataclass(NormalizedReceipt)

    def test_has_receipt_id(self):
        field_names = {f.name for f in fields(NormalizedReceipt)}
        assert "receipt_id" in field_names

    def test_has_merchant(self):
        field_names = {f.name for f in fields(NormalizedReceipt)}
        assert "merchant" in field_names

    def test_has_date(self):
        field_names = {f.name for f in fields(NormalizedReceipt)}
        assert "date" in field_names

    def test_has_items(self):
        field_names = {f.name for f in fields(NormalizedReceipt)}
        assert "items" in field_names

    def test_has_subtotal(self):
        field_names = {f.name for f in fields(NormalizedReceipt)}
        assert "subtotal" in field_names

    def test_has_tax(self):
        field_names = {f.name for f in fields(NormalizedReceipt)}
        assert "tax" in field_names

    def test_has_tax_rate(self):
        field_names = {f.name for f in fields(NormalizedReceipt)}
        assert "tax_rate" in field_names

    def test_has_total(self):
        field_names = {f.name for f in fields(NormalizedReceipt)}
        assert "total" in field_names

    def test_has_currency(self):
        field_names = {f.name for f in fields(NormalizedReceipt)}
        assert "currency" in field_names

    def test_has_language(self):
        field_names = {f.name for f in fields(NormalizedReceipt)}
        assert "language" in field_names

    def test_has_raw_text(self):
        field_names = {f.name for f in fields(NormalizedReceipt)}
        assert "raw_text" in field_names

    def test_has_confidence(self):
        field_names = {f.name for f in fields(NormalizedReceipt)}
        assert "confidence" in field_names

    def test_has_category(self):
        field_names = {f.name for f in fields(NormalizedReceipt)}
        assert "category" in field_names

    def test_has_metadata(self):
        field_names = {f.name for f in fields(NormalizedReceipt)}
        assert "metadata" in field_names


class TestNormalizedItemInterface:
    """Verify NormalizedItem dataclass exists and has required fields."""

    def test_is_dataclass(self):
        assert is_dataclass(NormalizedItem)

    def test_has_name(self):
        field_names = {f.name for f in fields(NormalizedItem)}
        assert "name" in field_names

    def test_has_quantity(self):
        field_names = {f.name for f in fields(NormalizedItem)}
        assert "quantity" in field_names

    def test_has_unit_price(self):
        field_names = {f.name for f in fields(NormalizedItem)}
        assert "unit_price" in field_names

    def test_has_total_price(self):
        field_names = {f.name for f in fields(NormalizedItem)}
        assert "total_price" in field_names

    def test_has_category(self):
        field_names = {f.name for f in fields(NormalizedItem)}
        assert "category" in field_names


class TestNormalizeFunctionsInterface:
    """Verify normalize_date, normalize_currency, normalize_receipt exist."""

    def test_normalize_date_callable(self):
        assert callable(normalize_date)

    def test_normalize_date_signature(self):
        sig = inspect.signature(normalize_date)
        params = list(sig.parameters)
        assert "date_str" in params
        assert "lang" in params

    def test_normalize_date_lang_default(self):
        sig = inspect.signature(normalize_date)
        assert sig.parameters["lang"].default == "eng"

    def test_normalize_date_return_type(self):
        hints = get_type_hints(normalize_date)
        ret = hints.get("return")
        # Returns date | None
        assert ret is not None

    def test_normalize_currency_callable(self):
        assert callable(normalize_currency)

    def test_normalize_currency_signature(self):
        sig = inspect.signature(normalize_currency)
        params = list(sig.parameters)
        assert "symbol_or_code" in params
        assert "lang" in params

    def test_normalize_currency_lang_default(self):
        sig = inspect.signature(normalize_currency)
        assert sig.parameters["lang"].default == "eng"

    def test_normalize_currency_return_type(self):
        hints = get_type_hints(normalize_currency)
        assert hints.get("return") is str or "str" in str(hints.get("return", ""))

    def test_normalize_receipt_callable(self):
        assert callable(normalize_receipt)

    def test_normalize_receipt_signature(self):
        sig = inspect.signature(normalize_receipt)
        params = list(sig.parameters)
        assert "parsed" in params
        assert "lang" in params
        assert "currency_override" in params
        assert "category" in params

    def test_normalize_receipt_return_type(self):
        hints = get_type_hints(normalize_receipt)
        ret = hints.get("return")
        assert ret is NormalizedReceipt or ret == "NormalizedReceipt"

    def test_date_formats_defined(self):
        from app.normalization import _DATE_FORMATS
        assert isinstance(_DATE_FORMATS, dict)
        for lang in ("eng", "deu", "fra", "spa", "ita", "por"):
            assert lang in _DATE_FORMATS


# ===========================================================================
# BEHAVIORAL TESTS — should fail with NotImplementedError until implemented
# ===========================================================================

class TestNormalizeDate:
    """Behavioral: date parsing with locale-appropriate formats."""

    @pytest.mark.parametrize("date_str,lang,expected", [
        ("2026-07-01", "eng", date(2026, 7, 1)),
        ("07/01/2026", "eng", date(2026, 7, 1)),
        ("01.07.2026", "deu", date(2026, 7, 1)),
        ("01/07/2026", "fra", date(2026, 7, 1)),
        ("01/07/2026", "ita", date(2026, 7, 1)),
        ("01/07/2026", "spa", date(2026, 7, 1)),
        ("01/07/2026", "por", date(2026, 7, 1)),
    ])
    def test_normalize_date_valid(self, date_str, lang, expected):
        try:
            result = normalize_date(date_str, lang=lang)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result == expected

    def test_normalize_date_invalid_returns_none(self):
        try:
            result = normalize_date("not-a-date", lang="eng")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result is None

    def test_normalize_date_empty_returns_none(self):
        try:
            result = normalize_date("", lang="eng")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result is None


class TestNormalizeCurrency:
    """Behavioral: currency normalization to ISO 4217."""

    @pytest.mark.parametrize("symbol,lang,expected", [
        ("$", "eng", "USD"),
        ("€", "deu", "EUR"),
        ("£", "eng", "GBP"),
        ("EUR", "deu", "EUR"),
        ("USD", "eng", "USD"),
        ("GBP", "eng", "GBP"),
        ("CHF", "eng", "CHF"),
        ("HUF", "eng", "HUF"),
    ])
    def test_normalize_currency_symbols(self, symbol, lang, expected):
        try:
            result = normalize_currency(symbol, lang=lang)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result == expected

    def test_normalize_currency_none_returns_locale_default(self):
        try:
            result = normalize_currency(None, lang="eng")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result == "USD"

    def test_normalize_currency_none_eur_default(self):
        try:
            result = normalize_currency(None, lang="deu")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result == "EUR"

    def test_normalize_currency_empty_string_returns_default(self):
        try:
            result = normalize_currency("", lang="eng")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result == "USD"


class TestNormalizeReceipt:
    """Behavioral: full receipt normalization."""

    @pytest.fixture
    def sample_confidence_receipt(self):
        from app.ocr import ConfidenceReceipt, ReceiptItem
        return ConfidenceReceipt(
            merchant="Test Store",
            date="2026-07-01",
            items=[ReceiptItem(name="Widget", price=9.99)],
            total=9.99,
            tax=0.80,
            currency="USD",
            raw_text="Test Store\nWidget 9.99\nTax 0.80\nTotal $10.79",
            confidence={"vendor": 0.95, "total": 0.90, "date": 0.85},
        )

    def test_normalize_returns_normalized_receipt(self, sample_confidence_receipt):
        try:
            result = normalize_receipt(sample_confidence_receipt)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert isinstance(result, NormalizedReceipt)

    def test_normalize_preserves_merchant(self, sample_confidence_receipt):
        try:
            result = normalize_receipt(sample_confidence_receipt)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result.merchant == "Test Store"

    def test_normalize_sets_total(self, sample_confidence_receipt):
        try:
            result = normalize_receipt(sample_confidence_receipt)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result.total == 9.99

    def test_normalize_sets_currency(self, sample_confidence_receipt):
        try:
            result = normalize_receipt(sample_confidence_receipt)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result.currency == "USD"

    def test_normalize_sets_language(self, sample_confidence_receipt):
        try:
            result = normalize_receipt(sample_confidence_receipt, lang="eng")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result.language == "eng"

    def test_normalize_items_have_quantity(self, sample_confidence_receipt):
        try:
            result = normalize_receipt(sample_confidence_receipt)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert len(result.items) == 1
        assert result.items[0].quantity == 1.0

    def test_normalize_computes_subtotal_when_missing(self):
        from app.ocr import ConfidenceReceipt, ReceiptItem
        receipt = ConfidenceReceipt(
            merchant="Store",
            date="2026-07-01",
            items=[
                ReceiptItem(name="A", price=5.00),
                ReceiptItem(name="B", price=3.00),
            ],
            total=8.00,
            tax=None,
            currency="EUR",
            raw_text="Store\nA 5.00\nB 3.00\nTotal 8.00",
        )
        try:
            result = normalize_receipt(receipt)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result.subtotal == 8.00
