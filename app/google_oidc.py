"""Google OpenID Connect — authorization-code flow, offline-tesztelhető.

A MealMind `app/services/google_oidc.py` mintájára, de `jose` helyett
`cryptography`-val (a receipts-lens-ben nincs jose, van cryptography 50 + httpx).
Lásd: docs/plans/google-sso-2026-08-26.md (G1).
"""
from __future__ import annotations

import base64
import json
import os
import time
from typing import Any

import httpx
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
DEFAULT_REDIRECT_URI = "https://receipts.allthezoo.com/api/auth/google/callback"


class OIDCError(Exception):
    """Provider response or ID-token validation failed."""


def _config() -> dict[str, str] | None:
    client_id = os.getenv("RECEIPTLENS_GOOGLE_CLIENT_ID", "").strip()
    secret = os.getenv("RECEIPTLENS_GOOGLE_CLIENT_SECRET", "").strip()
    if not client_id or not secret:
        return None
    redirect_uri = os.getenv("RECEIPTLENS_GOOGLE_REDIRECT_URI", DEFAULT_REDIRECT_URI).strip() or DEFAULT_REDIRECT_URI
    return {
        "client_id": client_id,
        "client_secret": secret,
        "redirect_uri": redirect_uri,
        "token_url": GOOGLE_TOKEN_URL,
        "jwks_url": GOOGLE_JWKS_URL,
    }


def is_configured() -> bool:
    return _config() is not None


def _b64url_decode(s: str) -> bytes:
    # urlsafe without padding
    s = s.strip()
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _jwk_to_public_key(jwk: dict[str, Any]):
    n = int.from_bytes(_b64url_decode(jwk["n"]), "big")
    e = int.from_bytes(_b64url_decode(jwk["e"]), "big")
    numbers = RSAPublicNumbers(e, n)
    return numbers.public_key()


async def exchange_google_code(
    code: str,
    expected_nonce: str,
    *,
    http_client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Exchange an authorization code and return verified ID-token claims.

    Raises OIDCError on any failure (not configured, token/JWKS fetch failed,
    missing id_token, bad signature, bad claims). Success returns the raw
    claims dict.
    """
    cfg = _config()
    if cfg is None:
        raise OIDCError("Google sign-in is not configured")

    close_client = False
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=10.0, follow_redirects=False)
        close_client = True

    try:
        token_response = await http_client.post(
            cfg["token_url"],
            data={
                "code": code,
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "redirect_uri": cfg["redirect_uri"],
                "grant_type": "authorization_code",
            },
        )
        if token_response.status_code != 200:
            raise OIDCError(f"Google code exchange failed: {token_response.status_code} {token_response.text[:200]}")
        data = token_response.json()
        id_token = data.get("id_token")
        if not isinstance(id_token, str) or not id_token:
            raise OIDCError("Google did not return an ID token")

        jwks_response = await http_client.get(cfg["jwks_url"])
        if jwks_response.status_code != 200:
            raise OIDCError("Google signing keys unavailable")
        jwks = jwks_response.json()
    finally:
        if close_client:
            await http_client.aclose()

    # --- verify JWT ---
    try:
        header_b64, payload_b64, sig_b64 = id_token.split(".")
    except ValueError as exc:
        raise OIDCError("Invalid Google ID token") from exc

    try:
        header = json.loads(_b64url_decode(header_b64).decode("utf-8"))
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception as exc:
        raise OIDCError("Invalid Google ID token") from exc

    kid = header.get("kid")
    if not isinstance(kid, str) or not kid:
        raise OIDCError("Invalid Google ID token: missing kid")

    # find matching JWK
    keys = jwks.get("keys") if isinstance(jwks, dict) else None
    if not isinstance(keys, list):
        raise OIDCError("Google signing keys unavailable")
    jwk = next((k for k in keys if k.get("kid") == kid), None)
    if jwk is None:
        raise OIDCError("Google signing key not found")

    # verify RS256 signature
    try:
        public_key = _jwk_to_public_key(jwk)
        signature = _b64url_decode(sig_b64)
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        public_key.verify(signature, signing_input, padding.PKCS1v15(), hashes.SHA256())
    except InvalidSignature as exc:
        raise OIDCError("Invalid Google ID token signature") from exc
    except Exception as exc:
        # any other crypto failure -> treat as invalid signature
        if isinstance(exc, OIDCError):
            raise
        raise OIDCError("Invalid Google ID token signature") from exc

    # --- claim checks ---
    iss = payload.get("iss")
    if iss not in {"https://accounts.google.com", "accounts.google.com"}:
        raise OIDCError("Invalid Google issuer")

    aud = payload.get("aud")
    if aud != cfg["client_id"]:
        raise OIDCError("Invalid Google audience")

    # exp is seconds since epoch
    exp = payload.get("exp")
    try:
        exp_int = int(exp)  # type: ignore[arg-type]
    except Exception:
        raise OIDCError("Invalid Google ID token: bad exp")
    if exp_int <= int(time.time()):
        raise OIDCError("Google ID token expired")

    nonce = payload.get("nonce")
    if nonce != expected_nonce:
        raise OIDCError("Invalid Google nonce")

    if payload.get("email_verified") is not True:
        raise OIDCError("Google email is not verified")

    if not payload.get("sub") or not payload.get("email"):
        raise OIDCError("Google identity is incomplete")

    return payload
