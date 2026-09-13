"""RED (pre-development) acceptance tests for FEAT-049 AI ol Hanover Park, IL 60133-chat.

SPEC: docs/specs/SPEC-049-ai-olvoso-chat.md (commit be36c79), REQ-049-01..08.
Planned contract (NOT implemented yet -- these tests must run RED):
  POST /api/v1/chat/query {question, tenant_id}
  -> 200 {answer, sources: [{receipt_id, amount}], query_debug}

Note: SPEC-049 SS10 sketches POST /api/v2/chat/ask {question, locale} +
X-Tenant-ID header; this RED pins the task-body contract above (body-carried
tenant_id, query_debug). The GREEN implementer reconciles both (SPEC-GAP).

Role boundary: tests/** only -- no app/** changes in this task.
"""

from __future__ import annotations

import concurrent.futures as _cf

import pytest
from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)

CHAT_URL = "/api/v1/chat/query"
TENANT_A = "red049-tenant-a"
TENANT_B = "red049-tenant-b"
TENANT_EMPTY = "red049-tenant-empty"
HEADERS_A = {"X-Tenant-ID": TENANT_A, "X-Role": "member"}

# In-test seed ledger: the GREEN implementation is expected to answer the
# question bank from tenant-scoped receipt data. Expected figures below are
# derived deterministically from this ledger (no LLM arithmetic allowed).
SEED_A = [
    {"receipt_id": "seed-a-001", "merchant": "Tesco", "category": "food", "amount": 12500.0, "date": "2026-07-03"},
    {"receipt_id": "seed-a-002", "merchant": "Spar", "category": "food", "amount": 8300.0, "date": "2026-07-11"},
    {"receipt_id": "seed-a-003", "merchant": "MOL", "category": "transport", "amount": 15000.0, "date": "2026-07-15"},
    {"receipt_id": "seed-a-004", "merchant": "Tesco", "category": "food", "amount": 4200.0, "date": "2026-08-02"},
    {"receipt_id": "seed-a-005", "merchant": "Libri", "category": "culture", "amount": 6990.0, "date": "2026-08-09"},
]
# Overlapping merchant/amounts on the OTHER tenant (leak detector).
SEED_B = [
    {"receipt_id": "seed-b-001", "merchant": "Tesco", "category": "food", "amount": 99999.0, "date": "2026-07-05"},
]

JULY_FOOD = 12500.0 + 8300.0  # 20800.0
AUGUST_TOTAL = 4200.0 + 6990.0  # 11190.0
TESCO_TOTAL = 12500.0 + 4200.0  # 16700.0
RECEIPT_COUNT = 5
AVERAGE = sum(r["amount"] for r in SEED_A) / len(SEED_A)  # 9998.0

# 10-item HU/EN question bank (SPEC SS11 AC-049-01): (qid, question, fragments
# that must appear verbatim in the deterministic answer).
QUESTION_BANK = [
    ("Q01", "Mennyit k\u00f6lt\u00f6ttem \u00e9telre j\u00faliusban?", ["20800"]),
    ("Q02", "How much did I spend on food in July?", ["20800"]),
    ("Q03", "Mennyi volt a legnagyobb nyugt\u00e1m j\u00faliusban?", ["15000"]),
    ("Q04", "Break down my July spending by merchant.", ["12500", "8300", "15000"]),
    ("Q05", "Mennyit k\u00f6lt\u00f6ttem k\u00f6zleked\u00e9sre?", ["15000"]),
    ("Q06", "What is my total spending in August?", ["11190"]),
    ("Q07", "H\u00e1ny nyugt\u00e1m van \u00f6sszesen?", ["5"]),
    ("Q08", "What was my average receipt amount?", ["9998"]),
    ("Q09", "Mennyit k\u00f6lt\u00f6ttem a Tesc\u00f3ban?", ["16700"]),
    ("Q10", "Which merchant did I spend the most with?", ["MOL", "15000"]),
]

WRITE_KEYWORDS = ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE")


def _post(question: str, tenant_id: str = TENANT_A, headers: dict | None = None):
    hdrs = dict(HEADERS_A) if headers is None else headers
    return client.post(CHAT_URL, json={"question": question, "tenant_id": tenant_id}, headers=hdrs)


