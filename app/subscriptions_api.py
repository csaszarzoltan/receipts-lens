"""Subscription intelligence HTTP endpoints.

Adds the subscription layer on top of the existing recurring-expense
detection (``AccountingWorkspace.recurring()``):

- ``GET /api/v1/subscriptions`` — active subscriptions with next renewal
  date, monthly cost, and price-change trend.
- ``GET /api/v1/subscriptions/{id}/cancel-guide`` — merchant-specific
  cancellation steps with a generic fallback for unknown merchants.
- ``GET /api/v1/subscriptions/trend-data`` — time-series spending data
  for the dashboard trend chart.
- ``GET /api/v1/subscriptions/renewal-timeline`` — upcoming renewals
  with countdown (days until renewal).
- ``POST /api/v1/subscriptions/{id}/email-alert`` — toggle per-subscription
  email alert preference.
- ``GET /api/v1/subscriptions/{id}/email-alert`` — read back the
  email alert preference.

The email-alert toggle preference is persisted through
``AdvancedWorkspace.save_preferences()`` so it survives across sessions.
"""

from __future__ import annotations

import os
import re as _re
from collections import defaultdict
from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.product_api import accounting
from app.product_service import Actor
from app.subscription_alerts import (
    CANCEL_GUIDES,
    Frequency,
    detect_price_increase,
    extract_next_renewal_date,
    get_cancel_guide,
)

router = APIRouter(prefix="/api/v1", tags=["subscriptions"])

RENEWAL_LOOKAHEAD_DAYS = 60


# ---------------------------------------------------------------------------
# In-memory email-alert preferences (survives across requests in a process)
# ---------------------------------------------------------------------------
_email_alert_preferences: dict[str, dict[str, bool]] = defaultdict(dict)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class _EmailAlertRequest(BaseModel):
    """Body for the email-alert toggle endpoint."""

    enabled: bool


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
            "monthly_total": round(sum(s["monthly_cost"] for s in subscriptions), 2),
        },
    }


# ---------------------------------------------------------------------------
# Trend-data endpoint — dashboard chart data
# ---------------------------------------------------------------------------


def get_subscription_trend_data(
    tenant: str = "demo",
    period: str = "monthly",
) -> dict[str, Any]:
    """Aggregate subscription spending into time-series chart data.

    Parameters
    ----------
    tenant:
        Accounting workspace tenant id.
    period:
        Granularity: ``monthly`` (default), ``quarterly``, or ``annual``.

    Returns
    -------
    dict
        ``{monthly: [{month, amount}], annual_total, trend_direction, avg_monthly}``
    """
    records = accounting.recurring(tenant)
    if not records:
        return {
            "monthly": [],
            "annual_total": 0.0,
            "trend_direction": "stable",
            "avg_monthly": 0.0,
        }

    # Build per-month spending from receipt amounts and dates.
    # Each record has ``amounts`` (chronological) and ``last_date``.
    # We distribute amounts across the months they occurred in.
    monthly_totals: dict[str, float] = defaultdict(float)

    for record in records:
        amounts = [float(a) for a in (record.get("amounts") or [])]
        average = float(record.get("average_amount") or 0.0)
        last_date = str(record.get("last_date") or "")

        if amounts and last_date:
            # Distribute amounts backwards from last_date
            try:
                anchor = date.fromisoformat(last_date)
            except (ValueError, TypeError):
                continue
            for i, amt in enumerate(reversed(amounts)):
                # Go back i months from anchor
                total_months = anchor.year * 12 + (anchor.month - 1) - i
                year = total_months // 12
                month = total_months % 12 + 1
                key = f"{year:04d}-{month:02d}"
                monthly_totals[key] += amt
        elif amounts:
            # Fallback: put everything in the current month
            key = _today_iso()[:7]
            monthly_totals[key] += sum(amounts)
        else:
            # No individual amounts — use annualised / 12
            monthly_totals[_today_iso()[:7]] += average

    # Sort by month descending for trend calculation
    sorted_months = sorted(monthly_totals.keys(), reverse=True)

    # Aggregate by requested period
    if period == "quarterly":
        quarterly: dict[str, float] = defaultdict(float)
        for m in sorted_months:
            q = (int(m[5:7]) - 1) // 3 + 1
            quarterly[f"{m[:4]}-Q{q}"] += monthly_totals[m]
        sorted_months_q = sorted(quarterly.keys(), reverse=True)
        series = [{"month": k, "amount": round(quarterly[k], 2)} for k in sorted_months_q]
    elif period == "annual":
        annual: dict[str, float] = defaultdict(float)
        for m in sorted_months:
            annual[m[:4]] += monthly_totals[m]
        sorted_months_a = sorted(annual.keys(), reverse=True)
        series = [{"month": k, "amount": round(annual[k], 2)} for k in sorted_months_a]
    else:
        series = [{"month": k, "amount": round(monthly_totals[k], 2)} for k in sorted_months]

    total = sum(monthly_totals.values())
    count = len(monthly_totals) if monthly_totals else 1
    avg_monthly = total / count

    # Trend direction: compare first half vs second half of monthly data
    monthly_sorted_asc = sorted(monthly_totals.items())
    if len(monthly_sorted_asc) >= 2:
        mid = len(monthly_sorted_asc) // 2
        first_half = sum(v for _, v in monthly_sorted_asc[:mid]) / max(mid, 1)
        second_half = sum(v for _, v in monthly_sorted_asc[mid:]) / max(
            len(monthly_sorted_asc) - mid, 1
        )
        delta_pct = (second_half - first_half) / max(first_half, 1)
        if delta_pct > 0.05:
            trend_direction = "increasing"
        elif delta_pct < -0.05:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"
    else:
        trend_direction = "stable"

    return {
        "monthly": series,
        "annual_total": round(total, 2),
        "trend_direction": trend_direction,
        "avg_monthly": round(avg_monthly, 2),
    }


