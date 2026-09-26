"""Pre-development interface + behavioral tests for Spending & Budget Analytics.

Covers P0-3 (GET /api/v1/analytics/spending) and P0-4 (GET /api/v1/analytics/budgets).

Layout:
  * Interface tests  — import, signature, class-existence checks.
    These MUST pass immediately (stubs exist with correct signatures).
  * Behavioral tests — real acceptance-criteria assertions that will fail
    with NotImplementedError until the feature is implemented.

Run with:
    pytest tests/test_analytics.py -v
"""
from __future__ import annotations

import inspect

import pytest
from starlette.testclient import TestClient

from app import api
from app.analytics import (
    BudgetAnalytics,
    SpendingAnalytics,
    SpendingGroup,
    TrendPoint,
    budget_analytics,
    spending_analytics,
)

# ============================================================================
# Fixtures / helpers
# ============================================================================


@pytest.fixture
def client() -> TestClient:
    return TestClient(api.app)


def _route_paths() -> set[str]:
    return {getattr(r, "path", None) for r in api.app.routes}


# ============================================================================
# INTERFACE TESTS — must pass immediately
# ============================================================================


class TestSpendingAnalyticsInterface:
    """P0-3: SpendingAnalytics import and signature checks."""

    @pytest.mark.test_id("TEST-ANL-001")
    @pytest.mark.requirements("FEAT-036")
    @pytest.mark.scenario("AC-ANL-001")
    def test_spending_analytics_importable(self) -> None:
        assert SpendingAnalytics is not None

    @pytest.mark.test_id("TEST-ANL-002")
    @pytest.mark.requirements("FEAT-036")
    @pytest.mark.scenario("AC-ANL-002")
    def test_spending_group_importable(self) -> None:
        assert SpendingGroup is not None

    @pytest.mark.test_id("TEST-ANL-003")
    @pytest.mark.requirements("FEAT-036")
    @pytest.mark.scenario("AC-ANL-003")
    def test_trend_point_importable(self) -> None:
        assert TrendPoint is not None

    @pytest.mark.test_id("TEST-ANL-004")
    @pytest.mark.requirements("FEAT-036")
    @pytest.mark.scenario("AC-ANL-004")
    def test_spending_analytics_singleton_exists(self) -> None:
        assert spending_analytics is not None
        assert isinstance(spending_analytics, SpendingAnalytics)

    @pytest.mark.test_id("TEST-ANL-005")
    @pytest.mark.requirements("FEAT-036")
    @pytest.mark.scenario("AC-ANL-005")
    def test_spending_overview_method_exists(self) -> None:
        assert hasattr(SpendingAnalytics, "spending_overview")
        assert callable(SpendingAnalytics.spending_overview)

    @pytest.mark.test_id("TEST-ANL-006")
    @pytest.mark.requirements("FEAT-036")
    @pytest.mark.scenario("AC-ANL-006")
    def test_spending_overview_signature(self) -> None:
        """spending_overview(date_from, date_to, group_by, category) -> dict"""
        sig = inspect.signature(SpendingAnalytics.spending_overview)
        params = list(sig.parameters)
        assert "date_from" in params
        assert "date_to" in params

    @pytest.mark.test_id("TEST-ANL-007")
    @pytest.mark.requirements("FEAT-036")
    @pytest.mark.scenario("AC-ANL-007")
    def test_spending_by_category_method_exists(self) -> None:
        assert hasattr(SpendingAnalytics, "by_category")
        assert callable(SpendingAnalytics.by_category)

    @pytest.mark.test_id("TEST-ANL-008")
    @pytest.mark.requirements("FEAT-036")
    @pytest.mark.scenario("AC-ANL-008")
    def test_spending_by_merchant_method_exists(self) -> None:
        assert hasattr(SpendingAnalytics, "by_merchant")
        assert callable(SpendingAnalytics.by_merchant)

    @pytest.mark.test_id("TEST-ANL-009")
    @pytest.mark.requirements("FEAT-036")
    @pytest.mark.scenario("AC-ANL-009")
    def test_spending_by_day_method_exists(self) -> None:
        assert hasattr(SpendingAnalytics, "by_day")
        assert callable(SpendingAnalytics.by_day)

    @pytest.mark.test_id("TEST-ANL-010")
    @pytest.mark.requirements("P0-4")
    @pytest.mark.scenario("AC-ANL-010")
    def test_spending_endpoint_exists(self) -> None:
        assert "/api/v1/analytics/spending" in _route_paths()


