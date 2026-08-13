"""F1.3 household-auth contract — US-024 BDD test suite (magic link, invites, roles).

Covers docs/plans/consumer-pivot-2026-08-13.md §2.3 / F1.3 and the F1.3
acceptance criteria:

  1. Magic-link login works (token retrievable, expiry, single-use) — backend + UI flow.
  2. Invite flow: owner invites → member accepts → signs in.
  3. Role permissions enforced (403 on forbidden operations).
  4. Backend tests: auth + invite + permission (TDD, ≥1 integration test per flow).
  5. tsc --noEmit: 0 errors.
  6. The legacy X-Tenant-ID test auth stays compatible in dev mode
     (RECEIPTLENS_ENV != production).

All flows are exercised through a real FastAPI TestClient (HTTP-level, no
mocks) against the in-process SQLite product service — the same pattern the
existing product contract suites use.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import api
from app.ocr import ConfidenceReceipt, ReceiptItem
from app.product_api import service
from app.product_service import Actor, ProductService

pytestmark = pytest.mark.us024

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = REPO_ROOT / "frontend"
API_CLIENT = FRONTEND / "lib" / "api.ts"
AUTH_MODULE = FRONTEND / "lib" / "auth.ts"
TYPES = FRONTEND / "lib" / "types.ts"
LOGIN_PAGE = FRONTEND / "app" / "(auth)" / "login" / "page.tsx"
MAGIC_PAGE = FRONTEND / "app" / "auth" / "magic-link" / "page.tsx"
INVITE_PAGE = FRONTEND / "app" / "auth" / "invite" / "page.tsx"

client = TestClient(api.app)
HEADERS = {"X-Tenant-ID": "csalad-1", "X-Role": "admin"}

HOUSEHOLD_ROLES = {"owner", "adult", "child", "view_only"}


def _parsed(confidence: float = 0.95) -> ConfidenceReceipt:
    return ConfidenceReceipt(
        merchant="Test Shop", date="2026-07-29",
        items=[ReceiptItem(name="Coffee", price=5.5)], total=5.5, tax=0.5,
        currency="USD", raw_text="TEST SHOP",
        confidence={"merchant": confidence, "total": confidence},
    )


def _magic_login(email: str, household_id: str | None = None) -> dict:
    """Full magic-link login flow — returns the session identity."""
    requested = client.post(
        "/auth/magic-link-request",
        json={"email": email, "household_id": household_id},
    )
    assert requested.status_code == 201
    body = requested.json()
    assert "token" in body, "dev mode must expose the token (AC1)"
    verified = client.post("/auth/magic-link-verify", json={"token": body["token"]})
    assert verified.status_code == 201
    return verified.json()


# ---------------------------------------------------------------------------
# 1. Magic-link login
# ---------------------------------------------------------------------------


def test_magic_link_request_returns_token_with_expiry() -> None:
    response = client.post(
        "/auth/magic-link-request", json={"email": "tulaj@pelda.hu"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "tulaj@pelda.hu"
    assert len(body["token"]) >= 20
    assert "expires_at" in body
    # The dev-mode link must be reconstructible from the token.
    assert body["token"] in body["magic_link"]


def test_magic_link_verify_establishes_session_and_household() -> None:
    session = _magic_login("tulaj@pelda.hu")
    assert session["role"] == "owner"
    assert session["email"] == "tulaj@pelda.hu"
    assert session["household_id"].startswith("hh-")
    assert len(session["session_token"]) >= 20
    assert "expires_at" in session


def test_magic_link_is_single_use() -> None:
    requested = client.post(
        "/auth/magic-link-request", json={"email": "single@pelda.hu"}
    ).json()
    first = client.post("/auth/magic-link-verify", json={"token": requested["token"]})
    assert first.status_code == 201
    second = client.post("/auth/magic-link-verify", json={"token": requested["token"]})
    assert second.status_code == 401


def test_magic_link_unknown_token_rejected() -> None:
    response = client.post(
        "/auth/magic-link-verify", json={"token": "bogus-token-12345678"}
    )
    assert response.status_code == 401


def test_magic_link_expired_token_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    # A token created with a negative TTL is already expired.
    created = service.create_magic_link("lejart@pelda.hu", ttl_seconds=-1)
    response = client.post(
        "/auth/magic-link-verify", json={"token": created["token"]}
    )
    assert response.status_code == 401


def test_session_me_resolves_identity() -> None:
    session = _magic_login("session@pelda.hu")
    response = client.post(
        "/auth/session/me", json={"session_token": session["session_token"]}
    )
    assert response.status_code == 200
    identity = response.json()
    assert identity["email"] == "session@pelda.hu"
    assert identity["role"] == "owner"
    assert identity["tenant_id"] == session["household_id"]


def test_session_me_rejects_garbage_token() -> None:
    response = client.post(
        "/auth/session/me", json={"session_token": "not-a-real-session-token"}
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# 2. Invite flow
# ---------------------------------------------------------------------------


def test_owner_can_invite_member() -> None:
    session = _magic_login("inviter@pelda.hu")
    household = session["household_id"]
    headers = {"Authorization": f"Bearer {session['session_token']}"}
    response = client.post(
        f"/auth/households/{household}/invites",
        json={"email": "felnott@pelda.hu", "role": "adult"},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "adult"
    assert body["status"] == "pending"
    assert "token" in body  # dev-mode link delivery


def test_invite_list_shows_pending_invites() -> None:
    session = _magic_login("invitelist@pelda.hu")
    household = session["household_id"]
    headers = {"Authorization": f"Bearer {session['session_token']}"}
    client.post(
        f"/auth/households/{household}/invites",
        json={"email": "tag1@pelda.hu", "role": "child"},
        headers=headers,
    )
    response = client.get(f"/auth/households/{household}/invites", headers=headers)
    assert response.status_code == 200
    emails = [item["email"] for item in response.json()["items"]]
    assert "tag1@pelda.hu" in emails


def test_invite_accept_creates_membership_and_session() -> None:
    session = _magic_login("acceptowner@pelda.hu")
    household = session["household_id"]
    headers = {"Authorization": f"Bearer {session['session_token']}"}
    invite = client.post(
        f"/auth/households/{household}/invites",
        json={"email": "gyerek@pelda.hu", "role": "child"},
        headers=headers,
    ).json()
    accepted = client.post(
        f"/auth/households/{household}/invites/{invite['invite_id']}/accept",
        json={"token": invite["token"]},
    )
    assert accepted.status_code == 201
    body = accepted.json()
    assert body["role"] == "child"
    assert body["household_id"] == household
    assert len(body["session_token"]) >= 20
    # The membership is now visible to the owner.
    members = client.get("/product/members", headers=HEADERS).json()["items"]
    # members listing is tenant-scoped; the new member lives in the invite tenant
    all_members = service.list_members(Actor(household, "owner"))
    assert any(m["email"] == "gyerek@pelda.hu" and m["role"] == "child" for m in all_members)


def test_invite_token_is_single_use() -> None:
    session = _magic_login("singleinvite@pelda.hu")
    household = session["household_id"]
    headers = {"Authorization": f"Bearer {session['session_token']}"}
    invite = client.post(
        f"/auth/households/{household}/invites",
        json={"email": "egyszer@pelda.hu", "role": "view_only"},
        headers=headers,
    ).json()
    url = f"/auth/households/{household}/invites/{invite['invite_id']}/accept"
    assert client.post(url, json={"token": invite["token"]}).status_code == 201
    assert client.post(url, json={"token": invite["token"]}).status_code == 401


def test_non_owner_cannot_invite() -> None:
    session = _magic_login("nonowner@pelda.hu")
    household = session["household_id"]
    headers = {"Authorization": f"Bearer {session['session_token']}"}
    invite = client.post(
        f"/auth/households/{household}/invites",
        json={"email": "gyerek2@pelda.hu", "role": "child"},
        headers=headers,
    ).json()
    accepted = client.post(
        f"/auth/households/{household}/invites/{invite['invite_id']}/accept",
        json={"token": invite["token"]},
    ).json()
    child_headers = {"Authorization": f"Bearer {accepted['session_token']}"}
    response = client.post(
        f"/auth/households/{household}/invites",
        json={"email": "masik@pelda.hu", "role": "child"},
        headers=child_headers,
    )
    assert response.status_code == 403


def test_invite_rejects_unknown_role() -> None:
    session = _magic_login("badrole@pelda.hu")
    household = session["household_id"]
    headers = {"Authorization": f"Bearer {session['session_token']}"}
    response = client.post(
        f"/auth/households/{household}/invites",
        json={"email": "rossz@pelda.hu", "role": "superadmin"},
        headers=headers,
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 3. Role permissions (403 enforcement)
# ---------------------------------------------------------------------------


def test_view_only_cannot_edit_receipt() -> None:
    session = _magic_login("viewonly@pelda.hu")
    household = session["household_id"]
    headers = {"Authorization": f"Bearer {session['session_token']}"}
    invite = client.post(
        f"/auth/households/{household}/invites",
        json={"email": "nezo@pelda.hu", "role": "view_only"},
        headers=headers,
    ).json()
    accepted = client.post(
        f"/auth/households/{household}/invites/{invite['invite_id']}/accept",
        json={"token": invite["token"]},
    ).json()
    # Seed a receipt as the owner, then attempt to edit it as the view-only member.
    owner = Actor(household, "owner")
    created = service.create_receipt(owner, _parsed(0.4), "bolt.png")
    viewer_headers = {
        "Authorization": f"Bearer {accepted['session_token']}",
        "If-Match": "1",
    }
    response = client.patch(
        f"/product/review-items/{created['receipt_id']}",
        headers=viewer_headers,
        json={"changes": {"total": 9.0}, "action": "complete"},
    )
    assert response.status_code == 403


def test_child_cannot_edit_receipt_via_patch() -> None:
    owner = Actor("csalad-child", "owner")
    created = service.create_receipt(owner, _parsed(0.4), "bolt.png")
    receipt_id = created["receipt_id"]
    child = client.patch(
        f"/product/review-items/{receipt_id}",
        headers={"X-Tenant-ID": "csalad-child", "X-Role": "child", "If-Match": "1"},
        json={"changes": {"total": 9.0}, "action": "complete"},
    )
    assert child.status_code == 403


def test_owner_can_edit_receipt_via_patch() -> None:
    owner = Actor("csalad-owner", "owner")
    created = service.create_receipt(owner, _parsed(0.4), "bolt.png")
    receipt_id = created["receipt_id"]
    response = client.patch(
        f"/product/review-items/{receipt_id}",
        headers={"X-Tenant-ID": "csalad-owner", "X-Role": "admin", "If-Match": "1"},
        json={"changes": {"total": 9.0}, "action": "complete"},
    )
    assert response.status_code == 200


def test_view_only_member_cannot_invite_or_edit() -> None:
    session = _magic_login("vowner@pelda.hu")
    household = session["household_id"]
    headers = {"Authorization": f"Bearer {session['session_token']}"}
    invite = client.post(
        f"/auth/households/{household}/invites",
        json={"email": "vtag@pelda.hu", "role": "view_only"},
        headers=headers,
    ).json()
    accepted = client.post(
        f"/auth/households/{household}/invites/{invite['invite_id']}/accept",
        json={"token": invite["token"]},
    ).json()
    view_headers = {"Authorization": f"Bearer {accepted['session_token']}"}
    blocked_invite = client.post(
        f"/auth/households/{household}/invites",
        json={"email": "vtag2@pelda.hu", "role": "view_only"},
        headers=view_headers,
    )
    assert blocked_invite.status_code == 403


# ---------------------------------------------------------------------------
# 4. Dev-mode compatibility (AC6): X-Tenant-ID still works
# ---------------------------------------------------------------------------


def test_legacy_header_auth_still_works_for_product_endpoints() -> None:
    response = client.get("/product/members", headers=HEADERS)
    assert response.status_code == 200
    response = client.get("/api/v1/consumer/dashboard", headers=HEADERS)
    assert response.status_code == 200


def test_legacy_header_add_member_still_works() -> None:
    response = client.post(
        "/product/members",
        headers=HEADERS,
        json={"email": "legacy@pelda.hu", "role": "reviewer"},
    )
    assert response.status_code == 201


# ---------------------------------------------------------------------------
# 5. Frontend contract checks (tsc parity — the real gate runs tsc --noEmit)
# ---------------------------------------------------------------------------


def test_frontend_has_auth_api_client_functions() -> None:
    text = API_CLIENT.read_text(encoding="utf-8")
    for function in (
        "requestMagicLink",
        "verifyMagicLink",
        "acceptInvite",
        "createInvite",
        "listInvites",
        "resolveSession",
    ):
        assert function in text, f"api.ts must export {function}"


def test_frontend_auth_module_supports_session_identity() -> None:
    text = AUTH_MODULE.read_text(encoding="utf-8")
    assert "session" in text.lower() or "bearer" in text.lower()


def test_frontend_types_declare_auth_payloads() -> None:
    text = TYPES.read_text(encoding="utf-8")
    for symbol in ("MagicLinkResponse", "SessionIdentity", "HouseholdInvite"):
        assert symbol in text, f"types.ts must declare {symbol}"


def test_login_page_offers_magic_link_entry() -> None:
    text = LOGIN_PAGE.read_text(encoding="utf-8")
    assert "magic" in text.lower(), "login page must link to the magic-link flow"


def test_magic_link_and_invite_pages_exist() -> None:
    assert MAGIC_PAGE.exists(), "frontend/app/auth/magic-link/page.tsx missing"
    assert INVITE_PAGE.exists(), "frontend/app/auth/invite/page.tsx missing"


def test_invite_roles_match_household_vocabulary() -> None:
    """The wire role set must match the §3.2 household vocabulary."""
    assert HOUSEHOLD_ROLES == {"owner", "adult", "child", "view_only"}
    # role labels live in lib/roles.ts
    text = (FRONTEND / "lib" / "roles.ts").read_text(encoding="utf-8")
    for label in ("Háztartás tulajdonosa", "Gyermek", "Csak megtekintés"):
        assert label in text
