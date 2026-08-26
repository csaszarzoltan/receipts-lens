"""G2 — Google auth routes integration tests (docs/plans/google-sso-2026-08-26.md).

Contract under test (``app/auth_api.py`` G2 routes):

  * ``GET  /api/auth/google/status``    → {enabled: bool}
  * ``GET  /api/auth/google/start``     → 307 redirect + CSRF cookie
  * ``GET  /api/auth/google/callback``  → 302 redirect with session fragment
  * ``POST /api/auth/session/logout``   → 204, session deleted

The Google code exchange is mocked so these tests run fully offline.
The OAuth CSRF cookie is validated; HMAC-derived nonce is exercised end-to-end.
"""
from __future__ import annotations

import os
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import api
from app.auth_api import _oauth_hmac
from app.product_api import service
from app.product_service import Actor

# Reuse the offline crypto helpers from the OIDC test suite so we can sign
# valid ID tokens without hitting Google.
from tests.test_google_oidc import CLIENT_ID, make_id_token, google_transport


client = TestClient(api.app)


@pytest.fixture(autouse=True)
def _google_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RECEIPTLENS_GOOGLE_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("RECEIPTLENS_GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv(
        "RECEIPTLENS_GOOGLE_REDIRECT_URI",
        "https://receipts.allthezoo.com/api/auth/google/callback",
    )
    yield


def _make_sync_exchange(transport):
    """Build a synchronous mock for exchange_google_code that uses the given transport."""
    import httpx
    import asyncio

    def _sync_exchange(code: str, expected_nonce: str, **kw: Any) -> dict[str, Any]:
        from app.google_oidc import exchange_google_code
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            # We're inside an async loop (TestClient). Use a thread.
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(1) as pool:
                future = pool.submit(asyncio.run, exchange_google_code(
                    code, expected_nonce,
                    http_client=httpx.AsyncClient(transport=transport, follow_redirects=False),
                ))
                return future.result(timeout=10)
        else:
            return asyncio.run(exchange_google_code(
                code, expected_nonce,
                http_client=httpx.AsyncClient(transport=transport, follow_redirects=False),
            ))
    return _sync_exchange


# ---------------------------------------------------------------------------
# 1. GET /api/auth/google/status
# ---------------------------------------------------------------------------


class TestGoogleStatus:
    def test_status_enabled_when_configured(self) -> None:
        resp = client.get("/api/auth/google/status")
        assert resp.status_code == 200
        assert resp.json() == {"enabled": True}

    def test_status_disabled_without_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("RECEIPTLENS_GOOGLE_CLIENT_ID")
        monkeypatch.delenv("RECEIPTLENS_GOOGLE_CLIENT_SECRET")
        resp = client.get("/api/auth/google/status")
        assert resp.status_code == 200
        assert resp.json() == {"enabled": False}


# ---------------------------------------------------------------------------
# 2. GET /api/auth/google/start
# ---------------------------------------------------------------------------


class TestGoogleStart:
    def test_start_redirects_to_google(self) -> None:
        resp = client.get("/api/auth/google/start", follow_redirects=False)
        assert resp.status_code == 307
        location = resp.headers["location"]
        assert location.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
        assert "client_id=" in location
        assert "response_type=code" in location
        assert "scope=openid+email+profile" in location
        assert "state=" in location

    def test_start_sets_csrf_cookie(self) -> None:
        resp = client.get("/api/auth/google/start", follow_redirects=False)
        cookies = resp.headers.get_list("set-cookie")
        oauth_cookie = [c for c in cookies if "receiptlens.oauth" in c]
        assert len(oauth_cookie) == 1
        assert "HttpOnly" in oauth_cookie[0]
        assert "Secure" in oauth_cookie[0]
        assert "SameSite=lax" in oauth_cookie[0]

    def test_start_503_without_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("RECEIPTLENS_GOOGLE_CLIENT_ID")
        monkeypatch.delenv("RECEIPTLENS_GOOGLE_CLIENT_SECRET")
        resp = client.get("/api/auth/google/start")
        assert resp.status_code == 503

    def test_start_state_in_url_matches_cookie(self) -> None:
        resp = client.get("/api/auth/google/start", follow_redirects=False)
        location = resp.headers["location"]
        from urllib.parse import parse_qs, urlparse
        qs = parse_qs(urlparse(location).query)
        state = qs["state"][0]
        cookies = resp.headers.get_list("set-cookie")
        oauth_cookie = [c for c in cookies if "receiptlens.oauth" in c][0]
        cookie_val = oauth_cookie.split(";")[0].split("=", 1)[1]
        assert cookie_val == state


# ---------------------------------------------------------------------------
# 3. GET /api/auth/google/callback
# ---------------------------------------------------------------------------


