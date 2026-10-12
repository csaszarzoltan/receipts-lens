"""Import receipts from the NAV eNyugta buyer app's data export.

The export is an XML ``ExportEnvelope`` whose layout NAV publishes
(github.com/nav-gov-hu/eRECEIPT, xsd/1.1/eCustomerApp/1.1/eReceiptExport.xsd,
v1.1 of 2025-06-27). Each element names the seller, the document number, the
gross total in HUF and the closing time in UTC, so no OCR is involved.

Only those fields are read. The line items sit inside a signed document
envelope that is not opened here, and the export also carries the receipt's
private key and search key: those are never read, kept or logged.
"""
from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

MAX_BYTES = 5_000_000
_BUDAPEST = ZoneInfo("Europe/Budapest")


class EnyugtaError(ValueError):
    """The file is not an eNyugta export; the message says why."""


@dataclass
class ExportedReceipt:
    key: str
    document_number: str | None
    supplier: str | None
    gross_huf: float
    day: str


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(element: ET.Element, name: str) -> str | None:
    for child in element:
        if _local(child.tag) == name:
            return (child.text or "").strip() or None
    return None


def _day_in_hungary(timestamp: str) -> str | None:
    """The calendar day in Hungary of a UTC timestamp such as 2026-10-05T20:30:00Z."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,3})?Z", timestamp):
        return None
    moment = datetime.fromisoformat(timestamp).astimezone(UTC)
    return moment.astimezone(_BUDAPEST).date().isoformat()


def parse_export(raw: bytes) -> tuple[list[ExportedReceipt], list[dict[str, object]]]:
    """The receipts in the file, and why any element could not be used."""
    if len(raw) > MAX_BYTES:
        raise EnyugtaError("The file is larger than 5 MB.")
    # Entity declarations are how an XML file can be made to expand into gigabytes; an export has none.
    if re.search(rb"<!\s*(DOCTYPE|ENTITY)", raw, re.IGNORECASE):
        raise EnyugtaError("The file contains a DTD, which an eNyugta export does not.")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise EnyugtaError("The file is not valid XML.") from exc
    if _local(root.tag) != "ExportEnvelope":
        raise EnyugtaError("This is not an eNyugta export (no ExportEnvelope).")

    receipts: list[ExportedReceipt] = []
    skipped: list[dict[str, object]] = []
    for index, element in enumerate((e for e in root if _local(e.tag) == "exportElements"), start=1):
        gross_text = _child_text(element, "documentGrossAmountHUF")
        issued = _child_text(element, "issueEndDateTime")
        if gross_text is None or issued is None:
            skipped.append({"index": index, "reason": "not_a_receipt"})
            continue
        day = _day_in_hungary(issued)
        try:
            gross = float(gross_text)
        except ValueError:
            gross = math.nan
        if day is None or not math.isfinite(gross) or gross < 0:
            skipped.append({"index": index, "reason": "unreadable"})
            continue
        number = _child_text(element, "documentNumber")
        supplier = _child_text(element, "supplierName")
        # Without a document number the same receipt is recognised by what it says.
        key = number or hashlib.sha256(f"{supplier}|{issued}|{gross_text}".encode()).hexdigest()
        receipts.append(ExportedReceipt(key, number, supplier, gross, day))
    if not receipts and not skipped:
        raise EnyugtaError("The file has no exported elements.")
    return receipts, skipped
