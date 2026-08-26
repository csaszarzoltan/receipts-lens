"""G1 — Google OIDC service unit tests (docs/plans/google-sso-2026-08-26.md).

Contract under test (``app/google_oidc.py``):

  * ``exchange_google_code(code, expected_nonce)`` exchanges an authorization
    code at the Google token endpoint, fetches the JWKS signing keys and
    verifies the returned ``id_token`` (RS256 signature, iss, aud, exp,
    nonce, email_verified, sub/email presence).
  * Any failure raises ``OIDCError``; success returns the raw claims dict.
  * Missing client configuration raises ``OIDCError`` ("not configured").

The tests are fully offline: HTTP traffic runs through ``httpx.MockTransport``
and the ID tokens are signed with a throwaway RSA key whose public half is
served as the JWKS — exactly what Google would return.
"""
from __future__ import annotations

import asyncio
import base64
import json
import time
from typing import Any

import httpx
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from app.google_oidc import OIDCError, exchange_google_code, is_configured

CLIENT_ID = "test-client-id.apps.googleusercontent.com"
CLIENT_SECRET = "test-client-secret"
REDIRECT_URI = "https://receipts.allthezoo.com/api/auth/google/callback"
KID = "test-key-1"

ENV = {
    "RECEIPTLENS_GOOGLE_CLIENT_ID": CLIENT_ID,
    "RECEIPTLENS_GOOGLE_CLIENT_SECRET": CLIENT_SECRET,
}

