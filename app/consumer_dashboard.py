"""Consumer dashboard engine — F1.2 (docs/plans/consumer-pivot-2026-08-13.md §3.4).

Aggregates the existing product engines (budget, spending analytics,
subscription intelligence, household members, receipts) into ONE
tenant-scoped payload for the consumer dashboard. All six blocks are fed
by live backend data — no placeholders:

  1. daily_remaining   — „Mennyit költhetek még ma?" (budget countdown)
  2. monthly_by_category — „Mire ment el a pénzem" (category pie/list)
  3. price_alerts      — drágulás-figyelmeztetések (existing price-increase
                         motor; subscription receipts for now — regular
                         purchases land in F2.1)
  4. cancellable       — lemondható előfizetések (existing motor)
  5. household         — családi keret-státusz (shared budget + members)
  6. recent_receipts   — legutóbbi nyugták (fast access)

Wire roles stay `admin | reviewer | integrator` (F1.3 brings real household
roles); the *presentation* layer (labels) is consumer vocabulary only.
"""
from __future__ import annotations

import calendar
import json
from datetime import UTC, date, datetime
from typing import Any

from app.budgets import BudgetPeriod, budget_store
from app.subscriptions_api import _build_subscriptions

# Cap the number of blocks rendered to keep the payload bounded.
_MAX_CATEGORIES = 8
_MAX_ALERTS = 5
_MAX_CANCELLABLE = 5
_MAX_RECENT = 6

# Consumer-facing category labels (F1.2 — no business jargon).
_CATEGORY_LABELS: dict[str, str] = {
    "Office": "Munka / iroda",
    "Meals": "Étkezés",
    "Transport": "Közlekedés",
    "Uncategorized": "Egyéb",
}


def _today() -> date:
    """Current UTC date — single indirection for deterministic tests."""
    return datetime.now(UTC).date()


def _month_bounds(today: date) -> tuple[str, str]:
    """ISO date_from/date_to for the current month."""
    last_day = calendar.monthrange(today.year, today.month)[1]
    return today.strftime("%Y-%m-01"), today.replace(day=last_day).isoformat()


def _money(value: float, currency: str = "USD") -> float:
    """Round to cents (money display contract)."""
    return round(float(value), 2)


def _tenant_receipt_payloads(tenant_id: str) -> list[dict[str, Any]]:
    """All of a tenant's stored receipt payloads (SQLite — the real write path).

    Block 1/2/5 must aggregate the receipts the product store actually holds
    (product_service.create_receipt → tenant SQLite), NOT the global
    in-memory ``receipt_store`` which production never writes to (F1.2 B1).
    """
    from app.product_api import service as product_service

    rows = product_service._db.execute(
        "SELECT payload FROM receipts WHERE tenant_id=?",
        (tenant_id,),
    ).fetchall()
    return [json.loads(row["payload"]) for row in rows]


def _tenant_monthly_budgets(tenant_id: str) -> list[Any]:
    """Monthly budgets owned by *tenant_id* (tenant-scoped — F1.2 B2)."""
    return [
        b for b in budget_store.list(tenant_id=tenant_id)
        if b.period == BudgetPeriod.MONTHLY
    ]


def _tenant_spent_this_month(
    tenant_id: str, today: date, payloads: list[dict[str, Any]] | None = None
) -> float:
    """Sum the tenant's receipt totals whose ISO date falls in the current month."""
    date_from, date_to = _month_bounds(today)
    payloads = _tenant_receipt_payloads(tenant_id) if payloads is None else payloads
    return sum(
        float(p.get("total") or 0.0)
        for p in payloads
        if date_from <= str(p.get("date") or "") <= date_to
    )


