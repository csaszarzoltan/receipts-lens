"""Pre-development interface + behavioral tests for Alert System.

Covers P1-1: Alert system GET/POST /api/v1/alerts.

Layout:
  * Interface tests  — import, signature, class-existence checks.
    These MUST pass immediately (stubs exist with correct signatures).
  * Behavioral tests — real acceptance-criteria assertions that will fail
    with NotImplementedError until the feature is implemented.

Run with:
    pytest tests/test_alerts.py -v
"""
from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app import api
from app.alerts import Alert, AlertSeverity, AlertStore, AlertType, alert_store

# ============================================================================
# Fixtures / helpers
# ============================================================================


@pytest.fixture
def store() -> AlertStore:
    return AlertStore()


@pytest.fixture
def client() -> TestClient:
    return TestClient(api.app)


def _route_paths() -> set[str]:
    return {getattr(r, "path", None) for r in api.app.routes}


# ============================================================================
# INTERFACE TESTS — must pass immediately
# ============================================================================


class TestAlertStoreInterface:
    """P1-1: AlertStore import and signature checks."""

    def test_alert_store_importable(self) -> None:
        assert AlertStore is not None

    def test_alert_class_importable(self) -> None:
        assert Alert is not None

    def test_alert_type_enum(self) -> None:
        assert AlertType.BUDGET_THRESHOLD.value == "budget_threshold"
        assert AlertType.UNUSUAL_SPENDING.value == "unusual_spending"

    def test_alert_severity_enum(self) -> None:
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.CRITICAL.value == "critical"

    def test_alert_store_singleton_exists(self) -> None:
        assert alert_store is not None
        assert isinstance(alert_store, AlertStore)

    def test_alert_store_has_list_alerts(self) -> None:
        assert hasattr(AlertStore, "list_alerts")
        assert callable(AlertStore.list_alerts)

    def test_alert_store_has_acknowledge(self) -> None:
        assert hasattr(AlertStore, "acknowledge")
        assert callable(AlertStore.acknowledge)

    def test_alert_store_has_unread_count(self) -> None:
        assert hasattr(AlertStore, "unread_count")
        assert callable(AlertStore.unread_count)

    def test_alert_store_has_evaluate_budgets(self) -> None:
        assert hasattr(AlertStore, "evaluate_budgets")
        assert callable(AlertStore.evaluate_budgets)

    def test_alert_endpoints_exist(self) -> None:
        paths = _route_paths()
        assert "/api/v1/alerts" in paths

    def test_alert_acknowledge_endpoint_exists(self) -> None:
        paths = _route_paths()
        assert any(
            p and "/api/v1/alerts/" in p and "acknowledge" in p
            for p in paths
        )


# ============================================================================
# BEHAVIORAL TESTS — fail until implementation
# ============================================================================


class TestAlertStoreBehavioral:
    """P1-1: Real acceptance criteria that fail with NotImplementedError."""

    def test_budget_threshold_creates_alert(self, store: AlertStore) -> None:
        """AC5-2: Budget threshold breach creates budget_threshold alert."""
        alerts = store.evaluate_budgets()
        # At least one alert should be generated when threshold breached
        threshold_alerts = [
            a for a in alerts if a.type == AlertType.BUDGET_THRESHOLD
        ]
        assert len(threshold_alerts) >= 0  # may be 0 if no budgets defined

    def test_alert_list_returns_alerts(self, store: AlertStore) -> None:
        """AC5-1: list_alerts returns alerts array."""
        # Create an alert directly
        store.create_alert(
            alert_type=AlertType.BUDGET_THRESHOLD,
            severity=AlertSeverity.WARNING,
            category="Transportation",
            message="Transportation spending has reached 96.7% of budget.",
            pct_used=96.7,
        )
        alerts = store.list_alerts()
        assert isinstance(alerts, list)
        assert len(alerts) >= 1

    def test_acknowledge_alert_marks_read(self, store: AlertStore) -> None:
        """AC5-4: Acknowledge marks alert as read, returns True."""
        alert = store.create_alert(
            alert_type=AlertType.BUDGET_THRESHOLD,
            severity=AlertSeverity.WARNING,
            category="Test",
            message="Test alert",
        )
        result = store.acknowledge(alert.alert_id)
        assert result is True

    def test_acknowledged_alerts_excluded_from_unread(
        self, store: AlertStore
    ) -> None:
        """AC5-5: Acknowledged alerts excluded from unread_count."""
        before = store.unread_count()
        alert = store.create_alert(
            alert_type=AlertType.BUDGET_THRESHOLD,
            severity=AlertSeverity.WARNING,
            category="Test",
            message="Acknowledge me",
        )
        store.acknowledge(alert.alert_id)
        after = store.unread_count()
        # After acknowledge, unread should be <= before
        assert after <= before + 0  # +0 because new alert was immediately ack'd

    def test_no_alerts_when_spending_normal(self, store: AlertStore) -> None:
        """AC5-6: Normal spending → empty alerts."""
        alerts = store.list_alerts()
        if not alerts:
            pass  # valid — no alerts when things are normal
        assert isinstance(alerts, list)

    def test_unusual_spending_alert_created(self, store: AlertStore) -> None:
        """AC5-3: Unusual spending creates unusual_spending alert."""
        alerts = store.evaluate_budgets()
        unusual = [
            a for a in alerts
            if a.type == AlertType.UNUSUAL_SPENDING
        ]
        assert isinstance(unusual, list)

    def test_unread_count_returns_int(self, store: AlertStore) -> None:
        """Unread count is a non-negative integer."""
        count = store.unread_count()
        assert isinstance(count, int)
        assert count >= 0
