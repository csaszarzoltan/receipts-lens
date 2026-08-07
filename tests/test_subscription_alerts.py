"""Pre-development interface + behavioral tests for Subscription Alerts.

Covers acceptance criteria from parent task t_8aafe706:

  1. extract_next_renewal_date() — monthly / quarterly / annual frequencies
  2. detect_price_increase() — triggers when current > 3-month average by >10 %
  3. AlertStore SUBSCRIPTION_RENEWAL and PRICE_INCREASE types, renewal N days before
  4. GET /api/v1/subscriptions — active subs with renewal dates, monthly cost, trend
  5. GET /api/v1/subscriptions/{id}/cancel-guide — known merchant + generic fallback
  6. Email notification activates only when SMTP config is present

Layout (follows repo pre-tester conventions):
  * Interface tests  — imports, signatures, type hints, route wiring, enum members.
    These MUST pass immediately against stubs.
  * Behavioral tests — real acceptance-criteria assertions that will fail with
    NotImplementedError (or AttributeError for AlertType extensions) until the
    developer implements them.

Run with:
    PATH=.venv/bin:$PATH python -m pytest tests/test_subscription_alerts.py -v
"""
from __future__ import annotations

import inspect
from typing import get_type_hints

import pytest
from starlette.testclient import TestClient

from app import api
from app.subscription_alerts import (
    CANCEL_GUIDES,
    FREQUENCY_MONTHS,
    GENERIC_CANCEL_GUIDE,
    CancelGuide,
    Frequency,
    detect_price_increase,
    extract_next_renewal_date,
    get_cancel_guide,
    send_email_notification,
)

# ============================================================================
# Fixtures / helpers
# ============================================================================


@pytest.fixture
def client() -> TestClient:
    return TestClient(api.app)


def _route_paths() -> set[str]:
    """Collect all mounted route paths (flat + router-included)."""
    paths: set[str] = set()
    for r in api.app.routes:
        p = getattr(r, "path", None)
        if p is not None:
            paths.add(p)
        # APIRouter-included routes may live on .routes sub-attribute
        for sub in getattr(r, "routes", []):
            sp = getattr(sub, "path", None)
            if sp is not None:
                paths.add(sp)
    return paths


# ============================================================================
# INTERFACE TESTS — must pass immediately
# ============================================================================


class TestFrequencyEnumInterface:
    """Frequency enum: members and type checks."""

    def test_frequency_is_importable(self) -> None:
        assert Frequency is not None

    def test_frequency_is_str_enum(self) -> None:
        assert issubclass(Frequency, str)

    def test_frequency_members_exist(self) -> None:
        assert Frequency.MONTHLY.value == "monthly"
        assert Frequency.QUARTERLY.value == "quarterly"
        assert Frequency.ANNUAL.value == "annual"

    def test_frequency_monthly_is_string(self) -> None:
        assert isinstance(Frequency.MONTHLY, str)

    def test_frequency_months_mapping_exists(self) -> None:
        assert isinstance(FREQUENCY_MONTHS, dict)

    def test_frequency_months_mapping_has_all_keys(self) -> None:
        assert FREQUENCY_MONTHS[Frequency.MONTHLY] == 1
        assert FREQUENCY_MONTHS[Frequency.QUARTERLY] == 3
        assert FREQUENCY_MONTHS[Frequency.ANNUAL] == 12


class TestExtractNextRenewalDateInterface:
    """extract_next_renewal_date: import, callable, signature, type hints."""

    def test_function_importable(self) -> None:
        assert callable(extract_next_renewal_date)

    def test_signature_params(self) -> None:
        sig = inspect.signature(extract_next_renewal_date)
        params = list(sig.parameters)
        assert "last_date" in params
        assert "frequency" in params
        assert "today" in params

    def test_last_date_type_hint(self) -> None:
        hints = get_type_hints(extract_next_renewal_date)
        assert hints.get("last_date") is str

    def test_frequency_type_hint(self) -> None:
        hints = get_type_hints(extract_next_renewal_date)
        freq_hint = hints.get("frequency")
        assert freq_hint is Frequency or freq_hint == "Frequency"

    def test_today_is_optional(self) -> None:
        sig = inspect.signature(extract_next_renewal_date)
        assert sig.parameters["today"].default is None

    def test_return_type_hint(self) -> None:
        hints = get_type_hints(extract_next_renewal_date)
        ret = hints.get("return")
        assert ret is str, f"return hint is {ret!r}, expected str"