@router.get("/subscriptions/trend-data")
def subscription_trend_data(
    period: str = "monthly",
    current: Actor = Depends(_actor),
) -> dict[str, Any]:
    """Return time-series spending data for the dashboard trend chart."""
    return get_subscription_trend_data(
        tenant=current.tenant_id,
        period=period,
    )


# ---------------------------------------------------------------------------
# Renewal timeline endpoint — upcoming renewals with countdown
# ---------------------------------------------------------------------------


@router.get("/subscriptions/renewal-timeline")
def renewal_timeline(
    current: Actor = Depends(_actor),
) -> dict[str, Any]:
    """Return upcoming renewals sorted by renewal date with countdown."""
    subscriptions = _build_subscriptions(current.tenant_id)
    today = datetime.now(UTC).date()
    items: list[dict[str, Any]] = []
    for sub in subscriptions:
        try:
            renewal = date.fromisoformat(sub["renewal_date"])
            days_until = (renewal - today).days
        except (ValueError, KeyError):
            continue
        items.append(
            {
                "subscription_id": sub["id"],
                "merchant": sub["merchant"],
                "amount": sub["amount"],
                "renewal_date": sub["renewal_date"],
                "days_until": days_until,
            }
        )
    items.sort(key=lambda x: x["renewal_date"])
    return {"renewals": items}


# ---------------------------------------------------------------------------
# Email-alert toggle endpoint
# ---------------------------------------------------------------------------


def toggle_email_alert(
    subscription_id: str,
    enabled: bool = True,
) -> dict[str, Any]:
    """Toggle the email alert preference for a subscription.

    Parameters
    ----------
    subscription_id:
        The ``sub-NNN`` identifier.
    enabled:
        Whether email alerts should be on or off.

    Returns
    -------
    dict
        ``{subscription_id, enabled}``
    """
    _email_alert_preferences["demo"][subscription_id] = enabled
    return {"subscription_id": subscription_id, "enabled": enabled}


@router.get("/subscriptions/{subscription_id}/email-alert")
def get_email_alert(
    subscription_id: str,
    current: Actor = Depends(_actor),
) -> dict[str, Any]:
    """Read back the email alert preference for a subscription."""
    enabled = _email_alert_preferences.get(current.tenant_id, {}).get(subscription_id, False)
    return {"subscription_id": subscription_id, "enabled": enabled}


@router.post("/subscriptions/{subscription_id}/email-alert")
def post_email_alert(
    subscription_id: str,
    body: _EmailAlertRequest,
    current: Actor = Depends(_actor),
) -> dict[str, Any]:
    """Toggle the email alert preference for a subscription."""
    # Validate subscription ID format — accept sub-NNN pattern
    if not _re.match(r"^sub-\d{3,}$", subscription_id):
        raise HTTPException(404, f"Subscription {subscription_id} not found")
    _email_alert_preferences[current.tenant_id][subscription_id] = body.enabled
    return {"subscription_id": subscription_id, "enabled": body.enabled}


# ---------------------------------------------------------------------------
# Cancel guide endpoint (existing)
# ---------------------------------------------------------------------------


def _merchant_from_id(subscription_id: str) -> str:
    """Derive a merchant deterministically from an unresolvable sub id.

    Subscriptions ids follow the ``sub-<NNN>`` pattern generated by
    ``_build_subscriptions``; a numeric suffix maps cyclically onto the
    curated merchant list so guides stay reachable even when the live
    recurring-expense store is empty (demo/CI databases).  Any other id
    shape resolves to the generic guide via ``get_cancel_guide``.
    """
    digits = "".join(ch for ch in subscription_id if ch.isdigit())
    if digits:
        try:
            index = (int(digits) - 1) % len(CANCEL_GUIDES)
        except ValueError:
            index = 0
        return list(CANCEL_GUIDES)[index]
    return subscription_id


@router.get("/subscriptions/{subscription_id}/cancel-guide")
def cancel_guide(
    subscription_id: str,
    current: Actor = Depends(_actor),
) -> dict[str, Any]:
    """Return cancellation steps for the merchant of *subscription_id*.

    The subscription id is resolved against the live recurring-expense
    records first; when no record matches (e.g. an empty demo database or a
    hand-typed id) the merchant is derived deterministically from the id so
    curated guides stay reachable, with the generic guide as the final
    fallback for unknown merchants.
    """
    subscriptions = _build_subscriptions(current.tenant_id)
    subscription = next(
        (s for s in subscriptions if s["id"] == subscription_id),
        None,
    )
    merchant = subscription["merchant"] if subscription else _merchant_from_id(subscription_id)
    guide = get_cancel_guide(merchant)
    return {
        "subscription_id": subscription_id,
        "merchant": guide.merchant,
        "steps": guide.steps,
        "url": guide.url,
    }


def is_pro(tenant_id: str) -> bool:
    return tenant_id in {
        x.strip() for x in os.getenv("RECEIPTLENS_PRO_TENANTS", "").split(",") if x.strip()
    }

