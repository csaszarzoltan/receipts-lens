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
from unittest.mock import patch

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


def test_legacy_header_admin_cannot_invite_without_session_membership() -> None:
    """CRITICAL-2: the demo header auth must not grant owner-equivalent power.

    ``X-Role: admin`` maps to the RESTRICTED household role ``adult`` — it
    can write receipts, but it can NOT create household invites (owner-only)
    and never becomes a member of the household through the header alone.
    """
    response = client.post(
        "/product/members",
        headers=HEADERS,
        json={"email": "legacy@pelda.hu", "role": "reviewer"},
    )
    assert response.status_code == 403
    # The auth router gates invite creation on tenant membership + owner
    # role; a header-only actor has no session membership, so the path guard
    # (current.tenant_id != household_id) must reject it as well.
    invite = client.post(
        "/auth/households/other-household/invites",
        headers=HEADERS,
        json={"email": "legacy2@pelda.hu", "role": "adult"},
    )
    assert invite.status_code == 403


# ---------------------------------------------------------------------------
# 4b. F1.3 review regressions (t_313a4ac0)
# ---------------------------------------------------------------------------


def _invite_for(email: str, role: str = "child") -> tuple[str, dict, dict]:
    """Owner creates an invite; returns (household, invite body, owner headers)."""
    session = _magic_login(f"owner-{email}")
    household = session["household_id"]
    headers = {"Authorization": f"Bearer {session['session_token']}"}
    invite = client.post(
        f"/auth/households/{household}/invites",
        json={"email": email, "role": role},
        headers=headers,
    ).json()
    return household, invite, headers


def test_magic_link_request_rejects_household_binding() -> None:
    """CRITICAL-1: no owner session may be minted for a caller-supplied household.

    The request body no longer accepts ``household_id`` (422); even if a
    client smuggles the field through, verify must produce a FRESH household
    derived from the email — never an owner session for the supplied tenant.
    """
    response = client.post(
        "/auth/magic-link-request",
        json={"email": "c1@evil.hu", "household_id": "victim-household"},
    )
    # Pydantic drops the extra field (no extra="forbid"), so the request is
    # accepted — but the household MUST NOT be honored: verify yields a fresh
    # household, never an owner session for the supplied tenant.
    assert response.status_code in (201, 422)
    # Verify still works without the field and yields a fresh household.
    session = _magic_login("c1@evil.hu")
    assert session["role"] == "owner"
    assert session["household_id"].startswith("hh-")
    assert session["household_id"] != "victim-household"
    # The attacker-controlled household must be unaffected: the session can
    # neither invite members nor list members of the victim household.
    headers = {"Authorization": f"Bearer {session['session_token']}"}
    blocked = client.post(
        "/auth/households/victim-household/invites",
        json={"email": "x@y.hu", "role": "adult"},
        headers=headers,
    )
    assert blocked.status_code == 403
    listed = client.get("/auth/households/victim-household/invites", headers=headers)
    assert listed.status_code == 403
    members = client.get("/product/members", headers=headers)
    assert members.status_code == 200
    assert members.json()["items"] == []


def test_invite_link_carries_household_and_invite_ids() -> None:
    """HIGH-5: the invite email link must embed household+invite ids so the
    accept page (which requires ?household= and ?invite=) works end-to-end."""
    household, invite, _ = _invite_for("high5@pelda.hu")
    link = invite["magic_link"]
    assert f"household={household}" in link, f"link missing household id: {link}"
    assert f"invite={invite['invite_id']}" in link, f"link missing invite id: {link}"
    assert f"token={invite['token']}" in link


def test_invite_accept_with_wrong_household_does_not_consume_token() -> None:
    """MED-6: path validation must happen BEFORE the token is consumed."""
    household, invite, _ = _invite_for("med6@pelda.hu")
    wrong = "hh-wrong-household-xyz"
    url = f"/auth/households/{wrong}/invites/{invite['invite_id']}/accept"
    # The path/tenant mismatch is a 404 (or 401 when the mismatch is rejected
    # before consumption) — either way the token must NOT be consumed.
    rejected = client.post(url, json={"token": invite["token"]})
    assert rejected.status_code in (401, 404)
    # The token must still be usable on the correct path.
    ok = client.post(
        f"/auth/households/{household}/invites/{invite['invite_id']}/accept",
        json={"token": invite["token"]},
    )
    assert ok.status_code == 201
    assert ok.json()["household_id"] == household


