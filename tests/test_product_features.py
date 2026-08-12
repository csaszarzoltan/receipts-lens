"""End-to-end contracts for the six product feature requirements."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api import app
from app.ocr import ConfidenceReceipt, ReceiptItem

client = TestClient(app)
HEADERS = {"X-Tenant-ID": "team-a", "X-Role": "admin"}
API_DOCS = Path(__file__).resolve().parents[1] / "docs" / "api.md"


def parsed(confidence: float = 0.95) -> ConfidenceReceipt:
    return ConfidenceReceipt(
        merchant="Test Shop", date="2026-07-29",
        items=[ReceiptItem(name="Coffee", price=5.5)], total=5.5, tax=0.5,
        currency="USD", raw_text="TEST SHOP", confidence={"merchant": confidence, "total": confidence},
    )


def test_workspace_is_human_usable() -> None:
    response = client.get("/workspace")
    assert response.status_code == 200
    assert "Upload receipt" in response.text
    assert "/product/receipts/upload" in response.text


def test_upload_history_review_correction_retry_and_cancel() -> None:
    with patch("app.product_api.parse_receipt_with_confidence", return_value=parsed(0.4)):
        created = client.post(
            "/product/receipts/upload", headers=HEADERS,
            files={"file": ("receipt.png", b"image", "image/png")},
        )
    assert created.status_code == 201
    body = created.json(); receipt_id = body["receipt_id"]; job_id = body["job_id"]
    assert body["status"] == "needs_review"

    history = client.get("/product/jobs", headers=HEADERS).json()["items"]
    assert any(j["job_id"] == job_id for j in history)

    review = client.get("/product/review-items", headers=HEADERS).json()["items"]
    assert any(r["receipt_id"] == receipt_id for r in review)
    corrected = client.patch(
        f"/product/review-items/{receipt_id}", headers={**HEADERS, "If-Match": "1"},
        json={"changes": {"total": 6.0}, "action": "complete"},
    )
    assert corrected.status_code == 200
    assert corrected.json()["receipt"]["total"] == 6.0

    retried = client.post(f"/product/jobs/{job_id}/retry", headers={**HEADERS, "Idempotency-Key": "retry-1"})
    assert retried.status_code == 200
    assert client.post(f"/product/jobs/{job_id}/cancel", headers=HEADERS).status_code == 409


def test_tenant_isolation_members_keys_connections_exports_and_dashboard() -> None:
    member = client.post("/product/members", headers=HEADERS, json={"email": "reviewer@example.com", "role": "reviewer"})
    assert member.status_code == 201
    key = client.post("/product/api-keys", headers=HEADERS, json={"name": "integration"})
    assert key.status_code == 201 and key.json()["secret"].startswith("rl_")

    connection = client.post(
        "/product/connections", headers=HEADERS,
        json={"name": "CSV Ledger", "provider": "csv", "mapping": {"vendor": "vendor", "total": "total", "currency": "currency"}},
    )
    assert connection.status_code == 201
    assert client.post(f"/product/connections/{connection.json()['connection_id']}/test", headers=HEADERS).json()["status"] == "ok"

    dashboard = client.get("/product/dashboard", headers=HEADERS)
    assert dashboard.status_code == 200
    assert set(dashboard.json()) >= {"usage", "quality", "privacy", "service"}

    other = client.get("/product/jobs", headers={"X-Tenant-ID": "team-b", "X-Role": "admin"}).json()["items"]
    assert all(item["tenant_id"] == "team-b" for item in other)


def test_negative_authorization_validation_and_stale_correction() -> None:
    assert client.post(
        "/product/members",
        headers={"X-Tenant-ID": "team-a", "X-Role": "integrator"},
        json={"email": "blocked@example.com", "role": "reviewer"},
    ).status_code == 403
    assert client.post(
        "/product/connections", headers=HEADERS,
        json={"name": "Broken", "provider": "csv", "mapping": {"vendor": "vendor"}},
    ).status_code == 422

    with patch("app.product_api.parse_receipt_with_confidence", return_value=parsed(0.2)):
        item = client.post(
            "/product/receipts/upload", headers=HEADERS,
            files={"file": ("review.png", b"image", "image/png")},
        ).json()
    stale = client.patch(
        f"/product/review-items/{item['receipt_id']}",
        headers={**HEADERS, "If-Match": "99"},
        json={"changes": {"total": 7.0}, "action": "save"},
    )
    assert stale.status_code == 409


def test_automation_rule_422_names_unsupported_keys() -> None:
    """BUG-008: the 422 for an invalid rule must name the bad key(s)."""
    bad_condition = client.post(
        "/product/automation-rules", headers=HEADERS,
        json={"name": "Bad", "conditions": {"vendor_contains": "SBB", "bad_key": "x"},
              "actions": {"tags": ["a"]}},
    )
    assert bad_condition.status_code == 422
    detail = bad_condition.json()["detail"]
    assert "bad_key" in detail and "supported conditions are" in detail

    bad_action = client.post(
        "/product/automation-rules", headers=HEADERS,
        json={"name": "Bad", "conditions": {"vendor_contains": "SBB"},
              "actions": {"tags": ["a"], "nope": True}},
    )
    assert bad_action.status_code == 422
    detail = bad_action.json()["detail"]
    assert "nope" in detail and "supported actions are" in detail

    ok = client.post(
        "/product/automation-rules", headers=HEADERS,
        json={"name": "Good", "conditions": {"vendor_contains": "SBB"},
              "actions": {"tags": ["a"]}},
    )
    assert ok.status_code == 201


def test_api_docs_cover_connections_automation_rules_and_export_runs() -> None:
    """BUG-010: docs/api.md must document the new product endpoints."""
    assert API_DOCS.exists(), f"{API_DOCS} is missing"
    text = API_DOCS.read_text(encoding="utf-8")

    for endpoint, marker in [
        ("`GET /product/connections`", "accounting connections"),
        ("`POST /product/connections`", "Create a new accounting connection"),
        ("`GET /product/automation-rules`", "List the tenant's automation rules"),
        ("`POST /product/automation-rules`", "Create an automation rule"),
        ("`GET /product/export-runs`", "List the tenant's export runs"),
        ("`POST /product/export-runs`", "Export a set of completed receipts"),
    ]:
        assert endpoint in text, f"docs/api.md must document {endpoint}"
        assert marker in text, f"docs/api.md missing description for {endpoint}"

    # The documented 422 error message must reflect the BUG-008 fix.
    assert "unsupported condition key(s)" in text, (
        "docs/api.md should show the specific automation 422 message"
    )
