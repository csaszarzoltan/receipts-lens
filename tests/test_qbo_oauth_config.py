"""Config-driven QBO OAuth URL construction (P1 fix, 2026-08-11)."""
import hashlib
import os

import httpx
import pytest

from app.connection_service import ConnectionService
from app.credential_store import CredentialStore
from app.intuit_oauth import IntuitOAuthClient
from app.product_service import ProductService


def _make_service():
    import tempfile
    tmp = tempfile.mkdtemp()
    return ProductService(os.path.join(tmp, "db.sqlite"))


def test_start_oauth_uses_env_client_id():
    os.environ["RECEIPTLENS_QBO_CLIENT_ID"] = "intuit-app-123"
    try:
        cs = ConnectionService(_make_service(), CredentialStore(b"k" * 32))
        started = cs.start_oauth(type("A", (), {"role": "admin", "tenant_id": "t1"})(), "/integrations")
        assert "client_id=intuit-app-123" in started["authorization_url"]
        assert "client_id=configured" not in started["authorization_url"]
    finally:
        os.environ.pop("RECEIPTLENS_QBO_CLIENT_ID", None)


def test_start_oauth_falls_back_to_placeholder_without_env():
    os.environ.pop("RECEIPTLENS_QBO_CLIENT_ID", None)
    cs = ConnectionService(_make_service(), CredentialStore(b"k" * 32))
    started = cs.start_oauth(type("A", (), {"role": "admin", "tenant_id": "t1"})(), "/integrations")
    assert "client_id=configured" in started["authorization_url"]


def test_start_oauth_uses_redirect_uri_override():
    cs = ConnectionService(_make_service(), CredentialStore(b"k" * 32),
                           redirect_uri="https://app.example.com/cb")
    started = cs.start_oauth(type("A", (), {"role": "admin", "tenant_id": "t1"})(), "/integrations")
    assert "redirect_uri=https%3A%2F%2Fapp.example.com%2Fcb" in started["authorization_url"]


def test_oauth_exchange_requires_pkce_verifier():
    """A live exchange without the stored verifier must be rejected."""
    from app.intuit_oauth import OAuthConfigError

    seen = {}

    class _Transport(httpx.BaseTransport):
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            seen["body"] = request.content.decode()
            return httpx.Response(400, json={"error": "invalid_request"}, request=request)

    cs = ConnectionService(
        _make_service(), CredentialStore(b"k" * 32),
        oauth=IntuitOAuthClient(
            client_id="intuit-app-123", client_secret="secret-value",
            redirect_uri="/product/connections/quickbooks/oauth/callback",
            client=httpx.Client(transport=_Transport()),
        ),
    )
    actor = type("A", (), {"role": "admin", "tenant_id": "t1"})()
    started = cs.start_oauth(actor, "/integrations")
    # The challenge must be derived from the stored verifier (RFC 7636 S256).
    verifier = cs.db.execute(
        "SELECT code_verifier FROM oauth_states WHERE state_hash=?",
        (hashlib.sha256(started["state"].encode()).hexdigest(),),
    ).fetchone()[0]
    challenge = cs._pkce_challenge(verifier)
    assert challenge == started["authorization_url"].split("code_challenge=")[1].split("&")[0]
    # The live exchange sends the verifier to Intuit's fixed token endpoint.
    with pytest.raises(OAuthConfigError):
        cs.complete_live_oauth(started["state"], "code", "realm-1")
    assert "grant_type=authorization_code" in seen["body"]
    assert f"code_verifier={verifier}" in seen["body"]