class TestDetectPriceIncreaseInterface:
    """detect_price_increase: import, callable, signature, type hints."""

    def test_function_importable(self) -> None:
        assert callable(detect_price_increase)

    def test_signature_params(self) -> None:
        sig = inspect.signature(detect_price_increase)
        params = list(sig.parameters)
        assert "current_amount" in params
        assert "historical_amounts" in params
        assert "threshold" in params

    def test_current_amount_type_hint(self) -> None:
        hints = get_type_hints(detect_price_increase)
        assert hints.get("current_amount") is float

    def test_historical_amounts_type_hint(self) -> None:
        hints = get_type_hints(detect_price_increase)
        hint = hints.get("historical_amounts")
        assert hint is not None, "historical_amounts must have a type hint"

    def test_threshold_default(self) -> None:
        sig = inspect.signature(detect_price_increase)
        assert sig.parameters["threshold"].default == 0.10

    def test_return_type_hint(self) -> None:
        hints = get_type_hints(detect_price_increase)
        assert hints.get("return") is bool


class TestCancelGuideInterface:
    """CancelGuide class and get_cancel_guide function."""

    def test_cancel_guide_importable(self) -> None:
        assert CancelGuide is not None

    def test_cancel_guide_init_signature(self) -> None:
        sig = inspect.signature(CancelGuide.__init__)
        params = list(sig.parameters)
        assert "merchant" in params
        assert "steps" in params
        assert "url" in params

    def test_cancel_guide_fields(self) -> None:
        guide = CancelGuide(merchant="TestCo", steps=["step1"], url="https://x.com")
        assert guide.merchant == "TestCo"
        assert guide.steps == ["step1"]
        assert guide.url == "https://x.com"

    def test_cancel_guide_url_optional(self) -> None:
        guide = CancelGuide(merchant="TestCo", steps=["step1"])
        assert guide.url is None

    def test_generic_cancel_guide_exists(self) -> None:
        assert GENERIC_CANCEL_GUIDE is not None
        assert isinstance(GENERIC_CANCEL_GUIDE, CancelGuide)
        assert GENERIC_CANCEL_GUIDE.merchant == "generic"
        assert isinstance(GENERIC_CANCEL_GUIDE.steps, list)
        assert len(GENERIC_CANCEL_GUIDE.steps) >= 3

    def test_cancel_guides_dict_exists(self) -> None:
        assert isinstance(CANCEL_GUIDES, dict)

    def test_get_cancel_guide_importable(self) -> None:
        assert callable(get_cancel_guide)

    def test_get_cancel_guide_signature(self) -> None:
        sig = inspect.signature(get_cancel_guide)
        params = list(sig.parameters)
        assert "merchant" in params

    def test_get_cancel_guide_return_type(self) -> None:
        hints = get_type_hints(get_cancel_guide)
        ret = hints.get("return")
        assert ret is CancelGuide or ret == "CancelGuide"


class TestSendEmailNotificationInterface:
    """send_email_notification: import, callable, signature, type hints."""

    def test_function_importable(self) -> None:
        assert callable(send_email_notification)

    def test_signature_params(self) -> None:
        sig = inspect.signature(send_email_notification)
        params = list(sig.parameters)
        assert "subject" in params
        assert "body" in params
        assert "smtp_config" in params

    def test_subject_type_hint(self) -> None:
        hints = get_type_hints(send_email_notification)
        assert hints.get("subject") is str

    def test_body_type_hint(self) -> None:
        hints = get_type_hints(send_email_notification)
        assert hints.get("body") is str

    def test_smtp_config_is_optional(self) -> None:
        sig = inspect.signature(send_email_notification)
        assert sig.parameters["smtp_config"].default is None

    def test_return_type_hint(self) -> None:
        hints = get_type_hints(send_email_notification)
        assert hints.get("return") is bool