# ---------------------------------------------------------------------------
# Offline crypto helpers — a throwaway Google lookalike
# ---------------------------------------------------------------------------


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_public_numbers = _private_key.public_key().public_numbers()
JWKS = {
    "keys": [
        {
            "kty": "RSA",
            "alg": "RS256",
            "use": "sig",
            "kid": KID,
            "n": _b64url(_public_numbers.n.to_bytes((_public_numbers.n.bit_length() + 7) // 8, "big")),
            "e": _b64url(_public_numbers.e.to_bytes(3, "big")),
        }
    ]
}


def make_id_token(**overrides: Any) -> str:
    """Sign a Google-shaped ID token with the test key."""
    now = int(time.time())
    claims = {
        "iss": "https://accounts.google.com",
        "azp": CLIENT_ID,
        "aud": CLIENT_ID,
        "sub": "google-user-1",
        "email": "user@example.com",
        "email_verified": True,
        "exp": now + 300,
        "iat": now,
        "nonce": "nonce-123",
    }
    claims.update(overrides)
    header = {"alg": "RS256", "kid": KID, "typ": "JWT"}
    signing_input = (
        _b64url(json.dumps(header, separators=(",", ":")).encode())
        + "."
        + _b64url(json.dumps(claims, separators=(",", ":")).encode())
    )
    signature = _private_key.sign(
        signing_input.encode(), padding.PKCS1v15(), hashes.SHA256()
    )
    return signing_input + "." + _b64url(signature)


# ---------------------------------------------------------------------------
# MockTransport plumbing — the fake Google endpoints
# ---------------------------------------------------------------------------


def google_transport(id_token: str | None, *, token_status: int = 200, jwks_status: int = 200):
    """Build an httpx.MockTransport standing in for accounts.google.com."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "oauth2.googleapis.com" and request.url.path == "/token":
            if token_status != 200:
                return httpx.Response(token_status, text={"error": "bad_grant"}.get("", "") or "invalid_grant")
            body = {
                "access_token": "ya29.test",
                "token_type": "Bearer",
                "id_token": id_token,
            }
            return httpx.Response(200, json=body)
        if request.url.path.endswith("/certs"):
            if jwks_status != 200:
                return httpx.Response(jwks_status, text="jwks down")
            return httpx.Response(200, json=JWKS)
        return httpx.Response(404, text=f"unexpected upstream call: {request.url}")

    return httpx.MockTransport(handler)


def exchange(code: str, nonce: str, **kw: Any) -> dict[str, Any]:
    async def _run() -> dict[str, Any]:
        return await exchange_google_code(
            code,
            nonce,
            http_client=httpx.AsyncClient(
                transport=kw.pop("transport"),
                follow_redirects=False,
            ),
            **kw,
        )

    return asyncio.run(_run())


@pytest.fixture(autouse=True)
def _google_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    yield
    # monkeypatch reverts automatically


# ---------------------------------------------------------------------------
# RED→GREEN behavioural suite
# ---------------------------------------------------------------------------


class TestGoogleOidcConfig:
    def test_is_configured_true_when_env_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        assert is_configured() is True

    def test_is_configured_false_without_secret(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("RECEIPTLENS_GOOGLE_CLIENT_SECRET")
        assert is_configured() is False

    def test_exchange_without_configuration_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("RECEIPTLENS_GOOGLE_CLIENT_ID")
        monkeypatch.delenv("RECEIPTLENS_GOOGLE_CLIENT_SECRET")
        with pytest.raises(OIDCError, match="not configured"):
            exchange("code", "nonce", transport=google_transport(make_id_token()))


class TestTokenExchange:
    def test_sends_authorization_code_grant(self) -> None:
        captured: dict[str, Any] = {}

        def spy(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/token":
                captured.update(
                    {
                        k: v[0]
                        for k, v in __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(
                            request.content.decode()
                        ).items()
                    }
                )
                return httpx.Response(
                    200, json={"id_token": make_id_token(nonce="nonce-123"), "access_token": "t"}
                )
            return httpx.Response(200, json=JWKS)

        exchange("abc-123", "nonce-123", transport=httpx.MockTransport(spy))
        assert captured["grant_type"] == "authorization_code"
        assert captured["code"] == "abc-123"
        assert captured["client_id"] == CLIENT_ID
        assert captured["client_secret"] == CLIENT_SECRET
        assert captured["redirect_uri"] == REDIRECT_URI

    def test_token_endpoint_error_raises(self) -> None:
        with pytest.raises(OIDCError, match="exchange failed"):
            exchange("code", "nonce", transport=google_transport(None, token_status=400))

    def test_missing_id_token_in_response_raises(self) -> None:
        with pytest.raises(OIDCError, match="ID token"):
            exchange("code", "nonce", transport=google_transport(None))

    def test_jwks_unavailable_raises(self) -> None:
        token = make_id_token()
        with pytest.raises(OIDCError, match="signing keys"):
            exchange("code", "nonce", transport=google_transport(token, jwks_status=500))


class TestIdTokenVerification:
    """Claim-level rejections — each malformed claim must raise OIDCError."""

    def test_valid_claims_returned(self) -> None:
        claims = exchange("code", "nonce-123", transport=google_transport(make_id_token()))
        assert claims["sub"] == "google-user-1"
        assert claims["email"] == "user@example.com"
        assert claims["email_verified"] is True
        assert claims["nonce"] == "nonce-123"

    def test_bad_issuer_rejected(self) -> None:
        token = make_id_token(iss="https://evil.example.com")
        with pytest.raises(OIDCError, match="issuer"):
            exchange("code", "nonce-123", transport=google_transport(token))

    def test_bad_audience_rejected(self) -> None:
        token = make_id_token(aud="attacker-client-id.apps.googleusercontent.com")
        with pytest.raises(OIDCError, match="audience"):
            exchange("code", "nonce-123", transport=google_transport(token))

    def test_expired_token_rejected(self) -> None:
        token = make_id_token(exp=int(time.time()) - 60)
        with pytest.raises(OIDCError, match="expired"):
            exchange("code", "nonce-123", transport=google_transport(token))

    def test_wrong_nonce_rejected(self) -> None:
        token = make_id_token(nonce="attacker-nonce")
        with pytest.raises(OIDCError, match="[Nn]once"):
            exchange("code", "nonce-123", transport=google_transport(token))

    @pytest.mark.parametrize("email_verified", [False, None])
    def test_unverified_email_rejected(self, email_verified: Any) -> None:
        token = make_id_token(email_verified=email_verified)
        with pytest.raises(OIDCError, match="not verified"):
            exchange("code", "nonce-123", transport=google_transport(token))

    def test_missing_email_rejected(self) -> None:
        token = make_id_token(email=None)
        with pytest.raises(OIDCError, match="incomplete"):
            exchange("code", "nonce-123", transport=google_transport(token))

    def test_tampered_signature_rejected(self) -> None:
        good = make_id_token()
        head, payload, _sig = good.split(".")
        forged_payload = _b64url(
            json.dumps({"iss": "https://accounts.google.com", "sub": "victim"}).encode()
        )
        with pytest.raises(OIDCError):
            exchange("code", "nonce", transport=google_transport(f"{head}.{forged_payload}.{_sig}"))

    def test_signed_by_other_key_rejected(self) -> None:
        other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        now = int(time.time())
        claims = {
            "iss": "https://accounts.google.com", "aud": CLIENT_ID, "sub": "x",
            "email": "x@example.com", "email_verified": True,
            "exp": now + 300, "iat": now, "nonce": "nonce-123",
        }
        signing_input = (
            _b64url(b'{"alg":"RS256","kid":"' + KID.encode() + b'","typ":"JWT"}')
            + "."
            + _b64url(json.dumps(claims).encode())
        )
        sig = other.sign(signing_input.encode(), padding.PKCS1v15(), hashes.SHA256())
        with pytest.raises(OIDCError, match="signature|Invalid"):
            exchange("code", "nonce-123", transport=google_transport(signing_input + "." + _b64url(sig)))

    def test_unknown_kid_rejected(self) -> None:
        good = make_id_token()
        head, payload, sig = good.split(".")
        forged_head = _b64url(json.dumps({"alg": "RS256", "kid": "unknown-kid"}).encode())
        with pytest.raises(OIDCError, match="signing key"):
            exchange("code", "nonce", transport=google_transport(f"{forged_head}.{payload}.{sig}"))
