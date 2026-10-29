"""Engine and spec behaviour for the v2 feature APIs (FEAT-038 .. FEAT-048)."""
from __future__ import annotations

import json
import sqlite3

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import feature_core
from app.feature_core import (
    CommandRequest,
    CreateRequest,
    DomainError,
    FeatureService,
    Hub,
    init_hub,
    make_router,
)
from app.feature_specs import SPECS, split_shares

TENANT = "tenant-a"
OTHER = "tenant-b"
KEY_PREFIX = "idem-key-"


@pytest.fixture
def hub():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE receipts(receipt_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, payload TEXT NOT NULL,"
        " original_payload TEXT NOT NULL, status TEXT NOT NULL, version INTEGER NOT NULL, created_at TEXT NOT NULL)"
    )
    return Hub(conn)


def add_receipt(hub_: Hub, tenant: str, receipt_id: str, total=50.0, status="completed"):
    hub_.conn.execute(
        "INSERT INTO receipts VALUES(?,?,?,?,?,?,?)",
        (receipt_id, tenant, json.dumps({"total": total, "currency": "HUF"}), "{}", status, 1, "2026-01-01"),
    )


_counter = iter(range(10**6))


def idem() -> str:
    return f"{KEY_PREFIX}{next(_counter):08d}"


def create(svc: FeatureService, tenant=TENANT, role="member", name="item", payload=None, rev=0):
    return svc.create(tenant, role, idem(), CreateRequest(client_reference=name, payload=payload or {}, expected_revision=rev))


def act(svc: FeatureService, item: dict, action: str, payload=None, reason=None, tenant=TENANT, role="admin"):
    return svc.command(
        tenant, role, item["id"], idem(),
        CommandRequest(action=action, expected_revision=item["revision"], payload=payload or {}, reason=reason),
    )


def svc_for(hub_: Hub, key: str) -> FeatureService:
    return FeatureService(SPECS[key], hub_)


def error_code(fn) -> str:
    with pytest.raises(DomainError) as exc:
        fn()
    return exc.value.code


# ---------------------------------------------------------------------------
# Spec structure
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", sorted(SPECS))
def test_every_status_is_reachable_and_every_target_is_declared(key):
    spec = SPECS[key]
    statuses = set(spec.statuses)
    assert spec.initial in statuses
    seen, frontier = {spec.initial}, [spec.initial]
    while frontier:
        current = frontier.pop()
        for action in spec.actions:
            if current not in action.sources:
                continue
            for target in action.targets:
                assert target in statuses, f"{key}.{action.name} targets unknown status {target}"
                if target not in seen:
                    seen.add(target)
                    frontier.append(target)
    assert seen == statuses, f"unreachable statuses in {key}: {statuses - seen}"


@pytest.mark.parametrize("key", sorted(SPECS))
def test_action_names_are_unique(key):
    names = [a.name for a in SPECS[key].actions]
    assert len(names) == len(set(names))


# ---------------------------------------------------------------------------
# Engine: idempotency, revisions, transitions, roles, tenancy
# ---------------------------------------------------------------------------

def test_create_then_same_key_same_body_returns_same_item(hub):
    svc = svc_for(hub, "missing_receipts")
    key = idem()
    body = CreateRequest(client_reference="a", payload={"merchant": "Bolt", "amount": 10})
    first = svc.create(TENANT, "member", key, body)
    second = svc.create(TENANT, "member", key, body)
    assert first["id"] == second["id"]
    assert len(svc.list(TENANT, "member")) == 1


def test_same_key_different_body_is_a_conflict(hub):
    svc = svc_for(hub, "missing_receipts")
    key = idem()
    svc.create(TENANT, "member", key, CreateRequest(client_reference="a", payload={"merchant": "Bolt", "amount": 10}))
    code = error_code(lambda: svc.create(
        TENANT, "member", key, CreateRequest(client_reference="b", payload={"merchant": "Bolt", "amount": 10})))
    assert code == "IDEMPOTENCY_CONFLICT"


def test_stale_revision_is_rejected(hub):
    svc = svc_for(hub, "missing_receipts")
    item = create(svc, payload={"merchant": "Bolt", "amount": 10})
    act(svc, item, "assign", payload={"assignee": "Anna"})
    code = error_code(lambda: svc.command(
        TENANT, "admin", item["id"], idem(), CommandRequest(action="assign", expected_revision=0, payload={"assignee": "Béla"})))
    assert code == "STALE_REVISION"


