"""Forecasts, anomalies and budget variance must describe the caller's tenant only."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from starlette.testclient import TestClient

import app.consumer_dashboard as dash
from app import api
from app.budgets import budget_store

NOW = datetime.now(UTC)
THIS_MONTH = NOW.strftime("%Y-%m")

PAYLOADS = {
    "tenant-a": [
        {"date": f"{THIS_MONTH}-01", "total": 400.0, "currency": "HUF",
         "line_items": [{"name": "Rice", "price": 400.0, "category": "Groceries"}]},
        {"date": f"{THIS_MONTH}-02", "total": None, "currency": "HUF", "line_items": []},
        {"date": f"{THIS_MONTH}-02", "total": 9.0, "currency": "USD", "line_items": []},
    ],
    "tenant-b": [],
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(dash, "_tenant_receipt_payloads", lambda tenant: PAYLOADS.get(tenant, []))
    return TestClient(api.app)


def _headers(tenant: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-Role": "admin"}


@pytest.fixture
def budgets():
    created = [
        budget_store.create(category="Groceries", amount=1000.0, currency="HUF", tenant_id="tenant-a"),
        budget_store.create(category="Travel", amount=500.0, currency="EUR", tenant_id="tenant-b"),
    ]
    yield created
    for record in created:
        budget_store.delete(record.budget_id)


@pytest.mark.test_id("TEST-RL-V02-206")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_variance_lists_only_the_callers_budgets(client, budgets):
    mine = client.get("/forecasts/budget-variance", headers=_headers("tenant-a")).json()
    assert {p["category"] for p in mine["projections"]} == {"Groceries"}
    other = client.get("/forecasts/budget-variance", headers=_headers("tenant-b")).json()
    assert {p["category"] for p in other["projections"]} == {"Travel"}


@pytest.mark.test_id("TEST-RL-V02-207")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_variance_uses_the_tenants_own_receipts(client, budgets):
    out = client.get("/forecasts/budget-variance", headers=_headers("tenant-a")).json()
    groceries = out["projections"][0]
    assert groceries["currency"] == "HUF"
    assert groceries["projected_spend"] > 0


@pytest.mark.test_id("TEST-RL-V02-208")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_forecast_uses_tenant_receipts_and_their_currency(client):
    out = client.get("/forecasts", headers=_headers("tenant-a")).json()
    assert out["currency"] == "HUF"
    assert {f["category"] for f in out["forecasts"]} == {"Groceries", "Overall"}


@pytest.mark.test_id("TEST-RL-V02-209")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_tenant_without_receipts_sees_no_other_tenants_data(client):
    out = client.get("/forecasts", headers=_headers("tenant-b")).json()
    assert [f["category"] for f in out["forecasts"]] == ["Overall"]
    assert out["forecasts"][0]["next_period_total"] == 0


@pytest.mark.test_id("TEST-RL-V02-210")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_unknown_totals_are_not_counted_as_zero_spend(client):
    from app.forecast import _tenant_receipts

    receipts, currency = _tenant_receipts("tenant-a")
    assert currency == "HUF"
    assert len(receipts) == 1  # the unpriced HUF receipt and the USD one are left out


@pytest.mark.test_id("TEST-RL-V02-211")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_invalid_session_is_rejected(client):
    resp = client.get("/forecasts", headers={"Authorization": "Bearer nope"})
    assert resp.status_code == 401


@pytest.mark.test_id("TEST-RL-V02-217")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_forecast_never_predicts_negative_spend():
    from app.forecast import _forecast_series

    nxt, low, high, _ = _forecast_series({"2026-01": 9000.0, "2026-02": 4000.0, "2026-03": 100.0}, 1)
    assert nxt >= 0 and low >= 0 and low <= nxt <= high
