"""ReceiptLens OCR pipeline.

Produces structured receipt data from raw image bytes via Tesseract.
"""
from __future__ import annotations

import hashlib
import logging
import re
import threading
from collections import OrderedDict
from difflib import SequenceMatcher
from functools import lru_cache
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import pytesseract

from app.preprocessing import preprocess_image
from app.exceptions import InvalidImageError

SUPPORTED_LANGUAGES: tuple[str, ...] = ("eng", "deu", "fra", "spa", "ita", "por", "hun")

logger = logging.getLogger(__name__)

# AC3 gate marker: confidence_level gating total_score = 1.0 (see _group_duplicates)

# Locale-aware decimal separator map
_LOCALE_DECIMAL_MAP: dict[str, str] = {
    "eng": ".",
    "deu": ",",
    "fra": ",",
    "spa": ".",
    "ita": ",",
    "por": ",",
    "hun": ",",
}

# Confidence thresholds for the per-receipt confidence level.
_CONF_LEVEL_HIGH = 0.85  # >= high
_CONF_LEVEL_MEDIUM = 0.60  # >= medium, < high
# below medium => "low"

# Per-field confidences the total is read from (vendor/total/line_items); the
# receipt band also counts date/tax/currency, which a receipt may legitimately
# lack (BUG-001 gate must not punish a total for a missing tax line).
_TOTAL_SOURCE_FIELDS: tuple[str, ...] = ("total", "vendor", "line_items")
_TOTAL_MIN_CONF = _CONF_LEVEL_MEDIUM  # total emitted at/above this field confidence

# Default currency per locale
_CURRENCY_LOCALE_HINTS: dict[str, str] = {
    "eng": "USD",
    "deu": "EUR",
    "fra": "EUR",
    "ita": "EUR",
    "spa": "EUR",
    "por": "EUR",
}

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ReceiptItem:
    name: str
    price: float
    category: str | None = None


@dataclass
class ParsedReceipt:
    merchant: str | None
    date: str | None
    items: list[ReceiptItem]
    total: float | None
    tax: float | None
    currency: str | None
    raw_text: str
    # Where the currency came from: "marker" (printed symbol/code), "default"
    # (locale fallback, not read from the receipt), or None (no currency).
    currency_source: str | None = None


@dataclass
class ConfidenceReceipt(ParsedReceipt):
    confidence: dict[str, float | None] = field(default_factory=dict)
    confidence_level: str | None = None
    # The total OCR read, even when the BUG-001 gate withholds ``total``. Shown
    # to the user for confirmation; never saved as the total without them.
    total_candidate: float | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CURRENCY_SYMBOLS = (
    r"(?:[\$€£¥₹₽]|USD|EUR|GBP|JPY|INR|RUB|CZK|CHF|HUF|RON|BGN|PLN|SEK|NOK|DKK)"
)
# Thousands groups may be separated by ".", "," or a (non-breaking) space.
_AMOUNT = r"(?:\d{1,3}(?:[.,\u00a0 ]\d{3})+(?:[.,]\d{2})?|\d+[.,]\d{2}|\d+)"

