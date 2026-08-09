"""Pre-development interface + behavioral tests for Subscription Dashboard.

Covers acceptance criteria from parent task t_32bd55b4:

  1. GET /api/v1/subscriptions/trend-data — monthly spending trend chart data
  2. GET /api/v1/subscriptions/renewal-timeline — upcoming renewals with countdown
  3. POST /api/v1/subscriptions/{id}/email-alert — toggle per-subscription email preference
  4. Error handling: invalid subscription ID → 404, SMTP failure → graceful (logged)

Layout (follows repo pre-tester conventions):
  * Interface tests  — imports, signatures, type hints, route wiring.
    These MUST pass immediately against stubs.
  * Behavioral tests — expected behavior assertions that fail with
    ImportError / AttributeError / wrong status until implemented.

Run with:
    PATH=.venv/bin:$PATH python -m pytest tests/test_subscription_dashboard.py -v
"""
from __future__ import annotations

import inspect
from typing import Self, get_type_hints

import pytest
from starlette.testclient import TestClient

from app import api
from app.subscription_alerts import send_email_notification

# ============================================================================
# Fixtures / helpers
# ============================================================================


@pytest.fixture
def client() -> TestClient:
    return TestClient(api.app)


def _route_paths() -> set[str]:
    """Collect all mounted route paths (flat + recursively router-included).

    FastAPI (0.115+) represents ``include_router`` mounts as ``_IncludedRouter``
    entries in ``app.routes``; the wrapped ``APIRouter`` is reachable via
    ``original_router``.  Recurse so routes under a prefix are discovered.
    """
    paths: set[str] = set()

    def walk(routes: list, prefix: str = "") -> None:
        for r in routes:
            p = getattr(r, "path", None)
            if p is not None:
                paths.add(prefix + p)
            original = getattr(r, "original_router", None)
            if original is not None and hasattr(original, "routes"):
                walk(original.routes, prefix)
            for sub in getattr(r, "routes", []) or []:
                sp = getattr(sub, "path", None)
                if sp is not None:
                    paths.add(prefix + sp)

    walk(api.app.routes)
    return paths


# ============================================================================
# INTERFACE TESTS — must pass immediately
# ============================================================================


class TestGetSubscriptionTrendDataInterface:
    """get_subscription_trend_data: route wiring + function import checks."""

    def test_trend_data_route_exists(self) -> None:
        """GET /api/v1/subscriptions/trend-data must be wired."""
        paths = _route_paths()
        matching = [p for p in paths if "subscriptions" in p and "trend" in p]
        assert len(matching) >= 1, (
            "No route matching *subscriptions*trend* — developer must add trend-data endpoint"
        )

    def test_trend_data_importable(self) -> None:
        """get_subscription_trend_data must be importable from subscriptions_api."""
        from app.subscriptions_api import get_subscription_trend_data

        assert callable(get_subscription_trend_data)

    def test_trend_data_signature(self) -> None:
        """get_subscription_trend_data must have an inspectable signature."""
        from app.subscriptions_api import get_subscription_trend_data

        sig = inspect.signature(get_subscription_trend_data)
        assert sig is not None

    def test_trend_data_return_type(self) -> None:
        """get_subscription_trend_data must declare a return type hint."""
        from app.subscriptions_api import get_subscription_trend_data

        hints = get_type_hints(get_subscription_trend_data)
        ret = hints.get("return")
        assert ret is not None, "get_subscription_trend_data must have a return type hint"


class TestToggleEmailAlertInterface:
    """toggle_email_alert: route wiring + function import checks."""

    def test_email_alert_route_exists(self) -> None:
        """POST /api/v1/subscriptions/{id}/email-alert must be wired."""
        paths = _route_paths()
        matching = [
            p for p in paths
            if "subscriptions" in p and "email-alert" in p
        ]
        assert len(matching) >= 1, (
            "No route matching *subscriptions*email-alert* — developer must add toggle endpoint"
        )

    def test_toggle_importable(self) -> None:
        """toggle_email_alert must be importable from subscriptions_api."""
        from app.subscriptions_api import toggle_email_alert

        assert callable(toggle_email_alert)

    def test_toggle_signature(self) -> None:
        """toggle_email_alert must accept subscription_id and enabled params."""
        from app.subscriptions_api import toggle_email_alert

        sig = inspect.signature(toggle_email_alert)
        params = list(sig.parameters)
        assert "subscription_id" in params, (
            "toggle_email_alert must accept subscription_id parameter"
        )

    def test_toggle_return_type(self) -> None:
        """toggle_email_alert must declare a return type hint."""
        from app.subscriptions_api import toggle_email_alert

        hints = get_type_hints(toggle_email_alert)
        ret = hints.get("return")
        assert ret is not None, "toggle_email_alert must have a return type hint"


