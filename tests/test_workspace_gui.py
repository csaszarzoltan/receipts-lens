"""Acceptance and integration tests for the ReceiptLens financial workspace GUI."""
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import app
from app.product_service import Actor, ProductService

client = TestClient(app)


def parsed(vendor="ACME", total=150.0, confidence=.9):
    return SimpleNamespace(
        merchant=vendor, date="2026-08-01", total=total, tax=10.0, currency="USD",
        items=[SimpleNamespace(name="Service", price=total)],
        confidence={"vendor":confidence,"date":confidence,"total":confidence,
                    "tax":confidence,"currency":confidence,"line_items":confidence},
    )


def test_workspace_has_application_shell_and_navigation():
    response=client.get("/workspace")
    assert response.status_code==200
    assert 'class="app-shell"' in response.text
    for label in ("Áttekintés","Nyugták","Feltöltés","Ellenőrzés","Jóváhagyások",
                  "Riportok","Integrációk","Beállítások"):
        assert label in response.text


def test_receipt_workspace_has_search_filters_bulk_actions_and_pagination():
    html=client.get("/workspace").text
    for marker in ("receiptQuery","statusFilter","tagFilter","minTotal","maxTotal",
                   "bulkApply","bulkApproval","prevPage","nextPage"):
        assert f'id="{marker}"' in html


def test_upload_workspace_has_multifile_drag_drop_camera_and_clipboard_contract():
    html=client.get("/workspace").text
    assert 'id="dropzone"' in html
    assert 'multiple capture="environment"' in html
    js=client.get("/assets/workspace.js").text
    assert "dragenter" in js and "clipboardData.files" in js and "uploadAll" in js


def test_review_workspace_has_split_view_confidence_and_keyboard_controls():
    html=client.get("/workspace").text
    assert 'class="review-grid"' in html
    assert "Biztos" in html and "Ellenőrzendő" in html and "Nem felismerhető" in html
    assert "Ctrl+Enter" in html and 'id="zoomIn"' in html and 'id="rotate"' in html


def test_approval_inbox_has_context_and_decision_actions():
    html=client.get("/workspace").text
    assert 'id="approvalList"' in html and 'id="newPolicy"' in html
    js=client.get("/assets/workspace.js").text
    assert "approved" in js and "rejected" in js and "policyThreshold" in js


def test_dashboard_reports_integrations_notifications_and_admin_are_present():
    html=client.get("/workspace").text
    for marker in ("kpis","actions","categoryChart","notificationBtn","reportBars",
                   "connectionCards","memberList","retentionDays","privacyExport"):
        assert f'id="{marker}"' in html


def test_accessibility_and_responsive_contracts_are_present():
    html=client.get("/workspace").text
    css=client.get("/assets/workspace.css").text
    assert 'class="skip"' in html and 'aria-live="polite"' in html
    assert ':focus-visible' in css and '@media(max-width:760px)' in css
    assert '.high-contrast' in css


def test_assets_are_allowlisted():
    assert client.get("/assets/workspace.css").status_code==200
    assert client.get("/assets/workspace.js").status_code==200
    assert client.get("/assets/secret.txt").status_code==404


def test_gui_supporting_list_apis_are_tenant_scoped():
    service=ProductService(":memory:")
    a=Actor("a","admin"); b=Actor("b","admin")
    service.add_member(a,"a@example.com","reviewer")
    service.add_member(b,"b@example.com","reviewer")
    service.create_connection(a,"CSV","csv",{"vendor":"v","total":"t","currency":"c"})
    assert [x["email"] for x in service.list_members(a)]==["a@example.com"]
    assert [x["name"] for x in service.list_connections(a)]==["CSV"]
    assert service.list_connections(b)==[]


def test_approval_list_joins_receipt_and_metadata_context():
    service=ProductService(":memory:"); actor=Actor("a","admin")
    receipt_id=service.create_receipt(actor,parsed(),"receipt.png")["receipt_id"]
    service.set_metadata(actor,receipt_id,["client"],"Apollo","CC-7")
    service.create_approval_policy(actor,"Manager",100,"USD")
    service.request_approval(actor,receipt_id)
    item=service.list_approvals(actor,"pending")[0]
    assert item["vendor"]=="ACME" and item["project"]=="Apollo"
    assert item["policy_name"]=="Manager" and item["total"]==150.0


def test_dashboard_uses_configured_retention():
    service=ProductService(":memory:"); actor=Actor("a","admin")
    service.set_retention(actor,90)
    assert service.dashboard(actor)["privacy"]["retention_days"]==90