def _daily_remaining(today: date, tenant_id: str) -> dict[str, Any] | None:
    """Block 1 — „Mennyit költhetek még ma?" (budget countdown).

    Monthly budgets only (the household-facing period). The daily remaining
    is (monthly budget − spent this month) / days left in month. Returns
    ``None`` when no monthly budget exists (the UI shows the empty state).
    Both the budget and the spent figure are tenant-scoped.
    """
    budgets = _tenant_monthly_budgets(tenant_id)
    if not budgets:
        return None

    total_budget = sum(b.amount for b in budgets)
    spent = _tenant_spent_this_month(tenant_id, today)
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_left = max(0, days_in_month - today.day + 1)
    remaining = max(0.0, total_budget - spent)
    daily = (remaining / days_left) if days_left > 0 else 0.0

    return {
        "budgeted": _money(total_budget),
        "spent_this_month": _money(spent),
        "remaining_this_month": _money(remaining),
        "days_left": days_left,
        "daily_remaining": _money(daily),
        "currency": budgets[0].currency,
        "pct_used": round((spent / total_budget * 100) if total_budget > 0 else 0.0, 1),
    }


def _monthly_by_category(today: date, tenant_id: str) -> dict[str, Any]:
    """Block 2 — „Mire ment el a pénzem" (spending analytics, live).

    Aggregates the tenant's stored receipts by line-item category (falling
    back to ``Uncategorized`` for receipts without categorized line items).
    """
    date_from, date_to = _month_bounds(today)
    payloads = _tenant_receipt_payloads(tenant_id)
    group_totals: dict[str, float] = {}
    group_counts: dict[str, int] = {}
    for payload in payloads:
        if not (date_from <= str(payload.get("date") or "") <= date_to):
            continue
        items = payload.get("line_items") or []
        if not items:
            key = "Uncategorized"
            group_totals[key] = group_totals.get(key, 0.0) + float(payload.get("total") or 0.0)
            group_counts[key] = group_counts.get(key, 0) + 1
            continue
        for item in items:
            key = str(item.get("category") or "Uncategorized") or "Uncategorized"
            group_totals[key] = group_totals.get(key, 0.0) + float(item.get("price", item.get("amount", 0)) or 0.0)
            group_counts[key] = group_counts.get(key, 0) + 1

    total = round(sum(group_totals.values()), 2)
    groups = sorted(group_totals.items(), key=lambda kv: kv[1], reverse=True)

    # Highest first, capped, with consumer labels.
    top = []
    for key, group_total in groups[:_MAX_CATEGORIES]:
        top.append(
            {
                "key": key,
                "label": _CATEGORY_LABELS.get(key, key),
                "total": _money(group_total),
                "count": int(group_counts[key]),
                "pct": round((group_total / total * 100) if total > 0 else 0.0, 1),
            }
        )
    currency = "USD"
    for payload in payloads:
        if str(payload.get("date") or "")[:7] == date_from[:7] and payload.get("currency"):
            currency = str(payload["currency"])
            break
    return {
        "month": date_from[:7],
        "total_spent": _money(total),
        "currency": currency,
        "categories": top,
    }


def _price_alerts(today: date, tenant_id: str) -> list[dict[str, Any]]:
    """Block 3 — drágulás-figyelmeztetések.

    Uses the existing subscription price-increase motor (detect_price_increase
    via the subscriptions view-models). The plan marks the *extension to
    regular purchases* OPTIONAL in this task (only if the motor already
    supports it) and schedules it explicitly for F2.1 — the subscription
    engine is the motor that exists today, so this is the F1.2 scope.
    """
    alerts: list[dict[str, Any]] = []
    for sub in _build_subscriptions(tenant_id):
        if sub.get("price_increase"):
            alerts.append(
                {
                    "merchant": sub["merchant"],
                    "amount": _money(sub["amount"]),
                    "currency": "USD",
                    "monthly_cost": _money(sub["monthly_cost"]),
                    "renewal_date": sub.get("renewal_date") or "",
                    "message": (
                        f"A(z) {sub['merchant']} drágult — most "
                        f"{_money(sub['amount']):.2f} USD az utolsó díj"
                    ),
                }
            )
    return alerts[:_MAX_ALERTS]