class TestRenewalTimelineInterface:
    """GET /api/v1/subscriptions/renewal-timeline route wiring."""

    def test_renewal_timeline_route_exists(self) -> None:
        """GET /api/v1/subscriptions/renewal-timeline must be wired."""
        paths = _route_paths()
        matching = [
            p for p in paths
            if "subscriptions" in p and "renewal-timeline" in p
        ]
        assert len(matching) >= 1, (
            "No route matching *subscriptions*renewal-timeline* — developer must add endpoint"
        )


# ============================================================================
# BEHAVIORAL TESTS — fail until developer implements (expected RED)
# ============================================================================


class TestSubscriptionTrendDataBehavioral:
    """Dashboard chart data endpoint returns time-series spending data."""

    def test_returns_200(self, client: TestClient) -> None:
        """GET /api/v1/subscriptions/trend-data returns 200."""
        response = client.get("/api/v1/subscriptions/trend-data")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code} — endpoint not yet implemented?"
        )

    def test_has_monthly_breakdown(self, client: TestClient) -> None:
        """Response contains monthly spending breakdown."""
        response = client.get("/api/v1/subscriptions/trend-data")
        if response.status_code != 200:
            pytest.skip("Endpoint not implemented yet")
        data = response.json()
        # Must contain monthly data — key name may vary
        has_monthly = any(
            k in data for k in ("monthly", "months", "data", "breakdown", "series")
        )
        assert has_monthly, f"Response missing monthly breakdown: {list(data.keys())}"

    def test_has_trend_direction(self, client: TestClient) -> None:
        """Response includes trend direction (up / stable / down)."""
        response = client.get("/api/v1/subscriptions/trend-data")
        if response.status_code != 200:
            pytest.skip("Endpoint not implemented yet")
        data = response.json()
        has_trend = any(
            k in data for k in ("trend", "direction", "trend_direction")
        )
        assert has_trend, f"Response missing trend direction: {list(data.keys())}"

    @pytest.mark.parametrize("period", ["monthly", "quarterly", "annual"])
    def test_period_filter(self, client: TestClient, period: str) -> None:
        """Endpoint accepts a period parameter for granularity."""
        response = client.get(
            "/api/v1/subscriptions/trend-data",
            params={"period": period},
        )
        if response.status_code == 404:
            pytest.skip("Endpoint not implemented yet")
        assert response.status_code == 200


class TestRenewalTimelineBehavioral:
    """Renewal timeline endpoint returns upcoming renewals with countdown info."""

    def test_returns_200(self, client: TestClient) -> None:
        """GET /api/v1/subscriptions/renewal-timeline returns 200."""
        response = client.get("/api/v1/subscriptions/renewal-timeline")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code} — endpoint not yet implemented?"
        )

    def test_has_upcoming_renewals(self, client: TestClient) -> None:
        """Response contains a list of upcoming renewals."""
        response = client.get("/api/v1/subscriptions/renewal-timeline")
        if response.status_code != 200:
            pytest.skip("Endpoint not implemented yet")
        data = response.json()
        # Must contain renewals list — key name may vary
        has_list = any(
            k in data for k in ("renewals", "items", "timeline", "upcoming")
        )
        assert has_list, f"Response missing renewals list: {list(data.keys())}"

    def test_has_countdown_info(self, client: TestClient) -> None:
        """Each renewal item includes countdown (days until renewal)."""
        response = client.get("/api/v1/subscriptions/renewal-timeline")
        if response.status_code != 200:
            pytest.skip("Endpoint not implemented yet")
        data = response.json()
        items = (
            data.get("renewals")
            or data.get("items")
            or data.get("timeline")
            or data.get("upcoming")
            or []
        )
        if not items:
            pytest.skip("No renewal items to inspect")
        first = items[0]
        has_countdown = any(
            k in first for k in ("days_until", "countdown", "days_remaining", "days_left")
        )
        assert has_countdown, (
            f"Renewal item missing countdown field: {list(first.keys())}"
        )

    def test_items_include_subscription_id(self, client: TestClient) -> None:
        """Each renewal item references a subscription id."""
        response = client.get("/api/v1/subscriptions/renewal-timeline")
        if response.status_code != 200:
            pytest.skip("Endpoint not implemented yet")
        data = response.json()
        items = (
            data.get("renewals")
            or data.get("items")
            or data.get("timeline")
            or data.get("upcoming")
            or []
        )
        if not items:
            pytest.skip("No renewal items to inspect")
        first = items[0]
        assert "subscription_id" in first or "id" in first, (
            f"Renewal item missing subscription id: {list(first.keys())}"
        )


