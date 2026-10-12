"""Check a bank or card statement (CSV) against the household's receipts.

The file is read in memory and never stored. Banks export different layouts, so
the delimiter, encoding, column names, date format and number format are all
detected, and what was assumed is reported back to the user.
"""
from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

MAX_BYTES = 1_000_000
MAX_LINES = 5000
#: A statement line and a receipt are the same purchase when their dates are this close.
DATE_WINDOW_DAYS = 5
#: A line and a receipt this far apart in amount are offered as a possible misread.
NEAR_MISS_RATIO = 0.25

_DATE_WORDS = ("dátum", "datum", "date", "könyvelés", "konyveles", "teljesítés", "teljesites", "értéknap")
_AMOUNT_WORDS = ("összeg", "osszeg", "amount", "érték", "ertek", "tétel", "betrag")
_DEBIT_WORDS = ("terhelés", "terheles", "debit", "kiadás", "kiadas", "withdrawal", "soll")
_CREDIT_WORDS = ("jóváírás", "jovairas", "credit", "bevétel", "bevetel", "deposit", "haben")
_TEXT_WORDS = ("közlemény", "kozlemeny", "partner", "leírás", "leiras", "description", "megnevezés",
               "megnevezes", "név", "nev", "name", "memo", "payee", "beneficiary", "kedvezményezett")
_CURRENCY_WORDS = ("pénznem", "penznem", "currency", "deviza", "valuta")


class StatementError(ValueError):
    """The file cannot be read as a statement; the message says why."""


@dataclass
class Line:
    row: int
    date: date
    amount: float
    description: str
    currency: str | None


def decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1250"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1")


def parse_amount(text: str) -> float | None:
    """A bank amount: signs, spaces, currency words and either separator style."""
    value = str(text or "").strip().replace("−", "-").replace("–", "-")
    if not value:
        return None
    negative = value.startswith("(") and value.endswith(")") or "-" in value
    digits = re.sub(r"[^\d.,]", "", value)
    if not digits or not re.search(r"\d", digits):
        return None
    if "," in digits and "." in digits:
        decimal = "," if digits.rfind(",") > digits.rfind(".") else "."
        group = "." if decimal == "," else ","
        digits = digits.replace(group, "").replace(decimal, ".")
    elif "," in digits or "." in digits:
        separator = "," if "," in digits else "."
        head, _, tail = digits.rpartition(separator)
        # One separator followed by exactly three digits groups thousands; otherwise it is the decimal point.
        if digits.count(separator) > 1 or (len(tail) == 3 and head):
            digits = digits.replace(separator, "")
        else:
            digits = head.replace(separator, "") + "." + tail
    try:
        number = float(digits)
    except ValueError:
        return None
    return -number if negative else number


def parse_date(text: str) -> date | None:
    value = str(text or "").strip().rstrip(".")
    value = re.sub(r"\s+", "", value)
    if m := re.fullmatch(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})(?:T.*)?", value):
        year, month, day = map(int, m.groups())
    elif m := re.fullmatch(r"(\d{1,2})[-./](\d{1,2})[-./](\d{4})", value):
        day, month, year = map(int, m.groups())  # day first, as European banks write it
    else:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _find(headers: list[str], words: tuple[str, ...]) -> int | None:
    for index, header in enumerate(headers):
        lowered = header.strip().lower()
        if any(word in lowered for word in words):
            return index
    return None


