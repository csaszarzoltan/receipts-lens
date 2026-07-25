"""ReceiptLens in-memory budget store.

``BudgetStore`` mirrors the ``ReceiptStore`` pattern (thread-safe, in-memory
dict) and stores budget definitions with computed spent/remaining/pct_used
fields.
"""
from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class BudgetPeriod(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class BudgetRecord:
    """A single budget definition with computed spend fields."""

    def __init__(
        self,
        budget_id: str,
        category: str,
        amount: float,
        currency: str = "USD",
        period: BudgetPeriod = BudgetPeriod.MONTHLY,
        alert_threshold: float = 0.8,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        self.budget_id = budget_id
        self.category = category
        self.amount = amount
        self.currency = currency
        self.period = period
        self.alert_threshold = alert_threshold
        self.created_at = created_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.updated_at = updated_at or self.created_at

        # Computed fields (set by store)
        self.spent: float = 0.0
        self.remaining: float = 0.0
        self.pct_used: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize the record to a dict, including computed fields."""
        return {
            "budget_id": self.budget_id,
            "category": self.category,
            "amount": self.amount,
            "currency": self.currency,
            "period": self.period.value if isinstance(self.period, BudgetPeriod) else self.period,
            "alert_threshold": self.alert_threshold,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "spent": self.spent,
            "remaining": self.remaining,
            "pct_used": self.pct_used,
        }


class BudgetStore:
    """Thread-safe in-memory store for budget definitions.

    Follows the same pattern as ``ReceiptStore`` (``_lock``, ``_data`` dict).
    A module-level ``budget_store`` singleton is the recommended entrypoint.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: dict[str, BudgetRecord] = {}

    def create(self, category: str, amount: float, **kwargs: Any) -> BudgetRecord:
        """Create a new budget definition and return the stored record.

        ``category`` must be non-empty; ``amount`` must be > 0.
        Returns the record with computed spent/remaining/pct_used.
        """
        if not category or not category.strip():
            raise ValueError("category must be non-empty")
        if amount <= 0:
            raise ValueError("amount must be > 0")

        period = kwargs.get("period", BudgetPeriod.MONTHLY)
        if isinstance(period, str):
            try:
                period = BudgetPeriod(period)
            except ValueError:
                raise ValueError(f"Invalid period: {period!r}")

        alert_threshold = kwargs.get("alert_threshold", 0.8)
        if not 0.0 <= alert_threshold <= 1.0:
            raise ValueError("alert_threshold must be between 0.0 and 1.0")

        budget_id = str(uuid.uuid4())
        record = BudgetRecord(
            budget_id=budget_id,
            category=category,
            amount=amount,
            currency=kwargs.get("currency", "USD"),
            period=period,
            alert_threshold=alert_threshold,
        )

        # Compute spend fields from receipt store data
        self._recompute(record)

        with self._lock:
            self._data[budget_id] = record

        return record

    def get(self, budget_id: str) -> BudgetRecord | None:
        """Retrieve a budget by id (includes computed spent fields)."""
        with self._lock:
            record = self._data.get(budget_id)
        if record is not None:
            self._recompute(record)
        return record

    def list(self) -> list[BudgetRecord]:
        """Return all budget definitions with computed spend fields."""
        with self._lock:
            records = list(self._data.values())
        for r in records:
            self._recompute(r)
        return records

    def update(
        self, budget_id: str, **kwargs: Any
    ) -> BudgetRecord | None:
        """Update fields on an existing budget.

        Returns the updated record, or **None** if the id is unknown.
        """
        with self._lock:
            record = self._data.get(budget_id)
            if record is None:
                return None

            if "category" in kwargs:
                val = kwargs["category"]
                if not val or not val.strip():
                    raise ValueError("category must be non-empty")
                record.category = val
            if "amount" in kwargs:
                val = kwargs["amount"]
                if val <= 0:
                    raise ValueError("amount must be > 0")
                record.amount = val
            if "currency" in kwargs:
                record.currency = kwargs["currency"]
            if "period" in kwargs:
                val = kwargs["period"]
                if isinstance(val, str):
                    val = BudgetPeriod(val)
                record.period = val
            if "alert_threshold" in kwargs:
                val = kwargs["alert_threshold"]
                if not 0.0 <= val <= 1.0:
                    raise ValueError("alert_threshold must be between 0.0 and 1.0")
                record.alert_threshold = val

            record.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Recompute spend fields outside the lock
        self._recompute(record)
        return record

    def delete(self, budget_id: str) -> bool:
        """Remove a budget.  Returns ``True`` if it existed, ``False`` otherwise."""
        with self._lock:
            if budget_id not in self._data:
                return False
            del self._data[budget_id]
        return True

    def _recompute(self, record: BudgetRecord) -> None:
        """Recompute spent/remaining/pct_used from ReceiptStore data."""
        from app.reports import receipt_store

        # Determine date range based on budget period
        now = datetime.now(timezone.utc)
        if record.period == BudgetPeriod.WEEKLY:
            # Current ISO week (Monday start)
            monday = now.date() - __import__("datetime").timedelta(days=now.weekday())
            sunday = monday + __import__("datetime").timedelta(days=6)
            date_from = monday.isoformat()
            date_to = sunday.isoformat()
        elif record.period == BudgetPeriod.MONTHLY:
            date_from = now.strftime("%Y-%m-01")
            import calendar
            last_day = calendar.monthrange(now.year, now.month)[1]
            date_to = now.replace(day=last_day).strftime("%Y-%m-%d")
        elif record.period == BudgetPeriod.YEARLY:
            date_from = now.strftime("%Y-01-01")
            date_to = now.strftime("%Y-12-31")
        else:
            date_from = now.strftime("%Y-%m-01")
            date_to = now.strftime("%Y-%m-%d")

        # Query receipts in the date range and sum up by category
        receipts = receipt_store.list(date_from=date_from, date_to=date_to)

        spent = 0.0
        # The receipt_store.list() returns ConfidenceReceipt objects
        # with merchant/date/items/total/tax/currency fields
        for receipt in receipts:
            # Match receipts whose merchant suggests the budget category
            # (approximate matching based on receipt items)
            if hasattr(receipt, "items") and receipt.items:
                for item in receipt.items:
                    if hasattr(item, "category"):
                        # Item-level category matching
                        if item.category and record.category.lower() in item.category.lower():
                            spent += item.price
                            continue

        record.spent = spent
        record.remaining = max(0.0, record.amount - spent)
        record.pct_used = round((spent / record.amount * 100) if record.amount > 0 else 0.0, 1)


# Singleton instance — same pattern as ``receipt_store`` in app/reports.py
budget_store = BudgetStore()
