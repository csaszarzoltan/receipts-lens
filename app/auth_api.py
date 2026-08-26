"""F1.3 household auth API — magic-link login, sessions, family invites
+ Google SSO authorization-code flow (G2).

Consumer pivot (docs/plans/consumer-pivot-2026-08-13.md §2.3): the
X-Tenant-ID demo auth is not sellable for a Family product, so this router
adds a real, password-less identity layer:

  * ``POST /auth/magic-link-request``  — email -> single-use expiring token
  * ``POST /auth/magic-link-verify``   — token -> session (or 401)
  * ``POST /auth/session/me``          — resolve a session token
  * ``POST /auth/households/{id}/invites``          — owner invites a member
  * ``GET  /auth/households/{id}/invites``          — list pending invites
  * ``POST /auth/households/{id}/invites/{id}/accept`` — accept + sign in

Google SSO (docs/plans/google-sso-2026-08-26.md §G2):
  * ``GET /api/auth/google/status``       — {enabled: bool} probe
  * ``GET /api/auth/google/start``        — set CSRF cookie + redirect to Google
  * ``GET /api/auth/google/callback``     — exchange code + create session
  * ``POST /api/auth/session/logout``     — delete session row, 204

Delivery contract (AC1): magic-link / invite emails are delivered through the
existing ``send_email_notification()`` when SMTP is configured AND
``RECEIPTLENS_SMTP_ENABLED=1``.  Outside production (RECEIPTLENS_ENV !=\nproduction) the link is additionally returned in the API response so the UI
flow is fully testable without a mail server.  In production the raw token
is NEVER returned.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.google_oidc import OIDCError, exchange_google_code, is_configured as google_is_configured
from app.product_api import service
from app.product_service import (
    HOUSEHOLD_ROLES,
    SESSION_TTL_SECONDS,
    Actor,
    is_production,
)
from app.subscription_alerts import send_email_notification

logger = logging.getLogger("uvicorn.error")

router = APIRouter()

INVITE_TTL_SECONDS = 7 * 24 * 60 * 60
SESSION_TTL_SECONDS = 180 * 24 * 60 * 60
OAUTH_COOKIE = "receiptlens.oauth"
OAUTH_COOKIE_MAX_AGE = 600
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
MAGIC_LINK_TTL_SECONDS = 15 * 60

LOGIN_LINK_TEMPLATE = "{base_url}/auth/magic-link?token={token}"
INVITE_LINK_TEMPLATE = "{base_url}/auth/invite?token={token}&household={household_id}&invite={invite_id}"
AUTH_BASE_URL = os.getenv(
    "RECEIPTLENS_AUTH_BASE_URL", "http://localhost:3000"
).rstrip("/")

# State-signing secret for the OAuth CSRF cookie.  If no explicit secret is
# configured we generate a random one per process start — this is fine for
# single-server deploys; multi-node would need a shared secret.
_STATE_SECRET = os.getenv(
    "RECEIPTLENS_OAUTH_STATE_SECRET",
    secrets.token_hex(32),
)


class MagicLinkRequest(BaseModel):
    email: str = Field(min_length=3)
    # ``household_id`` is deliberately NOT accepted: binding a magic link to
    # an arbitrary household without proof of membership would mint an owner
    # session for that household (F1.3 review CRITICAL-1).  A fresh household
    # is derived from the email at verify time; joining an existing household
    # goes through the owner-issued invite flow instead.


class MagicLinkVerifyRequest(BaseModel):
    token: str = Field(min_length=8)


class InviteRequest(BaseModel):
    email: str = Field(min_length=3)
    role: str = Field(pattern="^(owner|adult|child|view_only)$")


class AcceptInviteRequest(BaseModel):
    token: str = Field(min_length=8)


class SessionRequest(BaseModel):
    session_token: str = Field(min_length=8)


def _smtp_config() -> dict[str, Any] | None:
    """Return the SMTP config dict or None when delivery is not configured."""
    host = os.getenv("RECEIPTLENS_SMTP_HOST")
    if not host:
        return None
    return {
        "host": host,
        "port": os.getenv("RECEIPTLENS_SMTP_PORT", "587"),
        "user": os.getenv("RECEIPTLENS_SMTP_USER"),
        "password": os.getenv("RECEIPTLENS_SMTP_PASSWORD"),
        "from_addr": os.getenv("RECEIPTLENS_SMTP_FROM", "noreply@receiptlens.local"),
        "to_addr": None,
    }


def _deliver_or_return(token: str, link: str, email: str, subject: str, body: str) -> dict[str, Any]:
    """Send the email when possible; otherwise (dev mode) return the link.

    Production never echoes the raw token — it returns only the delivery
    status so the flow degrades to a visible error instead of leaking a
    credential through the API.
    """
    smtp = _smtp_config()
    if smtp:
        try:
            smtp["to_addr"] = email
            sent = send_email_notification(subject, body, smtp_config=smtp)
            if sent:
                return {"delivered": True}
        except (OSError, RuntimeError) as exc:
            logger.warning("magic-link email delivery failed: %s", exc)
    if is_production():
        return {"delivered": False, "detail": "Email delivery is not configured"}
    return {"delivered": False, "magic_link": link, "token": token}


def household_actor(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> Actor:
    """Resolve the caller identity: session first, then legacy dev headers.

    Session (Authorization: Bearer ***) wins — it is the real identity.
    The X-Tenant-ID/X-Role headers remain usable in development mode only
    (RECEIPTLENS_ENV != production), preserving the demo flow (AC6).
    """
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        try:
            identity = service.resolve_session(token)
        except KeyError as exc:
            raise HTTPException(401, "Invalid or expired session") from exc
        return Actor(identity["tenant_id"], identity["role"])
    if is_production():
        raise HTTPException(401, "Session required")
    if x_tenant_id is None or not x_tenant_id.strip():
        raise HTTPException(401, "Tenant identity is required")
    if x_role is None or x_role not in {"admin", "reviewer", "integrator", *HOUSEHOLD_ROLES}:
        raise HTTPException(403, "Unknown role")
    return Actor(x_tenant_id.strip(), x_role)


# ---------------------------------------------------------------------------
# Google SSO — authorization-code flow (G2)
# ---------------------------------------------------------------------------


def _oauth_hmac(state: str) -> str:
    """Derive a deterministic nonce from the OAuth state parameter.

    This avoids storing the nonce separately — the server recomputes it from
    the state value using the same HMAC secret.
    """
    return hmac.new(
        _STATE_SECRET.encode(), state.encode(), hashlib.sha256
    ).hexdigest()


def _safe_return_to(value: str | None) -> str:
    """Validate a return_to path — only relative paths starting with / are accepted."""
    if not value or not value.startswith("/") or value.startswith("//"):
        return "/dashboard"
    return value


@router.get("/api/auth/google/status")
def google_status() -> dict[str, bool]:
    """Probe whether Google SSO is configured at runtime."""
    return {"enabled": google_is_configured()}


@router.get("/api/auth/google/start")
def google_start(
    request: Request,
    return_to: str | None = None,
) -> RedirectResponse:
    """Start the Google OAuth authorization-code flow.

    1. Generate state + nonce (state is random 32 bytes; nonce = HMAC(state)).
    2. Set an HttpOnly+Secure+SameSite=Lax cookie containing the state.
    3. 307-redirect the browser to accounts.google.com.
    4. If Google SSO is not configured → 503.
    """
    if not google_is_configured():
        raise HTTPException(503, "Google sign-in is not configured")

    state = secrets.token_hex(32)  # 64 hex chars = 32 bytes
    state_hmac = _oauth_hmac(state)

    # The nonce passed to exchange_google_code is derived from the state
    # via HMAC — the server recomputes it from the returned state query param.
    safe_rt = _safe_return_to(return_to)
    cookie_value = state

    params = {
        "client_id": os.getenv("RECEIPTLENS_GOOGLE_CLIENT_ID"),
        "redirect_uri": os.getenv(
            "RECEIPTLENS_GOOGLE_REDIRECT_URI",
            "https://receipts.allthezoo.com/api/auth/google/callback",
        ),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }
    redirect_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    response = RedirectResponse(redirect_url, status_code=307)
    response.set_cookie(
        OAUTH_COOKIE,
        cookie_value,
        max_age=OAUTH_COOKIE_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    return response


@router.get("/api/auth/google/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    """Handle the Google OAuth callback.

    1. Validate the state matches the cookie (CSRF protection).
    2. Exchange the authorization code via ``exchange_google_code``.
    3. Find-or-create a household for the email (``hh-{email}``, owner role).
    4. Create a session.
    5. 302-redirect the frontend to ``/auth/google/callback#session_token=...&expires_at=...``.
    """
    frontend_url = AUTH_BASE_URL

    # On user denial or Google error
    if error:
        return RedirectResponse(
            f"{frontend_url}/login?error=oauth_cancelled", status_code=302
        )

    if not code or not state:
        return RedirectResponse(
            f"{frontend_url}/login?error=oauth_missing_params", status_code=302
        )

    # CSRF check: state must match the cookie
    cookie_state = request.cookies.get(OAUTH_COOKIE)
    if not cookie_state or not secrets.compare_digest(cookie_state, state):
        return RedirectResponse(
            f"{frontend_url}/login?error=oauth_invalid_state", status_code=302
        )

    # Derive the nonce from the state (same HMAC as /start)
    expected_nonce = _oauth_hmac(state)

    try:
        claims = await exchange_google_code(code, expected_nonce)
    except OIDCError as exc:
        logger.warning("Google OIDC exchange failed: %s", exc)
        return RedirectResponse(
            f"{frontend_url}/login?error=oauth_exchange_failed", status_code=302
        )

    email = claims["email"]
    tenant_id, _created = service.find_or_create_household_owner(email)
    session = service.create_session(email, tenant_id, "owner")

    # Build the redirect URL with fragment (JS reads it, not the server)
    fragment = urlencode({
        "session_token": session["session_token"],
        "expires_at": session["expires_at"],
    })
    redirect = RedirectResponse(
        f"{frontend_url}/auth/google/callback#{fragment}", status_code=302
    )
    # Clear the OAuth cookie
    redirect.delete_cookie(OAUTH_COOKIE, path="/")
    return redirect


# ---------------------------------------------------------------------------
# Magic-link login
# ---------------------------------------------------------------------------


@router.post("/auth/magic-link-request", status_code=201)
def magic_link_request(body: MagicLinkRequest) -> dict[str, Any]:
    """Create a magic-link token for *email* and deliver/return the link.

    The token carries no tenant — at verify time a fresh household is
    derived from the email.  Caller-supplied households are rejected
    (CRITICAL-1): binding a link to an arbitrary household without
    membership proof would mint an owner session for that household.
    """
    email = str(body.email).strip().lower()
    created = service.create_magic_link(email)
    token = created["token"]
    link = LOGIN_LINK_TEMPLATE.format(base_url=AUTH_BASE_URL, token=token)
    subject = "ReceiptLens — belépés"
    body_text = (
        "Kattints a linkre a bejelentkezéshez:\n\n"
        f"{link}\n\n"
        "A link 15 percig érvényes és egyszer használható."
    )
    result = _deliver_or_return(token, link, email, subject, body_text)
    result["email"] = email
    result["expires_at"] = created["expires_at"]
    return result


@router.post("/auth/magic-link-verify", status_code=201)
def magic_link_verify(body: MagicLinkVerifyRequest) -> dict[str, Any]:
    """Consume a magic-link token and establish a session.

    Unknown/expired/consumed tokens yield 401.  Tokens created without a
    household (fresh signup) get a new household derived from the email.
    """
    try:
        payload = service.verify_magic_link(body.token)
    except KeyError as exc:
        raise HTTPException(401, "Invalid, expired or already-used magic link") from exc
    email = payload["email"]
    tenant_id = payload["tenant_id"] or f"hh-{email.replace('@', '-').replace('.', '-')}"
    role = payload["role"] or "owner"
    session = service.create_session(email, tenant_id, role)
    return {
        "session_token": session["session_token"],
        "email": email,
        "household_id": tenant_id,
        "role": role,
        "expires_at": session["expires_at"],
    }


@router.post("/auth/session/me")
def session_me(body: SessionRequest) -> dict[str, Any]:
    """Resolve a session token into the current identity (401 on bad session)."""
    try:
        identity = service.resolve_session(body.session_token)
    except KeyError as exc:
        raise HTTPException(401, "Invalid or expired session") from exc
    return identity


@router.post("/auth/session/logout", status_code=204)
def session_logout(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> Response:
    """Delete a session — the client calls this on sign-out.

    Requires ``Authorization: Bearer <token>``.  Returns 204 on success
    (whether or not the token actually existed).
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Authorization header required")
    token = authorization.split(" ", 1)[1].strip()
    service.delete_session(token)
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Family invites
# ---------------------------------------------------------------------------