def test_action_from_wrong_status_is_rejected(hub):
    svc = svc_for(hub, "reconciliation")
    item = create(svc, payload={"bank_reference": "B1", "card_reference": "C1"})
    code = error_code(lambda: act(svc, item, "reopen"))
    assert code == "INVALID_TRANSITION"


def test_unknown_action_is_rejected(hub):
    svc = svc_for(hub, "reconciliation")
    item = create(svc, payload={"bank_reference": "B1"})
    code = error_code(lambda: act(svc, item, "teleport"))
    assert code == "UNKNOWN_ACTION"


def test_role_gate_blocks_non_reviewers(hub):
    svc = svc_for(hub, "cost_splits")
    item = create(svc, payload={"total": 30, "participants": "Anna, Béla"})
    item = act(svc, item, "submit")
    assert error_code(lambda: act(svc, item, "approve", role="member")) == "FORBIDDEN"
    assert act(svc, item, "approve", role="admin")["status"] == "APPROVED"


def test_items_are_tenant_isolated(hub):
    svc = svc_for(hub, "missing_receipts")
    item = create(svc, tenant=TENANT, payload={"merchant": "Bolt", "amount": 10})
    assert svc.list(OTHER, "admin") == []
    assert error_code(lambda: svc.get(OTHER, "admin", item["id"])) == "NOT_FOUND"
    assert error_code(lambda: act(svc, item, "assign", payload={"assignee": "x"}, tenant=OTHER)) == "NOT_FOUND"


def test_payload_keys_outside_the_allowlist_are_dropped(hub):
    svc = svc_for(hub, "missing_receipts")
    item = create(svc, payload={"merchant": "Bolt", "amount": 10, "status": "RESOLVED", "evil": "x"})
    assert "evil" not in item["data"]
    assert item["status"] == "OPEN"


def test_command_payload_only_writes_the_declared_input(hub):
    svc = svc_for(hub, "missing_receipts")
    item = create(svc, payload={"merchant": "Bolt", "amount": 10})
    done = act(svc, item, "assign", payload={"assignee": "Anna", "amount": 999})
    assert done["data"]["assignee"] == "Anna"
    assert done["data"]["amount"] == 10


def test_actions_listed_on_item_follow_status_and_role(hub):
    svc = svc_for(hub, "cost_splits")
    item = create(svc, payload={"total": 30, "participants": "Anna, Béla"})
    names = {a["action"] for a in svc.get(TENANT, "member", item["id"])["actions"]}
    assert "approve" not in names
    assert "submit" in names
    item = act(svc, item, "submit")
    admin_names = {a["action"] for a in svc.get(TENANT, "admin", item["id"])["actions"]}
    member_names = {a["action"] for a in svc.get(TENANT, "member", item["id"])["actions"]}
    assert "approve" in admin_names and "approve" not in member_names


# ---------------------------------------------------------------------------
# Per-feature validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key,payload,message", [
    ("reconciliation", {}, "bank_reference or card_reference"),
    ("missing_receipts", {"amount": 10}, "merchant is required"),
    ("missing_receipts", {"merchant": "Bolt", "amount": 0}, "amount must be greater than zero"),
    ("cost_splits", {"total": 10, "participants": "Anna"}, "at least two participants"),
    ("cost_splits", {"total": 0, "participants": "Anna, Béla"}, "total must be greater than zero"),
    ("savings_goals", {"target_amount": 100, "currency": "HUFF"}, "3-letter"),
    ("price_tracking", {"watch_price": 100}, "product is required"),
    ("period_close", {"period": "2026-13"}, "YYYY-MM"),
    ("offline_sync", {}, "device is required"),
    ("data_quality", {}, "issue_type is required"),
])
def test_create_rejects_invalid_payloads(hub, key, payload, message):
    svc = svc_for(hub, key)
    with pytest.raises(DomainError) as exc:
        create(svc, payload=payload)
    assert exc.value.code == "VALIDATION_FAILED"
    assert message in exc.value.message


def test_non_numeric_amount_is_a_validation_error(hub):
    svc = svc_for(hub, "missing_receipts")
    with pytest.raises(DomainError) as exc:
        create(svc, payload={"merchant": "Bolt", "amount": "abc"})
    assert exc.value.code == "VALIDATION_FAILED"
    assert "amount must be a number" in exc.value.message