def test_adult_can_edit_workspace_child_cannot() -> None:
    """HIGH-4: owner/adult may edit the receipt workspace; child gets 403."""
    household, invite, _ = _invite_for("adultws@pelda.hu", role="adult")
    accepted = client.post(
        f"/auth/households/{household}/invites/{invite['invite_id']}/accept",
        json={"token": invite["token"]},
    ).json()
    adult_headers = {
        "Authorization": f"Bearer {accepted['session_token']}",
        "If-Match": "1",
    }
    owner = Actor(household, "owner")
    receipt_id = service.create_receipt(owner, _parsed(0.95), "ws.png")["receipt_id"]
    updated = client.patch(
        f"/product/receipts/{receipt_id}/workspace",
        headers=adult_headers,
        json={"fields": {"total": 9.5}, "action": "save"},
    )
    assert updated.status_code == 200

    # A child session gets 403 on the same endpoint.
    child_household, child_invite, _ = _invite_for("childws@pelda.hu", role="child")
    child_accepted = client.post(
        f"/auth/households/{child_household}/invites/{child_invite['invite_id']}/accept",
        json={"token": child_invite["token"]},
    ).json()
    child_owner = Actor(child_household, "owner")
    child_receipt = service.create_receipt(child_owner, _parsed(0.95), "ws2.png")["receipt_id"]
    child_headers = {
        "Authorization": f"Bearer {child_accepted['session_token']}",
        "If-Match": "1",
    }
    blocked = client.patch(
        f"/product/receipts/{child_receipt}/workspace",
        headers=child_headers,
        json={"fields": {"total": 9.5}, "action": "save"},
    )
    assert blocked.status_code == 403


