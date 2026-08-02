"""ReceiptLens forecast engine — next-period spend forecasting.

Implements three stateless query engines over the shared in-memory stores:

* ``ForecastEngine`` — per-category and overall next-period spend forecast
  using a trailing moving average combined with linear trend extrapolation,
  returning point estimates with confidence bounds.  An optional, injectable
  ``narrator`` callable provides an LLM-assisted narrative seam (mocked in
  tests; disabled by default).
* ``AnomalyDetector`` — flags category-period spend that deviates from its
  historical baseline using either a z-score (mean/stddev) or MAD
  (median/median-absolute-deviation) statistic, following the
  ``app.alerts`` unusual-spending pattern.
* ``BudgetVarianceProjector`` — projects each budget's end-of-period spend
  from the current period's run rate (``app.budgets.BudgetStore`` +
  ``BudgetPeriod``) and reports the expected overage.

REST routes are exposed through the ``forecast_router`` APIRouter (prefix
``/forecasts``), wired into ``app.api``; the CLI ``forecast`` subcommand in
``app.cli`` delegates to ``forecast_engine``.

Public entrypoints are the module-level singletons ``forecast_engine``,
``anomaly_detector`` and ``budget_variance_projector`` — the same pattern
used by ``spending_analytics`` / ``budget_store`` / ``alert_store``.
"""
from __future__ import annotations

import calendar
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import APIRouter

from app.budgets import BudgetPeriod, budget_store
from app.reports import receipt_store

# ---------------------------------------------------------------------------
# Helpers — receipt access, period bucketing, series math
# ---------------------------------------------------------------------------


def _receipts_in_range(
    date_from: str | None, date_to: str | None
) -> list[Any]:
    """Return receipts filtered by an optional ISO date range.

    Uses ``ReceiptStore.list`` when both bounds are present; otherwise falls
    back to ``list_all`` and applies whichever bound was given, so callers
    can pass only one bound.
    """
    if date_from and date_to:
        return receipt_store.list(date_from=date_from, date_to=date_to)

    receipts = [r for _, r in receipt_store.list_all()]
    filtered: list[Any] = []
    for receipt in receipts:
        if receipt.date is None:
            continue
        if date_from and receipt.date < date_from:
            continue
        if date_to and receipt.date > date_to:
            continue
        filtered.append(receipt)
    return filtered


def _period_key(date_str: str, period: str) -> str:
    """Bucket an ISO date string into a period key.

    * ``weekly``  -> ``YYYY-Www`` (ISO week)
    * ``monthly`` -> ``YYYY-MM``
    * ``yearly``  -> ``YYYY``
    """
    if period == "weekly":
        try:
            iso = date.fromisoformat(date_str).isocalendar()
            return f"{iso[0]:04d}-W{iso[1]:02d}"
        except ValueError:
            return date_str[:7]
    if period == "yearly":
        return date_str[:4]
    return date_str[:7]


def _category_period_totals(
    receipts: list[Any], period: str
) -> dict[str, dict[str, float]]:
    """Aggregate spend per category per period bucket.

    Mirrors ``SpendingAnalytics.by_category``: item-level categories are
    summed by item price; receipts without items fall back to the
    ``"Uncategorized"`` bucket using the receipt total.
    """
    totals: dict[str, dict[str, float]] = {}
    for receipt in receipts:
        if receipt.date is None:
            continue
        key = _period_key(receipt.date, period)
        if receipt.items:
            for item in receipt.items:
                cat = item.category or "Uncategorized"
                bucket = totals.setdefault(cat, {})
                bucket[key] = bucket.get(key, 0.0) + (item.price or 0.0)
        else:
            cat = "Uncategorized"
            bucket = totals.setdefault(cat, {})
            bucket[key] = bucket.get(key, 0.0) + (receipt.total or 0.0)
    return totals


def _overall_period_totals(receipts: list[Any], period: str) -> dict[str, float]:
    """Aggregate total spend per period across all categories."""
    totals: dict[str, float] = {}
    for receipt in receipts:
        if receipt.date is None:
            continue
        key = _period_key(receipt.date, period)
        totals[key] = totals.get(key, 0.0) + (receipt.total or 0.0)
    return totals


