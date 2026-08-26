"""Google OIDC — authorization-code flow with cryptography RS256 verification.

Validates a Google ``id_token`` obtained via the authorization-code exchange:

  * token endpoint: ``https://oauth2.googleapis.com/token``
  * signing keys (JWKS): ``https://www.googleapis.com/oauth2/v3/certs``
  * signature: RS256 via ``cryptography`` + JWKS public key lookup (kid)
  * claim checks: ``iss``, ``aud``, ``exp``, ``nonce``, ``email_verified``,
    ``sub``/``email`` presence

No new Python dependency beyond ``httpx`` + ``cryptography`` (already in
``pyproject.toml``).  Modelled after ``mealmind/app/services/google_oidc.py``
but using ``cryptography`` instead of ``python-jose``.
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
GOOGLE_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}
DEFAULT_REDIRECT_URI = "https://receipts.allthezoo.com/api/auth/google/callback"


class OIDCError(Exception):
    """ID-token validation or provider response failed."""


def _b64url_decode(segment: str) -> bytes:
    padded = segment + "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(padded)


def _b64url_decode_int(segment: str) -> int:
    return int.from_bytes(_b64url_decode(segment), "big")


def _config() -> tuple[str | None, str | None, str]:
    cid = os.getenv("RECEIPTLENS_GOOGLE_CLIENT_ID") or None
    secret = os.getenv("RECEIPTLENS_GOOGLE_CLIENT_SECRET") or None
    redirect = os.getenv("RECEIPTLENS_GOOGLE_REDIRECT_URI", DEFAULT_REDIRECT_URI)
    return cid, secret, redirect


def is_configured() -> bool:
    cid, secret, _ = _config()
    return bool(cid and secret)


async def exchange_google_code(
    code: str,
    expected_nonce: str,
    *,
    http_client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Exchange *code* for an ``id_token`` and return its verified claims."""
    client_id, client_secret, redirect_uri = _config()
    if not client_id or not client_secret:
        raise OIDCError("Google sign-in is not configured")

    owns_client = http_client is None
    client = http_client if http_client is not None else httpx.AsyncClient(
        timeout=10.0, follow_redirects=False
    )
    try:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_response.status_code != 200:
            raise OIDCError(
                f"Google code exchange failed: {token_response.status_code} "
                f"{token_response.text[:200]}"
            )
        payload = token_response.json()
        id_token = payload.get("id_token")
        if not isinstance(id_token, str) or not id_token:
            raise OIDCError("Google did not return an ID token")

        jwks_response = await client.get(GOOGLE_JWKS_URL)
        if jwks_response.status_code != 200:
            raise OIDCError("Google signing keys unavailable")
        jwks = jwks_response.json()
    finally:
        if owns_client:
            await client.aclose()

    return _verify_id_token(id_token, jwks, client_id, expected_nonce)


def _verify_id_token(
    id_token: str,
    jwks: dict[str, Any],
    expected_audience: str,
    expected_nonce: str,
) -> dict[str, Any]:
    parts = id_token.split(".")
    if len(parts) != 3:
        raise OIDCError("Invalid Google ID token")
    header_b64, payload_b64, signature_b64 = parts

    try:
        header = json.loads(_b64url_decode(header_b64))
        claims: dict[str, Any] = json.loads(_b64url_decode(payload_b64))
        signature = _b64url_decode(signature_b64)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OIDCError("Invalid Google ID token") from exc

    if header.get("alg") != "RS256":
        raise OIDCError("Invalid Google ID token")

    kid = header.get("kid")
    keys = jwks.get("keys") if isinstance(jwks, dict) else None
    if not isinstance(keys, list):
        raise OIDCError("Google signing keys unavailable")

    jwk: dict[str, Any] | None = None
    for candidate in keys:
        if isinstance(candidate, dict) and candidate.get("kid") == kid:
            jwk = candidate
            break
    if jwk is None:
        raise OIDCError("Unknown Google signing key")

    try:
        n = _b64url_decode_int(jwk["n"])
        e = _b64url_decode_int(jwk["e"])
        public_numbers = RSAPublicNumbers(e, n)
        public_key = public_numbers.public_key()
    except (KeyError, ValueError, TypeError) as exc:
        raise OIDCError("Invalid Google signing key") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    try:
        public_key.verify(signature, signing_input, padding.PKCS1v15(), hashes.SHA256())
    except InvalidSignature as exc:
        raise OIDCError("Invalid Google ID token signature") from exc
    except Exception as exc:  # pragma: no cover — defensive
        raise OIDCError("Invalid Google ID token") from exc

    # iss
    if claims.get("iss") not in GOOGLE_ISSUERS:
        raise OIDCError("Invalid Google issuer")
    # aud — string or list containing the client id
    aud = claims.get("aud")
    if isinstance(aud, list):
        if expected_audience not in aud:
            raise OIDCError("Invalid Google audience")
    elif aud != expected_audience:
        raise OIDCError("Invalid Google audience")
    # exp
    exp = claims.get("exp")
    if not isinstance(exp, (int, float)) or float(exp) <= time.time():
        raise OIDCError("Google ID token expired")
    # nonce
    if claims.get("nonce") != expected_nonce:
        raise OIDCError("Invalid Google nonce")
    # email_verified
    if claims.get("email_verified") is not True:
        raise OIDCError("Google email is not verified")
    # sub + email
    if not claims.get("sub") or not claims.get("email"):
        raise OIDCError("Google identity is incomplete")

    return claims