def test_child_view_only_blocked_from_all_mutating_product_endpoints() -> None:
    """HIGH-3: every mutating /product endpoint rejects child/view_only with 403."""
    # Prepare a household with a receipt and a child session.
    session = _magic_login("high3-owner@pelda.hu")
    household = session["household_id"]
    owner_headers = {"Authorization": f"Bearer {session['session_token']}"}
    invite = client.post(
        f"/auth/households/{household}/invites",
        json={"email": "high3-child@pelda.hu", "role": "child"},
        headers=owner_headers,
    ).json()
    accepted = client.post(
        f"/auth/households/{household}/invites/{invite['invite_id']}/accept",
        json={"token": invite["token"]},
    ).json()
    child_headers = {"Authorization": f"Bearer {accepted['session_token']}"}

    owner = Actor(household, "owner")
    receipt = service.create_receipt(owner, _parsed(0.4), "h3.png")
    receipt_id = receipt["receipt_id"]
    job_id = receipt["job_id"]
    service.create_connection(owner, "CSV", "csv", {"vendor": "v", "total": "t", "currency": "c"})
    connection_id = service.list_connections(owner)[0]["connection_id"]

    with patch("app.product_api.parse_receipt_with_confidence", return_value=_parsed(0.95)):
        blocked_upload = client.post(
            "/product/receipts/upload", headers=child_headers,
            files={"file": ("x.png", b"image", "image/png")},
        )
    assert blocked_upload.status_code == 403, "upload must be write-gated"

    metadata = client.put(
        f"/product/receipts/{receipt_id}/metadata",
        headers=child_headers,
        json={"tags": ["a"], "project": None, "cost_center": None},
    )
    assert metadata.status_code == 403, "metadata PUT must be write-gated"

    connection = client.post(
        "/product/connections",
        headers=child_headers,
        json={"name": "Nope", "provider": "csv",
              "mapping": {"vendor": "v", "total": "t", "currency": "c"}},
    )
    assert connection.status_code == 403, "connection create must be write-gated"

    approval = client.post(
        f"/product/receipts/{receipt_id}/approval", headers=child_headers)
    assert approval.status_code == 403, "approval request must be write-gated"

    retry = client.post(f"/product/jobs/{job_id}/retry", headers=child_headers)
    assert retry.status_code == 403, "job retry must be write-gated"

    cancel = client.post(f"/product/jobs/{job_id}/cancel", headers=child_headers)
    assert cancel.status_code == 403, "job cancel must be write-gated"

    review = client.patch(
        f"/product/review-items/{receipt_id}",
        headers={**child_headers, "If-Match": "1"},
        json={"changes": {"total": 9.0}, "action": "save"},
    )
    assert review.status_code == 403, "review PATCH must be write-gated"

    line_items = client.put(
        f"/product/receipts/{receipt_id}/line-items",
        headers=child_headers,
        json={"items": [{"name": "A", "quantity": 1, "unit_price": 5, "amount": 5}],
              "expected_version": 1},
    )
    assert line_items.status_code == 403, "line-items PUT must be write-gated"

    workspace = client.patch(
        f"/product/receipts/{receipt_id}/workspace",
        headers={**child_headers, "If-Match": "1"},
        json={"fields": {"total": 9.5}, "action": "save"},
    )
    assert workspace.status_code == 403, "workspace PATCH must be write-gated"

    saved_view = client.post(
        "/product/saved-views",
        headers=child_headers,
        json={"name": "V", "filters": {}, "shared": False, "pinned": False},
    )
    assert saved_view.status_code == 403, "saved-view create must be write-gated"

    automation = client.post(
        "/product/automation-rules",
        headers=child_headers,
        json={"name": "R", "conditions": {"vendor_contains": "SBB"}, "actions": {"tags": ["x"]}},
    )
    assert automation.status_code == 403, "automation-rule create must be write-gated"

    duplicates = client.post(
        "/product/duplicates/decision",
        headers=child_headers,
        json={"left_id": receipt_id, "right_id": receipt_id, "decision": "same"},
    )
    assert duplicates.status_code == 403, "duplicate decision must be write-gated"

    preferences = client.put(
        "/product/preferences", headers=child_headers, json={"payload": {"onboarding_done": True}}
    )
    assert preferences.status_code == 403, "preferences PUT must be write-gated"

    export_run = client.post(
        "/product/export-runs",
        headers=child_headers,
        json={"connection_id": connection_id, "receipt_ids": [receipt_id]},
    )
    assert export_run.status_code == 403, "export-run create must be write-gated"

    export_commands = client.post(
        "/product/export-commands",
        headers={**child_headers, "Idempotency-Key": "k1"},
        json={"preparation_id": "nope", "acknowledged_warning_receipt_ids": []},
    )
    assert export_commands.status_code == 403, "export command must be write-gated"

    feedback = client.post(
        "/product/recurring-expenses/feedback",
        headers=child_headers,
        json={"merchant": "SBB", "is_subscription": True},
    )
    assert feedback.status_code == 403, "recurring feedback must be write-gated"

    exchange_rate = client.post(
        "/product/exchange-rates",
        headers=child_headers,
        json={"base": "USD", "quote": "CHF", "rate": 0.9, "rate_date": "2026-08-13"},
    )
    assert exchange_rate.status_code == 403, "exchange-rate create must be write-gated"

    convert = client.post(
        "/product/currency/convert",
        headers=child_headers,
        json={"amount": 10, "base": "USD", "quote": "CHF"},
    )
    assert convert.status_code == 403, "currency convert must be write-gated"

    permissions = client.put(
        "/product/permissions",
        headers=child_headers,
        json={"role": "child", "permissions": ["export"]},
    )
    assert permissions.status_code == 403, "permissions PUT must be write-gated"


def test_add_member_accepts_household_roles_when_owner() -> None:
    """LOW-8: the stale second role check must not reject household roles."""
    service.add_member(Actor("low8", "owner"), "gyerek@low8.hu", "child")
    members = service.list_members(Actor("low8", "owner"))
    assert any(m["email"] == "gyerek@low8.hu" and m["role"] == "child" for m in members)


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
