"""F1.3 household-auth contract — RED gap suite (US-024b).

Pre-tester deliverable for docs/plans/consumer-pivot-2026-08-13.md §2.3 / F1.3
(t_8659da58).  The main US-024 suite (tests/test_us_024_auth_contract.py) was
written by the developer hand-in-hand with the feature, so this file targets
the CONTRACT POINTS THE EXISTING SUITE DOES NOT COVER — found by empirical
probes against the live TestClient on 2026-08-13:

RED (contract promised, behaviour missing):
  * G1 — POST /auth/households/{id}/invites with ``role=owner`` is accepted
    (201) although docs/api.md says "``owner`` is rejected on invites — a
    household has exactly one owner".
  * G2 — POST /auth/households/{id}/invites/{invite_id}/accept with a
    *wrong household in the path* returns 401 although docs/api.md promises
    404 for "mismatched path".
  * G3 — PUT /product/receipts/{receipt_id}/metadata as ``view_only`` writes
    (200) although AC5 says "Csak megtekintés bármi írás → 403" and the role
    vocabulary (WRITE_ROLES = {owner, adult}) marks view_only read-only.
  * G4 — POST /product/receipts/upload as ``view_only``/``child`` stores the
    receipt (201) — the upload route has no ``can_write`` gate (only the
    review-items PATCH is gated).

GREEN (regression pins — must stay green after the gaps are fixed):
  * PATCH /product/receipts/{id}/workspace is already gated (403).
  * Expired sessions are rejected on /auth/session/me and /product/*.
  * A magic-link token created with ``household_id`` still derives a FRESH
    household from the email at verify (CRITICAL-1 — the id is ignored).
  * Accept with a wrong *invite_id* (same household) is already 404.

All flows run through the real FastAPI TestClient (HTTP-level, no mocks —
except the upload tests, which stub the OCR parser so the role gate itself
is what gets exercised rather than Tesseract).
"""
from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from app import api
from app.ocr import ConfidenceReceipt, ReceiptItem
from app.product_api import service
from app.product_service import Actor

client = TestClient(api.app)


def _parsed(confidence: float = 0.4) -> ConfidenceReceipt:
    return ConfidenceReceipt(
        merchant="Test Shop", date="2026-07-29",
        items=[ReceiptItem(name="Coffee", price=5.5)], total=5.5, tax=0.5,
        currency="USD", raw_text="TEST SHOP",
        confidence={"merchant": confidence, "total": confidence},
    )


def _magic_login(email: str) -> dict:
    """Full magic-link login flow — returns the session identity dict."""
    requested = client.post(
        "/auth/magic-link-request", json={"email": email}
    )
    assert requested.status_code == 201
    verified = client.post(
        "/auth/magic-link-verify",
        json={"token": requested.json()["token"]},
    )
    assert verified.status_code == 201
    return verified.json()


def _invite_member(owner_session: dict, email: str, role: str) -> dict:
    """Owner creates an invite; returns the accepted-member session."""
    headers = {"Authorization": f"Bearer {owner_session['session_token']}"}
    invite = client.post(
        f"/auth/households/{owner_session['household_id']}/invites",
        json={"email": email, "role": role},
        headers=headers,
    )
    assert invite.status_code == 201, invite.text
    accepted = client.post(
        f"/auth/households/{owner_session['household_id']}"
        f"/invites/{invite.json()['invite_id']}/accept",
        json={"token": invite.json()["token"]},
    )
    assert accepted.status_code == 201, accepted.text
    return accepted.json()


# ---------------------------------------------------------------------------
# RED G1 — invite role=owner must be rejected
# ---------------------------------------------------------------------------


def test_invite_role_owner_rejected() -> None:
    """docs/api.md: "``owner`` is rejected on invites — a household has
    exactly one owner".  Today the API accepts it (201)."""
    owner = _magic_login("g1-owner@pelda.hu")
    headers = {"Authorization": f"Bearer {owner['session_token']}"}
    response = client.post(
        f"/auth/households/{owner['household_id']}/invites",
        json={"email": "masodik-tulaj@pelda.hu", "role": "owner"},
        headers=headers,
    )
    assert response.status_code == 422, (
        f"invite role=owner must be rejected (422); got {response.status_code}"
    )


# ---------------------------------------------------------------------------
# RED G2 — wrong-household accept must be 404 AND must not burn the invite
# ---------------------------------------------------------------------------