class TestGoogleCallback:
    def test_callback_success(self) -> None:
        """Full happy-path: start → callback → session created."""
        # Step 1: start (get cookie + state)
        start_resp = client.get("/api/auth/google/start", follow_redirects=False)
        location = start_resp.headers["location"]
        from urllib.parse import parse_qs, urlparse
        state = parse_qs(urlparse(location).query)["state"][0]

        cookies = start_resp.headers.get_list("set-cookie")
        cookie_state = [c for c in cookies if "receiptlens.oauth" in c][0].split(";")[0].split("=", 1)[1]
        assert cookie_state == state

        # Step 2: callback with a valid code
        nonce = _oauth_hmac(state)
        id_token = make_id_token(nonce=nonce)
        transport = google_transport(id_token)

        with patch("app.auth_api.exchange_google_code", side_effect=_make_sync_exchange(transport)):
            client.cookies.set("receiptlens.oauth", cookie_state, path="/")
            try:
                cb_resp = client.get(
                    f"/api/auth/google/callback?code=test-code&state={state}",
                    follow_redirects=False,
                )
            finally:
                client.cookies.clear()

        assert cb_resp.status_code == 302
        cb_location = cb_resp.headers["location"]
        assert "#session_token=" in cb_location
        assert "expires_at=" in cb_location

        # Extract session token from fragment
        fragment = cb_location.split("#", 1)[1]
        params = parse_qs(fragment)
        session_token = params["session_token"][0]

        # Verify the session works
        me_resp = client.post(
            "/auth/session/me", json={"session_token": session_token}
        )
        assert me_resp.status_code == 200
        identity = me_resp.json()
        assert identity["email"] == "user@example.com"
        assert identity["role"] == "owner"
        assert identity["tenant_id"].startswith("hh-")

    def test_callback_rejects_missing_state(self) -> None:
        resp = client.get(
            "/api/auth/google/callback?code=abc",
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "oauth_missing_params" in resp.headers["location"]

    def test_callback_rejects_invalid_state(self) -> None:
        client.cookies.set("receiptlens.oauth", "cookie-state-value", path="/")
        try:
            resp = client.get(
                "/api/auth/google/callback?code=abc&state=bogus-state",
                follow_redirects=False,
            )
        finally:
            client.cookies.clear()
        assert resp.status_code == 302
        assert "oauth_invalid_state" in resp.headers["location"]

    def test_callback_rejects_missing_cookie(self) -> None:
        resp = client.get(
            "/api/auth/google/callback?code=abc&state=any-state",
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "oauth_invalid_state" in resp.headers["location"]

    def test_callback_rejects_error_param(self) -> None:
        resp = client.get(
            "/api/auth/google/callback?error=access_denied",
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "oauth_cancelled" in resp.headers["location"]

    def test_callback_oidc_exchange_failure(self) -> None:
        start_resp = client.get("/api/auth/google/start", follow_redirects=False)
        location = start_resp.headers["location"]
        from urllib.parse import parse_qs, urlparse
        state = parse_qs(urlparse(location).query)["state"][0]
        cookies = start_resp.headers.get_list("set-cookie")
        cookie_state = [c for c in cookies if "receiptlens.oauth" in c][0].split(";")[0].split("=", 1)[1]

        from app.google_oidc import OIDCError

        def _bad_exchange(*a: Any, **kw: Any) -> dict[str, Any]:
            raise OIDCError("token exchange failed")

        with patch("app.auth_api.exchange_google_code", side_effect=_bad_exchange):
            client.cookies.set("receiptlens.oauth", cookie_state, path="/")
            try:
                cb_resp = client.get(
                    f"/api/auth/google/callback?code=bad-code&state={state}",
                    follow_redirects=False,
                )
            finally:
                client.cookies.clear()
        assert cb_resp.status_code == 302
        assert "oauth_exchange_failed" in cb_resp.headers["location"]


# ---------------------------------------------------------------------------
# 4. POST /api/auth/session/logout
# ---------------------------------------------------------------------------


class TestSessionLogout:
    def test_logout_deletes_session(self) -> None:
        requested = client.post(
            "/auth/magic-link-request", json={"email": "logout-test@example.com"}
        ).json()
        verified = client.post(
            "/auth/magic-link-verify", json={"token": requested["token"]}
        ).json()
        token = verified["session_token"]

        me = client.post("/auth/session/me", json={"session_token": token})
        assert me.status_code == 200

        resp = client.post(
            "/auth/session/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

        me2 = client.post("/auth/session/me", json={"session_token": token})
        assert me2.status_code == 401

    def test_logout_requires_bearer(self) -> None:
        resp = client.post("/auth/session/logout")
        assert resp.status_code == 401

    def test_logout_with_bogus_token(self) -> None:
        resp = client.post(
            "/auth/session/logout",
            headers={"Authorization": "Bearer bogus-token-123"},
        )
        assert resp.status_code == 204
