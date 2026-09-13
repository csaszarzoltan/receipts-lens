"""RED (pre-development) acceptance tests for FEAT-033B proaktiv insight keZbesites.

SPEC: docs/specs/SPEC-033B-proaktiv-insight-kiterjesztes.md (commit 4b77cc7),
REQ-033B-01..09, AC-033B-01..09.
Planned contract (NOT implemented yet -- these tests must run RED):
  POST /api/v1/insights/evaluate {tenant_id}
    -> 200 {cards: [{insight_id, title, explanation, confidence, deep_link}]}
  GET /api/v1/insights/cards -> 200 {cards: [...]} (sajat tenant kartyai)
  POST /api/v1/insights/cards/{id}/feedback {verdict: 'false_positive'} -> 200
  POST /api/v1/insights/preferences {unsubscribed: true} -> 200

Fuggoseg: FEAT-049 chat EL (POST /api/v1/chat/query) -- a melylink celja
letezik, a kartyak deep_link-je ra mutat az insight kontextusaval.

Role boundary: tests/** only -- no app/** changes in this task.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)

EVALUATE_URL = "/api/v1/insights/evaluate"
CARDS_URL = "/api/v1/insights/cards"
PREFS_URL = "/api/v1/insights/preferences"
CHAT_URL = "/api/v1/chat/query"

TENANT_A = "red033b-tenant-a"
TENANT_B = "red033b-tenant-b"
TENANT_QUIET = "red033b-tenant-quiet"  # kuszob alatti jelek -> 0 kartya
HEADERS_A = {"X-Tenant-ID": TENANT_A, "X-Role": "member"}
HEADERS_B = {"X-Tenant-ID": TENANT_B, "X-Role": "member"}
HEADERS_QUIET = {"X-Tenant-ID": TENANT_QUIET, "X-Role": "member"}

CARD_KEYS = ("insight_id", "title", "explanation", "confidence", "deep_link")
BUDGET_KEYS = ("budget_context", "frame_context", "budget", "frame")


def _evaluate(tenant_id: str = TENANT_A, headers: dict | None = None):
    hdrs = dict(HEADERS_A) if headers is None else headers
    return client.post(EVALUATE_URL, json={"tenant_id": tenant_id}, headers=hdrs)


def _cards(headers: dict):
    return client.get(CARDS_URL, headers=headers)


def _assert_card_shape(card: dict) -> dict:
    for key in CARD_KEYS:
        assert key in card, f"card missing key {key!r}: {card!r}"
    assert str(card["insight_id"]).strip()
    assert str(card["title"]).strip()
    assert str(card["explanation"]).strip()
    assert isinstance(card["confidence"], (int, float))
    assert str(card["deep_link"]).strip()
    return card


@pytest.mark.test_id("TEST-033B-001")
@pytest.mark.requirements("REQ-033B-01")
@pytest.mark.scenario("AC-033B-01")
def test_insight_routes_registered():
    """Planned insight routes exist in OpenAPI (fails until GREEN adds them)."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    for url in (EVALUATE_URL, CARDS_URL, PREFS_URL):
        assert url in paths, f"planned route {url} missing from OpenAPI"


@pytest.mark.test_id("TEST-033B-002")
@pytest.mark.requirements("REQ-033B-01")
@pytest.mark.scenario("AC-033B-01")
def test_evaluate_returns_candidate_cards():
    """Scheduled evaluation yields candidate cards for above-threshold signals."""
    resp = _evaluate()
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}"
    body = resp.json()
    assert isinstance(body["cards"], list) and len(body["cards"]) >= 1
    for card in body["cards"]:
        _assert_card_shape(card)


@pytest.mark.test_id("TEST-033B-003")
@pytest.mark.requirements("REQ-033B-02")
@pytest.mark.scenario("AC-033B-02")
def test_card_carries_budget_context():
    """Card shows FEAT-012 frame context for near/over-limit categories."""
    resp = _evaluate()
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}"
    cards = resp.json()["cards"]
    assert len(cards) >= 1
    card = _assert_card_shape(cards[0])
    assert any(k in card for k in BUDGET_KEYS), f"no budget context: {card!r}"


@pytest.mark.test_id("TEST-033B-004")
@pytest.mark.requirements("REQ-033B-03")
@pytest.mark.scenario("AC-033B-03")
def test_evaluated_card_visible_via_cards_channel():
    """Evaluated card is delivered through the cards channel (FEAT-026 panel)."""
    eval_resp = _evaluate()
    assert eval_resp.status_code == 200, f"expected 200, got {eval_resp.status_code}"
    first_id = _assert_card_shape(eval_resp.json()["cards"][0])["insight_id"]
    resp = _cards(HEADERS_A)
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}"
    ids = [_assert_card_shape(c)["insight_id"] for c in resp.json()["cards"]]
    assert first_id in ids


@pytest.mark.test_id("TEST-033B-005")
@pytest.mark.requirements("REQ-033B-03")
@pytest.mark.requirements("REQ-033B-04")
@pytest.mark.scenario("AC-033B-04")
def test_card_deep_link_points_to_chat():
    """Card deep-link opens FEAT-049 chat with the insight context."""
    resp = _evaluate()
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}"
    card = _assert_card_shape(resp.json()["cards"][0])
    assert CHAT_URL in card["deep_link"], f"deep_link misses chat: {card!r}"
    assert str(card["insight_id"]) in card["deep_link"], f"no insight ctx: {card!r}"


