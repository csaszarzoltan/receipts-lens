"""ReceiptLens spending and budget analytics.

Stateless query engines that aggregate data from ``ReceiptStore`` and
``BudgetStore``.  Both ``SpendingAnalytics`` and ``BudgetAnalytics`` are
instantiated as module-level singletons.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.reports import receipt_store

# ---------------------------------------------------------------------------
# Spending analytics
# ---------------------------------------------------------------------------


class SpendingGroup:
    """Aggregated data for a single group (category/merchant/day/month)."""

    def __init__(
        self,
        key: str,
        total: float = 0.0,
        count: int = 0,
        avg: float = 0.0,
        max: float = 0.0,
        min: float = 0.0,
    ) -> None:
        self.key = key
        self.total = total
        self.count = count
        self.avg = avg
        self.max = max
        self.min = min


class TrendPoint:
    """Spending for a single period in a trend series."""

    def __init__(self, period: str, total: float, count: int) -> None:
        self.period = period
        self.total = total
        self.count = count


class SpendingAnalytics:
    """Stateless aggregator that queries ``ReceiptStore``.

    All methods are read-only and operate on the shared ``receipt_store``
    singleton imported from ``app.reports``.
    """

    def by_category(
        self,
        date_from: str,
        date_to: str,
        category: str | None = None,
    ) -> dict[str, Any]:
        """Aggregate spending grouped by category.

        Returns a dict with ``total_spent``, ``currency``, ``groups`` (list
        of ``SpendingGroup`` dicts), and optionally ``trend``.
        """
        receipts = receipt_store.list(date_from=date_from, date_to=date_to)

        # Group receipts by item-level category
        group_totals: dict[str, float] = defaultdict(float)
        group_counts: dict[str, int] = defaultdict(int)
        group_max: dict[str, float] = {}
        group_min: dict[str, float] = {}

        # Track totals per receipt for accurate counts per category
        for receipt in receipts:
            total = receipt.total or 0.0
            categories_found: set[str] = set()

            if receipt.items:
                for item in receipt.items:
                    item_cat = item.category or "Uncategorized"
                    # If category filter is set, skip non-matching items
                    if category and category.lower() not in item_cat.lower():
                        continue
                    categories_found.add(item_cat)
                    group_totals[item_cat] += item.price
                    group_counts[item_cat] += 1
                    if item_cat not in group_max or item.price > group_max[item_cat]:
                        group_max[item_cat] = item.price
                    if item_cat not in group_min or item.price < group_min[item_cat]:
                        group_min[item_cat] = item.price
            else:
                # No items, use merchant as category proxy
                cat = "Uncategorized"
                if category and category.lower() not in cat.lower():
                    continue
                categories_found.add(cat)
                group_totals[cat] += total
                group_counts[cat] += 1
                if cat not in group_max or total > group_max[cat]:
                    group_max[cat] = total
                if cat not in group_min or total < group_min[cat]:
                    group_min[cat] = total

        groups = [
            SpendingGroup(
                key=cat,
                total=round(group_totals[cat], 2),
                count=group_counts[cat],
                avg=round(group_totals[cat] / group_counts[cat], 2) if group_counts[cat] > 0 else 0.0,
                max=round(group_max.get(cat, 0.0), 2),
                min=round(group_min.get(cat, 0.0), 2),
            )
            for cat in sorted(group_totals.keys())
            if not category or category.lower() in cat.lower()
        ]

        total_spent = round(sum(g.total for g in groups), 2)
        trend = self._build_trend(date_from, date_to)

        return {
            "total_spent": total_spent,
            "currency": "USD",
            "groups": [g.__dict__ for g in groups],
            "trend": [t.__dict__ for t in trend],
            "date_from": date_from,
            "date_to": date_to,
        }

    def by_merchant(
        self,
        date_from: str,
        date_to: str,
    ) -> dict[str, Any]:
        """Aggregate spending grouped by merchant."""
        receipts = receipt_store.list(date_from=date_from, date_to=date_to)

        group_totals: dict[str, float] = defaultdict(float)
        group_counts: dict[str, int] = defaultdict(int)
        group_max: dict[str, float] = {}
        group_min: dict[str, float] = {}

        for receipt in receipts:
            merchant = receipt.merchant or "Unknown"
            total = receipt.total or 0.0
            group_totals[merchant] += total
            group_counts[merchant] += 1
            if merchant not in group_max or total > group_max[merchant]:
                group_max[merchant] = total
            if merchant not in group_min or total < group_min[merchant]:
                group_min[merchant] = total

        groups = [
            SpendingGroup(
                key=m,
                total=round(group_totals[m], 2),
                count=group_counts[m],
                avg=round(group_totals[m] / group_counts[m], 2) if group_counts[m] > 0 else 0.0,
                max=round(group_max.get(m, 0.0), 2),
                min=round(group_min.get(m, 0.0), 2),
            )
            for m in sorted(group_totals.keys())
        ]

        total_spent = round(sum(g.total for g in groups), 2)
        trend = self._build_trend(date_from, date_to)

        return {
            "total_spent": total_spent,
            "currency": "USD",
            "groups": [g.__dict__ for g in groups],
            "trend": [t.__dict__ for t in trend],
            "date_from": date_from,
            "date_to": date_to,
        }

    def by_day(
        self,
        date_from: str,
        date_to: str,
    ) -> dict[str, Any]:
        """Aggregate spending grouped by day."""
        receipts = receipt_store.list(date_from=date_from, date_to=date_to)

        group_totals: dict[str, float] = defaultdict(float)
        group_counts: dict[str, int] = defaultdict(int)

        for receipt in receipts:
            day = receipt.date or "unknown"
            total = receipt.total or 0.0
            group_totals[day] += total
            group_counts[day] += 1

        groups = [
            SpendingGroup(
                key=d,
                total=round(group_totals[d], 2),
                count=group_counts[d],
                avg=round(group_totals[d] / group_counts[d], 2) if group_counts[d] > 0 else 0.0,
                max=0.0,
                min=0.0,
            )
            for d in sorted(group_totals.keys())
        ]

        total_spent = round(sum(g.total for g in groups), 2)
        trend = self._build_trend(date_from, date_to)

        return {
            "total_spent": total_spent,
            "currency": "USD",
            "groups": [g.__dict__ for g in groups],
            "trend": [t.__dict__ for t in trend],
            "date_from": date_from,
            "date_to": date_to,
        }

    def by_month(
        self,
        date_from: str,
        date_to: str,
    ) -> dict[str, Any]:
        """Aggregate spending grouped by month."""
        receipts = receipt_store.list(date_from=date_from, date_to=date_to)

        group_totals: dict[str, float] = defaultdict(float)
        group_counts: dict[str, int] = defaultdict(int)

        for receipt in receipts:
            date_str = receipt.date
            if not date_str:
                continue
            # Extract YYYY-MM from date string
            month_key = date_str[:7]
            total = receipt.total or 0.0
            group_totals[month_key] += total
            group_counts[month_key] += 1

        groups = [
            SpendingGroup(
                key=m,
                total=round(group_totals[m], 2),
                count=group_counts[m],
                avg=round(group_totals[m] / group_counts[m], 2) if group_counts[m] > 0 else 0.0,
                max=0.0,
                min=0.0,
            )
            for m in sorted(group_totals.keys())
        ]

        total_spent = round(sum(g.total for g in groups), 2)
        trend = self._build_trend(date_from, date_to)

        return {
            "total_spent": total_spent,
            "currency": "USD",
            "groups": [g.__dict__ for g in groups],
            "trend": [t.__dict__ for t in trend],
            "date_from": date_from,
            "date_to": date_to,
        }

    def spending_overview(
        self,
        date_from: str,
        date_to: str,
        group_by: str = "category",
        category: str | None = None,
    ) -> dict[str, Any]:
        """General-purpose aggregation endpoint.

        Delegates to ``by_category`` / ``by_merchant`` / ``by_day`` /
        ``by_month`` based on **group_by**.
        """
        if group_by == "category":
            return self.by_category(date_from, date_to, category=category)
        elif group_by == "merchant":
            return self.by_merchant(date_from, date_to)
        elif group_by == "day":
            return self.by_day(date_from, date_to)
        elif group_by == "month":
            return self.by_month(date_from, date_to)
        else:
            raise ValueError(f"Invalid group_by: {group_by!r}")

    def _build_trend(
        self, date_from: str, date_to: str
    ) -> list[dict[str, Any]]:
        """Build monthly trend data for a date range."""
        receipts = receipt_store.list(date_from=date_from, date_to=date_to)

        monthly: dict[str, dict[str, float]] = defaultdict(
            lambda: {"total": 0.0, "count": 0}
        )

        for receipt in receipts:
            date_str = receipt.date
            if not date_str:
                continue
            month_key = date_str[:7]  # YYYY-MM
            total = receipt.total or 0.0
            monthly[month_key]["total"] += total
            monthly[month_key]["count"] += 1

        trend = [
            TrendPoint(
                period=m,
                total=round(monthly[m]["total"], 2),
                count=int(monthly[m]["count"]),
            )
            for m in sorted(monthly.keys())
        ]

        return trend


# ---------------------------------------------------------------------------
# Budget analytics
# ---------------------------------------------------------------------------


class BudgetAnalytics:
    """Stateless engine that joins ``BudgetStore`` + ``ReceiptStore``.

    Produces per-budget comparisons (budgeted vs spent) and summary
    statistics for ``GET /api/v1/analytics/budgets``.
    """

    def budget_overview(
        self,
        period: str | None = None,
    ) -> dict[str, Any]:
        """Compare every budget against current spending.

        Returns a dict with ``period``, ``currency``, ``budgets`` (list
        of budget dicts with computed fields), and ``summary``.
        """
        from app.budgets import budget_store

        budgets = budget_store.list()

        # Optionally filter by period
        if period is not None:
            budgets = [b for b in budgets if b.period.value == period]

        budget_dicts = []
        summary_total_budgeted = 0.0
        summary_total_spent = 0.0
        summary_on_track = 0
        summary_warning = 0
        summary_over_budget = 0

        for b in budgets:
            status = self._compute_status(b.pct_used / 100.0, b.alert_threshold)

            budget_dicts.append({
                "budget_id": b.budget_id,
                "category": b.category,
                "budgeted": b.amount,
                "spent": b.spent,
                "remaining": b.remaining,
                "pct_used": b.pct_used,
                "period": b.period.value if hasattr(b.period, "value") else str(b.period),
                "status": status,
            })

            summary_total_budgeted += b.amount
            summary_total_spent += b.spent
            if status == "on_track":
                summary_on_track += 1
            elif status == "warning":
                summary_warning += 1
            elif status == "over_budget":
                summary_over_budget += 1

        total_remaining = max(0.0, summary_total_budgeted - summary_total_spent)
        overall_pct = round(
            (summary_total_spent / summary_total_budgeted * 100)
            if summary_total_budgeted > 0 else 0.0,
            1,
        )

        return {
            "period": period or "monthly",
            "currency": "USD",
            "budgets": budget_dicts,
            "summary": {
                "total_budgeted": round(summary_total_budgeted, 2),
                "total_spent": round(summary_total_spent, 2),
                "total_remaining": round(total_remaining, 2),
                "overall_pct": overall_pct,
                "on_track": summary_on_track,
                "warning": summary_warning,
                "over_budget": summary_over_budget,
            },
        }

    def _compute_status(self, pct_used: float, alert_threshold: float) -> str:
        """on_track / warning / over_budget based on thresholds."""
        if pct_used >= 1.0:
            return "over_budget"
        elif pct_used >= alert_threshold:
            return "warning"
        else:
            return "on_track"


# Singleton instances
spending_analytics = SpendingAnalytics()
budget_analytics = BudgetAnalytics()