def test_accept_wrong_household_path_is_404() -> None:
    """docs/api.md: "mismatched path: 404".  A valid invite token presented
    against a different household in the URL today yields 401."""
    owner = _magic_login("g2-owner@pelda.hu")
    household = owner["household_id"]
    headers = {"Authorization": f"Bearer {owner['session_token']}"}
    invite = client.post(
        f"/auth/households/{household}/invites",
        json={"email": "g2-tag@pelda.hu", "role": "adult"},
        headers=headers,
    ).json()
    response = client.post(
        f"/auth/households/nem-az-en-haztartasom"
        f"/invites/{invite['invite_id']}/accept",
        json={"token": invite["token"]},
    )
    assert response.status_code == 404, (
        f"mismatched household path must be 404; got {response.status_code}"
    )


def test_accept_wrong_household_path_does_not_burn_invite() -> None:
    """A 404 (wrong household in the URL) must NOT consume the single-use
    invite token — today the accept handler consumes the token *before*
    validating the path, so a typo'd link permanently invalidates a valid
    invite and the intended recipient can never join."""
    owner = _magic_login("g2b-owner@pelda.hu")
    household = owner["household_id"]
    headers = {"Authorization": f"Bearer {owner['session_token']}"}
    invite = client.post(
        f"/auth/households/{household}/invites",
        json={"email": "g2b-tag@pelda.hu", "role": "adult"},
        headers=headers,
    ).json()
    url = f"/auth/households/{household}/invites/{invite['invite_id']}/accept"

    wrong = client.post(
        f"/auth/households/nem-az-en-haztartasom"
        f"/invites/{invite['invite_id']}/accept",
        json={"token": invite["token"]},
    )
    assert wrong.status_code == 404, wrong.status_code

    # The same token must still work against the correct path.
    right = client.post(url, json={"token": invite["token"]})
    assert right.status_code == 201, (
        f"404 on a wrong path must not consume the invite; "
        f"correct-path accept got {right.status_code}"
    )


# ---------------------------------------------------------------------------
# RED G3 — view_only must not write receipt metadata
# ---------------------------------------------------------------------------


def test_view_only_cannot_put_receipt_metadata() -> None:
    """AC5: "Csak megtekintés bármi írás → 403".  PUT /product/receipts/
    {id}/metadata is a write and must be gated; today it returns 200."""
    owner = _magic_login("g3-owner@pelda.hu")
    household = owner["household_id"]
    viewer = _invite_member(owner, "g3-nezo@pelda.hu", "view_only")
    created = service.create_receipt(Actor(household, "owner"), _parsed(), "bolt.png")
    response = client.put(
        f"/product/receipts/{created['receipt_id']}/metadata",
        headers={"Authorization": f"Bearer {viewer['session_token']}"},
        json={"metadata": {"keszlet": "igen"}},
    )
    assert response.status_code == 403, (
        f"view_only PUT metadata must be 403; got {response.status_code}"
    )


def test_child_cannot_put_receipt_metadata() -> None:
    """Same write-gate for the child role (Gyermek / korlátozott tag)."""
    owner = _magic_login("g3b-owner@pelda.hu")
    household = owner["household_id"]
    child = _invite_member(owner, "g3b-gyerek@pelda.hu", "child")
    created = service.create_receipt(Actor(household, "owner"), _parsed(), "bolt.png")
    response = client.put(
        f"/product/receipts/{created['receipt_id']}/metadata",
        headers={"Authorization": f"Bearer {child['session_token']}"},
        json={"metadata": {"keszlet": "igen"}},
    )
    assert response.status_code == 403, (
        f"child PUT metadata must be 403; got {response.status_code}"
    )


# ---------------------------------------------------------------------------
# RED G4 — read-only roles must not upload receipts
# ---------------------------------------------------------------------------