@router.post("/auth/households/{household_id}/invites", status_code=201)
def create_invite(
    household_id: str,
    body: InviteRequest,
    current: Actor = Depends(household_actor),
) -> dict[str, Any]:
    """Household owner invites a member by email with a household role."""
    if current.tenant_id != household_id:
        raise HTTPException(403, "Not a member of this household")
    try:
        invite = service.create_invite(current, str(body.email), body.role)
    except PermissionError as exc:
        raise HTTPException(403, "Only the household owner can invite members") from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    token = invite["token"]
    link = INVITE_LINK_TEMPLATE.format(
        base_url=AUTH_BASE_URL, token=token,
        household_id=household_id, invite_id=invite["invite_id"],
    )
    subject = "ReceiptLens — családi meghívó"
    body_text = (
        f"Csatlakozz a ReceiptLens háztartáshoz ({household_id}):\n\n"
        f"{link}\n\n"
        "A meghívó 7 napig érvényes."
    )
    delivery = _deliver_or_return(token, link, invite["email"], subject, body_text)
    return {
        "invite_id": invite["invite_id"],
        "email": invite["email"],
        "role": invite["role"],
        "status": invite["status"],
        "expires_at": invite["expires_at"],
        **delivery,
    }


@router.get("/auth/households/{household_id}/invites")
def list_invites(
    household_id: str,
    current: Actor = Depends(household_actor),
) -> dict[str, Any]:
    """List the household's pending invites (owner only)."""
    if current.tenant_id != household_id:
        raise HTTPException(403, "Not a member of this household")
    try:
        items = service.list_invites(current)
    except PermissionError as exc:
        raise HTTPException(403, "Only the household owner can list invites") from exc
    return {"items": items}


@router.post(
    "/auth/households/{household_id}/invites/{invite_id}/accept", status_code=201
)
def accept_invite(
    household_id: str,
    invite_id: str,
    body: AcceptInviteRequest,
) -> dict[str, Any]:
    """Accept a family invite: creates the membership and signs the user in."""
    try:
        payload = service.accept_invite(body.token, expected_tenant_id=household_id,
                                        expected_invite_id=invite_id)
    except KeyError as exc:
        # Unknown/expired/used token, or a path mismatch (wrong household or
        # wrong invite id).  A path mismatch must NOT consume the token, so
        # the service rejects it before consumption — surfaced as 404 to
        # match the documented contract.
        raise HTTPException(404, "Invite not found") from exc
    return {
        "session_token": payload["session_token"],
        "email": payload["email"],
        "household_id": payload["tenant_id"],
        "role": payload["role"],
        "expires_at": payload["expires_at"],
    }