def _forecast_series(
    period_totals: dict[str, float], horizon: int
) -> tuple[float, float, float, float]:
    """Forecast the next period from a per-period spend series.

    Returns ``(next_period_total, confidence_low, confidence_high, trend)``.

    The point estimate is a trailing moving average (last up to 3 periods)
    plus the linear-trend slope extrapolated ``horizon`` periods ahead; the
    confidence bounds are ``± 1.96 ×`` the residual standard deviation, so
    ``confidence_low <= next_period_total <= confidence_high`` always holds.
    """
    values = [period_totals[k] for k in sorted(period_totals)]
    n = len(values)
    if n == 0:
        return 0.0, 0.0, 0.0, 0.0
    if n == 1:
        value = round(values[0], 2)
        return value, value, value, 0.0

    # Trailing moving average over the last up-to-3 periods.
    window = values[-3:]
    moving_avg = sum(window) / len(window)

    # Linear trend (least squares) over the period index.
    mean_x = (n - 1) / 2.0
    mean_y = sum(values) / n
    var_x = sum((x - mean_x) ** 2 for x in range(n))
    slope = (
        sum((x - mean_x) * (y - mean_y) for x, y in zip(range(n), values))
        / var_x
        if var_x > 0
        else 0.0
    )

    forecast = moving_avg + slope * horizon

    # Residual standard deviation around the fitted line -> confidence bounds.
    fitted = [mean_y + slope * (x - mean_x) for x in range(n)]
    std = (sum((y - f) ** 2 for y, f in zip(values, fitted)) / n) ** 0.5
    k = 1.96
    return (
        round(forecast, 2),
        round(forecast - k * std, 2),
        round(forecast + k * std, 2),
        round(slope, 2),
    )


def _source_range(
    receipts: list[Any], date_from: str | None, date_to: str | None
) -> dict[str, str]:
    """Describe the source data range used for a computation."""
    dates = [r.date for r in receipts if r.date]
    return {
        "date_from": date_from or (min(dates) if dates else ""),
        "date_to": date_to or (max(dates) if dates else ""),
    }


# ---------------------------------------------------------------------------
# ForecastEngine
# ---------------------------------------------------------------------------


class ForecastEngine:
    """Forecast next-period spending per category and overall.

    Uses moving-average smoothing combined with linear trend extrapolation
    and returns confidence bounds around the point estimate.  An optional
    ``narrator`` callable (e.g. an LLM wrapper) can enrich the result with a
    human-readable narrative; it is never required and never blocks the
    forecast when it raises.
    """

    def __init__(self, narrator: Callable[[dict[str, Any]], str] | None = None) -> None:
        self._narrator = narrator

    def forecast(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        period: str = "monthly",
        category: str | None = None,
        horizon: int = 1,
    ) -> dict[str, Any]:
        """Forecast the next period(s) for one category or overall spend.

        Returns a dict with ``period``, ``currency``, ``source_range`` and
        ``forecasts`` (a list of per-category entries plus an ``"Overall"``
        entry when **category** is None; each entry carries ``category``,
        ``next_period_total``, ``confidence_low``, ``confidence_high``,
        ``trend``, ``method``).
        """
        receipts = _receipts_in_range(date_from, date_to)
        by_category = _category_period_totals(receipts, period)
        overall = _overall_period_totals(receipts, period)

        forecasts: list[dict[str, Any]] = []
        if category is not None:
            series = by_category.get(category, {})
            next_total, low, high, trend = _forecast_series(series, horizon)
            forecasts.append(
                self._entry(category, next_total, low, high, trend)
            )
        else:
            for cat in sorted(by_category):
                series = by_category[cat]
                next_total, low, high, trend = _forecast_series(series, horizon)
                forecasts.append(self._entry(cat, next_total, low, high, trend))
            next_total, low, high, trend = _forecast_series(overall, horizon)
            forecasts.append(self._entry("Overall", next_total, low, high, trend))

        result: dict[str, Any] = {
            "period": period,
            "currency": "USD",
            "forecasts": forecasts,
            "source_range": _source_range(receipts, date_from, date_to),
        }
        if self._narrator is not None:
            try:
                result["narrative"] = self._narrator(result)
            except Exception:  # noqa: BLE001 — narrative is optional; a provider failure must not break the forecast
                result["narrative"] = ""
        return result

    def forecast_by_category(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        period: str = "monthly",
        horizon: int = 1,
    ) -> dict[str, Any]:
        """Forecast next-period spend for every category separately."""
        result = self.forecast(
            date_from=date_from,
            date_to=date_to,
            period=period,
            horizon=horizon,
        )
        result["forecasts"] = [
            e for e in result["forecasts"] if e["category"] != "Overall"
        ]
        return result

    def forecast_overall(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        period: str = "monthly",
        horizon: int = 1,
    ) -> dict[str, Any]:
        """Forecast next-period overall spend (all categories combined)."""
        result = self.forecast(
            date_from=date_from,
            date_to=date_to,
            period=period,
            horizon=horizon,
        )
        result["forecasts"] = [
            e for e in result["forecasts"] if e["category"] == "Overall"
        ]
        return result

    @staticmethod
    def _entry(
        category: str,
        next_total: float,
        low: float,
        high: float,
        trend: float,
    ) -> dict[str, Any]:
        """Build a single forecast entry dict."""
        return {
            "category": category,
            "next_period_total": next_total,
            "confidence_low": low,
            "confidence_high": high,
            "trend": trend,
            "method": "moving_average_trend",
        }