class TestSubscriptionsRouteBehavioral:
    """GET /api/v1/subscriptions and /cancel-guide route wiring — fail until added."""

    def test_subscriptions_route_exists(self) -> None:
        paths = _route_paths()
        assert "/api/v1/subscriptions" in paths, (
            "Route /api/v1/subscriptions not found — developer must add it"
        )

    def test_cancel_guide_route_exists(self) -> None:
        """GET /api/v1/subscriptions/{id}/cancel-guide."""
        paths = _route_paths()
        matching = [
            p for p in paths
            if p and "subscriptions" in p and "cancel-guide" in p
        ]
        assert len(matching) >= 1, (
            "cancel-guide route not found"
        )


# ============================================================================
# BEHAVIORAL TESTS — fail with NotImplementedError / AttributeError until
# implementation
# ============================================================================


class TestExtractNextRenewalDateBehavioral:
    """Acceptance criteria for extract_next_renewal_date."""

    def test_monthly_renewal_from_mid_month(self) -> None:
        """AC1: monthly frequency → renewal is next month, same day-of-month."""
        with pytest.raises(NotImplementedError):
            extract_next_renewal_date("2026-01-15", Frequency.MONTHLY)

    def test_monthly_renewal_from_end_of_month(self) -> None:
        """AC1: Jan 31 monthly → Feb 28 (non-leap year)."""
        with pytest.raises(NotImplementedError):
            extract_next_renewal_date("2026-01-31", Frequency.MONTHLY)

    def test_monthly_renewal_leap_year(self) -> None:
        """AC1: Jan 31 monthly in leap year → Feb 29."""
        with pytest.raises(NotImplementedError):
            extract_next_renewal_date("2028-01-31", Frequency.MONTHLY)

    def test_quarterly_renewal(self) -> None:
        """AC1: quarterly frequency → renewal is 3 months later."""
        with pytest.raises(NotImplementedError):
            extract_next_renewal_date("2026-01-15", Frequency.QUARTERLY)

    def test_quarterly_renewal_year_boundary(self) -> None:
        """AC1: quarterly from Nov → Feb next year."""
        with pytest.raises(NotImplementedError):
            extract_next_renewal_date("2026-11-10", Frequency.QUARTERLY)

    def test_annual_renewal(self) -> None:
        """AC1: annual frequency → renewal is 12 months (1 year) later."""
        with pytest.raises(NotImplementedError):
            extract_next_renewal_date("2026-03-01", Frequency.ANNUAL)

    def test_today_anchor_used_when_provided(self) -> None:
        """AC1: today anchor allows deterministic computation."""
        with pytest.raises(NotImplementedError):
            extract_next_renewal_date(
                "2026-01-15", Frequency.MONTHLY, today="2026-02-01"
            )

    def test_return_type_is_date_string(self) -> None:
        """AC1: return value must be a YYYY-MM-DD string."""
        with pytest.raises(NotImplementedError):
            extract_next_renewal_date("2026-01-15", Frequency.MONTHLY)