@pytest.mark.test_id("TEST-033B-006")
@pytest.mark.requirements("REQ-033B-05")
@pytest.mark.scenario("AC-033B-05")
def test_below_threshold_signal_yields_no_card():
    """Below-threshold signal -> 0 cards (quiet branch)."""
    resp = _evaluate(TENANT_QUIET, HEADERS_QUIET)
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}"
    assert resp.json()["cards"] == []


@pytest.mark.test_id("TEST-033B-007")
@pytest.mark.requirements("REQ-033B-05")
@pytest.mark.scenario("AC-033B-05")
def test_card_explanation_present():
    """Card explains the signal (REQ-033-02: what baseline it is unusual vs)."""
    resp = _evaluate()
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}"
    card = _assert_card_shape(resp.json()["cards"][0])
    assert len(card["explanation"].strip()) >= 20, f"explanation too thin: {card!r}"


@pytest.mark.test_id("TEST-033B-008")
@pytest.mark.requirements("REQ-033B-06")
@pytest.mark.scenario("AC-033B-06")
def test_false_positive_feedback_accepted():
    """'Teves jelzes' feedback on a card is accepted and stored."""
    eval_resp = _evaluate()
    assert eval_resp.status_code == 200, f"expected 200, got {eval_resp.status_code}"
    card_id = _assert_card_shape(eval_resp.json()["cards"][0])["insight_id"]
    resp = client.post(
        f"{CARDS_URL}/{card_id}/feedback",
        json={"verdict": "false_positive"},
        headers=HEADERS_A,
    )
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}"


@pytest.mark.test_id("TEST-033B-009")
@pytest.mark.requirements("REQ-033B-06")
@pytest.mark.scenario("AC-033B-06")
def test_unsubscribed_tenant_gets_no_new_card():
    """After unsubscribe, scheduled evaluation delivers no new card."""
    eval_resp = _evaluate()
    assert eval_resp.status_code == 200, f"expected 200, got {eval_resp.status_code}"
    assert len(eval_resp.json()["cards"]) >= 1
    pref_resp = client.post(
        PREFS_URL, json={"unsubscribed": True}, headers=HEADERS_A
    )
    assert pref_resp.status_code == 200, f"expected 200, got {pref_resp.status_code}"
    again = _evaluate()
    assert again.status_code == 200, f"expected 200, got {again.status_code}"
    assert again.json()["cards"] == []


@pytest.mark.test_id("TEST-033B-010")
@pytest.mark.requirements("REQ-033B-07")
@pytest.mark.scenario("AC-033B-07")
def test_cross_tenant_cards_not_visible():
    """Tenant B never sees tenant A cards (no cross-household leak)."""
    eval_resp = _evaluate(TENANT_A, HEADERS_A)
    assert eval_resp.status_code == 200, f"expected 200, got {eval_resp.status_code}"
    ids_a = {_assert_card_shape(c)["insight_id"] for c in eval_resp.json()["cards"]}
    assert len(ids_a) >= 1
    resp = _cards(HEADERS_B)
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}"
    ids_b = {_assert_card_shape(c)["insight_id"] for c in resp.json()["cards"]}
    assert ids_a.isdisjoint(ids_b), f"tenant leak: {ids_a & ids_b!r}"


@pytest.mark.test_id("TEST-033B-011")
@pytest.mark.requirements("REQ-033B-07")
@pytest.mark.scenario("AC-033B-07")
def test_missing_tenant_unauthorized():
    """No tenant identity at all -> 401/403, never data."""
    resp = client.post(EVALUATE_URL, json={})
    assert resp.status_code in (401, 403), f"expected 401/403, got {resp.status_code}"


@pytest.mark.test_id("TEST-033B-012")
@pytest.mark.requirements("REQ-033B-08")
@pytest.mark.scenario("AC-033B-08")
def test_failed_evaluation_never_shows_half_card():
    """Failed evaluation is a retryable error, never a half card as success."""
    resp = _evaluate()
    if resp.status_code == 200:
        body = resp.json()
        assert isinstance(body["cards"], list)
        for card in body["cards"]:
            _assert_card_shape(card)
    elif resp.status_code == 503:
        body = resp.json()
        assert body.get("retryable") is True
        assert body.get("error")
    else:
        pytest.fail(f"failure surfaced as HTTP {resp.status_code}, expected 200/503")


@pytest.mark.test_id("TEST-033B-013")
@pytest.mark.requirements("REQ-033B-09")
@pytest.mark.scenario("AC-033B-09")
def test_repeated_signal_no_duplicate_card():
    """Same signal re-evaluated -> 1 card, signal-id dedup, no duplication."""
    first = _evaluate()
    assert first.status_code == 200, f"expected 200, got {first.status_code}"
    second = _evaluate()
    assert second.status_code == 200, f"expected 200, got {second.status_code}"
    ids = [
        _assert_card_shape(c)["insight_id"]
        for c in first.json()["cards"] + second.json()["cards"]
    ]
    assert len(ids) >= 1
    assert len(set(ids)) == len(ids), f"duplicate cards: {ids!r}"
    stored = _cards(HEADERS_A)
    assert stored.status_code == 200, f"expected 200, got {stored.status_code}"
    stored_ids = [_assert_card_shape(c)["insight_id"] for c in stored.json()["cards"]]
    assert len(set(stored_ids)) == len(stored_ids), f"duplicate stored: {stored_ids!r}"