def test_required_action_input_is_enforced(hub):
    svc = svc_for(hub, "missing_receipts")
    item = create(svc, payload={"merchant": "Bolt", "amount": 10})
    assert error_code(lambda: act(svc, item, "assign")) == "VALIDATION_FAILED"


# ---------------------------------------------------------------------------
# Domain rules
# ---------------------------------------------------------------------------

def test_cost_split_shares_sum_to_total_with_remainder_cents_first(hub):
    shares = split_shares({"total": 100.00, "participants": "Anna, Béla, Cili"})
    assert [s["amount"] for s in shares] == [33.34, 33.33, 33.33]
    assert round(sum(s["amount"] for s in shares), 2) == 100.00


def test_cost_split_deduplicates_participants_case_insensitively(hub):
    assert [s["name"] for s in split_shares({"total": 10, "participants": "Anna, anna, Béla"})] == ["Anna", "Béla"]


def test_savings_progress_and_achievement(hub):
    svc = svc_for(hub, "savings_goals")
    item = create(svc, payload={"target_amount": 100, "currency": "HUF"})
    item = act(svc, act(svc, item, "activate"), "contribute", payload={"amount": 40})
    assert item["data"]["progress"] == 0.4 and item["data"]["remaining"] == 60.0
    assert item["status"] == "ON_TRACK"
    item = act(svc, item, "contribute", payload={"amount": 60})
    assert item["status"] == "ACHIEVED" and item["data"]["progress"] == 1.0


def test_price_observation_below_watch_needs_review(hub):
    svc = svc_for(hub, "price_tracking")
    item = act(svc, create(svc, payload={"product": "Tej", "watch_price": 300}), "track")
    item = act(svc, item, "observe", payload={"observed_price": 320})
    assert item["status"] == "TRACKED" and item["data"]["below_watch"] is False
    item = act(svc, item, "observe", payload={"observed_price": 280})
    assert item["status"] == "NEEDS_REVIEW" and item["data"]["below_watch"] is True
    assert item["data"]["last_price"] == 280


def test_refund_cannot_exceed_receipt_total(hub):
    add_receipt(hub, TENANT, "r-1", total=50.0)
    svc = svc_for(hub, "refunds")
    item = create(svc, payload={"merchant": "Bolt", "amount": 80})
    with pytest.raises(DomainError) as exc:
        act(svc, item, "match", payload={"original_receipt": "r-1"})
    assert exc.value.code == "VALIDATION_FAILED" and "larger than the receipt total" in exc.value.message


def test_partial_refund_must_stay_below_total(hub):
    add_receipt(hub, TENANT, "r-2", total=50.0)
    svc = svc_for(hub, "refunds")
    item = create(svc, payload={"merchant": "Bolt", "amount": 50})
    assert error_code(lambda: act(svc, item, "partial", payload={"original_receipt": "r-2"})) == "VALIDATION_FAILED"


def test_refund_match_fails_for_unknown_receipt(hub):
    svc = svc_for(hub, "refunds")
    item = create(svc, payload={"merchant": "Bolt", "amount": 5})
    assert error_code(lambda: act(svc, item, "match", payload={"original_receipt": "nope"})) == "VALIDATION_FAILED"


def test_missing_receipt_resolution_needs_an_existing_receipt(hub):
    add_receipt(hub, TENANT, "r-3")
    svc = svc_for(hub, "missing_receipts")
    item = create(svc, payload={"merchant": "Bolt", "amount": 10})
    assert error_code(lambda: act(svc, item, "resolve", payload={"receipt": "ghost"})) == "VALIDATION_FAILED"
    assert act(svc, item, "resolve", payload={"receipt": "r-3"})["status"] == "RESOLVED"


def test_quality_task_with_unknown_receipt_is_rejected(hub):
    svc = svc_for(hub, "data_quality")
    with pytest.raises(DomainError):
        create(svc, payload={"issue_type": "amount", "receipt": "ghost"})


