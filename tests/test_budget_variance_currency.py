"""Budget variance must report the budgets' own currency, not a hard-coded USD."""

from __future__ import annotations

import pytest

from app.budgets import budget_store
from app.forecast import BudgetVarianceProjector


@pytest.fixture
def huf_budget():
    record = budget_store.create(category="Groceries", amount=150000.0, currency="HUF", tenant_id="t-currency")
    yield record
    budget_store.delete(record.budget_id)


@pytest.mark.test_id("TEST-RL-V02-204")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_variance_reports_budget_currency(huf_budget):
    out = BudgetVarianceProjector().project_variance()
    mine = [p for p in out["projections"] if p["budget_id"] == huf_budget.budget_id]
    assert mine and mine[0]["currency"] == "HUF"
    assert out["currency"] in {p["currency"] for p in out["projections"]}


@pytest.mark.test_id("TEST-RL-V02-205")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_variance_without_budgets_falls_back_to_usd(monkeypatch):
    monkeypatch.setattr(budget_store, "list", lambda **kwargs: [])
    assert BudgetVarianceProjector().project_variance() == {"currency": "USD", "projections": []}
