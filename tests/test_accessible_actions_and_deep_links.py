"""TDD acceptance contracts for precise tasks and accessible consequential actions."""
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import app
from app.product_service import Actor, ProductService

client = TestClient(app)


def parsed(confidence: float = 0.95):
    return SimpleNamespace(
        merchant="Action Shop", date="2026-08-01", total=42.0, tax=3.0,
        currency="CHF", items=[SimpleNamespace(name="Paper", price=42.0)],
        confidence={key: confidence for key in ("vendor", "date", "total", "tax", "currency")},
    )


def test_export_blocker_task_deep_links_to_receipt_and_field():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "admin")
    receipt_id = service.create_receipt(actor, parsed(), "receipt.png")["receipt_id"]

    task = next(item for item in service.work_queue(actor)["items"] if item["type"] == "export_blocker")

    assert task["action_url"] == f"#receipts?receipt={receipt_id}&field=cost_center"


def test_review_and_approval_tasks_have_precise_deep_links():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "admin")
    review_id = service.create_receipt(actor, parsed(0.2), "review.png")["receipt_id"]
    completed_id = service.create_receipt(actor, parsed(), "approval.png")["receipt_id"]
    service.create_approval_policy(actor, "Manager", 10, "CHF")
    approval = service.request_approval(actor, completed_id)

    tasks = service.work_queue(actor)["items"]
    review = next(item for item in tasks if item["type"] == "review" and item["receipt_id"] == review_id)
    approval_task = next(item for item in tasks if item["type"] == "approval")

    assert review["action_url"] == f"#review?receipt={review_id}"
    assert approval_task["action_url"] == f"#approvals?approval={approval['approval_id']}"


def test_workspace_has_no_browser_prompt_or_confirm_for_business_actions():
    js = client.get("/assets/workspace.js").text

    assert "const note=prompt(" not in js
    assert "const name=prompt(" not in js
    assert "if(!confirm(" not in js
    assert "openDecisionDialog" in js
    assert "openKeyDialog" in js
    assert "openSavedViewDialog" in js
    assert "openPurgeDialog" in js


def test_dialog_contract_contains_inline_errors_and_described_consequences():
    js = client.get("/assets/workspace.js").text
    html = client.get("/workspace").text

    assert 'id="dialogError"' in js
    assert 'aria-describedby="dialogDescription"' in html
    assert "Az elutasítás oka kötelező" in js
    assert "véglegesen törlődnek" in js


def test_dashboard_uses_full_action_url_instead_of_stripping_query_context():
    js = client.get("/assets/workspace.js").text

    assert "data-action-url" in js
    assert "navigateTask" in js
    assert "action_url.replace('#','')" not in js