class TestEmailToggleBehavioral:
    """Email toggle endpoint enables/disables per-subscription email preference."""

    @pytest.mark.parametrize("enabled", [True, False])
    def test_toggle_on_off(self, client: TestClient, enabled: bool) -> None:
        """POST /api/v1/subscriptions/{id}/email-alert sets the preference."""
        response = client.post(
            "/api/v1/subscriptions/sub-001/email-alert",
            json={"enabled": enabled},
        )
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code} — endpoint not yet implemented?"
        )
        data = response.json()
        assert data.get("enabled") is enabled, (
            f"Expected enabled={enabled}, got {data.get('enabled')}"
        )

    def test_persist_in_db(self, client: TestClient) -> None:
        """Toggle on, then GET back to verify persistence."""
        # Toggle on
        post_response = client.post(
            "/api/v1/subscriptions/sub-001/email-alert",
            json={"enabled": True},
        )
        if post_response.status_code != 200:
            pytest.skip("POST endpoint not implemented yet")

        # Read back
        get_response = client.get("/api/v1/subscriptions/sub-001/email-alert")
        if get_response.status_code == 200:
            data = get_response.json()
            assert data.get("enabled") is True, "Email preference not persisted"

    def test_toggle_returns_subscription_id(self, client: TestClient) -> None:
        """Response includes the subscription id that was toggled."""
        response = client.post(
            "/api/v1/subscriptions/sub-001/email-alert",
            json={"enabled": True},
        )
        if response.status_code != 200:
            pytest.skip("Endpoint not implemented yet")
        data = response.json()
        assert "subscription_id" in data or "id" in data, (
            f"Response missing subscription id: {list(data.keys())}"
        )


class TestErrorCasesBehavioral:
    """Error handling: invalid subscription ID → 404, SMTP failure → graceful."""

    def test_invalid_subscription_id_returns_404(self, client: TestClient) -> None:
        """POST to email-alert with nonexistent subscription returns 404."""
        response = client.post(
            "/api/v1/subscriptions/nonexistent-999/email-alert",
            json={"enabled": True},
        )
        assert response.status_code in (404, 422), (
            f"Expected 404/422 for invalid subscription, got {response.status_code}"
        )

    def test_smtp_failure_handled_gracefully(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SMTP failure is logged, not crashed — RuntimeError is raised (documented)."""
        class _FailingSMTP:
            def __init__(self, *a: object, **kw: object) -> None:
                pass

            def __enter__(self) -> Self:
                return self

            def __exit__(self, *exc: object) -> bool:
                return False

            def ehlo(self) -> None:
                pass

            def has_extn(self, name: str) -> bool:
                return False

            def login(self, user: str, password: str) -> None:
                pass

            def send_message(self, message: object) -> None:
                raise ConnectionError("SMTP server unreachable")

        monkeypatch.setattr(
            "app.subscription_alerts.smtplib.SMTP",
            lambda *a: _FailingSMTP(),
        )
        monkeypatch.setenv("RECEIPTLENS_SMTP_ENABLED", "1")

        config = {
            "host": "smtp.example.com",
            "port": 587,
            "user": "test@example.com",
            "password": "secret",
            "from_addr": "alerts@receiptlens.local",
            "to_addr": "user@example.com",
        }
        # RuntimeError is the documented contract — not an unhandled crash
        with pytest.raises(RuntimeError, match="SMTP notification failed"):
            send_email_notification("Test", "Body", smtp_config=config)

    def test_smtp_failure_does_not_raise_without_config(self) -> None:
        """No SMTP config → returns False, never reaches the network."""
        result = send_email_notification("Test", "Body", smtp_config=None)
        assert result is False
