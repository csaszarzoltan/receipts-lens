"""G2 — Sliding session TTL tests (docs/plans/google-sso-2026-08-26.md §D3).

Contract under test (``app/product_service.py``):

  * ``resolve_session(token)`` returns identity AND extends ``expires_at``
    to ``now + SESSION_TTL_SECONDS`` on every authenticated call.
  * ``SESSION_TTL_SECONDS`` is 180 days (not the old 30 days).
  * ``create_session()`` uses the new 180-day TTL.
  * ``delete_session(token)`` removes the row and returns True/False.
  * ``find_or_create_household_owner(email)`` creates owner membership once.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import api
from app.product_api import service
from app.product_service import SESSION_TTL_SECONDS, Actor, ProductService


client = TestClient(api.app)


class TestSessionTTLConstant:
    def test_session_ttl_is_180_days(self) -> None:
        assert SESSION_TTL_SECONDS == 180 * 24 * 60 * 60


class TestCreateSessionTTL:
    def test_create_session_uses_180_day_ttl(self) -> None:
        session = service.create_session("ttl-test@example.com", "hh-ttl", "owner")
        expires = datetime.fromisoformat(session["expires_at"])
        now = datetime.now(UTC)
        delta = expires - now
        assert delta.days >= 179
        assert delta.days <= 181


class TestSlidingExpiry:
    def test_resolve_session_extends_expiry(self) -> None:
        session = service.create_session("slide@example.com", "hh-slide", "owner")
        token = session["session_token"]

        identity = service.resolve_session(token)
        assert identity["email"] == "slide@example.com"

        row = service._db.execute(
            "SELECT expires_at FROM sessions WHERE session_token=?", (token,)
        ).fetchone()
        new_expires = datetime.fromisoformat(row["expires_at"])
        now = datetime.now(UTC)

        delta = new_expires - now
        assert delta.days >= 179
        assert delta.days <= 181

    def test_resolve_session_does_not_change_identity(self) -> None:
        session = service.create_session("id@example.com", "hh-id", "adult")
        token = session["session_token"]

        first = service.resolve_session(token)
        second = service.resolve_session(token)

        assert first["email"] == second["email"]
        assert first["tenant_id"] == second["tenant_id"]
        assert first["role"] == second["role"]

    def test_expired_session_rejected_even_after_ttl_update(self) -> None:
        session = service.create_session(
            "expired@example.com", "hh-exp", "owner", ttl_seconds=-1
        )
        token = session["session_token"]

        with pytest.raises(KeyError, match="expired"):
            service.resolve_session(token)

    def test_nonexistent_session_rejected(self) -> None:
        with pytest.raises(KeyError, match="unknown session"):
            service.resolve_session("totally-fake-token-xyz")


class TestDeleteSession:
    def test_delete_existing_session(self) -> None:
        session = service.create_session("del@example.com", "hh-del", "owner")
        token = session["session_token"]

        assert service.resolve_session(token)["email"] == "del@example.com"

        result = service.delete_session(token)
        assert result is True

        with pytest.raises(KeyError):
            service.resolve_session(token)

    def test_delete_nonexistent_returns_false(self) -> None:
        result = service.delete_session("no-such-token")
        assert result is False


class TestFindOrCreateHouseholdOwner:
    def test_creates_new_household(self) -> None:
        tenant_id, created = service.find_or_create_household_owner("newuser@example.com")
        assert created is True
        assert tenant_id == "hh-newuser-example-com"

        row = service._db.execute(
            "SELECT role FROM members WHERE tenant_id=? AND email=?",
            (tenant_id, "newuser@example.com"),
        ).fetchone()
        assert row is not None
        assert row["role"] == "owner"

    def test_finds_existing_household(self) -> None:
        tenant_id1, created1 = service.find_or_create_household_owner("existing@example.com")
        assert created1 is True

        tenant_id2, created2 = service.find_or_create_household_owner("existing@example.com")
        assert created2 is False
        assert tenant_id1 == tenant_id2

    def test_household_id_is_deterministic(self) -> None:
        tid_a, _ = service.find_or_create_household_owner("user.name@domain.com")
        tid_b, _ = service.find_or_create_household_owner("user.name@domain.com")
        assert tid_a == tid_b == "hh-user-name-domain-com"


# ---------------------------------------------------------------------------
# Integration: Google callback creates session with sliding TTL
# ---------------------------------------------------------------------------


class TestGoogleCallbackSliding:
    """Verify the full flow: Google callback → session → resolve extends TTL."""

    @pytest.fixture(autouse=True)
    def _google_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("RECEIPTLENS_GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
        monkeypatch.setenv("RECEIPTLENS_GOOGLE_CLIENT_SECRET", "test-secret")
        monkeypatch.setenv(
            "RECEIPTLENS_GOOGLE_REDIRECT_URI",
            "https://receipts.allthezoo.com/api/auth/google/callback",
        )

    def test_callback_session_is_sliding(self) -> None:
        from app.auth_api import _oauth_hmac
        from tests.test_google_oidc import make_id_token, google_transport
        from urllib.parse import parse_qs, urlparse

        # Start
        start = client.get("/auth/google/start", follow_redirects=False)
        state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
        cookies = start.headers.get_list("set-cookie")
        cookie_state = [c for c in cookies if "receiptlens.oauth" in c][0].split(";")[0].split("=", 1)[1]

        nonce = _oauth_hmac(state)
        id_token = make_id_token(nonce=nonce, email="slide-cb@example.com")
        transport = google_transport(id_token)

        # Use thread-based sync exchange mock (same as test_google_auth_routes)
        import concurrent.futures, asyncio, httpx

        def _sync_exchange(code, expected_nonce, **kw):
            from app.google_oidc import exchange_google_code
            with concurrent.futures.ThreadPoolExecutor(1) as pool:
                return pool.submit(asyncio.run, exchange_google_code(
                    code, expected_nonce,
                    http_client=httpx.AsyncClient(transport=transport, follow_redirects=False),
                )).result(timeout=10)

        with patch("app.auth_api.exchange_google_code", side_effect=_sync_exchange):
            client.cookies.set("receiptlens.oauth", cookie_state, path="/")
            try:
                cb = client.get(
                    f"/auth/google/callback?code=valid&state={state}",
                    follow_redirects=False,
                )
            finally:
                client.cookies.clear()

        assert cb.status_code == 302
        fragment = cb.headers["location"].split("#", 1)[1]
        params = parse_qs(fragment)
        token = params["session_token"][0]

        # First resolve — extends TTL
        identity = service.resolve_session(token)
        assert identity["email"] == "slide-cb@example.com"

        # Check the DB expiry is ~180 days from now
        row = service._db.execute(
            "SELECT expires_at FROM sessions WHERE session_token=?", (token,)
        ).fetchone()
        exp = datetime.fromisoformat(row["expires_at"])
        assert (exp - datetime.now(UTC)).days >= 179