def test_period_close_blocked_by_open_quality_task_then_locked(hub):
    quality = svc_for(hub, "data_quality")
    period = svc_for(hub, "period_close")
    task = create(quality, payload={"issue_type": "amount", "period": "2026-08"})
    item = create(period, payload={"period": "2026-08"})
    item = act(period, item, "precheck")
    assert item["status"] == "BLOCKED" and item["data"]["open_quality_tasks"] == 1
    assert error_code(lambda: act(period, item, "close")) == "INVALID_TRANSITION"

    act(quality, task, "resolve", payload={"note": "fixed"})
    item = act(period, item, "precheck")
    assert item["status"] == "READY_TO_CLOSE"
    item = act(period, item, "close", role="accountant")
    assert item["status"] == "CLOSED"

    locked = {a["action"] for a in period.get(TENANT, "admin", item["id"])["actions"]}
    assert locked == {"request_reopen"}, "a closed period accepts no other change"
    item = act(period, item, "request_reopen", reason="late invoice")
    assert error_code(lambda: act(period, item, "approve_reopen", role="member")) == "FORBIDDEN"
    item = act(period, item, "approve_reopen", role="admin")
    assert item["status"] == "REOPENED"


def test_period_close_ignores_quality_tasks_from_other_periods(hub):
    quality = svc_for(hub, "data_quality")
    period = svc_for(hub, "period_close")
    create(quality, payload={"issue_type": "amount", "period": "2026-07"})
    item = act(period, create(period, payload={"period": "2026-08"}), "precheck")
    assert item["status"] == "READY_TO_CLOSE"


def test_offline_sync_conflict_and_success_paths(hub):
    svc = svc_for(hub, "offline_sync")
    item = create(svc, payload={"device": "phone-1"})
    item = act(svc, act(svc, act(svc, item, "queue"), "start_upload"), "process")
    conflicted = act(svc, item, "sync", payload={"base_revision": 7})
    assert conflicted["status"] == "CONFLICT"
    retried = act(svc, conflicted, "retry")
    item = act(svc, act(svc, act(svc, retried, "start_upload"), "process"), "sync", payload={"base_revision": 0})
    assert item["status"] == "SYNCED" and item["data"]["server_revision"] == 1


def test_mobile_capture_follows_its_receipt(hub):
    add_receipt(hub, TENANT, "r-4", status="needs_review")
    add_receipt(hub, TENANT, "r-5", status="completed")
    svc = svc_for(hub, "mobile_receipts")
    item = act(svc, create(svc), "attach", payload={"receipt": "r-4"})
    assert item["status"] == "PREVIEW"
    assert act(svc, item, "sync")["status"] == "NEEDS_REVIEW"
    later = act(svc, act(svc, create(svc), "attach", payload={"receipt": "r-5"}), "sync")
    assert later["status"] == "APPROVED"


def test_mobile_approval_needs_a_reviewer(hub):
    add_receipt(hub, TENANT, "r-6", status="needs_review")
    svc = svc_for(hub, "mobile_receipts")
    item = act(svc, act(svc, create(svc), "attach", payload={"receipt": "r-6"}), "sync")
    assert error_code(lambda: act(svc, item, "approve", role="member")) == "FORBIDDEN"
    assert act(svc, item, "approve", role="accountant")["status"] == "APPROVED"


# ---------------------------------------------------------------------------
# HTTP layer
# ---------------------------------------------------------------------------

SESSIONS = {"token-admin": {"tenant_id": TENANT, "role": "admin"},
            "token-child": {"tenant_id": TENANT, "role": "child"}}


def fake_resolve(token: str) -> dict:
    if token not in SESSIONS:
        raise KeyError(token)
    return SESSIONS[token]


@pytest.fixture
def client(hub):
    init_hub(hub.conn, resolve_session=fake_resolve, is_production=lambda: False)
    app = FastAPI()
    app.include_router(make_router(SPECS["missing_receipts"]))
    return TestClient(app)


