"""G2 — Google SSO backend route + sliding session + logout tests."""
from __future__ import annotations

import os
import re
import sqlite3
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from fastapi.testclient import TestClient

from app.auth_api import router as auth_router
from app.product_service import ProductService


@pytest.fixture()
def tmp_service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ProductService:
    db = tmp_path / "g2.db"
    svc = ProductService(database=db)
    # Point the global service used by auth_api to this fixture
    import app.product_api as pa

    monkeypatch.setattr(pa, "service", svc)
    import app.auth_api as aa

    monkeypatch.setattr(aa, "service", svc)
    return svc


@pytest.fixture()
def client(tmp_service: ProductService) -> TestClient:
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(auth_router)
    return TestClient(app, raise_server_exceptions=False)


class TestGoogleStatus:
    def test_disabled_when_no_env(self, client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("RECEIPTLENS_GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("RECEIPTLENS_GOOGLE_CLIENT_SECRET", raising=False)
        resp = client.get("/auth/google/status")
        assert resp.status_code == 200
        assert resp.json() == {"enabled": False}

    def test_enabled_when_configured(self, client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("RECEIPTLENS_GOOGLE_CLIENT_ID", "cid.apps.googleusercontent.com")
        monkeypatch.setenv("RECEIPTLENS_GOOGLE_CLIENT_SECRET", "secret")
        resp = client.get("/auth/google/status")
        assert resp.json() == {"enabled": True}


class TestGoogleStart:
    def test_returns_503_when_not_configured(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("RECEIPTLENS_GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("RECEIPTLENS_GOOGLE_CLIENT_SECRET", raising=False)
        resp = client.get("/auth/google/start", follow_redirects=False)
        assert resp.status_code == 503

    def test_redirects_to_google_with_state_and_cookie(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("RECEIPTLENS_GOOGLE_CLIENT_ID", "cid.apps.googleusercontent.com")
        monkeypatch.setenv("RECEIPTLENS_GOOGLE_CLIENT_SECRET", "secret")
        monkeypatch.setenv("RECEIPTLENS_CREDENTIAL_KEY", "test-cred-key-1234567890abcdef")
        monkeypatch.setenv("RECEIPTLENS_GOOGLE_REDIRECT_URI", "https://receipts.allthezoo.com/api/auth/google/callback")
        resp = client.get("/auth/google/start?return_to=/dashboard", follow_redirects=False)
        assert resp.status_code == 307
        loc = resp.headers["location"]
        assert "accounts.google.com" in loc
        assert "client_id=cid.apps.googleusercontent.com" in loc
        assert "response_type=code" in loc
        # oauth cookie present
        assert "receiptlens.oauth" in resp.headers.get("set-cookie", "")

    def test_return_to_open_redirect_sanitized(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("RECEIPTLENS_GOOGLE_CLIENT_ID", "cid.apps.googleusercontent.com")
        monkeypatch.setenv("RECEIPTLENS_GOOGLE_CLIENT_SECRET", "secret")
        monkeypatch.setenv("RECEIPTLENS_CREDENTIAL_KEY", "test-cred-key-1234567890abcdef")
        resp = client.get("/auth/google/start?return_to=https://evil.com", follow_redirects=False)
        assert resp.status_code == 307
        # decode state return_to
        loc = resp.headers["location"]
        import base64, hashlib, hmac, json

        qs = parse_qs(urlparse(loc).query)
        state = qs["state"][0]
        raw_b64, _sig = state.rsplit(".", 1)
        raw = base64.urlsafe_b64decode(raw_b64 + "=" * (-len(raw_b64) % 4)).decode()
        payload = json.loads(raw)
        assert payload["return_to"] == "/dashboard"


class TestGoogleCallback:
    def test_missing_code_or_state_redirects_with_error(self, client: TestClient) -> None:
        resp = client.get("/auth/google/callback", follow_redirects=False)
        assert resp.status_code == 303
        assert "oauth_state_invalid" in resp.headers["location"]

    def test_error_param_redirects(self, client: TestClient) -> None:
        resp = client.get("/auth/google/callback?error=access_denied&state=x", follow_redirects=False)
        assert resp.status_code == 303
        assert "access_denied" in resp.headers["location"]

    def test_full_flow_creates_session_and_redirects_to_frontend(
        self, client: TestClient, tmp_service: ProductService, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("RECEIPTLENS_GOOGLE_CLIENT_ID", "cid.apps.googleusercontent.com")
        monkeypatch.setenv("RECEIPTLENS_GOOGLE_CLIENT_SECRET", "secret")
        monkeypatch.setenv("RECEIPTLENS_CREDENTIAL_KEY", "test-cred-key-1234567890abcdef")
        monkeypatch.setenv("RECEIPTLENS_AUTH_BASE_URL", "https://receipts.allthezoo.com")
        import app.auth_api as aa

        monkeypatch.setattr(aa, "AUTH_BASE_URL", "https://receipts.allthezoo.com")
        # Build a valid state via /start, then mock exchange_google_code
        start_resp = client.get("/auth/google/start", follow_redirects=False)
        assert start_resp.status_code == 307
        loc = start_resp.headers["location"]
        qs = parse_qs(urlparse(loc).query)
        state = qs["state"][0]
        nonce = qs["nonce"][0]

        import app.auth_api as aa

        async def fake_exchange(code: str, expected_nonce: str, *, http_client=None):  # type: ignore[no-untyped-def]
            assert expected_nonce == nonce
            assert code == "auth-code-123"
            return {"email": "GoogleUser@Example.COM", "sub": "google-1", "email_verified": True, "aud": "cid.apps.googleusercontent.com"}

        monkeypatch.setattr(aa, "exchange_google_code", fake_exchange)

        resp = client.get(f"/auth/google/callback?code=auth-code-123&state={state}", follow_redirects=False)
        assert resp.status_code == 303
        loc2 = resp.headers["location"]
        assert "receipts.allthezoo.com/auth/google/callback#" in loc2
        assert "session_token=" in loc2
        # Extract and verify session
        frag = loc2.split("#", 1)[1]
        frag_qs = parse_qs(frag)
        token = frag_qs["session_token"][0]
        identity = tmp_service.resolve_session(token)
        assert identity["email"] == "googleuser@example.com"
        assert identity["tenant_id"] == "hh-googleuser-example-com"


class TestLogout:
    def test_logout_without_bearer_401(self, client: TestClient) -> None:
        resp = client.post("/auth/session/logout")
        assert resp.status_code == 401

    def test_logout_invalidates_session(self, client: TestClient, tmp_service: ProductService) -> None:
        sess = tmp_service.create_session("user@example.com", "hh-user", "owner")
        token = sess["session_token"]
        resp = client.post("/auth/session/logout", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204
        # Subsequent resolve is 401
        me = client.post("/auth/session/me", json={"session_token": token})
        assert me.status_code == 401

    def test_logout_idempotent(self, client: TestClient, tmp_service: ProductService) -> None:
        sess = tmp_service.create_session("user@example.com", "hh-user", "owner")
        token = sess["session_token"]
        client.post("/auth/session/logout", headers={"Authorization": f"Bearer {token}"})
        resp2 = client.post("/auth/session/logout", headers={"Authorization": f"Bearer {token}"})
        assert resp2.status_code == 204


class TestSlidingSession:
    def test_resolve_refreshes_expiry(self, client: TestClient, tmp_service: ProductService) -> None:
        import time

        sess = tmp_service.create_session("user@example.com", "hh-user", "owner")
        token = sess["session_token"]
        orig = tmp_service._db.execute(
            "SELECT expires_at FROM sessions WHERE session_token=?", (token,)
        ).fetchone()["expires_at"]
        # Simulate time passing
        time.sleep(0.01)
        tmp_service.resolve_session(token)
        refreshed = tmp_service._db.execute(
            "SELECT expires_at FROM sessions WHERE session_token=?", (token,)
        ).fetchone()["expires_at"]
        assert refreshed >= orig
