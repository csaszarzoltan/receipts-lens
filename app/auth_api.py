"""F1.3 household auth API — magic-link login, sessions, family invites.

Consumer pivot (docs/plans/consumer-pivot-2026-08-13.md §2.3): the
X-Tenant-ID demo auth is not sellable for a Family product, so this router
adds a real, password-less identity layer:

  * ``POST /auth/magic-link-request``  — email -> single-use expiring token
  * ``POST /auth/magic-link-verify``   — token -> session (or 401)
  * ``POST /auth/session/me``          — resolve a session token
  * ``POST /auth/households/{id}/invites``          — owner invites a member
  * ``GET  /auth/households/{id}/invites``          — list pending invites
  * ``POST /auth/households/{id}/invites/{id}/accept`` — accept + sign in

Delivery contract (AC1): magic-link / invite emails are delivered through the
existing ``send_email_notification()`` when SMTP is configured AND
``RECEIPTLENS_SMTP_ENABLED=1``.  Outside production (RECEIPTLENS_ENV !=
production) the link is additionally returned in the API response so the UI
flow is fully testable without a mail server.  In production the raw token
is NEVER returned.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.product_api import service
from app.product_service import (
    HOUSEHOLD_ROLES,
    Actor,
    is_production,
)

logger = logging.getLogger("uvicorn.error")

router = APIRouter()

INVITE_TTL_SECONDS = 7 * 24 * 60 * 60
SESSION_TTL_SECONDS = 30 * 24 * 60 * 60
MAGIC_LINK_TTL_SECONDS = 15 * 60

LOGIN_LINK_TEMPLATE = "{base_url}/auth/magic-link?token={token}"
INVITE_LINK_TEMPLATE = "{base_url}/auth/invite?token={token}&household={household_id}&invite={invite_id}"
AUTH_BASE_URL = os.getenv(
    "RECEIPTLENS_AUTH_BASE_URL", "http://localhost:3000"
).rstrip("/")


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

    Session (Authorization: Bearer <token>) wins — it is the real identity.
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


# Late import to satisfy the SMTP delivery path without a circular dep at
# module top (product_api imports this module).
from app.subscription_alerts import send_email_notification
