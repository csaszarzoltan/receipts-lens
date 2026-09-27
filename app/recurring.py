"""ReceiptLens recurring spend detection.

Stateless aggregator that groups ``ProductService.list_reviews`` results
by normalized merchant and computes weekly recurrence signals.
Mirrors ``app/analytics.py`` style (SpendingAnalytics / SpendingGroup).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any


def _normalize_merchant(value: str | None) -> str:
    """Lower + strip merchant name for grouping."""
    return (value or "").strip().lower()


def _parse_date(value: str | None) -> datetime | None:
    """Parse YYYY-MM-DD into aware datetime or None."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=UTC)
    except ValueError:
        return None


def _frequency_for_dates(dates: list[datetime], occurrences: int) -> str:
    """Return ``weekly`` if >=3 distinct weeks in the active 12-week window."""
    if not dates:
        return "weekly" if occurrences >= 3 else "monthly"
    latest = max(dates)
    window_start = latest - timedelta(days=84)
    active = [d for d in dates if d >= window_start]
    weeks = {(d.isocalendar()[0], d.isocalendar()[1]) for d in active}
    if len(weeks) >= 3:
        return "weekly"
    # Fallback without window: still weekly if 3 distinct weeks overall
    all_weeks = {(d.isocalendar()[0], d.isocalendar()[1]) for d in dates}
    if len(all_weeks) >= 3:
        return "weekly"
    return "monthly"


class RecurringGroup:
    """Aggregated data for a single merchant."""

    def __init__(
        self,
        merchant: str,
        occurrences: int = 0,
        frequency: str = "monthly",
        avg_amount: float = 0.0,
        last_amount: float = 0.0,
        delta_pct: float = 0.0,
    ) -> None:
        self.merchant = merchant
        self.occurrences = occurrences
        self.frequency = frequency
        self.avg_amount = avg_amount
        self.last_amount = last_amount
        self.delta_pct = delta_pct


class RecurringAnalytics:
    """Stateless aggregator that groups ``list_reviews`` payloads by merchant."""

    def from_reviews(self, reviews: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Group ``ProductService.list_reviews`` result by normalized merchant.

        Args:
            reviews: return value of ``ProductService.list_reviews`` (dict with
                ``items``) or a plain list of review items.

        Returns:
            List of dicts with ``merchant``, ``occurrences``, ``frequency``,
            ``avg_amount``, ``last_amount``, ``delta_pct``. Empty input yields
            an empty list (not an error).
        """
        if reviews is None:
            return []
        if isinstance(reviews, dict):
            items = reviews.get("items") or []
        elif isinstance(reviews, list):
            items = reviews
        else:
            return []

        if not items:
            return []

        # merchant_norm -> entries
        buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        display: dict[str, str] = {}

        for item in items:
            payload = item.get("receipt") if isinstance(item, dict) else None
            if payload is None:
                payload = item if isinstance(item, dict) else {}
            merchant_raw = payload.get("vendor")
            if merchant_raw is None:
                merchant_raw = payload.get("merchant")
            norm = _normalize_merchant(str(merchant_raw) if merchant_raw is not None else "")
            if not norm:
                continue
            # preserve first display name stripped (not lower)
            if norm not in display:
                display[norm] = str(merchant_raw).strip() if merchant_raw is not None else norm
            total = payload.get("total")
            if total is None:
                total = payload.get("amount")
            try:
                amount = float(total) if total is not None else 0.0
            except (TypeError, ValueError):
                amount = 0.0
            date_str = payload.get("date")
            buckets[norm].append({"amount": amount, "date": str(date_str) if date_str else ""})

        groups: list[dict[str, Any]] = []
        for norm, entries in buckets.items():
            occurrences = len(entries)
            amounts = [e["amount"] for e in entries]
            avg = sum(amounts) / len(amounts) if amounts else 0.0
            avg_rounded = round(avg, 2)
            # last by date string (YYYY-MM-DD lexical == chronological)
            entries_sorted = sorted(entries, key=lambda e: e["date"])
            last_amount = round(float(entries_sorted[-1]["amount"]), 2) if entries_sorted else 0.0
            if avg == 0:
                delta_pct = 0.0
            else:
                delta_pct = round((last_amount - avg) / avg * 100, 2)

            # dates for frequency
            parsed_dates = [d for d in (_parse_date(e["date"]) for e in entries) if d is not None]
            frequency = _frequency_for_dates(parsed_dates, occurrences)

            group = RecurringGroup(
                merchant=display[norm],
                occurrences=occurrences,
                frequency=frequency,
                avg_amount=avg_rounded,
                last_amount=last_amount,
                delta_pct=delta_pct,
            )
            groups.append(group.__dict__)

        # deterministic order: merchant asc
        groups.sort(key=lambda g: g["merchant"].lower())
        return groups

    def for_actor(self, actor: Any, service: Any) -> list[dict[str, Any]]:
        """Fetch reviews for *actor* via *service* and group them."""
        reviews = service.list_reviews(actor, limit=200)
        return self.from_reviews(reviews)


recurring_analytics = RecurringAnalytics()