def parse_statement(raw: bytes) -> dict[str, Any]:
    """Read the file into spending lines plus a note of what was assumed."""
    if len(raw) > MAX_BYTES:
        raise StatementError("The file is larger than 1 MB.")
    text = decode(raw)
    head = [line for line in text.splitlines() if line.strip()][:5]
    # A delimiter that every one of the first lines has wins; commas are tried last because decimals use them.
    delimiter = next((d for d in (";", "\t", "|") if head and all(d in line for line in head)), ",")

    class dialect(csv.excel):
        pass

    dialect.delimiter = delimiter
    rows = [r for r in csv.reader(io.StringIO(text), dialect) if any(cell.strip() for cell in r)]
    header_at = next((i for i, r in enumerate(rows[:30])
                      if _find(r, _DATE_WORDS) is not None
                      and (_find(r, _AMOUNT_WORDS) is not None or _find(r, _DEBIT_WORDS) is not None)), None)
    if header_at is None:
        raise StatementError("No date and amount columns were found in the file.")
    headers = rows[header_at]
    date_col = _find(headers, _DATE_WORDS)
    amount_col = _find(headers, _AMOUNT_WORDS)
    debit_col = _find(headers, _DEBIT_WORDS)
    credit_col = _find(headers, _CREDIT_WORDS)
    text_cols = [i for i, h in enumerate(headers) if any(w in h.lower() for w in _TEXT_WORDS)]
    currency_col = _find(headers, _CURRENCY_WORDS)

    parsed: list[tuple[int, date, float, str, str | None]] = []
    skipped = 0
    for number, row in enumerate(rows[header_at + 1:], start=header_at + 2):
        if len(row) <= date_col:
            skipped += 1
            continue
        when = parse_date(row[date_col])
        amount = None
        if amount_col is not None and amount_col < len(row):
            amount = parse_amount(row[amount_col])
        if amount is None and debit_col is not None and debit_col < len(row):
            debit = parse_amount(row[debit_col])
            amount = -abs(debit) if debit else None
        if amount is None and credit_col is not None and credit_col < len(row) and parse_amount(row[credit_col]):
            continue  # money coming in, not spending
        if when is None or amount is None:
            skipped += 1
            continue
        description = " · ".join(row[i].strip() for i in text_cols if i < len(row) and row[i].strip())
        currency = row[currency_col].strip().upper() if currency_col is not None and currency_col < len(row) else None
        parsed.append((number, when, amount, description, currency or None))
    if not parsed:
        raise StatementError("No rows with a date and an amount could be read.")
    if len(parsed) > MAX_LINES:
        raise StatementError(f"The file has more than {MAX_LINES} rows.")

    has_negative = any(a < 0 for _, _, a, _, _ in parsed)
    if has_negative:
        spending = [Line(n, d, -a, t, c) for n, d, a, t, c in parsed if a < 0]
        direction = "negative_is_spending"
    else:
        spending = [Line(n, d, a, t, c) for n, d, a, t, c in parsed if a > 0]
        direction = "all_positive_is_spending"
    return {"lines": spending, "skipped": skipped, "direction": direction,
            "delimiter": delimiter}


def _same_amount(a: float, b: float) -> bool:
    return abs(a - b) <= max(0.005, 0.0005 * abs(b))


def _amount_of(receipt: dict[str, Any]) -> tuple[float | None, bool]:
    """The amount to compare, and whether the user has confirmed it."""
    if receipt["total"] is not None:
        return float(receipt["total"]), True
    if receipt["total_candidate"] is not None:
        return float(receipt["total_candidate"]), False
    return None, False


