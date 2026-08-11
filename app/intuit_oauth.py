"""Intuit OAuth2 token operations for QuickBooks Online.

Handles the code->token exchange, refresh, and revoke calls against
Intuit's fixed OAuth2 token endpoint. All hostnames are hard-coded
(no user-controlled base URL). Client credentials come from the
environment (RECEIPTLENS_QBO_CLIENT_ID / RECEIPTLENS_QBO_CLIENT_SECRET);
when the secret is unset the exchange cannot run and every operation
fails fast with a clear configuration error instead of leaking a
placeholder credential to Intuit.
"""
from __future__ import annotations

import os
from typing import Any

import httpx

# Intuit OAuth2 endpoints (fixed hosts — never configurable).
TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
REVOKE_URL = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"
_DEFAULT_TIMEOUT = 20.0


class OAuthConfigError(RuntimeError):
    """Raised when Intuit client credentials are not configured."""


class IntuitOAuthClient:
    """Minimal OAuth2 token client for Intuit QuickBooks Online."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.client_id = client_id if client_id is not None else os.getenv("RECEIPTLENS_QBO_CLIENT_ID", "")
        self.client_secret = client_secret if client_secret is not None else os.getenv("RECEIPTLENS_QBO_CLIENT_SECRET", "")
        self.redirect_uri = redirect_uri if redirect_uri is not None else os.getenv(
            "RECEIPTLENS_QBO_REDIRECT_URI", "/product/connections/quickbooks/oauth/callback"
        )
        self._client = client or httpx.Client(timeout=_DEFAULT_TIMEOUT)

    # -- helpers ---------------------------------------------------------
    def _require_credentials(self) -> tuple[str, str]:
        if not self.client_id or not self.client_secret:
            raise OAuthConfigError("QBO OAuth client_id/client_secret are not configured (RECEIPTLENS_QBO_CLIENT_ID / RECEIPTLENS_QBO_CLIENT_SECRET)")
        return self.client_id, self.client_secret

    def _auth_header(self) -> str:
        client_id, client_secret = self._require_credentials()
        import base64

        raw = f"{client_id}:{client_secret}".encode()
        return "Basic " + base64.b64encode(raw).decode()

    @staticmethod
    def _raise_for_oauth(response: httpx.Response) -> None:
        """Raise a bounded, non-credential error for a failed OAuth call."""
        if response.status_code < 400:
            return
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if payload and isinstance(payload, dict) and payload.get("error"):
            raise OAuthConfigError(f"Intuit OAuth error: {payload['error']}")
        raise OAuthConfigError(f"Intuit OAuth HTTP {response.status_code}")

    # -- OAuth2 operations ------------------------------------------------
    def exchange_code(self, code: str, state: str, verifier: str | None = None) -> dict[str, Any]:
        """Exchange an authorization code for tokens.

        ``verifier`` is the PKCE code verifier stored when the authorization
        URL was created; when the flow started with ``code_challenge_method=S256``
        (the default) the verifier is required or Intuit rejects the exchange.
        """
        client_id, _ = self._require_credentials()
        body = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": client_id,
        }
        if verifier is not None:
            body["code_verifier"] = verifier
        resp = self._client.post(
            TOKEN_URL,
            data=body,
            headers={"Authorization": self._auth_header(), "Accept": "application/json"},
        )
        self._raise_for_oauth(resp)
        return resp.json()

    def refresh(self, refresh_token: str) -> dict[str, Any]:
        """Refresh an expiring access token using its refresh token."""
        client_id, _ = self._require_credentials()
        body = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
        }
        resp = self._client.post(
            TOKEN_URL,
            data=body,
            headers={"Authorization": self._auth_header(), "Accept": "application/json"},
        )
        self._raise_for_oauth(resp)
        return resp.json()

    def revoke(self, refresh_token: str) -> None:
        """Revoke a refresh token at Intuit (best-effort)."""
        client_id, client_secret = self._require_credentials()
        body = {"token": refresh_token, "client_id": client_id, "client_secret": client_secret}
        resp = self._client.post(
            REVOKE_URL,
            data=body,
            headers={"Authorization": self._auth_header(), "Accept": "application/json"},
        )
        self._raise_for_oauth(resp)