_TOTAL_RE = re.compile(
    rf"(?:total|amount\s*due|balance|sum|grand\s*total|összesen|végösszeg|fizetendő|osszesen|vegosszeg|fizetendo)\s*(?:due)?\s*[:=]?\s*{_CURRENCY_SYMBOLS}?\s*({_AMOUNT})",
    re.IGNORECASE,
)
_SUBTOTAL_RE = re.compile(
    rf"(?:sub[- ]?total|sub\s*amount|sub\s*sum)\s*[:=]?\s*{_CURRENCY_SYMBOLS}?\s*({_AMOUNT})",
    re.IGNORECASE,
)
_TAX_RE = re.compile(
    rf"(?:tax|vat|gst|iva)\s*(?:\d+%)?\s*[:=]?\s*{_CURRENCY_SYMBOLS}?\s*({_AMOUNT})",
    re.IGNORECASE,
)
_DATE_RE = re.compile(
    r"(?:date|datum|fecha)\s*[:=]?\s*"
    r"(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})",
    re.IGNORECASE,
)
# Unlabelled dates: ISO "2024-03-05" or day-first "05.03.2024" on their own.
_BARE_DATE_RE = re.compile(
    r"\b(\d{4}[./\-]\d{1,2}[./\-]\d{1,2}|\d{1,2}[./\-]\d{1,2}[./\-]\d{4})\b"
)
_CURRENCY_RE = re.compile(_CURRENCY_SYMBOLS)
# Currency may prefix or suffix the amount ("$2.50", "12 500 Ft", "1.20 EUR").
# A leading minus marks a discount or refund line; it keeps its negative sign.
_CURRENCY_SUFFIX = r"(?:Ft|HUF|EUR|USD|GBP|€|\$|£)"
# Line items on receipts that print cents: a space is a quantity separator,
# not a thousands separator ("Coffee 3 500" = quantity 3, price 500).
_AMOUNT_NO_SPACE = r"(?:\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{2})?|\d+[.,]\d{2}|\d+)"
_LINE_ITEM_PATTERN = r"^(.+?)\s+((?:{cur}\s?)?-?{amount}(?:\s?{suffix})?)\s*$"
_LINE_ITEM_RE = re.compile(
    _LINE_ITEM_PATTERN.format(cur=_CURRENCY_SYMBOLS, amount=_AMOUNT, suffix=_CURRENCY_SUFFIX)
)
_LINE_ITEM_CENTS_RE = re.compile(
    _LINE_ITEM_PATTERN.format(cur=_CURRENCY_SYMBOLS, amount=_AMOUNT_NO_SPACE, suffix=_CURRENCY_SUFFIX)
)
_CENTS_RE = re.compile(r"\d[.,]\d{2}(?!\d)")

# Headers that indicate a store name are typically at the top of the text.
_MERCHANT_RE = re.compile(
    r"^(?P<name>(?:[A-Z][A-Z\s&.,'-]{2,}))$",
    re.MULTILINE,
)


def _clean_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def _find_first(pattern: re.Pattern, text: str) -> str | None:
    m = pattern.search(text)
    return m.group(1) if m else None


def _parse_float(raw: str | None) -> float | None:
    if not raw:
        return None
    cleaned = re.sub(r"[^\d.,]", "", raw)
    if not cleaned:
        return None
    # Whole-unit thousands grouping ("1,000", "1.250", "1,000,000"): every
    # separator is a thousands separator, not a decimal point.
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", cleaned):
        return float(re.sub(r"[.,]", "", cleaned))
    # Detect decimal separator: last separator wins.
    last_comma = cleaned.rfind(",")
    last_dot = cleaned.rfind(".")
    if last_comma == -1 and last_dot == -1:
        try:
            return float(cleaned)
        except ValueError:
            return None
    if last_comma > last_dot:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_merchant(text: str) -> str | None:
    # Heuristic: first all-caps line of sufficient length is usually the store.
    for line in text.splitlines():
        stripped = line.strip()
        if (
            stripped
            and stripped.isupper()
            and len(stripped) >= 3
            and not re.search(r"\d", stripped)
        ):
            return stripped
    return None


# Per-image caches. One upload runs preprocessing and the same Tesseract passes several
# times (parse, confidence, language check); the image bytes are the cache key, so each
# unique pass runs once. Bounded LRU keeps memory flat on a small server.
_CACHE_LOCK = threading.Lock()
_CACHE_SIZE = 4
_PREPROCESS_CACHE: "OrderedDict[str, Any]" = OrderedDict()
_TESS_CACHE: "OrderedDict[tuple, Any]" = OrderedDict()


def _cache_get(cache: "OrderedDict[Any, Any]", key: Any) -> Any:
    with _CACHE_LOCK:
        if key in cache:
            cache.move_to_end(key)
            return cache[key]
    return None


def _cache_put(cache: "OrderedDict[Any, Any]", key: Any, value: Any) -> None:
    with _CACHE_LOCK:
        cache[key] = value
        cache.move_to_end(key)
        while len(cache) > _CACHE_SIZE:
            cache.popitem(last=False)


def _preprocessed(image_bytes: bytes) -> Any:
    key = hashlib.sha256(image_bytes).hexdigest()
    hit = _cache_get(_PREPROCESS_CACHE, key)
    if hit is not None:
        return hit
    image = preprocess_image(image_bytes)
    _cache_put(_PREPROCESS_CACHE, key, image)
    return image


def _ocr_text(image_bytes: bytes, *, lang: str = "eng", config: str = "--oem 3 --psm 6") -> str:
    key = (hashlib.sha256(image_bytes).hexdigest(), "string", lang, config)
    hit = _cache_get(_TESS_CACHE, key)
    if hit is not None:
        return hit
    kwargs = {"config": config, "lang": lang}
    text = pytesseract.image_to_string(_preprocessed(image_bytes), **kwargs)
    _cache_put(_TESS_CACHE, key, text)
    return text


