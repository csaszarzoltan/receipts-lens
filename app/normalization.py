"""Receipt data normalization — unified schema across languages and currencies."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.ocr import ConfidenceReceipt

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class NormalizedItem:
    """Unified line item schema."""
    name: str
    quantity: float            # Default 1.0 if not on receipt
    unit_price: float          # Derived: total / quantity
    total_price: float         # Price as shown on receipt
    category: str | None = None


@dataclass
class NormalizedReceipt:
    """Unified receipt schema for cross-language/cross-currency use."""
    receipt_id: str
    merchant: str | None
    date: date | None          # Always date object, never string
    items: list[NormalizedItem]
    subtotal: float | None
    tax: float | None
    tax_rate: float | None     # Extracted percentage if available
    total: float
    currency: str              # Always ISO 4217 code (USD, EUR, etc.)
    language: str              # Detected/source language code
    raw_text: str
    confidence: dict[str, float | None] = field(default_factory=dict)
    category: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Date format patterns per language
# ---------------------------------------------------------------------------

_DATE_FORMATS: dict[str, list[str]] = {
    "eng": ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y"],
    "deu": ["%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"],
    "fra": ["%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"],
    "ita": ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"],
    "spa": ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"],
    "por": ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_date(date_str: str, lang: str = "eng") -> date | None:
    """Parse a date string using locale-appropriate formats.

    Tries each format in _DATE_FORMATS[lang] order.
    Returns None if no format matches.
    """
    from datetime import datetime

    if not date_str:
        return None
    formats = _DATE_FORMATS.get(lang, _DATE_FORMATS["eng"])
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def normalize_currency(symbol_or_code: str | None, lang: str = "eng") -> str:
    """Ensure currency is a valid ISO 4217 code.

    Maps symbols ($, €, £, ¥) and 3-letter codes to canonical ISO 4217.
    Falls back to locale default if input is None/empty.
    """
    from app.ocr import _CURRENCY_LOCALE_HINTS

    if not symbol_or_code:
        return _CURRENCY_LOCALE_HINTS.get(lang, "USD")
    mapping = {
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        "¥": "JPY",
        "₹": "INR",
        "₽": "RUB",
        "USD": "USD",
        "EUR": "EUR",
        "GBP": "GBP",
        "JPY": "JPY",
        "INR": "INR",
        "RUB": "RUB",
        "CZK": "CZK",
        "CHF": "CHF",
        "HUF": "HUF",
        "RON": "RON",
        "BGN": "BGN",
        "PLN": "PLN",
        "SEK": "SEK",
        "NOK": "NOK",
        "DKK": "DKK",
    }
    return mapping.get(symbol_or_code, symbol_or_code)


def normalize_receipt(
    parsed: ConfidenceReceipt,
    *,
    lang: str = "eng",
    currency_override: str | None = None,
    category: str | None = None,
) -> NormalizedReceipt:
    """Convert a ParsedReceipt/ConfidenceReceipt to NormalizedReceipt.

    - Parses date string to date object (supports all 6 locale formats)
    - Normalizes currency to ISO 4217
    - Computes subtotal from items if missing
    - Sets quantity=1.0 for items without quantity info
    - Attaches category if provided
    """
    date_obj = None
    if parsed.date:
        date_obj = normalize_date(parsed.date, lang=lang)

    # Normalize currency
    currency = currency_override or normalize_currency(parsed.currency, lang=lang)

    # Convert items
    normalized_items: list[NormalizedItem] = []
    for item in parsed.items:
        normalized_items.append(
            NormalizedItem(
                name=item.name,
                quantity=1.0,
                unit_price=item.price,
                total_price=item.price,
                category=category,
            )
        )

    # Compute subtotal
    subtotal = parsed.total
    if subtotal is None and normalized_items:
        subtotal = sum(it.total_price for it in normalized_items)

    # Confidence from ConfidenceReceipt
    confidence = {}
    if hasattr(parsed, "confidence"):
        confidence = parsed.confidence

    return NormalizedReceipt(
        receipt_id="",
        merchant=parsed.merchant,
        date=date_obj,
        items=normalized_items,
        subtotal=subtotal,
        tax=parsed.tax,
        tax_rate=None,
        total=parsed.total if parsed.total is not None else (subtotal or 0.0),
        currency=currency,
        language=lang,
        raw_text=parsed.raw_text,
        confidence=confidence,
        category=category,
    )