def _cancellable(today: date, tenant_id: str) -> list[dict[str, Any]]:
    """Block 4 — lemondható előfizetések (existing motor, consumer view).

    Any detected subscription can be cancelled; the ones with an upcoming
    renewal are surfaced first.
    """
    subs = _build_subscriptions(tenant_id)
    upcoming = [s for s in subs if s.get("renewal_date")]
    upcoming.sort(key=lambda s: str(s.get("renewal_date") or "9999"))
    return [
        {
            "id": s["id"],
            "merchant": s["merchant"],
            "amount": _money(s["amount"]),
            "monthly_cost": _money(s["monthly_cost"]),
            "annualized": _money(s["annualized"]),
            "renewal_date": s.get("renewal_date") or "",
            "frequency": s.get("frequency") or "monthly",
            "trend": s.get("trend") or "stable",
            "price_increase": bool(s.get("price_increase")),
        }
        for s in upcoming[:_MAX_CANCELLABLE]
    ]


def _household(today: date, tenant_id: str) -> dict[str, Any]:
    """Block 5 — családi keret-státusz (shared budget + member breakdown).

    Member-level *spend attribution* needs per-member receipt ownership,
    which the F1.3 auth model introduces. Until then the block is live for
    the shared budget (budget + spent + remaining) and shows the household
    members from the product store with their role labels.
    """
    from app.product_api import service as product_service

    budgets = _tenant_monthly_budgets(tenant_id)
    total_budget = sum(b.amount for b in budgets)
    spent = _tenant_spent_this_month(tenant_id, today)
    currency = budgets[0].currency if budgets else "USD"

    members = []
    try:
        for m in product_service.list_members(_TenantActor(tenant_id)):
            role = str(m.get("role") or "reviewer")
            members.append(
                {
                    "member_id": m["member_id"],
                    "email": m["email"],
                    "role": role,
                    "role_label": _ROLE_LABELS.get(role, role),
                }
            )
    except Exception:  # noqa: BLE001 — members are best-effort; the budget is primary
        members = []

    return {
        "shared_budget": _money(total_budget),
        "spent": _money(spent),
        "remaining": _money(max(0.0, total_budget - spent)),
        "currency": currency,
        "members": members,
        "member_breakdown_note": (
            "A tagok szerinti bontás az új belépési mód bevezetésével "
            "(F1.3) válik elérhetővé."
        ),
    }


# Household role labels (§3.2 of the plan — consumer vocabulary).
_ROLE_LABELS: dict[str, str] = {
    "admin": "Háztartás tulajdonosa",
    "reviewer": "Felnőtt tag",
    "integrator": "Könyvelő / tanácsadó (Business mód)",
}


class _TenantActor:
    """Minimal actor for read-only product-store lookups (members)."""

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self.role = "admin"


def _recent_receipts(tenant_id: str) -> list[dict[str, Any]]:
    """Block 6 — legutóbbi nyugták (fast access from the product store)."""
    from app.product_api import service as product_service

    page = product_service.search_receipts(_TenantActor(tenant_id), limit=_MAX_RECENT)
    items = []
    for item in page["items"]:
        payload = item["receipt"]
        items.append(
            {
                "receipt_id": item["receipt_id"],
                "merchant": str(payload.get("vendor") or "Ismeretlen üzlet"),
                "total": _money(payload.get("total") or 0.0),
                "currency": str(payload.get("currency") or "USD"),
                "date": payload.get("date") or "",
                "status": item.get("status") or "completed",
                "confidence_level": payload.get("confidence_level") or None,
            }
        )
    return items


def build_consumer_dashboard(tenant_id: str, today: date | None = None) -> dict[str, Any]:
    """Assemble the full consumer dashboard payload (all six blocks)."""
    anchor = today or _today()
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "tenant": tenant_id,
        "daily_remaining": _daily_remaining(anchor, tenant_id),
        "monthly_by_category": _monthly_by_category(anchor, tenant_id),
        "price_alerts": _price_alerts(anchor, tenant_id),
        "cancellable_subscriptions": _cancellable(anchor, tenant_id),
        "household": _household(anchor, tenant_id),
        "recent_receipts": _recent_receipts(tenant_id),
    }