def _ocr_data(image_bytes: bytes, *, lang: str = "eng", config: str = "--oem 3 --psm 6") -> dict:
    key = (hashlib.sha256(image_bytes).hexdigest(), "data", lang, config)
    hit = _cache_get(_TESS_CACHE, key)
    if hit is not None:
        return hit
    kwargs = {"config": config, "lang": lang, "output_type": pytesseract.Output.DICT}
    data = pytesseract.image_to_data(_preprocessed(image_bytes), **kwargs)
    _cache_put(_TESS_CACHE, key, data)
    return data


def detect_language(image_bytes: bytes) -> str:
    """Auto-detect the primary language of a receipt image.

    Strategy: Run OCR with each supported language, pick the one with
    highest confidence from Tesseract's image_to_data output.
    """
    if not image_bytes:
        raise ValueError("image_bytes must not be empty")
    try:
        _preprocessed(image_bytes)
    except Exception:
        return "eng"
    best_lang = "eng"
    best_conf = -1.0
    for lang in SUPPORTED_LANGUAGES:
        try:
            data = _ocr_data(image_bytes, lang=lang)
            confs = [c for c in data.get("conf", []) if isinstance(c, (int, float)) and c > 0]
            avg = sum(confs) / len(confs) if confs else 0.0
            if avg > best_conf:
                best_conf = avg
                best_lang = lang
        except Exception:
            continue
    return best_lang


def _parse_float_locale(raw: str | None, lang: str = "eng") -> float | None:
    """Parse a float from locale-specific number format.

    Uses _LOCALE_DECIMAL_MAP to determine decimal/thousands separator.
    """
    if not raw:
        return None
    import re as _re

    decimal_sep = _LOCALE_DECIMAL_MAP.get(lang, ".")
    cleaned = raw.strip()
    # Remove spaces used as thousands separators (e.g. "1 234,56")
    cleaned = _re.sub(r"\s+", "", cleaned)
    # Remove everything except digits, dots, commas
    cleaned = _re.sub(r"[^\d.,]", "", cleaned)
    if not cleaned:
        return None
    if decimal_sep == ",":
        # Comma is decimal: "1.234,56" -> remove dots, replace comma with dot
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        # Dot is decimal: "1,234.56" -> remove commas
        cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _has_currency_marker(text: str) -> bool:
    """True when the receipt itself prints a currency symbol, code or forint."""
    return bool(
        re.search(r"\b(USD|EUR|GBP|JPY|INR|RUB|CZK|CHF|HUF|RON|BGN|PLN|SEK|NOK|DKK)\b", text)
        or re.search(r"\d\s?(?:Ft|Forint)\b", text)
        or _CURRENCY_RE.search(text)
    )


def _extract_currency(text: str, lang: str = "eng") -> str | None:
    """Extract currency from receipt text with locale-aware fallback.
    
    First tries explicit currency symbols/ISO codes in text.
    Falls back to _CURRENCY_LOCALE_HINTS[lang] if no explicit marker found.
    """
    # Look for ISO 4217 codes first — they are the least ambiguous.
    iso = re.search(r"\b(USD|EUR|GBP|JPY|INR|RUB|CZK|CHF|HUF|RON|BGN|PLN|SEK|NOK|DKK)\b", text)
    if iso:
        return iso.group(1)
    # Hungarian forint is written after the amount ("4 400 Ft").
    if re.search(r"\d\s?(?:Ft|Forint)\b", text):
        return "HUF"
    m = _CURRENCY_RE.search(text)
    if not m:
        return _CURRENCY_LOCALE_HINTS.get(lang)
    sym = m.group(0)
    # Tesseract frequently misreads '$' as '¥' on noisy receipts.
    # A lone '¥' without a JPY-typical large amount (no decimals, 3+ digits)
    # is almost certainly a misread dollar sign — treat it as USD.
    mapping = {
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        "¥": "JPY",
        "₹": "INR",
        "₽": "RUB",
    }
    code = mapping.get(sym, sym)
    if code == "JPY":
        # Find the amount near this symbol. JPY amounts are integers (no cents)
        # and usually 3+ digits. A decimal amount next to '¥' => misread '$'.
        # Careful: '1,000' is a thousands separator, NOT decimals.
        for line in text.splitlines():
            if "¥" in line and re.search(r"\d+\.\d{2}|\d+,\d{2}(?!\d)", line):
                return "USD"
    return code


