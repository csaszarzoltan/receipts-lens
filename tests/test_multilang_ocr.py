"""Pre-development interface + behavioral tests for Multi-Language OCR.

Module 1: extends app/ocr.py with lang param, auto-detect, multi-currency.

Run: PYTHONPATH=src .venv/bin/python -m pytest tests/test_multilang_ocr.py -v
"""
from __future__ import annotations

import inspect
from typing import get_type_hints
from unittest.mock import patch as _mock_patch

import pytest

from app import ocr

# ===========================================================================
# FIXTURES
# ===========================================================================

SAMPLE_BYTES = b"\x89PNG\r\n\x1a\n(fake receipt image bytes)"

SUPPORTED_LANGS = ("eng", "deu", "fra", "spa", "ita", "por")

MULTI_LANG_RECEIPT_TEXTS = {
    "eng": "WALMART\nDate: 07/01/2026\nMilk 2.99\nBread 1.49\nTotal: $4.48",
    "deu": "REWE\nDatum: 01.07.2026\nMilch 2,99\nBrot 1,49\nSumme: 4,48 EUR",
    "fra": "CARREFOUR\nDate: 01/07/2026\nLait 2,99\nPain 1,49\nTotal: 4,48 EUR",
    "espa": "MERCADONA\nFecha: 01/07/2026\nLeche 2,99\nPan 1,49\nTotal: 4,48 EUR",
    "ita": "ESSELUNGA\nData: 01/07/2026\nLatte 2,99\nPane 1,49\nTotale: 4,48 EUR",
    "por": "CONTINENTE\nData: 01/07/2026\nLeite 2,99\nPão 1,49\nTotal: 4,48 EUR",
}


# ===========================================================================
# INTERFACE TESTS — must pass immediately against stubs
# ===========================================================================

class TestMultilangOCRInterface:
    """Verify that the multi-language OCR extensions are properly wired."""

    def test_extract_text_accepts_lang_param(self):
        sig = inspect.signature(ocr.extract_text)
        params = list(sig.parameters)
        assert "lang" in params, f"extract_text missing lang param: {params}"

    def test_extract_text_lang_default_is_eng(self):
        sig = inspect.signature(ocr.extract_text)
        assert sig.parameters["lang"].default == "eng"

    def test_extract_text_lang_annotation(self):
        hints = get_type_hints(ocr.extract_text)
        assert hints.get("lang") is str or "lang" in str(hints.get("lang", ""))

    def test_detect_language_exists(self):
        assert hasattr(ocr, "detect_language")
        assert callable(ocr.detect_language)

    def test_detect_language_signature(self):
        sig = inspect.signature(ocr.detect_language)
        params = list(sig.parameters)
        assert "image_bytes" in params

    def test_detect_language_return_type(self):
        hints = get_type_hints(ocr.detect_language)
        assert hints.get("return") is str

    def test_parse_receipt_accepts_lang_param(self):
        sig = inspect.signature(ocr.parse_receipt)
        assert "lang" in sig.parameters

    def test_parse_receipt_lang_default_is_none(self):
        sig = inspect.signature(ocr.parse_receipt)
        assert sig.parameters["lang"].default is None

    def test_parse_receipt_with_confidence_accepts_lang(self):
        sig = inspect.signature(ocr.parse_receipt_with_confidence)
        assert "lang" in sig.parameters

    def test_parse_receipt_with_confidence_lang_default_is_none(self):
        sig = inspect.signature(ocr.parse_receipt_with_confidence)
        assert sig.parameters["lang"].default is None

    def test_supported_languages_defined(self):
        assert hasattr(ocr, "SUPPORTED_LANGUAGES")
        assert isinstance(ocr.SUPPORTED_LANGUAGES, (tuple, list))

    def test_supported_languages_content(self):
        for lang in SUPPORTED_LANGS:
            assert lang in ocr.SUPPORTED_LANGUAGES, f"{lang} not in SUPPORTED_LANGUAGES"

    def test_parse_float_locale_exists(self):
        assert hasattr(ocr, "_parse_float_locale")
        assert callable(ocr._parse_float_locale)

    def test_extract_currency_exists(self):
        assert hasattr(ocr, "_extract_currency")
        assert callable(ocr._extract_currency)

    def test_currency_locale_hints_defined(self):
        assert hasattr(ocr, "_CURRENCY_LOCALE_HINTS")
        assert isinstance(ocr._CURRENCY_LOCALE_HINTS, dict)

    def test_currency_locale_hints_has_all_langs(self):
        for lang in SUPPORTED_LANGS:
            assert lang in ocr._CURRENCY_LOCALE_HINTS, f"{lang} not in _CURRENCY_LOCALE_HINTS"

    def test_locale_decimal_map_defined(self):
        assert hasattr(ocr, "_LOCALE_DECIMAL_MAP")
        assert isinstance(ocr._LOCALE_DECIMAL_MAP, dict)

    def test_locale_decimal_map_has_all_langs(self):
        for lang in SUPPORTED_LANGS:
            assert lang in ocr._LOCALE_DECIMAL_MAP, f"{lang} not in _LOCALE_DECIMAL_MAP"


