"""Subscription intelligence HTTP endpoints.

Adds the subscription layer on top of the existing recurring-expense
detection (``AccountingWorkspace.recurring()``):

- ``GET /api/v1/subscriptions`` — active subscriptions with next renewal
  date, monthly cost, and price-change trend.
- ``GET /api/v1/subscriptions/{id}/cancel-guide`` — merchant-specific
  cancellation steps with a generic fallback for unknown merchants.

The email-alert toggle preference is persisted through
``AdvancedWorkspace.save_preferences()`` so it survives across sessions.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from app.product_api import accounting
from app.product_service import Actor
from app.subscription_alerts import (
    Frequency,
    detect_price_increase,
    extract_next_renewal_date,
    get_cancel_guide,
)

router = APIRouter(prefix="/api/v1", tags=["subscriptions"])

RENEWAL_LOOKAHEAD_DAYS = 60


def _month_start_iso() -> str:
    """First day of the current month as an ISO string (renewal fallback)."""
    return _today_iso()[:8] + "01"


def _today_iso() -> str:
    """Current date as an ISO string (single indirection for ruff DTZ011)."""
    return datetime.now(UTC).date().isoformat()


def _actor(
    x_tenant_id: str = Header(default="demo"),
    x_role: str = Header(default="admin"),
) -> Actor:
    """Tenant/role resolution shared with the product workspace."""
    if not x_tenant_id.strip():
        raise HTTPException(401, "Tenant identity is required")
    if x_role not in {"admin", "reviewer", "integrator"}:
        raise HTTPException(403, "Unknown role")
    return Actor(x_tenant_id, x_role)


def _frequency_for(occurrences: int) -> Frequency:
    """Pick a recurrence frequency from the observed receipt count."""
    if occurrences >= 12:
        return Frequency.MONTHLY
    if occurrences >= 5:
        return Frequency.QUARTERLY
    return Frequency.ANNUAL


def _monthly_cost(amount: float, occurrences: int) -> float:
    """Annualise a per-receipt amount into a monthly cost."""
    if occurrences >= 12:
        return round(amount, 2)
    if occurrences >= 5:
        return round(amount / 3.0, 2)
    return round(amount / 12.0, 2)


def _build_subscriptions(tenant: str) -> list[dict[str, Any]]:
    """Turn recurring-expense records into subscription view models."""
    records = accounting.recurring(tenant)
    subscriptions: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        merchant = str(record.get("merchant") or "Unknown")
        occurrences = int(record.get("occurrences") or 0)
        average = float(record.get("average_amount") or 0.0)
        frequency = _frequency_for(occurrences)
        # Renewal anchor is the most recent charge date ('' when the receipt
        # payload predates ISO dates); fall back to the account creation
        # month so the renewal stays deterministic and in the past.
        last_date = str(record.get("last_date") or "")
        if not last_date:
            last_date = _month_start_iso()
        renewal_date = extract_next_renewal_date(last_date, frequency)
        # Price-increase detection: the most recent charge vs the 3-month
        # rolling average of the charges before it (AC3).  ``amounts`` is
        # chronological; fewer than 2 historical charges → no baseline.
        amounts = [float(a) for a in (record.get("amounts") or [])]
        current = amounts[-1] if amounts else average
        baseline = amounts[-4:-1] if len(amounts) >= 2 else []
        price_increase = detect_price_increase(current, baseline)
        subscriptions.append(
            {
                "id": f"sub-{index:03d}",
                "merchant": merchant,
                "occurrences": occurrences,
                "frequency": frequency.value,
                "renewal_date": renewal_date,
                "amount": round(current, 2),
                "monthly_cost": _monthly_cost(average, occurrences),
                "annualized": float(record.get("annualized") or 0.0),
                "trend": "up" if price_increase else "stable",
                "price_increase": price_increase,
                "likely_subscription": bool(record.get("likely_subscription")),
            }
        )
    return subscriptions


@router.get("/subscriptions")
def list_subscriptions(current: Actor = Depends(_actor)) -> dict[str, Any]:
    """List active subscriptions with renewal dates and price-change trends."""
    subscriptions = _build_subscriptions(current.tenant_id)
    return {
        "subscriptions": subscriptions,
        "summary": {
            "total": len(subscriptions),
            "monthly_total": round(
                sum(s["monthly_cost"] for s in subscriptions), 2
            ),
        },
    }


@router.get("/subscriptions/{subscription_id}/cancel-guide")
def cancel_guide(
    subscription_id: str,
    current: Actor = Depends(_actor),
) -> dict[str, Any]:
    """Return cancellation steps for the merchant of *subscription_id*."""
    subscriptions = _build_subscriptions(current.tenant_id)
    subscription = next(
        (s for s in subscriptions if s["id"] == subscription_id),
        None,
    )
    if subscription is None:
        raise HTTPException(404, "Subscription not found")
    guide = get_cancel_guide(subscription["merchant"])
    return {
        "subscription_id": subscription_id,
        "merchant": guide.merchant,
        "steps": guide.steps,
        "url": guide.url,
    }