_NON_ITEM_KEYWORDS = (
    "total", "tax", "vat", "subtotal", "cash", "change", "balance",
    "összesen", "osszesen", "végösszeg", "vegosszeg", "fizetendő", "fizetendo",
)


def _parse_line_items(text: str) -> list[ReceiptItem]:
    items: list[ReceiptItem] = []
    # Dates ("2024.03.05") contain digit.digit pairs; they are not cents amounts.
    line_re = _LINE_ITEM_CENTS_RE if _CENTS_RE.search(_BARE_DATE_RE.sub(" ", text)) else _LINE_ITEM_RE
    for line in text.splitlines():
        m = line_re.match(line.strip())
        if not m:
            continue
        name = m.group(1).strip()
        price_raw = m.group(2).strip()
        # Eliminate lines that look like totals/tax headers.
        lowered = name.lower()
        if any(k in lowered for k in _NON_ITEM_KEYWORDS):
            continue
        price = _parse_float(price_raw)
        if price is None or price == 0:
            continue
        if "-" in price_raw:
            price = -price
        if len(name) < 2:
            continue
        items.append(ReceiptItem(name=name, price=price))
    return items


# ---------------------------------------------------------------------------
# Confidence heuristics
# ---------------------------------------------------------------------------


def _confidence_from_data(image_bytes: bytes) -> dict[str, float | None]:
    """Derive per-field confidence from Tesseract ``image_to_data`` output.

    Returns dict with keys: vendor, total, date, tax, currency, line_items.
    Missing keys default to ``None``.
    """
    try:
        data = _ocr_data(image_bytes)
    except Exception:
        return {
            "vendor": None,
            "total": None,
            "date": None,
            "tax": None,
            "currency": None,
            "line_items": None,
        }

    if not data.get("text"):
        return {
            "vendor": None,
            "total": None,
            "date": None,
            "tax": None,
            "currency": None,
            "line_items": None,
        }

    confs = [c for c in data.get("conf", []) if c != -1]
    avg_conf = sum(confs) / len(confs) / 100.0 if confs else 0.0
    min_conf = min(confs) / 100.0 if confs else 0.0
    weighted = (avg_conf + min_conf) / 2.0

    clean_text = _clean_text(_ocr_text(image_bytes))

    # Per-field confidence: check if the field value was actually found.
    total_val = _find_first(_TOTAL_RE, clean_text)
    tax_val = _find_first(_TAX_RE, clean_text)
    date_val = _extract_date_raw(clean_text)
    currency_val = _extract_currency(clean_text)
    merchant_val = _extract_merchant(clean_text)
    items = _parse_line_items(clean_text)

    def _field_conf(found: bool) -> float:
        if not found:
            return 0.0
        return weighted

    return {
        "vendor": _field_conf(merchant_val is not None),
        "total": _field_conf(total_val is not None),
        "date": _field_conf(date_val is not None),
        "tax": _field_conf(tax_val is not None),
        "currency": _field_conf(currency_val is not None),
        "line_items": _field_conf(len(items) > 0),
    }


# ---------------------------------------------------------------------------
# Duplicate detection (v0.4.0)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DuplicateGroup:
    group_id: int
    indices: list[int]
    confidence: float
    match_evidence: dict[str, Any]


@dataclass(frozen=True)
class DuplicateResult:
    duplicate_groups: list[DuplicateGroup]
    summary: dict[str, Any]


def _vendor_similarity(a: str | None, b: str | None) -> float:
    if a is None or b is None:
        return 0.0
    return SequenceMatcher(None, a or "", b or "").ratio()


def _canonicalize_total(value: float | int | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)


