"""Savings summary analytics for consumer households.

Aggregates per-category overspend versus category average and ranks
over-spending recurring merchants. Reuses ``SpendingAnalytics.by_category``
and ``RecurringAnalytics.for_actor`` without re-deriving aggregates.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.recurring import RecurringAnalytics


def _period_bounds(period: str) -> tuple[str, str]:
    """Map ``90d``/``30d`` to ``(date_from, date_to)`` ISO strings."""
    days = 90
    try:
        raw = period.strip().lower()
        if raw.endswith("d"):
            raw = raw[:-1]
        days = int(raw)
    except (ValueError, AttributeError):
        days = 90
    if days <= 0:
        days = 90
    today = datetime.now(UTC).date()
    date_from = (today - timedelta(days=days)).isoformat()
    date_to = today.isoformat()
    return date_from, date_to


def _category_groups(
    tenant_id: str | None, date_from: str, date_to: str
) -> dict[str, Any]:
    """Per-category spend for *tenant_id* straight from the product store.

    Reads the tenant SQLite through the dashboard's payload reader (the real
    ``/api/v1`` write path), NOT the global in-memory ``receipt_store`` that
    production never populates (F1.2 B1). The import is function-local so
    importing this module for a pure date helper does not build the
    ``ProductService`` singleton as a side effect.
    """
    from app.consumer_dashboard import _tenant_receipt_payloads

    payloads = _tenant_receipt_payloads(tenant_id) if tenant_id else []
    group_totals: dict[str, float] = {}
    group_counts: dict[str, int] = {}
    group_max: dict[str, float] = {}
    group_min: dict[str, float] = {}
    for payload in payloads:
        if not (date_from <= str(payload.get("date") or "") <= date_to):
            continue
        items = payload.get("line_items") or []
        if not items:
            key = "Uncategorized"
            amount = float(payload.get("total") or 0.0)
            group_totals[key] = group_totals.get(key, 0.0) + amount
            group_counts[key] = group_counts.get(key, 0) + 1
            if key not in group_max or amount > group_max[key]:
                group_max[key] = amount
            if key not in group_min or amount < group_min[key]:
                group_min[key] = amount
            continue
        for item in items:
            key = str(item.get("category") or "Uncategorized") or "Uncategorized"
            amount = float(item.get("price", item.get("amount", 0)) or 0.0)
            group_totals[key] = group_totals.get(key, 0.0) + amount
            group_counts[key] = group_counts.get(key, 0) + 1
            if key not in group_max or amount > group_max[key]:
                group_max[key] = amount
            if key not in group_min or amount < group_min[key]:
                group_min[key] = amount

    groups = [
        {
            "key": cat,
            "total": round(group_totals[cat], 2),
            "count": group_counts[cat],
            "avg": round(group_totals[cat] / group_counts[cat], 2) if group_counts[cat] else 0.0,
            "max": round(group_max.get(cat, 0.0), 2),
            "min": round(group_min.get(cat, 0.0), 2),
        }
        for cat in sorted(group_totals)
    ]
    return {
        "total_spent": round(sum(g["total"] for g in groups), 2),
        "currency": "USD",
        "groups": groups,
    }


class SavingsAnalytics:
    """Stateless savings summary engine mirroring ``RecurringAnalytics``."""

    def for_actor(
        self,
        actor: Any,
        service: Any,
        period: str = "90d",
    ) -> dict[str, Any]:
        """Build savings summary for *actor* via *service* and category averages.

        Args:
            actor: household actor with ``tenant_id``.
            service: ``ProductService`` used for recurring spend.
            period: window like ``90d`` echoed in the response.

        Returns:
            Dict with ``period``, ``potential_saving``, ``total_spent``,
            ``avg_by_category``, ``currency``, ``top_candidates``.
        """
        date_from, date_to = _period_bounds(period)
        tenant_id = getattr(actor, "tenant_id", None)
        cat = _category_groups(tenant_id, date_from, date_to)
        groups: list[dict[str, Any]] = cat.get("groups", [])
        avg_by_category = {g["key"]: g["avg"] for g in groups}
        total_spent = float(cat.get("total_spent", 0.0))
        potential_saving = round(
            sum(max(0.0, float(g["total"]) - float(g["avg"])) for g in groups),
            2,
        )

        recurring = RecurringAnalytics().for_actor(actor, service)
        candidates: list[dict[str, Any]] = []
        for item in recurring:
            delta = float(item.get("delta_pct", 0) or 0)
            if delta <= 0:
                continue
            pot = round(
                max(0.0, float(item.get("last_amount", 0)) - float(item.get("avg_amount", 0))),
                2,
            )
            if pot <= 0:
                continue
            candidates.append(
                {
                    "merchant": item.get("merchant"),
                    "potential_saving": pot,
                    "delta_pct": item.get("delta_pct"),
                }
            )
        candidates.sort(key=lambda x: x["potential_saving"], reverse=True)
        top_candidates = candidates[:2]

        return {
            "period": period,
            "potential_saving": potential_saving,
            "total_spent": total_spent,
            "avg_by_category": avg_by_category,
            "currency": "USD",
            "top_candidates": top_candidates,
        }


savings_analytics = SavingsAnalytics()