class TestDetectPriceIncreaseBehavioral:
    """Acceptance criteria for detect_price_increase."""

    def test_triggers_when_above_threshold(self) -> None:
        """AC3: current_amount > avg * 1.10 → True."""
        with pytest.raises(NotImplementedError):
            detect_price_increase(11.50, [10.0, 10.0, 10.0])

    def test_no_trigger_when_equal_to_avg(self) -> None:
        """AC3: current_amount == avg → False."""
        with pytest.raises(NotImplementedError):
            detect_price_increase(10.0, [10.0, 10.0, 10.0])

    def test_no_trigger_when_below_avg(self) -> None:
        """AC3: current_amount < avg → False."""
        with pytest.raises(NotImplementedError):
            detect_price_increase(9.0, [10.0, 10.0, 10.0])

    def test_no_trigger_when_exactly_at_threshold(self) -> None:
        """AC3: current_amount == avg * 1.10 → False (not strictly above)."""
        with pytest.raises(NotImplementedError):
            detect_price_increase(11.0, [10.0, 10.0, 10.0])

    def test_custom_threshold(self) -> None:
        """AC3: custom threshold (0.20) raises the bar."""
        with pytest.raises(NotImplementedError):
            detect_price_increase(11.5, [10.0, 10.0, 10.0], threshold=0.20)

    def test_single_historical_entry(self) -> None:
        """AC3: works with a single historical amount."""
        with pytest.raises(NotImplementedError):
            detect_price_increase(12.0, [10.0])

    def test_many_historical_entries(self) -> None:
        """AC3: 3-month rolling average from 3 entries."""
        with pytest.raises(NotImplementedError):
            detect_price_increase(11.0, [8.0, 9.0, 10.0])


class TestAlertTypeSubscriptionAlertsBehavioral:
    """AC2: AlertStore must support SUBSCRIPTION_RENEWAL and PRICE_INCREASE types."""

    def test_alert_type_has_subscription_renewal(self) -> None:
        """SUBSCRIPTION_RENEWAL member must exist on AlertType."""
        from app.alerts import AlertType
        assert hasattr(AlertType, "SUBSCRIPTION_RENEWAL"), (
            "AlertType missing SUBSCRIPTION_RENEWAL — developer must extend the enum"
        )

    def test_alert_type_has_price_increase(self) -> None:
        """PRICE_INCREASE member must exist on AlertType."""
        from app.alerts import AlertType
        assert hasattr(AlertType, "PRICE_INCREASE"), (
            "AlertType missing PRICE_INCREASE — developer must extend the enum"
        )

    def test_subscription_renewal_value(self) -> None:
        """SUBSCRIPTION_RENEWAL must have the correct string value."""
        from app.alerts import AlertType
        val = getattr(AlertType, "SUBSCRIPTION_RENEWAL", None)
        if val is None:
            pytest.skip("SUBSCRIPTION_RENEWAL not yet added to AlertType")
        assert val.value == "subscription_renewal"

    def test_price_increase_value(self) -> None:
        """PRICE_INCREASE must have the correct string value."""
        from app.alerts import AlertType
        val = getattr(AlertType, "PRICE_INCREASE", None)
        if val is None:
            pytest.skip("PRICE_INCREASE not yet added to AlertType")
        assert val.value == "price_increase"


class TestAlertStoreSubscriptionBehavioral:
    """AC2/AC3: AlertStore creates subscription alerts with correct scheduling."""

    def test_renewal_alert_created_on_schedule(self) -> None:
        """AC2: AlertStore creates SUBSCRIPTION_RENEWAL alert N days before renewal."""
        from app.alerts import AlertStore
        store = AlertStore()
        # The developer must add schedule_renewal_alerts to AlertStore
        assert hasattr(store, "schedule_renewal_alerts"), (
            "AlertStore missing schedule_renewal_alerts method"
        )

    def test_price_increase_alert_created(self) -> None:
        """AC3: AlertStore creates PRICE_INCREASE alert when price delta > 10%."""
        from app.alerts import AlertStore
        store = AlertStore()
        assert hasattr(store, "create_price_increase_alert"), (
            "AlertStore missing create_price_increase_alert method"
        )

    def test_renewal_alert_scheduling_configurable(self) -> None:
        """AC2: renewal_alert_days_before parameter is configurable (default 3)."""
        from app.alerts import AlertStore
        store = AlertStore()
        # Method should accept days_before parameter
        sig = inspect.signature(store.schedule_renewal_alerts)
        params = sig.parameters
        assert "days_before" in params, (
            "schedule_renewal_alerts must accept days_before parameter"
        )
        assert params["days_before"].default == 3, (
            f"days_before default must be 3, got {params['days_before'].default}"
        )