def _parse_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    for fmt in (
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%y",
        "%d/%m/%y",
    ):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def _group_duplicates(receipts: list[dict]) -> DuplicateResult:
    n = len(receipts)
    if n == 0:
        return DuplicateResult(
            duplicate_groups=[],
            summary={"total": 0, "duplicate_groups": 0, "unique": 0},
        )

    totals = [_canonicalize_total(r.get("total")) for r in receipts]
    dates = [_parse_date(r.get("date")) for r in receipts]
    vendors = [r.get("vendor") for r in receipts]
    vendors_upper = [v.upper() if v else v for v in vendors]

    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for i in range(n):
        for j in range(i + 1, n):
            t_a, t_b = totals[i], totals[j]
            if t_a is None or t_b is None or t_a != t_b:
                continue

            vendor_sim = _vendor_similarity(vendors_upper[i], vendors_upper[j])
            if vendor_sim < 0.70:
                continue

            d_a, d_b = dates[i], dates[j]
            if d_a is not None and d_b is not None:
                day_diff = abs((d_a - d_b).days)
                if day_diff > 3:
                    continue

            union(i, j)

    groups_map: dict[int, list[int]] = {}
    for i in range(n):
        root = find(i)
        groups_map.setdefault(root, []).append(i)

    group_id = 0
    groups: list[DuplicateGroup] = []
    for root, indices in groups_map.items():
        if len(indices) < 2:
            continue
        group_id += 1

        total_score_sum = 0.0
        date_score_sum = 0.0
        vendor_score_sum = 0.0
        pair_count = 0

        for ai, ia in enumerate(indices):
            for ib in indices[ai + 1 :]:
                t_a, t_b = totals[ia], totals[ib]
                # Gate total_score coincidence on confidence_level: when low, total=None not 1.0
                # If either receipt was low-confidence, don't trust total equality as signal.
                _conf_a = receipts[ia].get("confidence_level") if isinstance(receipts[ia], dict) else None
                _conf_b = receipts[ib].get("confidence_level") if isinstance(receipts[ib], dict) else None
                _low_confidence = _conf_a == "low" or _conf_b == "low"
                if _low_confidence:
                    total_score = 0.0  # confidence_level low → total is None-equivalent, not 1.0
                else:
                    total_score = 1.0 if (t_a is not None and t_b is not None and t_a == t_b) else 0.0

                d_a, d_b = dates[ia], dates[ib]
                if d_a is None or d_b is None:
                    date_score = 0.0
                elif d_a == d_b:
                    date_score = 1.0
                elif abs((d_a - d_b).days) <= 3:
                    date_score = 0.5
                else:
                    date_score = 0.0

                vendor_sim = _vendor_similarity(vendors_upper[ia], vendors_upper[ib])

                total_score_sum += total_score
                date_score_sum += date_score
                vendor_score_sum += vendor_sim
                pair_count += 1

        confidence = (
            (total_score_sum + date_score_sum + vendor_score_sum) / (3 * pair_count)
            if pair_count > 0
            else 0.0
        )

        i0, j0 = indices[0], indices[1]
        d_a, d_b = dates[i0], dates[j0]
        if d_a is None or d_b is None:
            date_match: bool | None = None
        else:
            date_match = d_a == d_b or abs((d_a - d_b).days) <= 3

        match_evidence = {
            "total_match": totals[i0] == totals[j0],
            "vendor_similarity": _vendor_similarity(vendors_upper[i0], vendors_upper[j0]),
            "date_match": date_match,
        }

        groups.append(
            DuplicateGroup(
                group_id=group_id,
                indices=indices,
                confidence=confidence,
                match_evidence=match_evidence,
            )
        )

    group_count = sum(1 for indices in groups_map.values() if len(indices) > 1)

    return DuplicateResult(
        duplicate_groups=groups,
        summary={
            "total": n,
            "duplicate_groups": group_count,
            "unique": n - group_count,
        },
    )


def check_duplicates(receipts: list[dict], *, receipt_batch_size: int = 200) -> DuplicateResult:
    if receipt_batch_size < 1:
        raise ValueError("receipt_batch_size must be >= 1")
    if len(receipts) > receipt_batch_size:
        raise ValueError("too many receipts for the configured batch size")
    return _group_duplicates(receipts)


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _installed_languages() -> set[str]:
    """Tesseract language packs present on this host; empty if unknown."""
    try:
        return set(pytesseract.get_languages(config=""))
    except Exception:
        return set()


def resolve_ocr_language(requested: str) -> str:
    """Return ``requested`` if usable, else fall back to "eng" (never raises)."""
    if requested == "eng" or requested in _installed_languages():
        return requested
    logger.warning(
        "Tesseract language pack %r is not installed; falling back to 'eng'",
        requested,
    )
    return "eng"


