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


def parse_period_days(period: str) -> int:
    """Map a ``"90d"``/``"30"`` period label to a day count.

    Stricter than the sibling ``app/savings.py:16-31``: an unparseable or
    out-of-range value raises ``ValueError`` (translated to ``422`` by the
    route) instead of silently falling back to 90 days, which would return a
    90-day answer under a ``period=7x`` label.
    """
    raw = period.strip().lower()
    if raw.endswith("d"):
        raw = raw[:-1]
    days = int(raw)  # ValueError propagates on non-numeric input
    if not 1 <= days <= 3650:
        raise ValueError(f"Invalid period: {period!r}. Expected 1d..3650d.")
    return days


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

    def from_reviews(
        self,
        reviews: dict[str, Any] | list[dict[str, Any]],
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        """Group ``ProductService.list_reviews`` result by normalized merchant.

        Args:
            reviews: return value of ``ProductService.list_reviews`` (dict with
                ``items``) or a plain list of review items.
            date_from: inclusive lower ISO ``YYYY-MM-DD`` bound; ``None`` means
                no filtering.
            date_to: inclusive upper ISO ``YYYY-MM-DD`` bound; ``None`` means
                no filtering.

        Returns:
            List of dicts with ``merchant``, ``occurrences``, ``frequency``,
            ``avg_amount``, ``last_amount``, ``delta_pct``, ``price_trend``.
            Empty input yields an empty list (not an error).
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
            # Window filter BEFORE aggregation, at bucket-build time, so
            # occurrences/avg_amount/delta_pct/price_trend describe the window
            # only. Filtering after grouping would leave avg_amount all-time.
            # The ISO YYYY-MM-DD string compares lexically == chronologically,
            # but only once both sides are plain 10-char dates. Slicing to [:10]
            # makes an ISO timestamp ("2026-08-31T10:00:00") compare equal to its
            # own date instead of being falsely rejected by the upper bound.
            d = str(payload.get("date") or "").strip()[:10]
            # A missing/blank date cannot be ordered against a bound, and the
            # old asymmetric guard kept it whenever only date_to was set. Drop
            # it explicitly so both bounds behave the same with one or both set.
            if not d:
                continue
            # A non-ISO date cannot be ordered correctly against an ISO bound:
            # "2026-8-31" is 9 chars and "-"(0x2d) < "0"(0x30) makes an
            # unpadded month sort before every padded one ("2026-1-15" sorts
            # below "2025-12-31"), so slicing cannot make it safe. Reject it
            # rather than guess -- a wrongly dropped receipt is recoverable, a
            # silently mis-windowed one is not.
            if len(d) != 10 or d[4] != "-" or d[7] != "-":
                continue
            if date_from is not None and d < date_from:
                continue
            if date_to is not None and d > date_to:
                continue
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
            group_dict = group.__dict__
            # price_trend is derived ONLY from delta_pct, no new computation.
            # The 10% band is closed: exactly +/-10.0 is "flat" (spec section 2).
            trend_delta = float(group_dict["delta_pct"])
            if trend_delta > 10.0:
                group_dict["price_trend"] = "up"
            elif trend_delta < -10.0:
                group_dict["price_trend"] = "down"
            else:
                group_dict["price_trend"] = "flat"
            groups.append(group_dict)

        # deterministic order: merchant asc
        groups.sort(key=lambda g: g["merchant"].lower())
        return groups

    def for_actor(self, actor: Any, service: Any, period: str | None = None) -> list[dict[str, Any]]:
        """Fetch reviews for *actor* via *service* and group them.

        Args:
            period: ``"90d"``-style label scoping the window. ``None`` (the
                default, e.g. ``app/savings.py:171``) applies no filtering.
                An unparseable value raises ``ValueError``.
        """
        reviews = service.list_reviews(actor, limit=200)
        if period is None:
            return self.from_reviews(reviews)
        days = parse_period_days(period)
        today = datetime.now(UTC).date()
        date_from = (today - timedelta(days=days)).isoformat()
        return self.from_reviews(reviews, date_from=date_from, date_to=today.isoformat())


recurring_analytics = RecurringAnalytics()