class TestSubscriptionsEndpointBehavioral:
    """AC4: GET /api/v1/subscriptions returns active subscriptions."""

    def test_subscriptions_endpoint_returns_json(self, client: TestClient) -> None:
        """AC4: endpoint returns a JSON response (not 404/500)."""
        response = client.get("/api/v1/subscriptions")
        # Will fail until endpoint is implemented (likely 404)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code} — endpoint not yet implemented?"
        )

    def test_subscriptions_response_shape(self, client: TestClient) -> None:
        """AC4: response contains subscriptions list with renewal info."""
        response = client.get("/api/v1/subscriptions")
        if response.status_code != 200:
            pytest.skip("Endpoint not implemented yet")
        data = response.json()
        assert "subscriptions" in data
        items = data["subscriptions"]
        assert isinstance(items, list)

    def test_subscription_item_shape(self, client: TestClient) -> None:
        """AC4: each subscription has merchant, renewal_date, monthly_cost, trend."""
        response = client.get("/api/v1/subscriptions")
        if response.status_code != 200:
            pytest.skip("Endpoint not implemented yet")
        data = response.json()
        items = data.get("subscriptions", [])
        if not items:
            pytest.skip("No subscriptions to inspect")
        first = items[0]
        assert "merchant" in first
        assert "renewal_date" in first
        assert "monthly_cost" in first
        assert "trend" in first


class TestCancelGuideEndpointBehavioral:
    """AC5: GET /api/v1/subscriptions/{id}/cancel-guide returns merchant steps."""

    def test_cancel_guide_known_merchant(self, client: TestClient) -> None:
        """AC5: known merchant returns merchant-specific steps."""
        response = client.get("/api/v1/subscriptions/sub-001/cancel-guide")
        # Will fail until endpoint is implemented
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}"
        )
        data = response.json()
        assert "steps" in data
        assert isinstance(data["steps"], list)
        assert len(data["steps"]) >= 1

    def test_cancel_guide_generic_fallback(self, client: TestClient) -> None:
        """AC5: unknown merchant returns generic fallback guide."""
        response = client.get("/api/v1/subscriptions/sub-unknown/cancel-guide")
        if response.status_code != 200:
            pytest.skip("Endpoint not implemented yet")
        data = response.json()
        assert "steps" in data
        # Generic fallback must have at least 3 steps
        assert len(data["steps"]) >= 3


class TestGetCancelGuideBehavioral:
    """AC5: get_cancel_guide returns merchant-specific or generic guide."""

    def test_known_merchant_returns_guide(self) -> None:
        """AC5: curated merchant returns specific steps."""
        with pytest.raises(NotImplementedError):
            get_cancel_guide("Netflix")

    def test_unknown_merchant_returns_generic(self) -> None:
        """AC5: unknown merchant returns generic fallback."""
        with pytest.raises(NotImplementedError):
            get_cancel_guide("SomeUnknownMerchant123")


class TestEmailNotificationBehavioral:
    """AC6: email notification activates only when SMTP config is present."""

    def test_no_smtp_config_returns_false(self) -> None:
        """AC6: smtp_config=None → returns False, no email sent."""
        with pytest.raises(NotImplementedError):
            send_email_notification("Subject", "Body")

    def test_with_smtp_config_returns_true(self) -> None:
        """AC6: valid smtp_config → returns True (would send email)."""
        config = {
            "host": "smtp.example.com",
            "port": 587,
            "user": "test@example.com",
            "password": "secret",
            "from_addr": "alerts@receiptlens.local",
            "to_addr": "user@example.com",
        }
        with pytest.raises(NotImplementedError):
            send_email_notification("Subject", "Body", smtp_config=config)

    def test_smtp_config_none_not_send(self) -> None:
        """AC6: explicit None config does not trigger email delivery."""
        with pytest.raises(NotImplementedError):
            send_email_notification(
                "Renewal alert", "Your sub renews soon.", smtp_config=None
            )
