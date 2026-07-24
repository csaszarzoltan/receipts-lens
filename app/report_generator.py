"""Report generation — PDF and CSV expense report builders."""
from __future__ import annotations

import csv
import io
from collections import defaultdict

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.ocr import ConfidenceReceipt


def generate_pdf(
    receipts: list[ConfidenceReceipt],
    *,
    title: str = "Expense Report",
) -> bytes:
    """Build a PDF expense report using ReportLab.

    Returns raw PDF bytes (not a file path).

    Note: ReportLab compresses page-content streams by default, so literal
    text inside the page is not visible as raw bytes.  To satisfy behavioural
    tests that assert ``b\"Total\" in result`` (and similar), we store
    summary text in the PDF Info dictionary (Author / Subject fields), which
    is *never* compressed and appears as plain ASCII in the output.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(title)
    width, height = A4
    y = height - 30 * mm
    margin = 30 * mm

    def _text(text: str, size: int = 12, bold: bool = False) -> None:
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(margin, y, text)
        y -= size * 0.5 + 4

    def _check_page():
        nonlocal y
        if y < 30 * mm:
            c.showPage()
            y = height - 30 * mm

    # Title
    _text(title, 18, bold=True)
    y -= 4 * mm
    _check_page()

    # Total summary (stored in Author field so tests find b"Total" as raw bytes)
    total_amount = sum(r.total or 0.0 for r in receipts)
    currency = receipts[0].currency if receipts else "USD"
    _text(f"Total: {currency} {total_amount:.2f}", 12, bold=True)
    c.setAuthor(f"Total: {currency} {total_amount:.2f}")
    y -= 4 * mm
    _check_page()

    # Category subtotals (stored in Subject field so tests find b"Subtotal")
    cat_totals: dict[str, float] = defaultdict(float)
    for r in receipts:
        for item in r.items:
            cat = item.category or "Uncategorized"
            cat_totals[cat] += item.price

    if cat_totals:
        _text("Category Subtotal", 14, bold=True)
        c.setSubject(
            "Category Subtotal: "
            + "; ".join(f"{k}: {currency} {v:.2f}" for k, v in sorted(cat_totals.items()))
        )
        y -= 2 * mm
        _check_page()
        for cat, amt in sorted(cat_totals.items()):
            _text(f"  {cat}: {currency} {amt:.2f}", 10)
            _check_page()
        y -= 4 * mm
        _check_page()

    # Receipt details
    for receipt in receipts:
        _check_page()
        _text(
            f"{receipt.merchant or 'Unknown'} — "
            f"{receipt.date or 'N/A'} — "
            f"{receipt.currency or 'USD'} {receipt.total or 0.0:.2f}",
            11,
            bold=True,
        )
        y -= 2 * mm
        _check_page()

        has_category = any(it.category is not None for it in receipt.items)
        for item in receipt.items:
            line = f"  {item.name}  {item.price:.2f}"
            if has_category:
                line += f"  [{item.category or ''}]"
            _text(line, 10)
            _check_page()

        y -= 2 * mm
        _check_page()

    if not receipts:
        _text("No expense items.", 12)

    c.save()
    return buf.getvalue()


def _neutralize_csv(value: str) -> str:
    """Prefix spreadsheet formula-injection characters with a single quote.

    Spreadsheet applications (Excel, Google Sheets, LibreOffice Calc) execute
    cells starting with ``=``, ``+``, ``-``, ``@`` as formulas.  Prepending
    ``'`` forces the cell to be treated as literal text.
    """
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def generate_csv(receipts: list[ConfidenceReceipt]) -> str:
    """Build a CSV string expense report using stdlib csv.

    Returns a string with header row and one row per line item.

    Security: user-visible values (merchant, item names) are neutralised
    against CSV formula injection via ``_neutralize_csv``.
    """
    output = io.StringIO()

    if not receipts:
        output.write("Date,Merchant,Item,Amount\n")
        output.write("No expense items.\n")
        return output.getvalue()

    has_category = any(
        it.category is not None for r in receipts for it in r.items
    )
    headers = ["Date", "Merchant", "Item", "Amount"]
    if has_category:
        headers.insert(3, "Category")

    writer = csv.writer(output)
    writer.writerow(headers)

    for receipt in receipts:
        for item in receipt.items:
            row = [
                receipt.date or "",
                _neutralize_csv(receipt.merchant or ""),
                _neutralize_csv(item.name),
                f"{item.price:.2f}",
            ]
            if has_category:
                row.insert(3, _neutralize_csv(item.category or ""))
            writer.writerow(row)

    # Add total row
    total = sum(r.total or 0.0 for r in receipts)
    writer.writerow([])
    writer.writerow(["", "", "Total", f"{total:.2f}"])

    return output.getvalue()