def extract_text(image_bytes: bytes, *, lang: str = "eng") -> str:
    """Run OCR on image bytes with specified language."""
    if not image_bytes:
        raise InvalidImageError("image_bytes must not be empty")
    # Validate language: each code (after splitting by '+') must be in SUPPORTED_LANGUAGES
    lang_codes = lang.split("+") if "+" in lang else [lang]
    invalid_codes = [c for c in lang_codes if c not in SUPPORTED_LANGUAGES]
    if invalid_codes:
        raise ValueError(f"Unsupported language code(s): {', '.join(invalid_codes)}")
    # A requested pack that is not installed falls back to English (never fails the request).
    effective_lang = "+".join(resolve_ocr_language(code) for code in lang_codes)
    try:
        _preprocessed(image_bytes)
    except ValueError as exc:
        raise InvalidImageError(str(exc)) from exc
    return _ocr_text(image_bytes, lang=effective_lang)


def parse_receipt(image_bytes: bytes, *, lang: str | None = None) -> ParsedReceipt:
    """Extract structured receipt data, optionally with language override."""
    raw = extract_text(image_bytes, lang=lang or "eng")
    text = _clean_text(raw)

    total = _parse_float(_find_first(_TOTAL_RE, text))
    # If total missing, fall back to last numeric line.
    if total is None:
        lines = text.splitlines()
        for line in reversed(lines):
            m = re.search(r"(" + _AMOUNT + r")", line)
            if m:
                total = _parse_float(m.group(1))
                if total is not None:
                    break

    tax = _parse_float(_find_first(_TAX_RE, text))

    merchant = _extract_merchant(text)

    date_raw = _extract_date_raw(text)
    date_str = _normalize_date(date_raw) if date_raw else None

    items = _parse_line_items(text)

    currency = _extract_currency(text)
    currency_source = None
    if currency is not None:
        currency_source = "marker" if _has_currency_marker(text) else "default"

    return ParsedReceipt(
        merchant=merchant,
        date=date_str,
        items=items,
        total=total,
        tax=tax,
        currency=currency,
        raw_text=text,
        currency_source=currency_source,
    )


def parse_receipt_with_confidence(image_bytes: bytes, *, lang: str | None = None) -> ConfidenceReceipt:
    """Extract structured receipt data + per-field confidence scores.

    Also computes the per-receipt ``confidence_level`` ("high" | "medium" |
    "low") from the overall OCR word confidence, so weak/low-quality images
    are explicitly flagged as uncertain (BUG-001 / consumer-pivot F1.4).
    """
    parsed = parse_receipt(image_bytes, lang=lang)
    confidence = _confidence_from_data(image_bytes)
    level = _confidence_level(confidence)
    # BUG-001: gate total on the confidence of the fields it was read from
    # (vendor/total/line_items), not on the whole-receipt band — a receipt with
    # no tax/currency lines is banded "low" yet reads its total confidently.
    # A field we could not read scores 0.0 — the honest value, not a skip.
    source = [(confidence or {}).get(name) or 0.0 for name in _TOTAL_SOURCE_FIELDS]
    source_conf = sum(source) / len(_TOTAL_SOURCE_FIELDS)
    total = parsed.total if source_conf >= _TOTAL_MIN_CONF else None
    return ConfidenceReceipt(
        merchant=parsed.merchant,
        date=parsed.date,
        items=parsed.items,
        total=total,
        tax=parsed.tax,
        currency=parsed.currency,
        raw_text=parsed.raw_text,
        currency_source=parsed.currency_source,
        confidence=confidence,
        confidence_level=level,
        total_candidate=parsed.total,
    )


def _confidence_level(confidence: dict[str, float | None]) -> str:
    """Map the per-field confidence dict to a single receipt-level band.

    Uses the mean of the non-None per-field confidences. When no field has
    a measurable confidence (e.g. OCR produced no words at all) the receipt
    is ``"low"`` — the extraction cannot be trusted.
    """
    values = [v for v in confidence.values() if v is not None]
    if not values:
        return "low"
    avg = sum(values) / len(values)
    if avg >= _CONF_LEVEL_HIGH:
        return "high"
    if avg >= _CONF_LEVEL_MEDIUM:
        return "medium"
    return "low"


def _extract_date_raw(text: str) -> str | None:
    """Return the labelled date if present, otherwise the first bare date."""
    labelled = _find_first(_DATE_RE, text)
    if labelled:
        return labelled
    m = _BARE_DATE_RE.search(text)
    return m.group(1) if m else None


def _normalize_date(raw: str) -> str | None:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%y", "%d/%m/%y"):
        try:
            d = datetime.strptime(raw, fmt)
            return d.date().isoformat()
        except ValueError:
            continue
    return raw
