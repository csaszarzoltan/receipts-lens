"""Pre-development interface + behavioral tests for the Forecast Engine.

Covers next-period spend forecasting (moving-average + trend extrapolation
with confidence bounds), anomaly detection (z-score / MAD), budget variance
projection (weekly/monthly/yearly with expected overage), the REST endpoints
GET /forecasts, /forecasts/anomalies, /forecasts/budget-variance, and the
CLI ``receipts-lens forecast --period monthly`` subcommand.

Layout:
  * Interface tests  — import, signature, class-existence, router and CLI
    wiring checks.  These MUST pass immediately (stubs exist with correct
    signatures and are wired into app.api / app.cli).
  * Behavioral tests — real acceptance-criteria assertions that fail with
    NotImplementedError until the feature is implemented.

Run with:
    .venv/bin/python -m pytest tests/test_forecast.py -v
"""
from __future__ import annotations

import argparse
import inspect
from typing import Any, get_type_hints

import pytest
from fastapi import APIRouter
from starlette.testclient import TestClient

from app import api
from app.cli import _build_parser, _cmd_forecast, main
from app.forecast import (
    AnomalyDetector,
    BudgetVarianceProjector,
    ForecastEngine,
    anomaly_detector,
    budget_variance_projector,
    forecast_engine,
    forecast_router,
    get_budget_variance,
    get_forecast_anomalies,
    get_forecasts,
)

# ============================================================================
# Fixtures / helpers
# ============================================================================


@pytest.fixture
def client() -> TestClient:
    return TestClient(api.app)


@pytest.fixture
def seeded_budget():
    """Create a monthly Groceries budget in the shared store, then clean up."""
    from app.budgets import budget_store

    record = budget_store.create(category="Groceries", amount=300.0, period="monthly")
    yield record
    budget_store.delete(record.budget_id)


def _openapi_paths() -> set[str]:
    """Resolved app-level paths (included routers are lazy ``_IncludedRouter``
    wrappers in app.routes, so the OpenAPI schema is the reliable check)."""
    return set(api.app.openapi().get("paths", {}).keys())


def _router_paths() -> set[str]:
    return {getattr(r, "path", None) for r in forecast_router.routes}


# ============================================================================
# INTERFACE TESTS — must pass immediately
# ============================================================================


class TestForecastModuleInterface:
    """Module-level imports, classes and singletons."""

    def test_module_importable(self) -> None:
        import app.forecast

        assert app.forecast is not None

    def test_forecast_engine_importable(self) -> None:
        assert ForecastEngine is not None

    def test_anomaly_detector_importable(self) -> None:
        assert AnomalyDetector is not None

    def test_budget_variance_projector_importable(self) -> None:
        assert BudgetVarianceProjector is not None

    def test_forecast_engine_singleton_exists(self) -> None:
        assert forecast_engine is not None
        assert isinstance(forecast_engine, ForecastEngine)

    def test_anomaly_detector_singleton_exists(self) -> None:
        assert anomaly_detector is not None
        assert isinstance(anomaly_detector, AnomalyDetector)

    def test_budget_variance_projector_singleton_exists(self) -> None:
        assert budget_variance_projector is not None
        assert isinstance(budget_variance_projector, BudgetVarianceProjector)


class TestForecastEngineInterface:
    """ForecastEngine method existence, signatures and type hints."""

    def test_forecast_method_exists(self) -> None:
        assert hasattr(ForecastEngine, "forecast")
        assert callable(ForecastEngine.forecast)

    def test_forecast_signature_params(self) -> None:
        sig = inspect.signature(ForecastEngine.forecast)
        params = list(sig.parameters)
        assert "date_from" in params
        assert "date_to" in params
        assert "period" in params
        assert "category" in params
        assert "horizon" in params

    def test_forecast_signature_defaults(self) -> None:
        sig = inspect.signature(ForecastEngine.forecast)
        assert sig.parameters["period"].default == "monthly"
        assert sig.parameters["category"].default is None
        assert sig.parameters["horizon"].default == 1
        assert sig.parameters["date_from"].default is None
        assert sig.parameters["date_to"].default is None

    def test_forecast_return_annotation(self) -> None:
        hints = get_type_hints(ForecastEngine.forecast)
        ret = hints.get("return")
        assert ret is not None
        assert ret == dict[str, Any] or ret == "dict[str, Any]"

    def test_forecast_by_category_method_exists(self) -> None:
        assert hasattr(ForecastEngine, "forecast_by_category")
        assert callable(ForecastEngine.forecast_by_category)

    def test_forecast_by_category_signature(self) -> None:
        sig = inspect.signature(ForecastEngine.forecast_by_category)
        params = list(sig.parameters)
        assert "date_from" in params
        assert "date_to" in params
        assert "period" in params
        assert "horizon" in params

    def test_forecast_overall_method_exists(self) -> None:
        assert hasattr(ForecastEngine, "forecast_overall")
        assert callable(ForecastEngine.forecast_overall)

    def test_forecast_overall_signature(self) -> None:
        sig = inspect.signature(ForecastEngine.forecast_overall)
        params = list(sig.parameters)
        assert "date_from" in params
        assert "date_to" in params
        assert "period" in params
        assert "horizon" in params


