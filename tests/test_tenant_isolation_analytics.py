"""Tenant-izolacio RED-tesztek az analytics/alerts/reports endpointokra.

Audit-findingok: API2-1 (reports), API2-2 (spending), API2-3 (budgets),
API2-4/5 (alerts). Ezek az endpointok jelenleg auth nelkul, tenant-szures
nelkul szolgalnak ki — barmely hivó masik tenant adatait latja.

A javitas utan:
- auth (Bearer session) nelkul -> 401 (dev-ben a header-auth elfogadott,
  lasd test_us_024: "legacy X-Tenant-ID test auth stays compatible in dev"),
- masik tenant adata -> nem lathato (ures lista / csak sajat),
- idegen alert acknowledge -> 404.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import api

client = TestClient(api.app)


def _magic_login(email: str) -> dict:
    requested = client.post(
        "/auth/magic-link-request",
        json={"email": email},
    )
    assert requested.status_code == 201
    body = requested.json()
    verified = client.post("/auth/magic-link-verify", json={"token": body["token"]})
    assert verified.status_code == 201
    return verified.json()


def _auth(email: str) -> dict[str, str]:
    session = _magic_login(email)
    return {"Authorization": f"Bearer {session['session_token']}"}


# ---------------------------------------------------------------------------
# API2-2: spending analytics — auth nelkul 401 kell (nem 200 minden adattal)
# ---------------------------------------------------------------------------


@pytest.mark.test_id("TEST-TENANT-001")
@pytest.mark.requirements("REQ-A2-02")
@pytest.mark.scenario("AC-A2-02")
def test_spending_analytics_requires_auth() -> None:
    """API2-2: auth nelkul a spending analytics nem szolgalhat ki (401)."""
    resp = client.get(
        "/api/v1/analytics/spending",
        params={"date_from": "2020-01-01", "date_to": "2026-12-31"},
    )
    assert resp.status_code == 401, (
        f"auth nelkul 401 kell, nem {resp.status_code} (cross-tenant szivargas)"
    )


@pytest.mark.test_id("TEST-TENANT-002")
@pytest.mark.requirements("REQ-A2-02")
@pytest.mark.scenario("AC-A2-02")
def test_spending_analytics_only_own_data() -> None:
    """API2-2: A tenant csak a sajat adatait lathatja, B adatait nem."""
    auth_a = _auth("tenant-a-red@example.com")
    auth_b = _auth("tenant-b-red@example.com")
    resp_a = client.get(
        "/api/v1/analytics/spending",
        params={"date_from": "2020-01-01", "date_to": "2026-12-31"},
        headers=auth_a,
    )
    resp_b = client.get(
        "/api/v1/analytics/spending",
        params={"date_from": "2020-01-01", "date_to": "2026-12-31"},
        headers=auth_b,
    )
    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    # A seed-adatok kozosek, de a valasz tenant-scope-olt kell legyen:
    # ha B-nek nincs sajat receiptje, a totalja 0 kell legyen.
    assert resp_b.json()["total_spent"] == 0.0, (
        "B tenant ures kell legyen — a kozos seed nem szivaroghat at"
    )


# ---------------------------------------------------------------------------
# API2-3: budget analytics — auth nelkul 401 kell
# ---------------------------------------------------------------------------


@pytest.mark.test_id("TEST-TENANT-003")
@pytest.mark.requirements("REQ-A2-03")
@pytest.mark.scenario("AC-A2-03")
def test_budget_analytics_requires_auth() -> None:
    """API2-3: auth nelkul a budget analytics nem szolgalhat ki (401)."""
    resp = client.get("/api/v1/analytics/budgets")
    assert resp.status_code == 401, (
        f"auth nelkul 401 kell, nem {resp.status_code} (cross-tenant szivargas)"
    )


# ---------------------------------------------------------------------------
# API2-4/5: alerts — auth nelkul 401, idegen alert 404
# ---------------------------------------------------------------------------


@pytest.mark.test_id("TEST-TENANT-004")
@pytest.mark.requirements("REQ-A2-04")
@pytest.mark.scenario("AC-A2-04")
def test_alerts_requires_auth() -> None:
    """API2-4: auth nelkul az alerts-lista nem szolgalhat ki (401)."""
    resp = client.get("/api/v1/alerts")
    assert resp.status_code == 401, (
        f"auth nelkul 401 kell, nem {resp.status_code} (cross-tenant szivargas)"
    )


@pytest.mark.test_id("TEST-TENANT-005")
@pytest.mark.requirements("REQ-A2-05")
@pytest.mark.scenario("AC-A2-05")
def test_acknowledge_foreign_alert_404() -> None:
    """API2-5: idegen alert acknowledge 404 kell legyen, nem csendes elnémítás."""
    auth_a = _auth("tenant-ack-a@example.com")
    auth_b = _auth("tenant-ack-b@example.com")
    from app.alerts import (
        AlertSeverity,
        AlertType,
        alert_store,
    )

    victim = alert_store.create_alert(
        alert_type=AlertType.BUDGET_THRESHOLD,
        severity=AlertSeverity.WARNING,
        category="Meals",
        message="victim alert",
        tenant_id="__victim__",
    )
    # A victim alert tenantjet atirjuk a victim session tenantjere:
    # (a create utan a store-ban levo objektumot cimkezzuk)
    victim_session = _magic_login("tenant-ack-victim@example.com")
    victim_tenant = victim_session["household_id"]
    victim.tenant_id = victim_tenant
    resp = client.post(
        f"/api/v1/alerts/{victim.alert_id}/acknowledge",
        headers=auth_b,
    )
    assert resp.status_code == 404, (
        f"idegen alertre 404 kell, nem {resp.status_code}"
    )
    # A victim alertje nem némulhatott el:
    assert victim.acknowledged is False