def headers(tenant=TENANT, role="admin", key=None, token="token-admin"):
    h = {"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant, "X-Role": role}
    if key:
        h["Idempotency-Key"] = key
    return h


def test_http_requires_authentication(client):
    assert client.get("/api/v2/missing-receipts").status_code == 401


def test_http_rejects_unknown_role_without_session(client):
    response = client.get("/api/v2/missing-receipts", headers={"X-Tenant-ID": TENANT, "X-Role": "guest"})
    assert response.status_code == 403


def test_http_session_decides_tenant_and_role_not_headers(client):
    """A client cannot pick another tenant by sending X-Tenant-ID next to a session token."""
    key = idem()
    created = client.post("/api/v2/missing-receipts", headers=headers(tenant=OTHER, key=key),
                          json={"client_reference": "mine", "payload": {"merchant": "Bolt", "amount": 1}})
    assert created.status_code == 201
    # The header names OTHER, but the session belongs to TENANT, so TENANT's item is what comes back.
    spoofed = client.get("/api/v2/missing-receipts", headers=headers(tenant=OTHER))
    assert [i["client_reference"] for i in spoofed.json()["items"]] == ["mine"]
    # Without a session, headers are trusted only outside production, and OTHER has no items.
    headers_only = client.get("/api/v2/missing-receipts", headers={"X-Tenant-ID": OTHER, "X-Role": "admin"})
    assert headers_only.json()["items"] == []


def test_http_rejects_unknown_or_expired_session(client):
    assert client.get("/api/v2/missing-receipts", headers=headers(token="expired")).status_code == 401


def test_http_child_can_read_but_not_write(client):
    key = idem()
    response = client.post("/api/v2/missing-receipts", headers=headers(token="token-child", key=key),
                           json={"client_reference": "x", "payload": {"merchant": "Bolt", "amount": 1}})
    assert response.status_code == 403 and response.json()["code"] == "FORBIDDEN"
    assert client.get("/api/v2/missing-receipts", headers=headers(token="token-child")).status_code == 200


def test_production_requires_a_session(hub):
    init_hub(hub.conn, resolve_session=fake_resolve, is_production=lambda: True)
    app = FastAPI()
    app.include_router(make_router(SPECS["missing_receipts"]))
    client_prod = TestClient(app)
    assert client_prod.get("/api/v2/missing-receipts", headers={"X-Tenant-ID": TENANT, "X-Role": "admin"}).status_code == 401
    init_hub(hub.conn, resolve_session=fake_resolve, is_production=lambda: False)


def test_http_create_requires_idempotency_key(client):
    response = client.post("/api/v2/missing-receipts", headers=headers(), json={"client_reference": "x"})
    assert response.status_code == 422


def test_http_create_and_action_round_trip(client):
    key = idem()
    created = client.post("/api/v2/missing-receipts", headers=headers(key=key),
                          json={"client_reference": "Hiányzó", "payload": {"merchant": "Bolt", "amount": 10}})
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "OPEN" and body["actions"]
    again = client.post("/api/v2/missing-receipts", headers=headers(key=key),
                        json={"client_reference": "Hiányzó", "payload": {"merchant": "Bolt", "amount": 10}})
    assert again.json()["id"] == body["id"]
    done = client.patch(f"/api/v2/missing-receipts/{body['id']}", headers=headers(key=idem()),
                        json={"action": "assign", "expected_revision": 0, "payload": {"assignee": "Anna"}})
    assert done.status_code == 200 and done.json()["status"] == "ASSIGNED"
    bad = client.patch(f"/api/v2/missing-receipts/{body['id']}", headers=headers(key=idem()),
                       json={"action": "reopen", "expected_revision": 1})
    assert bad.status_code == 409
    assert bad.json()["code"] == "INVALID_TRANSITION"
    assert bad.headers["content-type"].startswith("application/problem+json")


def test_http_unknown_item_is_404(client):
    response = client.get("/api/v2/missing-receipts/nope", headers=headers())
    assert response.status_code == 404 and response.json()["code"] == "NOT_FOUND"


def test_hub_falls_back_to_isolated_store_without_product_db():
    feature_core._hub = None
    assert isinstance(feature_core.hub(), Hub)
    feature_core._hub = None


def test_view_only_role_cannot_run_actions(hub):
    svc = svc_for(hub, "missing_receipts")
    item = create(svc, payload={"merchant": "Bolt", "amount": 10})
    assert error_code(lambda: act(svc, item, "assign", payload={"assignee": "x"}, role="view_only")) == "FORBIDDEN"


def test_actions_report_blank_requirements_but_not_their_own_input(hub):
    recon = svc_for(hub, "reconciliation")
    item = create(recon, payload={"bank_reference": "B1"})
    confirm = next(a for a in recon.get(TENANT, "admin", item["id"])["actions"] if a["action"] == "confirm")
    assert confirm["missing"] == ["card_reference"]
    missing = svc_for(hub, "missing_receipts")
    assign_item = create(missing, payload={"merchant": "Bolt", "amount": 10})
    assign = next(a for a in missing.get(TENANT, "admin", assign_item["id"])["actions"] if a["action"] == "assign")
    assert assign["missing"] == [], "assignee is the input the user supplies, so it is not reported missing"