def test_view_only_cannot_upload_receipt(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC5: read-only roles must not be able to add receipts either.
    The upload route has no can_write gate; with the OCR parser stubbed so
    the gate is what gets tested, a view_only session today stores a 201."""
    from app import product_api

    monkeypatch.setattr(product_api, "parse_receipt_with_confidence", lambda _b: _parsed())
    owner = _magic_login("g4-owner@pelda.hu")
    viewer = _invite_member(owner, "g4-nezo@pelda.hu", "view_only")
    response = client.post(
        "/product/receipts/upload",
        files={"file": ("bolt.png", io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 64), "image/png")},
        headers={"Authorization": f"Bearer {viewer['session_token']}"},
    )
    assert response.status_code == 403, (
        f"view_only upload must be 403; got {response.status_code}"
    )


def test_child_cannot_upload_receipt(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import product_api

    monkeypatch.setattr(product_api, "parse_receipt_with_confidence", lambda _b: _parsed())
    owner = _magic_login("g4b-owner@pelda.hu")
    child = _invite_member(owner, "g4b-gyerek@pelda.hu", "child")
    response = client.post(
        "/product/receipts/upload",
        files={"file": ("bolt.png", io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 64), "image/png")},
        headers={"Authorization": f"Bearer {child['session_token']}"},
    )
    assert response.status_code == 403, (
        f"child upload must be 403; got {response.status_code}"
    )


# ---------------------------------------------------------------------------
# GREEN — regression pins (must stay green once the gaps are fixed)
# ---------------------------------------------------------------------------


def test_adult_can_upload_receipt(monkeypatch: pytest.MonkeyPatch) -> None:
    """The write gate must not over-restrict: adult (Felnőtt tag) may upload."""
    from app import product_api

    monkeypatch.setattr(product_api, "parse_receipt_with_confidence", lambda _b: _parsed())
    owner = _magic_login("g-green-owner@pelda.hu")
    adult = _invite_member(owner, "g-green-felnott@pelda.hu", "adult")
    response = client.post(
        "/product/receipts/upload",
        files={"file": ("bolt.png", io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 64), "image/png")},
        headers={"Authorization": f"Bearer {adult['session_token']}"},
    )
    assert response.status_code == 201, (
        f"adult upload must stay allowed (201); got {response.status_code}"
    )


def test_view_only_patch_workspace_still_403() -> None:
    """Existing gate on PATCH /product/receipts/{id}/workspace (403) must
    survive any write-gate refactor."""
    owner = _magic_login("g-green2@pelda.hu")
    household = owner["household_id"]
    viewer = _invite_member(owner, "g-green2-nezo@pelda.hu", "view_only")
    created = service.create_receipt(Actor(household, "owner"), _parsed(), "bolt.png")
    response = client.patch(
        f"/product/receipts/{created['receipt_id']}/workspace",
        headers={
            "Authorization": f"Bearer {viewer['session_token']}",
            "If-Match": "1",
        },
        json={"status": "completed"},
    )
    assert response.status_code == 403, (
        f"view_only PATCH workspace must stay 403; got {response.status_code}"
    )


def test_expired_session_rejected_everywhere() -> None:
    """Sessions with a negative TTL must be rejected by session/me and by
    the bearer-token path of /product/*."""
    expired = service.create_session("lejart@pelda.hu", "hh-lejart", "owner", ttl_seconds=-1)
    me = client.post("/auth/session/me", json={"session_token": expired["session_token"]})
    assert me.status_code == 401
    members = client.get(
        "/product/members",
        headers={"Authorization": f"Bearer {expired['session_token']}"},
    )
    assert members.status_code == 401


def test_magic_link_with_household_binds_owner() -> None:
    """F1.3 review CRITICAL-1 pin: a caller-supplied ``household_id`` must
    NOT bind the session — the link always derives a fresh household from
    the email at verify time (no owner session can be minted for an
    arbitrary household)."""
    requested = client.post(
        "/auth/magic-link-request",
        json={"email": "kotott@pelda.hu", "household_id": "hh-kotott-1"},
    )
    assert requested.status_code == 201
    verified = client.post(
        "/auth/magic-link-verify",
        json={"token": requested.json()["token"]},
    )
    assert verified.status_code == 201
    identity = verified.json()
    assert identity["role"] == "owner"
    # Fresh household derived from the email — the supplied id is ignored.
    assert identity["household_id"].startswith("hh-")
    assert identity["household_id"] != "hh-kotott-1"


def test_accept_wrong_invite_id_same_household_is_404() -> None:
    """A wrong invite_id in the path (same household) is already 404 — pin
    it so the G2 fix (wrong household → 404) doesn't widen to a 401."""
    owner = _magic_login("g-green3@pelda.hu")
    household = owner["household_id"]
    headers = {"Authorization": f"Bearer {owner['session_token']}"}
    invite = client.post(
        f"/auth/households/{household}/invites",
        json={"email": "g-green3-tag@pelda.hu", "role": "adult"},
        headers=headers,
    ).json()
    response = client.post(
        f"/auth/households/{household}/invites/00000000-0000-0000-0000-000000000000/accept",
        json={"token": invite["token"]},
    )
    assert response.status_code == 404, (
        f"wrong invite_id must stay 404; got {response.status_code}"
    )
