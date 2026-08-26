"""
US-001: Dashboard megnyitás — API szerződéstesztek (behavior-first).

Forrás: docs/stories/US-001-dashboard-megnyitas.md (4 AC).
Mind a 4 AC-nek 1 teszt; RED→GREEN már bizonyított (a Bearer fix előtt
AC1 piroson bukott: consumer_dashboard 401 session-nel).

Fut: pytest -q tests/test_us_001_dashboard.py
Evolúciós gate: scripts/bdd-gate.sh — hiányzik → release blokkolva.
"""
from __future__ import annotations

import pytest

# fastapi TestClient — offline, session helperrel
from fastapi.testclient import TestClient

from app.api import app
from app.product_api import service as product_service
from app.product_service import SESSION_TTL_SECONDS


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch: pytest.MonkeyPatch):
    # Production flag kikapcsolva, hogy X-Tenant fallback is tesztelhető legyen,
    # de a Bearer út mindig elsőbbséget élvez (US-001 AC1).
    monkeypatch.delenv("RECEIPTLENS_ENV", raising=False)


def _client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def _new_session(client: TestClient, email: str = "us001@example.com") -> str:
    # magic-link útvonalon hozunk létre sessiont (dev: token visszajön)
    req = client.post("/auth/magic-link-request", json={"email": email})
    assert req.status_code == 201, req.text
    token = req.json()["token"]
    ver = client.post("/auth/magic-link-verify", json={"token": token})
    assert ver.status_code == 201, ver.text
    return ver.json()["session_token"]


class TestUS001AC1HappySessionBearer:
    """AC1: session-nel a /api/v1/consumer/dashboard 200 és élő adat."""

    def test_dashboard_with_bearer_returns_live_data(self):
        c = _client()
        token = _new_session(c, "us001-ac1@example.com")
        r = c.get("/api/v1/consumer/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert "generated_at" in body
        assert "tenant" in body
        assert body["tenant"].startswith("hh-")

    def test_bearer_takes_precedence_over_bad_tenant_header(self):
        c = _client()
        token = _new_session(c, "us001-ac1b@example.com")
        r = c.get(
            "/api/v1/consumer/dashboard",
            headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": "WRONG", "X-Role": "unknown"},
        )
        # Bearer nyer — még rossz X-Tenant is ok
        assert r.status_code == 200, r.text


class TestUS001AC2ErrorNoSession:
    """AC2: session/Bearer és header nélkül 401; nem ragad loadingban."""

    def test_no_auth_returns_401(self):
        c = _client()
        r = c.get("/api/v1/consumer/dashboard")
        assert r.status_code == 401

    def test_invalid_bearer_returns_401(self):
        c = _client()
        r = c.get("/api/v1/consumer/dashboard", headers={"Authorization": "Bearer bogus-token-xyz"})
        assert r.status_code == 401

    def test_expired_session_returns_401(self):
        c = _client()
        sess = product_service.create_session("us001-ac2c@example.com", "hh-us001-ac2c", "owner", ttl_seconds=-1)
        token = sess["session_token"]
        r = c.get("/api/v1/consumer/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401

    def test_budgets_without_session_also_401(self):
        # A budgets 5 route ugyanezt a szerződést követi (US-001 edgecoverage)
        c = _client()
        r = c.get("/api/v1/budgets")
        assert r.status_code == 401


class TestUS001AC3EdgeOnboarding:
    """AC3: üres háztartásnál a preferences.onboarding_done hamis → modal jönne.

    Backend oldal: a preferences endpoint tükrözi a szerződést.
    UI modal-t a frontend E2E (us_001_dashboard.spec.ts AC3) fedi — itt csak
    a session körüli perzisztenciát ellenőrizzük: onboarding állapot a tenant
    sajátja, session-nel is őrződik.
    """

    def test_preferences_onboarding_done_roundtrips(self):
        c = _client()
        token = _new_session(c, "us001-ac3@example.com")
        h = {"Authorization": f"Bearer {token}"}
        # alapból false (friss tenant)
        r0 = c.get("/product/preferences", headers=h)
        assert r0.status_code == 200
        # beállítás
        r1 = c.put("/product/preferences", headers=h, json={"payload": {"onboarding_done": True}})
        assert r1.status_code == 200
        r2 = c.get("/product/preferences", headers=h)
        assert r2.json().get("onboarding_done") is True


class TestUS001AC4GUIContractHeaders:
    """AC4: GUI szerződés API oldala — a dashboard tenant-scope-olt és
    tenant nem szivárog (B2). Session 180 napig él (sliding)."""

    def test_tenant_scoping_not_leaked(self):
        c = _client()
        tok_a = _new_session(c, "us001-ac4a@example.com")
        tok_b = _new_session(c, "us001-ac4b@example.com")
        ra = c.get("/api/v1/consumer/dashboard", headers={"Authorization": f"Bearer {tok_a}"}).json()
        rb = c.get("/api/v1/consumer/dashboard", headers={"Authorization": f"Bearer {tok_b}"}).json()
        assert ra["tenant"] != rb["tenant"]

    def test_session_ttl_is_180_days(self):
        assert SESSION_TTL_SECONDS == 180 * 24 * 60 * 60