class TestAnomalyDetectorInterface:
    """AnomalyDetector method existence, signatures and type hints."""

    def test_detect_anomalies_method_exists(self) -> None:
        assert hasattr(AnomalyDetector, "detect_anomalies")
        assert callable(AnomalyDetector.detect_anomalies)

    def test_detect_anomalies_signature_params(self) -> None:
        sig = inspect.signature(AnomalyDetector.detect_anomalies)
        params = list(sig.parameters)
        assert "date_from" in params
        assert "date_to" in params
        assert "method" in params
        assert "threshold" in params

    def test_detect_anomalies_signature_defaults(self) -> None:
        sig = inspect.signature(AnomalyDetector.detect_anomalies)
        assert sig.parameters["method"].default == "zscore"
        assert sig.parameters["threshold"].default == 2.0

    def test_detect_anomalies_return_annotation(self) -> None:
        hints = get_type_hints(AnomalyDetector.detect_anomalies)
        ret = hints.get("return")
        assert ret is not None
        assert ret == dict[str, Any] or ret == "dict[str, Any]"


class TestBudgetVarianceProjectorInterface:
    """BudgetVarianceProjector method existence, signatures and type hints."""

    def test_project_variance_method_exists(self) -> None:
        assert hasattr(BudgetVarianceProjector, "project_variance")
        assert callable(BudgetVarianceProjector.project_variance)

    def test_project_variance_signature_params(self) -> None:
        sig = inspect.signature(BudgetVarianceProjector.project_variance)
        params = list(sig.parameters)
        assert "period" in params
        assert "horizon" in params

    def test_project_variance_signature_defaults(self) -> None:
        sig = inspect.signature(BudgetVarianceProjector.project_variance)
        assert sig.parameters["period"].default is None
        assert sig.parameters["horizon"].default == 1

    def test_project_variance_return_annotation(self) -> None:
        hints = get_type_hints(BudgetVarianceProjector.project_variance)
        ret = hints.get("return")
        assert ret is not None
        assert ret == dict[str, Any] or ret == "dict[str, Any]"


class TestForecastRouterInterface:
    """REST router wiring and handler signatures."""

    def test_forecast_router_is_apirouter(self) -> None:
        assert isinstance(forecast_router, APIRouter)

    def test_forecast_router_prefix(self) -> None:
        assert forecast_router.prefix == "/forecasts"

    def test_forecast_router_has_three_routes(self) -> None:
        assert len(forecast_router.routes) == 3

    def test_forecasts_route_registered(self) -> None:
        assert "/forecasts" in _router_paths()
        assert "/forecasts" in _openapi_paths()

    def test_forecasts_anomalies_route_registered(self) -> None:
        assert "/forecasts/anomalies" in _router_paths()
        assert "/forecasts/anomalies" in _openapi_paths()

    def test_forecasts_budget_variance_route_registered(self) -> None:
        assert "/forecasts/budget-variance" in _router_paths()
        assert "/forecasts/budget-variance" in _openapi_paths()

    def test_get_forecasts_handler_exists(self) -> None:
        assert callable(get_forecasts)

    def test_get_forecasts_signature(self) -> None:
        sig = inspect.signature(get_forecasts)
        params = list(sig.parameters)
        assert "period" in params
        assert "category" in params
        assert "horizon" in params
        assert "date_from" in params
        assert "date_to" in params

    def test_get_forecast_anomalies_handler_exists(self) -> None:
        assert callable(get_forecast_anomalies)

    def test_get_forecast_anomalies_signature(self) -> None:
        sig = inspect.signature(get_forecast_anomalies)
        params = list(sig.parameters)
        assert "period" in params
        assert "method" in params
        assert "threshold" in params
        assert "date_from" in params
        assert "date_to" in params

    def test_get_budget_variance_handler_exists(self) -> None:
        assert callable(get_budget_variance)

    def test_get_budget_variance_signature(self) -> None:
        sig = inspect.signature(get_budget_variance)
        params = list(sig.parameters)
        assert "period" in params
        assert "horizon" in params


