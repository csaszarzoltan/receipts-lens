"""ReceiptLens forecast engine — pre-development stubs.

RED-phase scaffolding for next-period spend forecasting, anomaly detection,
and budget variance projection.  Every public method raises
``NotImplementedError`` until the developer implements the real behaviour
(see ``tests/test_forecast.py`` for the acceptance contract).

Public API (implement against these signatures):
    * ``ForecastEngine``      — per-category + overall next-period spend
                                forecast via moving-average + trend
                                extrapolation with confidence bounds.
    * ``AnomalyDetector``     — z-score or MAD based anomaly detection over
                                a historical spend series.
    * ``BudgetVarianceProjector`` — projected spend vs budgeted amount for
                                weekly/monthly/yearly budgets, including the
                                expected overage.

REST routes are exposed through the ``forecast_router`` APIRouter
(prefix ``/forecasts``), wired into ``app.api``; the CLI ``forecast``
subcommand in ``app.cli`` delegates to ``forecast_engine``.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

# ---------------------------------------------------------------------------
# ForecastEngine
# ---------------------------------------------------------------------------


class ForecastEngine:
    """Forecast next-period spending per category and overall.

    Uses moving-average smoothing combined with linear trend extrapolation
    and returns confidence bounds around the point estimate.
    """

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
        entry; each entry carries ``category``, ``next_period_total``,
        ``confidence_low``, ``confidence_high``, ``trend``, ``method``).
        """
        raise NotImplementedError("ForecastEngine.forecast not implemented")

    def forecast_by_category(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        period: str = "monthly",
        horizon: int = 1,
    ) -> dict[str, Any]:
        """Forecast next-period spend for every category separately."""
        raise NotImplementedError("ForecastEngine.forecast_by_category not implemented")

    def forecast_overall(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        period: str = "monthly",
        horizon: int = 1,
    ) -> dict[str, Any]:
        """Forecast next-period overall spend (all categories combined)."""
        raise NotImplementedError("ForecastEngine.forecast_overall not implemented")


# ---------------------------------------------------------------------------
# AnomalyDetector
# ---------------------------------------------------------------------------


class AnomalyDetector:
    """Detect anomalous spending periods via z-score or MAD."""

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
        raise NotImplementedError("AnomalyDetector.detect_anomalies not implemented")


# ---------------------------------------------------------------------------
# BudgetVarianceProjector
# ---------------------------------------------------------------------------


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
        raise NotImplementedError(
            "BudgetVarianceProjector.project_variance not implemented"
        )


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
    raise NotImplementedError("GET /forecasts not implemented")


@forecast_router.get("/anomalies", response_model=dict)
def get_forecast_anomalies(
    period: str = "monthly",
    method: str = "zscore",
    threshold: float = 2.0,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """Return detected spending anomalies for the period."""
    raise NotImplementedError("GET /forecasts/anomalies not implemented")


@forecast_router.get("/budget-variance", response_model=dict)
def get_budget_variance(
    period: str | None = None,
    horizon: int = 1,
) -> dict[str, Any]:
    """Return projected budget variance with expected overage."""
    raise NotImplementedError("GET /forecasts/budget-variance not implemented")