@pytest.mark.test_id("TEST-049-001")
@pytest.mark.requirements("REQ-049-01")
@pytest.mark.scenario("AC-049-01")
def test_chat_endpoint_registered():
    """Planned contract route exists in OpenAPI (fails until GREEN adds it)."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    assert CHAT_URL in paths
    assert "post" in paths[CHAT_URL]


@pytest.mark.test_id("TEST-049-002")
@pytest.mark.requirements("REQ-049-01")
@pytest.mark.requirements("REQ-049-04")
@pytest.mark.scenario("AC-049-01")
@pytest.mark.parametrize("qid,question,fragments", QUESTION_BANK, ids=[q[0] for q in QUESTION_BANK])
def test_question_bank_deterministic_match(qid: str, question: str, fragments: list):
    """10 HU/EN questions: answer matches deterministic DB aggregation."""
    resp = _post(question)
    assert resp.status_code == 200, f"{qid}: expected 200, got {resp.status_code}"
    body = resp.json()
    assert isinstance(body["answer"], str) and body["answer"].strip()
    for frag in fragments:
        assert frag in body["answer"], f"{qid}: {frag!r} missing from answer"
    assert isinstance(body["sources"], list) and len(body["sources"]) > 0
    assert "query_debug" in body
    debug = str(body.get("query_debug", ""))
    assert "SELECT" in debug.upper()
    assert not any(kw in debug.upper() for kw in WRITE_KEYWORDS)


@pytest.mark.test_id("TEST-049-003")
@pytest.mark.requirements("REQ-049-02")
@pytest.mark.scenario("AC-049-02")
def test_answer_sources_reference_receipt_rows():
    """Every figure traces to source rows; source amounts sum to the total."""
    resp = _post("Mennyit k\u00f6lt\u00f6ttem \u00e9telre j\u00faliusban?")
    assert resp.status_code == 200
    body = resp.json()
    sources = body["sources"]
    assert len(sources) >= 2
    for src in sources:
        assert src["receipt_id"] and isinstance(src["amount"], (int, float))
    total = sum(float(s["amount"]) for s in sources)
    assert total == pytest.approx(JULY_FOOD)
    assert "20800" in body["answer"]


@pytest.mark.test_id("TEST-049-004")
@pytest.mark.requirements("REQ-049-03")
@pytest.mark.scenario("AC-049-03")
def test_cross_tenant_no_leak():
    """Tenant B rows (overlapping Tesco merchant) never leak into tenant A."""
    resp = _post("Mennyit k\u00f6lt\u00f6ttem a Tesc\u00f3ban j\u00faliusban?", tenant_id=TENANT_A)
    assert resp.status_code == 200
    body = resp.json()
    leaked_ids = [s["receipt_id"] for s in body["sources"] if str(s["receipt_id"]).startswith("seed-b-")]
    assert leaked_ids == []
    assert "99999" not in body["answer"]


@pytest.mark.test_id("TEST-049-005")
@pytest.mark.requirements("REQ-049-05")
@pytest.mark.scenario("AC-049-05")
def test_no_data_explicit_signal():
    """Empty tenant slice -> explicit no-data signal, no invented figures."""
    resp = _post(
        "Mennyit k\u00f6lt\u00f6ttem \u00e9telre j\u00faliusban?",
        tenant_id=TENANT_EMPTY,
        headers={"X-Tenant-ID": TENANT_EMPTY, "X-Role": "member"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["sources"] == []
    lowered = body["answer"].lower()
    assert any(token in lowered for token in ("nincs", "no data", "not enough data", "\u00fcres", "empty"))


@pytest.mark.test_id("TEST-049-006")
@pytest.mark.requirements("REQ-049-06")
@pytest.mark.scenario("AC-049-06")
def test_write_request_refused_without_side_effect():
    """Write-type question changes nothing and points at the read-only limit."""
    before = client.get("/api/v1/receipts", headers=HEADERS_A).json()
    before_count = len(before.get("receipts", []))
    resp = _post("Jav\u00edtsd \u00e1t a Tesco nyugta kateg\u00f3ri\u00e1j\u00e1t \u00e9tteremre!")
    assert resp.status_code == 200
    lowered = resp.json()["answer"].lower()
    assert any(
        token in lowered
        for token in ("nem tudok m\u00f3dos\u00edtani", "cannot modify", "read-only", "feat-050")
    )
    after = client.get("/api/v1/receipts", headers=HEADERS_A).json()
    assert len(after.get("receipts", [])) == before_count


@pytest.mark.test_id("TEST-049-007")
@pytest.mark.requirements("REQ-049-07")
@pytest.mark.scenario("AC-049-07")
def test_error_branch_never_shows_failure_as_answer():
    """Response is either a valid answer or a retryable 503 -- never a 404/500 masquerading."""
    resp = _post("Mennyit k\u00f6lt\u00f6ttem \u00e9telre j\u00faliusban?")
    if resp.status_code == 200:
        body = resp.json()
        assert body["answer"] and isinstance(body["sources"], list)
    elif resp.status_code == 503:
        body = resp.json()
        assert body.get("retryable") is True
        assert body.get("error")
    else:
        pytest.fail(f"failure surfaced as HTTP {resp.status_code}, expected 200 or retryable 503")


@pytest.mark.test_id("TEST-049-008")
@pytest.mark.requirements("REQ-049-08")
@pytest.mark.scenario("AC-049-07")
def test_concurrent_questions_idempotent():
    """Parallel identical questions: same answer, no duplicated side effects."""
    question = "Mennyit k\u00f6lt\u00f6ttem \u00e9telre j\u00faliusban?"
    with _cf.ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(_post, question) for _ in range(8)]
        responses = [f.result(timeout=60) for f in futures]
    assert all(r.status_code == 200 for r in responses)
    answers = [r.json()["answer"] for r in responses]
    assert all(a == answers[0] for a in answers)
    first_sources = responses[0].json()["sources"]
    assert all(r.json()["sources"] == first_sources for r in responses)


@pytest.mark.test_id("TEST-049-009")
@pytest.mark.requirements("REQ-049-01")
@pytest.mark.scenario("AC-049-01")
def test_empty_question_rejected_422():
    """Empty question is a validation error, not an answer."""
    resp = _post("")
    assert resp.status_code == 422


@pytest.mark.test_id("TEST-049-010")
@pytest.mark.requirements("REQ-049-03")
@pytest.mark.scenario("AC-049-03")
def test_missing_tenant_unauthorized():
    """No tenant identity at all -> 401/403, never data."""
    resp = client.post(CHAT_URL, json={"question": "Mennyit k\u00f6lt\u00f6ttem?"})
    assert resp.status_code in (401, 403)