class TestForecastCLIInterface:
    """CLI ``forecast`` subcommand wiring."""

    def test_cmd_forecast_exists(self) -> None:
        assert callable(_cmd_forecast)

    def test_cmd_forecast_signature(self) -> None:
        sig = inspect.signature(_cmd_forecast)
        assert "args" in sig.parameters

    def test_parser_has_forecast_subcommand(self) -> None:
        parser = _build_parser()
        args, _ = parser.parse_known_args(["forecast", "--period", "monthly"])
        assert args.command == "forecast"

    def test_forecast_has_period_option(self) -> None:
        parser = _build_parser()
        args, _ = parser.parse_known_args(["forecast", "--period", "weekly"])
        assert args.period == "weekly"

    def test_forecast_period_default_monthly(self) -> None:
        parser = _build_parser()
        args, _ = parser.parse_known_args(["forecast"])
        assert args.period == "monthly"

    def test_forecast_has_category_option(self) -> None:
        parser = _build_parser()
        args, _ = parser.parse_known_args(["forecast", "--category", "Groceries"])
        assert args.category == "Groceries"

    def test_forecast_has_horizon_option(self) -> None:
        parser = _build_parser()
        args, _ = parser.parse_known_args(["forecast", "--horizon", "3"])
        assert args.horizon == 3

    def test_main_routes_forecast_command(self) -> None:
        # main() dispatches "forecast" to _cmd_forecast (stub raises NotImplementedError
        # during RED, which main() converts to exit code 2).
        result = main(["forecast", "--period", "monthly"])
        assert isinstance(result, int)


# ============================================================================
# BEHAVIORAL TESTS — fail with NotImplementedError until implementation
# ============================================================================


class TestForecastEngineBehavior:
    """Moving-average + trend extrapolation forecast with confidence bounds."""

    def test_forecast_returns_expected_structure(self) -> None:
        result = forecast_engine.forecast(period="monthly")
        assert "period" in result
        assert "currency" in result
        assert "forecasts" in result
        assert isinstance(result["forecasts"], list)
        assert "source_range" in result

    def test_forecast_period_honored(self) -> None:
        result = forecast_engine.forecast(period="monthly")
        assert result["period"] == "monthly"

    def test_forecast_entries_have_confidence_bounds(self) -> None:
        result = forecast_engine.forecast(period="monthly")
        for entry in result["forecasts"]:
            assert "category" in entry
            assert "next_period_total" in entry
            assert "confidence_low" in entry
            assert "confidence_high" in entry
            assert "trend" in entry
            assert "method" in entry

    def test_forecast_confidence_bounds_are_sane(self) -> None:
        result = forecast_engine.forecast(period="monthly")
        for entry in result["forecasts"]:
            assert entry["confidence_low"] <= entry["next_period_total"]
            assert entry["next_period_total"] <= entry["confidence_high"]

    def test_forecast_includes_overall_entry(self) -> None:
        result = forecast_engine.forecast(period="monthly")
        assert any(e["category"] == "Overall" for e in result["forecasts"])

    def test_forecast_by_category_excludes_overall(self) -> None:
        result = forecast_engine.forecast_by_category(period="monthly")
        assert "forecasts" in result
        assert all(e["category"] != "Overall" for e in result["forecasts"])

    def test_forecast_overall_returns_single_overall_entry(self) -> None:
        result = forecast_engine.forecast_overall(period="monthly")
        assert "forecasts" in result
        assert len(result["forecasts"]) == 1
        assert result["forecasts"][0]["category"] == "Overall"

    def test_forecast_category_filter(self) -> None:
        result = forecast_engine.forecast(period="monthly", category="Groceries")
        assert all(e["category"] == "Groceries" for e in result["forecasts"])

    def test_forecast_weekly_period_supported(self) -> None:
        result = forecast_engine.forecast(period="weekly")
        assert result["period"] == "weekly"

    def test_forecast_horizon_greater_than_one(self) -> None:
        result = forecast_engine.forecast(period="monthly", horizon=3)
        assert "forecasts" in result


class TestAnomalyDetectorBehavior:
    """Z-score / MAD anomaly detection over the spend series."""

    def test_detect_anomalies_returns_expected_structure(self) -> None:
        result = anomaly_detector.detect_anomalies()
        assert "method" in result
        assert "threshold" in result
        assert "anomalies" in result
        assert isinstance(result["anomalies"], list)

    def test_detect_anomalies_default_method(self) -> None:
        result = anomaly_detector.detect_anomalies()
        assert result["method"] == "zscore"

    @pytest.mark.parametrize("method", ["zscore", "mad"])
    def test_detect_anomalies_method_honored(self, method: str) -> None:
        result = anomaly_detector.detect_anomalies(method=method)
        assert result["method"] == method

    def test_detect_anomalies_threshold_honored(self) -> None:
        result = anomaly_detector.detect_anomalies(threshold=3.0)
        assert result["threshold"] == 3.0

    def test_anomaly_entries_have_fields(self) -> None:
        result = anomaly_detector.detect_anomalies()
        for anomaly in result["anomalies"]:
            assert "period" in anomaly
            assert "category" in anomaly
            assert "expected" in anomaly
            assert "actual" in anomaly
            assert "score" in anomaly
            assert "flagged" in anomaly

    def test_flagged_anomalies_exceed_threshold(self) -> None:
        result = anomaly_detector.detect_anomalies(threshold=2.0)
        for anomaly in result["anomalies"]:
            if anomaly["flagged"]:
                assert anomaly["score"] >= 2.0


