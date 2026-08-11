"""Config-driven QBO OAuth URL construction (P1 fix, 2026-08-11)."""
import os
from app.connection_service import ConnectionService
from app.credential_store import CredentialStore
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
