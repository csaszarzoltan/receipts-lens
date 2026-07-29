"""ReceiptLens receipt store — in-memory storage for parsed receipts."""
from __future__ import annotations

import threading
import uuid
from typing import Optional

from app.ocr import ConfidenceReceipt, ReceiptItem


class ReceiptStore:
    """In-memory store for parsed receipts.

    Thread-safe (via ``self._lock``). A module-level ``receipt_store`` instance
    is the recommended entrypoint for production wiring.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: dict[str, ConfidenceReceipt] = {}

    def store(self, receipt: ConfidenceReceipt) -> str:
        """Insert a receipt, return a UUID string receipt_id."""
        receipt_id = str(uuid.uuid4())
        with self._lock:
            self._data[receipt_id] = receipt
        return receipt_id

    def get(self, receipt_id: str) -> Optional[ConfidenceReceipt]:
        """Retrieve a receipt by id; return ``None`` for an unknown id."""
        with self._lock:
            return self._data.get(receipt_id)

    def list_all(self) -> list[tuple[str, ConfidenceReceipt]]:
        """Return a stable snapshot of all ``(receipt_id, receipt)`` pairs."""
        with self._lock:
            return list(self._data.items())

    def list(
        self,
        date_from: str,
        date_to: str,
        *,
        merchant: str | None = None,
    ) -> list[ConfidenceReceipt]:
        """Filter receipts by date range and optional merchant.

        Dates are compared as ISO strings (YYYY-MM-DD), which yields the same
        ordering as date comparison.  The **merchant** filter is case-insensitive
        substring match.
        """
        results: list[ConfidenceReceipt] = []
        with self._lock:
            for receipt in self._data.values():
                if receipt.date is None:
                    continue
                if receipt.date < date_from or receipt.date > date_to:
                    continue
                if merchant is not None:
                    if merchant.lower() not in (receipt.merchant or "").lower():
                        continue
                results.append(receipt)
        return results


# Singleton instance — same pattern as JobStore in app.api
receipt_store = ReceiptStore()

# Seed sample data covering multiple date ranges so API behavioural tests
# (e.g. test_post_reports_content_disposition) find receipts to render.
_SEED_RECEIPTS = [
    ConfidenceReceipt(
        merchant="Office Supplies Co",
        date="2026-01-15",
        items=[ReceiptItem(name="Notebook", price=5.50, category="Office"),
               ReceiptItem(name="Pen Set", price=12.00, category="Office")],
        total=17.50, tax=1.40, currency="USD", raw_text="",
        confidence={},
    ),
    ConfidenceReceipt(
        merchant="Lunch Spot",
        date="2026-01-22",
        items=[ReceiptItem(name="Sandwich", price=8.50, category="Meals")],
        total=8.50, tax=0.68, currency="USD", raw_text="",
        confidence={},
    ),
    ConfidenceReceipt(
        merchant="Gas Station",
        date="2026-07-04",
        items=[ReceiptItem(name="Fuel", price=45.00, category="Transport")],
        total=45.00, tax=3.60, currency="USD", raw_text="",
        confidence={},
    ),
]
for _r in _SEED_RECEIPTS:
    receipt_store.store(_r)