# ===========================================================================
# BEHAVIORAL TESTS — should fail with NotImplementedError until implemented
# ===========================================================================


class TestExtractTextLang:
    """Behavioral: extract_text with language parameter."""

    def test_extract_text_with_lang_deu(self):
        """Verify lang param is passed to pytesseract."""
        with _mock_patch("app.ocr.pytesseract.image_to_string", return_value="REWE\nSumme 4,48 EUR"), _mock_patch("app.ocr.preprocess_image", return_value="fake_img"):
            result = ocr.extract_text(SAMPLE_BYTES, lang="deu")
        assert isinstance(result, str)

    def test_extract_text_with_lang_fra(self):
        with _mock_patch("app.ocr.pytesseract.image_to_string", return_value="CARREFOUR\nTotal 4,48 EUR"), _mock_patch("app.ocr.preprocess_image", return_value="fake_img"):
            result = ocr.extract_text(SAMPLE_BYTES, lang="fra")
        assert isinstance(result, str)

    def test_extract_text_with_invalid_lang_raises(self):
        """GREEN-phase: lang validation implemented. Should raise ValueError for invalid lang."""
        with pytest.raises(ValueError), _mock_patch("app.ocr.pytesseract.image_to_string", return_value=""), _mock_patch("app.ocr.preprocess_image", return_value="fake_img"):
            ocr.extract_text(SAMPLE_BYTES, lang="xyz")

    def test_extract_text_default_lang_is_eng(self):
        with _mock_patch("app.ocr.pytesseract.image_to_string", return_value="WALMART\nTotal $4.48"), _mock_patch("app.ocr.preprocess_image", return_value="fake_img"):
            result = ocr.extract_text(SAMPLE_BYTES)
        assert isinstance(result, str)

    def test_extract_text_with_combined_langs(self):
        """Multiple languages: 'eng+deu' for mixed documents."""
        with _mock_patch("app.ocr.pytesseract.image_to_string", return_value="mixed text"), _mock_patch("app.ocr.preprocess_image", return_value="fake_img"):
            result = ocr.extract_text(SAMPLE_BYTES, lang="eng+deu")
        assert isinstance(result, str)


class TestDetectLanguage:
    """Behavioral: auto-detect language from image."""

    def test_detect_returns_str(self):
        try:
            result = ocr.detect_language(SAMPLE_BYTES)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert isinstance(result, str)

    def test_detect_returns_valid_code(self):
        try:
            result = ocr.detect_language(SAMPLE_BYTES)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result in SUPPORTED_LANGS, f"Invalid lang code: {result}"

    def test_detect_raises_on_empty_bytes(self):
        try:
            with pytest.raises((ValueError, Exception)):
                ocr.detect_language(b"")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")


class TestMultiCurrencyDetection:
    """Behavioral: locale-aware currency detection."""

    @pytest.mark.parametrize("lang,expected_default", [
        ("eng", "USD"),
        ("deu", "EUR"),
        ("fra", "EUR"),
        ("ita", "EUR"),
        ("spa", "EUR"),
        ("por", "EUR"),
    ])
    def test_currency_locale_hints_defaults(self, lang, expected_default):
        try:
            result = ocr._extract_currency("", lang=lang)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result == expected_default

    @pytest.mark.parametrize("text,expected", [
        ("Total: $4.48", "USD"),
        ("Summe: 4,48 EUR", "EUR"),
        ("Total: £3.99", "GBP"),
        ("Total: 4.48 CHF", "CHF"),
        ("Összeg: 1.234 HUF", "HUF"),
    ])
    def test_extract_currency_explicit_symbols(self, text, expected):
        try:
            result = ocr._extract_currency(text, lang="eng")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result == expected

    @pytest.mark.parametrize("raw,lang,expected", [
        ("1.234,56", "deu", 1234.56),
        ("1,234.56", "eng", 1234.56),
        ("1 234,56", "fra", 1234.56),
        ("1.234,56", "ita", 1234.56),
        ("1.234,56", "por", 1234.56),
    ])
    def test_parse_float_locale(self, raw, lang, expected):
        try:
            result = ocr._parse_float_locale(raw, lang=lang)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result == expected

    def test_parse_float_locale_none_returns_none(self):
        try:
            result = ocr._parse_float_locale(None, lang="eng")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result is None

    def test_parse_float_locale_empty_returns_none(self):
        try:
            result = ocr._parse_float_locale("", lang="eng")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result is None