# ---------------------------------------------------------------------------
# AnomalyDetector
# ---------------------------------------------------------------------------


class AnomalyDetector:
    """Detect anomalous spending periods via z-score or MAD.

    For every category with a usable historical baseline (>= 2 periods) each
    period is scored against the *other* periods of the same category
    (leave-one-out), so a single spike cannot corrupt its own baseline.
    """

    def detect_anomalies(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        method: str = "zscore",
        threshold: float = 2.0,
    ) -> dict[str, Any]:
        """Flag periods whose spend deviates from the historical pattern.

        ``method`` is ``"zscore"`` or ``"mad"``; ``threshold`` is the
        deviation cutoff.  Returns a dict with ``method``, ``threshold`` and
        ``anomalies`` (a list of entries with ``period``, ``category``,
        ``expected``, ``actual``, ``score``, ``flagged``).
        """
        receipts = _receipts_in_range(date_from, date_to)
        by_category = _category_period_totals(receipts, "monthly")

        anomalies: list[dict[str, Any]] = []
        for cat in sorted(by_category):
            totals = by_category[cat]
            keys = sorted(totals)
            if len(keys) < 2:
                # No baseline to deviate from.
                continue
            for idx, key in enumerate(keys):
                actual = totals[key]
                others = [totals[k] for k in keys if k != key]
                expected, score = self._score(others, actual, method)
                anomalies.append(
                    {
                        "period": key,
                        "category": cat,
                        "expected": round(expected, 2),
                        "actual": round(actual, 2),
                        "score": round(score, 4),
                        "flagged": score >= threshold,
                    }
                )

        return {
            "method": method,
            "threshold": threshold,
            "anomalies": anomalies,
        }

    @staticmethod
    def _score(others: list[float], actual: float, method: str) -> tuple[float, float]:
        """Compute ``(expected, deviation_score)`` for one period.

        z-score uses mean/stddev of the baseline; MAD uses median / median
        absolute deviation (scaled by 0.6745 to approximate stddev).  A
        degenerate baseline (zero spread) yields score ``0.0``.
        """
        n = len(others)
        if n == 0:
            return 0.0, 0.0

        if method == "mad":
            ordered = sorted(others)
            median = ordered[n // 2] if n % 2 else (
                (ordered[n // 2 - 1] + ordered[n // 2]) / 2.0
            )
            deviations = sorted(abs(v - median) for v in others)
            mad = deviations[n // 2] if n % 2 else (
                (deviations[n // 2 - 1] + deviations[n // 2]) / 2.0
            )
            if mad <= 1e-12:
                return median, 0.0
            return median, 0.6745 * (actual - median) / mad

        mean = sum(others) / n
        variance = sum((v - mean) ** 2 for v in others) / n
        std = variance ** 0.5
        if std <= 1e-12:
            return mean, 0.0
        return mean, (actual - mean) / std


# ---------------------------------------------------------------------------
# BudgetVarianceProjector
# ---------------------------------------------------------------------------


def _budget_window(period: str) -> tuple[str, str]:
    """Return the current ``(date_from, date_to)`` window for a budget period."""
    now = datetime.now(UTC)
    if period == "weekly":
        monday = now.date() - timedelta(days=now.weekday())
        return monday.isoformat(), (monday + timedelta(days=6)).isoformat()
    if period == "yearly":
        return f"{now.year:04d}-01-01", f"{now.year:04d}-12-31"
    last = calendar.monthrange(now.year, now.month)[1]
    return (
        f"{now.year:04d}-{now.month:02d}-01",
        f"{now.year:04d}-{now.month:02d}-{last:02d}",
    )


def _fraction_elapsed(period: str) -> float:
    """Fraction of the current budget period already elapsed (0..1]."""
    now = datetime.now(UTC)
    today = now.date()
    if period == "weekly":
        return (today.weekday() + 1) / 7.0
    if period == "yearly":
        total = 366 if calendar.isleap(now.year) else 365
        return today.timetuple().tm_yday / total
    return today.day / calendar.monthrange(now.year, now.month)[1]


def _category_spend(receipts: list[Any], category: str) -> float:
    """Sum item-level spend matching a budget category (case-insensitive).

    Mirrors ``BudgetStore._recompute`` so projections agree with the
    spent/remaining figures the store already computes.
    """
    spent = 0.0
    for receipt in receipts:
        if not receipt.items:
            continue
        for item in receipt.items:
            if item.category and category.lower() in item.category.lower():
                spent += item.price or 0.0
    return spent


class BudgetVarianceProjector:
    """Project spend against budgets and compute expected overage."""

    def project_variance(
        self,
        period: str | None = None,
        horizon: int = 1,
    ) -> dict[str, Any]:
        """Project variance for weekly/monthly/yearly budgets.

        ``period`` filters to one of ``"weekly"`` / ``"monthly"`` /
        ``"yearly"`` (None = all).  Returns a dict with ``currency`` and
        ``projections`` (a list of entries with ``budget_id``, ``category``,
        ``period``, ``budgeted``, ``projected_spend``, ``expected_overage``,
        ``status``).
        """
        projections: list[dict[str, Any]] = []
        for budget in budget_store.list():
            budget_period = (
                budget.period.value
                if isinstance(budget.period, BudgetPeriod)
                else str(budget.period)
            )
            if period is not None and budget_period != period:
                continue

            date_from, date_to = _budget_window(budget_period)
            spent = _category_spend(
                receipt_store.list(date_from=date_from, date_to=date_to),
                budget.category,
            )

            fraction = _fraction_elapsed(budget_period)
            projected = (spent / fraction) if fraction > 0 else spent
            projected *= max(1, horizon)
            projected_spend = round(projected, 2)

            pct_used = projected_spend / budget.amount if budget.amount > 0 else 0.0
            projections.append(
                {
                    "budget_id": budget.budget_id,
                    "category": budget.category,
                    "period": budget_period,
                    "budgeted": budget.amount,
                    "projected_spend": projected_spend,
                    "expected_overage": round(projected_spend - budget.amount, 2),
                    "status": self._compute_status(pct_used, budget.alert_threshold),
                }
            )

        return {"currency": "USD", "projections": projections}

    @staticmethod
    def _compute_status(pct_used: float, alert_threshold: float) -> str:
        """on_track / warning / over_budget based on projected usage."""
        if pct_used >= 1.0:
            return "over_budget"
        if pct_used >= alert_threshold:
            return "warning"
        return "on_track"


# ---------------------------------------------------------------------------
# Singletons — same pattern as spending_analytics / budget_store / alert_store
# ---------------------------------------------------------------------------

forecast_engine = ForecastEngine()
anomaly_detector = AnomalyDetector()
budget_variance_projector = BudgetVarianceProjector()

# ---------------------------------------------------------------------------
# REST router — GET /forecasts, /forecasts/anomalies, /forecasts/budget-variance
# ---------------------------------------------------------------------------

forecast_router = APIRouter(prefix="/forecasts")


@forecast_router.get("", response_model=dict)
def get_forecasts(
    period: str = "monthly",
    category: str | None = None,
    horizon: int = 1,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """Return next-period spend forecast (overall + per category)."""
    return forecast_engine.forecast(
        date_from=date_from,
        date_to=date_to,
        period=period,
        category=category,
        horizon=horizon,
    )


@forecast_router.get("/anomalies", response_model=dict)
def get_forecast_anomalies(
    period: str = "monthly",
    method: str = "zscore",
    threshold: float = 2.0,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """Return detected spending anomalies for the period.

    ``period`` selects the aggregation granularity of the spend series; the
    detector always works over monthly buckets internally.
    """
    return anomaly_detector.detect_anomalies(
        date_from=date_from,
        date_to=date_to,
        method=method,
        threshold=threshold,
    )


@forecast_router.get("/budget-variance", response_model=dict)
def get_budget_variance(
    period: str | None = None,
    horizon: int = 1,
) -> dict[str, Any]:
    """Return projected budget variance with expected overage."""
    return budget_variance_projector.project_variance(
        period=period,
        horizon=horizon,
    )
