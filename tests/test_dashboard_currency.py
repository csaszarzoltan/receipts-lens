"""Dashboard totals must not add different currencies together.

Receipts in HUF and USD used to be summed as one number (4 400 HUF + 10 USD
shown as 4 410 "USD"). Totals are now per currency: the dashboard reports the
budget currency (or the currency with the most spend) and lists the rest
separately, without guessing an exchange rate.
"""

from __future__ import annotations

from datetime import date

import pytest

import app.consumer_dashboard as dash
from app.product_api import service as product_service

TODAY = date(2026, 10, 9)

PAYLOADS = [
    {"date": "2026-10-02", "total": 10.0, "currency": "USD", "line_items": []},
    {"date": "2026-10-03", "total": 4400.0, "currency": "HUF",
     "line_items": [{"name": "Tea", "price": 4400.0, "category": "Food"}]},
    {"date": "2026-10-04", "total": None, "currency": "USD", "line_items": []},
    {"date": "2026-10-05", "total": 5.0, "currency": None, "line_items": []},
]


@pytest.mark.test_id("TEST-RL-V02-185")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_spend_is_split_by_currency_and_unpriced_counted():
    spend, unpriced = dash._spend_by_currency(PAYLOADS, TODAY)
    assert spend == {"USD": 10.0, "HUF": 4400.0}
    assert unpriced == 2


@pytest.mark.test_id("TEST-RL-V02-186")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_primary_currency_prefers_budget_currency():
    assert dash._primary_currency({"USD": 10.0, "HUF": 4400.0}, "USD") == "USD"


@pytest.mark.test_id("TEST-RL-V02-187")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_primary_currency_without_budget_is_largest_spend():
    assert dash._primary_currency({"USD": 10.0, "HUF": 4400.0}, None) == "HUF"


@pytest.fixture
def stored(monkeypatch):
    monkeypatch.setattr(dash, "_tenant_receipt_payloads", lambda tenant_id: PAYLOADS)
    monkeypatch.setattr(product_service, "list_members", lambda actor: [])


@pytest.mark.test_id("TEST-RL-V02-188")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_household_reports_budget_currency_and_lists_others(monkeypatch, stored):
    budget = type("B", (), {"amount": 100.0, "currency": "USD"})()
    monkeypatch.setattr(dash, "_tenant_monthly_budgets", lambda tenant_id: [budget])
    out = dash._household(TODAY, "tenant-a")
    assert out["currency"] == "USD"
    assert out["spent"] == 10.0
    assert out["remaining"] == 90.0
    assert out["spent_other_currencies"] == {"HUF": 4400.0}
    assert out["unpriced_receipts"] == 2


@pytest.mark.test_id("TEST-RL-V02-189")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_household_without_budget_uses_largest_spend_currency(monkeypatch, stored):
    monkeypatch.setattr(dash, "_tenant_monthly_budgets", lambda tenant_id: [])
    out = dash._household(TODAY, "tenant-a")
    assert out["currency"] == "HUF"
    assert out["spent"] == 4400.0
    assert out["spent_other_currencies"] == {"USD": 10.0}


@pytest.mark.test_id("TEST-RL-V02-190")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_household_has_no_developer_note_text(monkeypatch, stored):
    monkeypatch.setattr(dash, "_tenant_monthly_budgets", lambda tenant_id: [])
    out = dash._household(TODAY, "tenant-a")
    assert "F1.3" not in str(out.get("member_breakdown_note"))


@pytest.mark.test_id("TEST-RL-V02-191")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_category_breakdown_only_counts_primary_currency(stored):
    out = dash._monthly_by_category(TODAY, "tenant-a")
    assert out["currency"] == "HUF"
    assert out["total_spent"] == 4400.0
    assert out["other_currency_totals"] == {"USD": 10.0}