class TestBudgetAnalyticsInterface:
    """P0-4: BudgetAnalytics import and signature checks."""

    @pytest.mark.test_id("TEST-ANL-011")
    @pytest.mark.requirements("FEAT-036")
    @pytest.mark.scenario("AC-ANL-011")
    def test_budget_analytics_importable(self) -> None:
        assert BudgetAnalytics is not None

    @pytest.mark.test_id("TEST-ANL-012")
    @pytest.mark.requirements("FEAT-036")
    @pytest.mark.scenario("AC-ANL-012")
    def test_budget_analytics_singleton_exists(self) -> None:
        assert budget_analytics is not None
        assert isinstance(budget_analytics, BudgetAnalytics)

    @pytest.mark.test_id("TEST-ANL-013")
    @pytest.mark.requirements("FEAT-036")
    @pytest.mark.scenario("AC-ANL-013")
    def test_budget_overview_method_exists(self) -> None:
        assert hasattr(BudgetAnalytics, "budget_overview")
        assert callable(BudgetAnalytics.budget_overview)

    @pytest.mark.test_id("TEST-ANL-014")
    @pytest.mark.requirements("FEAT-036")
    @pytest.mark.scenario("AC-ANL-014")
    def test_budget_overview_signature(self) -> None:
        """budget_overview(period=None) -> dict"""
        sig = inspect.signature(BudgetAnalytics.budget_overview)
        params = list(sig.parameters)
        assert "period" in params

    @pytest.mark.test_id("TEST-ANL-015")
    @pytest.mark.requirements("FEAT-036")
    @pytest.mark.scenario("AC-ANL-015")
    def test_budget_endpoint_exists(self) -> None:
        assert "/api/v1/analytics/budgets" in _route_paths()


# ============================================================================
# BEHAVIORAL TESTS — fail until implementation
# ============================================================================


class TestSpendingAnalyticsBehavioral:
    """P0-3: Real acceptance criteria that fail with NotImplementedError."""

    @pytest.mark.test_id("TEST-ANL-016")
    @pytest.mark.requirements("AC3-1")
    @pytest.mark.scenario("AC-ANL-016")
    def test_spending_overview_returns_expected_structure(self) -> None:
        """AC3-1: Returns dict with total_spent, groups, etc."""
        result = spending_analytics.spending_overview(
            date_from="2026-01-01",
            date_to="2026-07-25",
            group_by="category",
        )
        assert "total_spent" in result
        assert "groups" in result
        assert "date_from" in result
        assert "date_to" in result

    @pytest.mark.test_id("TEST-ANL-017")
    @pytest.mark.requirements("AC3-2")
    @pytest.mark.scenario("AC-ANL-017")
    def test_spending_overview_by_category_groups_correctly(self) -> None:
        """AC3-2, AC3-3: Groups by category with correct fields."""
        result = spending_analytics.spending_overview(
            date_from="2026-01-01",
            date_to="2026-07-25",
            group_by="category",
        )
        for group in result["groups"]:
            assert "key" in group
            assert "total" in group
            assert "count" in group
            assert "avg" in group
            assert "max" in group
            assert "min" in group

    @pytest.mark.test_id("TEST-ANL-018")
    @pytest.mark.requirements("AC3-4")
    @pytest.mark.scenario("AC-ANL-018")
    def test_spending_overview_date_from_gt_date_to_422(self, client: TestClient) -> None:
        """AC3-4: date_from > date_to returns 422 (auth header kell a 401 helyett)."""
        resp = client.get(
            "/api/v1/analytics/spending",
            params={"date_from": "2026-07-25", "date_to": "2026-01-01"},
            headers={"X-Tenant-ID": "t-analytics", "X-Role": "admin"},
        )
        assert resp.status_code == 422

    @pytest.mark.test_id("TEST-ANL-019")
    @pytest.mark.requirements("AC3-5")
    @pytest.mark.scenario("AC-ANL-019")
    def test_spending_overview_invalid_group_by_422(self, client: TestClient) -> None:
        """AC3-5: Invalid group_by returns 422 (auth header kell a 401 helyett)."""
        resp = client.get(
            "/api/v1/analytics/spending",
            params={
                "date_from": "2026-01-01",
                "date_to": "2026-07-25",
                "group_by": "invalid_dimension",
            },
            headers={"X-Tenant-ID": "t-analytics", "X-Role": "admin"},
        )
        assert resp.status_code == 422

    @pytest.mark.test_id("TEST-ANL-020")
    @pytest.mark.requirements("AC3-6")
    @pytest.mark.scenario("AC-ANL-020")
    def test_spending_overview_trend_present(self) -> None:
        """AC3-6: Trend data when group_by=category over multi-month."""
        result = spending_analytics.spending_overview(
            date_from="2026-01-01",
            date_to="2026-07-25",
            group_by="category",
        )
        assert "trend" in result
        assert len(result["trend"]) > 0

    @pytest.mark.test_id("TEST-ANL-021")
    @pytest.mark.requirements("AC3-7")
    @pytest.mark.scenario("AC-ANL-021")
    def test_spending_overview_empty_range(self) -> None:
        """AC3-7: No receipts in range → zeroed response."""
        result = spending_analytics.spending_overview(
            date_from="2025-01-01",
            date_to="2025-01-31",
            group_by="category",
        )
        assert result["total_spent"] == 0
        assert result["groups"] == []

    @pytest.mark.test_id("TEST-ANL-022")
    @pytest.mark.requirements("AC3-8")
    @pytest.mark.scenario("AC-ANL-022")
    def test_spending_overview_filter_by_category(self) -> None:
        """AC3-8: category filter narrows results to single category."""
        result = spending_analytics.spending_overview(
            date_from="2026-01-01",
            date_to="2026-07-25",
            group_by="category",
            category="Transportation",
        )
        assert all(g["key"] == "Transportation" for g in result["groups"])