def match(lines: list[Line], receipts: list[dict[str, Any]]) -> dict[str, Any]:
    """Pair statement lines with receipts: same amount, close dates, one receipt per line."""
    taken: set[str] = set()
    matched: list[dict[str, Any]] = []
    unmatched_lines: list[Line] = []
    window = timedelta(days=DATE_WINDOW_DAYS)
    for line in sorted(lines, key=lambda x: x.date):
        best: tuple[int, dict[str, Any]] | None = None
        for receipt in receipts:
            if receipt["receipt_id"] in taken or not receipt["date"]:
                continue
            amount, _ = _amount_of(receipt)
            if amount is None or not _same_amount(line.amount, amount):
                continue
            if line.currency and receipt["currency"] and line.currency != receipt["currency"]:
                continue
            gap = abs(date.fromisoformat(receipt["date"]) - line.date)
            if gap <= window and (best is None or gap.days < best[0]):
                best = (gap.days, receipt)
        if best is None:
            unmatched_lines.append(line)
            continue
        receipt = best[1]
        taken.add(receipt["receipt_id"])
        _, confirmed = _amount_of(receipt)
        matched.append({"line": line, "receipt": receipt, "confirmed": confirmed})

    first = min((x.date for x in lines), default=None)
    last = max((x.date for x in lines), default=None)
    unmatched_receipts = [
        r for r in receipts
        if r["receipt_id"] not in taken and r["date"] and first and last
        and first - window <= date.fromisoformat(r["date"]) <= last + window
    ]

    suggestions: list[dict[str, Any]] = []
    used_receipts: set[str] = set()
    for line in unmatched_lines:
        for receipt in unmatched_receipts:
            amount, _ = _amount_of(receipt)
            if receipt["receipt_id"] in used_receipts or amount is None or amount <= 0:
                continue
            if abs(date.fromisoformat(receipt["date"]) - line.date) > window:
                continue
            if abs(line.amount - amount) / max(line.amount, amount) <= NEAR_MISS_RATIO:
                suggestions.append({"line": line, "receipt": receipt, "receipt_amount": amount})
                used_receipts.add(receipt["receipt_id"])
                break
    suggested_lines = {id(s["line"]) for s in suggestions}
    return {
        "matched": matched,
        "suggestions": suggestions,
        "unmatched_lines": [x for x in unmatched_lines if id(x) not in suggested_lines],
        "unmatched_receipts": [r for r in unmatched_receipts if r["receipt_id"] not in used_receipts],
        "period": {"from": first.isoformat() if first else None, "to": last.isoformat() if last else None},
    }


def _line_view(line: Line) -> dict[str, Any]:
    return {"row": line.row, "date": line.date.isoformat(), "amount": line.amount,
            "description": line.description, "currency": line.currency}


def _receipt_view(receipt: dict[str, Any]) -> dict[str, Any]:
    amount, confirmed = _amount_of(receipt)
    return {"receipt_id": receipt["receipt_id"], "vendor": receipt["vendor"], "date": receipt["date"],
            "amount": amount, "confirmed": confirmed, "currency": receipt["currency"],
            "version": receipt["version"]}


def check(raw: bytes, receipts: list[dict[str, Any]]) -> dict[str, Any]:
    """The whole check: parse the file, match it, and describe the result for the page."""
    parsed = parse_statement(raw)
    result = match(parsed["lines"], receipts)
    return {
        "assumptions": {"direction": parsed["direction"], "skipped_rows": parsed["skipped"],
                        "date_order": "day_first"},
        "period": result["period"],
        "counts": {"lines": len(parsed["lines"]), "matched": len(result["matched"]),
                   "unmatched_lines": len(result["unmatched_lines"]),
                   "unmatched_receipts": len(result["unmatched_receipts"]),
                   "suggestions": len(result["suggestions"])},
        "matched": [{"line": _line_view(m["line"]), "receipt": _receipt_view(m["receipt"]),
                     "confirmed": m["confirmed"]} for m in result["matched"]],
        "suggestions": [{"line": _line_view(s["line"]), "receipt": _receipt_view(s["receipt"])}
                        for s in result["suggestions"]],
        "unmatched_lines": [_line_view(x) for x in result["unmatched_lines"]],
        "unmatched_receipts": [_receipt_view(r) for r in result["unmatched_receipts"]],
    }


def tenant_receipts(db: Any, tenant_id: str) -> list[dict[str, Any]]:
    """The household's receipts in the shape ``match`` compares."""
    rows = db.execute("SELECT receipt_id, payload, version FROM receipts WHERE tenant_id=?", (tenant_id,)).fetchall()
    out = []
    for row in rows:
        payload = json.loads(row["payload"])
        date_text = payload.get("date")
        try:
            date.fromisoformat(date_text or "")
        except ValueError:
            date_text = None
        out.append({"receipt_id": row["receipt_id"], "vendor": payload.get("vendor"), "date": date_text,
                    "total": payload.get("total"), "total_candidate": payload.get("total_candidate"),
                    "currency": payload.get("currency"), "version": row["version"]})
    return out