class TestBudgetVarianceProjectorBehavior:
    """Budget variance projection for weekly/monthly/yearly budgets."""

    def test_project_variance_returns_expected_structure(self) -> None:
        result = budget_variance_projector.project_variance()
        assert "currency" in result
        assert "projections" in result
        assert isinstance(result["projections"], list)

    @pytest.mark.parametrize("period", ["weekly", "monthly", "yearly"])
    def test_project_variance_period_honored(self, period: str) -> None:
        result = budget_variance_projector.project_variance(period=period)
        assert all(p["period"] == period for p in result["projections"])

    def test_projection_entries_have_fields(self) -> None:
        result = budget_variance_projector.project_variance()
        for projection in result["projections"]:
            assert "budget_id" in projection
            assert "category" in projection
            assert "period" in projection
            assert "budgeted" in projection
            assert "projected_spend" in projection
            assert "expected_overage" in projection
            assert "status" in projection

    def test_expected_overage_matches_projected_minus_budgeted(self) -> None:
        result = budget_variance_projector.project_variance()
        for projection in result["projections"]:
            expected = round(projection["projected_spend"] - projection["budgeted"], 2)
            assert projection["expected_overage"] == expected

    def test_seeded_monthly_budget_appears_in_monthly_projection(
        self, seeded_budget
    ) -> None:
        result = budget_variance_projector.project_variance(period="monthly")
        ids = {p["budget_id"] for p in result["projections"]}
        assert seeded_budget.budget_id in ids

    def test_seeded_monthly_budget_absent_from_weekly_projection(
        self, seeded_budget
    ) -> None:
        result = budget_variance_projector.project_variance(period="weekly")
        ids = {p["budget_id"] for p in result["projections"]}
        assert seeded_budget.budget_id not in ids


class TestForecastAPIBehavior:
    """REST endpoints via TestClient — expected response shapes."""

    def test_get_forecasts_returns_200(self, client: TestClient) -> None:
        resp = client.get("/forecasts")
        assert resp.status_code == 200
        data = resp.json()
        assert "period" in data
        assert "currency" in data
        assert "forecasts" in data
        assert isinstance(data["forecasts"], list)

    def test_get_forecasts_period_param(self, client: TestClient) -> None:
        resp = client.get("/forecasts", params={"period": "weekly"})
        assert resp.status_code == 200
        assert resp.json()["period"] == "weekly"

    def test_get_forecasts_category_param(self, client: TestClient) -> None:
        resp = client.get("/forecasts", params={"category": "Groceries"})
        assert resp.status_code == 200
        data = resp.json()
        assert all(e["category"] == "Groceries" for e in data["forecasts"])

    def test_get_forecasts_anomalies_returns_200(self, client: TestClient) -> None:
        resp = client.get("/forecasts/anomalies")
        assert resp.status_code == 200
        data = resp.json()
        assert "method" in data
        assert "threshold" in data
        assert "anomalies" in data
        assert isinstance(data["anomalies"], list)

    def test_get_forecasts_anomalies_method_param(self, client: TestClient) -> None:
        resp = client.get("/forecasts/anomalies", params={"method": "mad"})
        assert resp.status_code == 200
        assert resp.json()["method"] == "mad"

    def test_get_budget_variance_returns_200(self, client: TestClient) -> None:
        resp = client.get("/forecasts/budget-variance")
        assert resp.status_code == 200
        data = resp.json()
        assert "currency" in data
        assert "projections" in data
        assert isinstance(data["projections"], list)

    def test_get_budget_variance_period_param(self, client: TestClient) -> None:
        resp = client.get("/forecasts/budget-variance", params={"period": "yearly"})
        assert resp.status_code == 200
        data = resp.json()
        assert all(p["period"] == "yearly" for p in data["projections"])


class TestForecastCLIBehavior:
    """CLI ``receipts-lens forecast --period monthly`` behaviour."""

    def test_cmd_forecast_returns_zero(self) -> None:
        args = argparse.Namespace(period="monthly", category=None, horizon=1)
        result = _cmd_forecast(args)
        assert result == 0

    def test_main_forecast_returns_zero(self) -> None:
        result = main(["forecast", "--period", "monthly"])
        assert result == 0

    def test_main_forecast_prints_summary(self, capsys) -> None:
        result = main(["forecast", "--period", "monthly"])
        captured = capsys.readouterr()
        assert result == 0
        assert "Forecast" in captured.out
        assert "monthly" in captured.out