class TestBudgetAnalyticsBehavioral:
    """P0-4: Real acceptance criteria that fail with NotImplementedError."""

    @pytest.mark.test_id("TEST-ANL-023")
    @pytest.mark.requirements("AC4-1")
    @pytest.mark.scenario("AC-ANL-023")
    def test_budget_overview_returns_expected_structure(self) -> None:
        """AC4-1: Returns period, currency, budgets, summary."""
        result = budget_analytics.budget_overview(period="monthly")
        assert "period" in result
        assert "currency" in result
        assert "budgets" in result
        assert "summary" in result

    @pytest.mark.test_id("TEST-ANL-024")
    @pytest.mark.requirements("AC4-2")
    @pytest.mark.scenario("AC-ANL-024")
    def test_budget_overview_has_computed_fields(self) -> None:
        """AC4-2: Each budget has budgeted/spent/remaining/pct_used."""
        result = budget_analytics.budget_overview()
        for b in result["budgets"]:
            assert "budgeted" in b
            assert "spent" in b
            assert "remaining" in b
            assert "pct_used" in b

    @pytest.mark.test_id("TEST-ANL-025")
    @pytest.mark.requirements("AC4-3")
    @pytest.mark.scenario("AC-ANL-025")
    def test_budget_overview_status_on_track(self) -> None:
        """AC4-3: Budget under threshold shows 'on_track'."""
        # Implementation should compute status based on pct_used < alert_threshold
        status = budget_analytics._compute_status(0.5, 0.8)
        assert status == "on_track"

    @pytest.mark.test_id("TEST-ANL-026")
    @pytest.mark.requirements("AC4-3")
    @pytest.mark.scenario("AC-ANL-026")
    def test_budget_overview_status_warning(self) -> None:
        """AC4-3: Budget near threshold shows 'warning'."""
        status = budget_analytics._compute_status(0.85, 0.8)
        assert status == "warning"

    @pytest.mark.test_id("TEST-ANL-027")
    @pytest.mark.requirements("AC4-3")
    @pytest.mark.scenario("AC-ANL-027")
    def test_budget_overview_status_over_budget(self) -> None:
        """AC4-3: Budget exceeded shows 'over_budget'."""
        status = budget_analytics._compute_status(1.0, 0.8)
        assert status == "over_budget"

    @pytest.mark.test_id("TEST-ANL-028")
    @pytest.mark.requirements("AC4-4")
    @pytest.mark.scenario("AC-ANL-028")
    def test_budget_overview_summary_aggregates(self) -> None:
        """AC4-4: Summary aggregates totals across budgets."""
        result = budget_analytics.budget_overview()
        summary = result["summary"]
        assert "total_budgeted" in summary
        assert "total_spent" in summary
        assert "total_remaining" in summary
        assert "overall_pct" in summary
        assert "on_track" in summary
        assert "warning" in summary
        assert "over_budget" in summary

    @pytest.mark.test_id("TEST-ANL-029")
    @pytest.mark.requirements("AC4-5")
    @pytest.mark.scenario("AC-ANL-029")
    def test_budget_overview_no_budgets(self) -> None:
        """AC4-5: No budgets → 200 with empty budgets array."""
        result = budget_analytics.budget_overview()
        # When no budgets exist, budgets should be empty, summary zeroed
        assert isinstance(result["budgets"], list)
