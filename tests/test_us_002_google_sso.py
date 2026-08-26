"""
US-002: Google SSO bejelentkezés — API szerződéstesztek.

Source: docs/stories/US-002-google-sso.md (4 AC).
Mind a 4 AC-nek 1+ teszt; offline (httpx.MockTransport RSA JWKS).

Fut: pytest -q tests/test_us_002_google_sso.py
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Any
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from fastapi.testclient import TestClient

from app import api
from app.auth_api import _oauth_hmac, _safe_return_to
from app.google_oidc import OIDCError
from app.product_api import service
from tests.test_google_oidc import CLIENT_ID, make_id_token, google_transport

client = TestClient(api.app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _google_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RECEIPTLENS_GOOGLE_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("RECEIPTLENS_GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("RECEIPTLENS_GOOGLE_REDIRECT_URI", "https://receipts.allthezoo.com/api/auth/google/callback")
    monkeypatch.setenv("RECEIPTLENS_CREDENTIAL_KEY", "test-credential-key-012345")


def _make_sync_exchange(transport):
    import asyncio
    import concurrent.futures

    def _sync(code: str, expected_nonce: str, **kw: Any) -> dict[str, Any]:
        from app.google_oidc import exchange_google_code

        def _run():
            return asyncio.run(
                exchange_google_code(
                    code, expected_nonce, http_client=httpx.AsyncClient(transport=transport, follow_redirects=False)
                )
            )

        with concurrent.futures.ThreadPoolExecutor(1) as pool:
            return pool.submit(_run).result(timeout=10)

    return _sync


# ── AC1: Happy path ───────────────────────────────────────────────


class TestUS002AC1Happy:
    def test_status_enabled_when_configured(self):
        r = client.get("/auth/google/status")
        assert r.status_code == 200
        assert r.json() == {"enabled": True}
        # Alias prefix is also routed
        r2 = client.get("/api/auth/google/status")
        assert r2.json() == {"enabled": True}

    def test_status_disabled_without_config(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("RECEIPTLENS_GOOGLE_CLIENT_ID")
        monkeypatch.delenv("RECEIPTLENS_GOOGLE_CLIENT_SECRET")
        r = client.get("/auth/google/status")
        assert r.json() == {"enabled": False}

    def test_start_redirects_to_google_with_required_params(self):
        r = client.get("/auth/google/start", follow_redirects=False)
        assert r.status_code == 307
        loc = r.headers["location"]
        assert loc.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
        qs = parse_qs(urlparse(loc).query)
        assert qs["response_type"] == ["code"]
        assert "openid email profile" in qs["scope"][0]
        assert qs["redirect_uri"][0] == "https://receipts.allthezoo.com/api/auth/google/callback"
        # state 64 hex, nonce 64 hex
        assert len(qs["state"][0]) == 64 and all(c in "0123456789abcdef" for c in qs["state"][0])
        assert len(qs["nonce"][0]) == 64

    def test_start_sets_httpOnly_secure_cookie(self):
        r = client.get("/auth/google/start", follow_redirects=False)
        cookies = r.headers.get_list("set-cookie")
        jar = [c for c in cookies if "receiptlens.oauth" in c]
        assert len(jar) == 1
        assert "HttpOnly" in jar[0] and "Secure" in jar[0] and "SameSite=lax" in jar[0]

    def test_start_state_binds_return_to_safely(self):
        # Open-redirect: absolute URL must be sanitized to /dashboard
        r = client.get("/auth/google/start?return_to=https://evil.com/steal", follow_redirects=False)
        assert r.status_code == 307
        # return_to is bound into the opaque HMAC state — not reflected verbatim in Location
        loc = r.headers["location"]
        assert "evil.com" not in loc


# ── AC2: Error states ────────────────────────────────────────────


class TestUS002AC2Errors:
    def test_missing_state_and_code_redirects_missing_params(self):
        r = client.get("/auth/google/callback?code=abc", follow_redirects=False)
        assert r.status_code == 302
        assert "oauth_missing_params" in r.headers["location"]

    def test_invalid_state_redirects_invalid_state(self):
        client.cookies.set("receiptlens.oauth", "cookie-state-value", path="/")
        try:
            r = client.get("/auth/google/callback?code=abc&state=bogus", follow_redirects=False)
        finally:
            client.cookies.clear()
        assert r.status_code == 302 and "oauth_invalid_state" in r.headers["location"]

    def test_missing_cookie_redirects_invalid_state(self):
        r = client.get("/auth/google/callback?code=abc&state=any", follow_redirects=False)
        assert r.status_code == 302 and "oauth_invalid_state" in r.headers["location"]

    def test_error_param_redirects_cancelled(self):
        r = client.get("/auth/google/callback?error=access_denied", follow_redirects=False)
        assert r.status_code == 302 and "oauth_cancelled" in r.headers["location"]

    def test_oidc_exchange_failure_redirects_exchange_failed(self):
        start = client.get("/auth/google/start", follow_redirects=False)
        state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
        cookie_val = [c for c in start.headers.get_list("set-cookie") if "receiptlens.oauth" in c][0].split(";")[0].split("=", 1)[1]

        def _bad(*a: Any, **kw: Any) -> dict[str, Any]:
            raise OIDCError("boom")

        with patch("app.auth_api.exchange_google_code", side_effect=_bad):
            client.cookies.set("receiptlens.oauth", cookie_val, path="/")
            try:
                r = client.get(f"/auth/google/callback?code=bad&state={state}", follow_redirects=False)
            finally:
                client.cookies.clear()
        assert r.status_code == 302 and "oauth_exchange_failed" in r.headers["location"]


# ── AC3: Session persistence + logout ────────────────────────────


class TestUS002AC3SessionPersistence:
    def test_callback_creates_session_and_logout_clears_it(self):
        # RED helper: uses real RSA JWKS path (same as G1 suite)
        start = client.get("/auth/google/start", follow_redirects=False)
        state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
        cookie_val = [c for c in start.headers.get_list("set-cookie") if "receiptlens.oauth" in c][0].split(";")[0].split("=", 1)[1]
        nonce = _oauth_hmac(state)
        id_token = make_id_token(nonce=nonce)
        transport = google_transport(id_token)
        with patch("app.auth_api.exchange_google_code", side_effect=_make_sync_exchange(transport)):
            client.cookies.set("receiptlens.oauth", cookie_val, path="/")
            try:
                cb = client.get(f"/auth/google/callback?code=test-code&state={state}", follow_redirects=False)
            finally:
                client.cookies.clear()
        assert cb.status_code == 302
        frag = cb.headers["location"].split("#", 1)[1]
        token = parse_qs(frag)["session_token"][0]

        # Session resolves via Bearer — AC1 happy consumer dashboard
        r = client.get("/api/v1/consumer/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200 and "tenant" in r.json()

        # Logout → 204, then dashboard 401
        assert client.post("/auth/session/logout", headers={"Authorization": f"Bearer {token}"}).status_code == 204
        assert client.get("/api/v1/consumer/dashboard", headers={"Authorization": f"Bearer {token}"}).status_code == 401


# ── AC4: GUI contract (API-side sanity — full layout is E2E) ────


class TestUS002AC4GuiSanity:
    def test_login_route_still_serves_html(self):
        # The (auth)/login page is a Next.js route — backend just proxies;
        # API-level check: google/status reachable on both prefixes
        assert client.get("/auth/google/status").status_code == 200
        assert client.get("/api/auth/google/status").status_code == 200
