"""Tests each ReceiptLens 1.1 UI capability and its tenant-safe service."""
from types import SimpleNamespace
import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.accounting_workspace import AccountingWorkspace
from app.api import app
from app.product_service import Actor, ProductService

client=TestClient(app)

def parsed(vendor="Vendor", total=120.0, tax=10.0, currency="CHF", day="2026-07-01"):
    return SimpleNamespace(merchant=vendor,date=day,total=total,tax=tax,currency=currency,
        items=[SimpleNamespace(name="Item",price=total)],
        confidence={"vendor":.9,"date":.9,"total":.9,"tax":.9,"currency":.9})

@pytest.fixture
def env():
    service=ProductService(":memory:"); workspace=AccountingWorkspace(service); actor=Actor("a","admin")
    return service,workspace,actor

def test_01_line_item_editor_updates_version_and_calculates_total(env):
    service,w,a=env; rid=service.create_receipt(a,parsed(),"x")["receipt_id"]
    result=w.update_line_items(a,rid,[{"name":"Coffee","quantity":2,"unit_price":5,"amount":10,"category":"Meals"}],1)
    assert result["version"]==2 and result["line_items_total"]==10
    with pytest.raises(RuntimeError): w.update_line_items(a,rid,[],1)

def test_02_accounting_validation_detects_mismatch_and_tax_errors(env):
    service,w,a=env; rid=service.create_receipt(a,parsed(total=10,tax=20),"x")["receipt_id"]
    service._db.execute("UPDATE receipts SET payload=json_set(payload, '$.line_items[0].price', 7) WHERE receipt_id=?", (rid,))
    result=w.validate(a,rid)
    assert result["readiness"]=="blocked"
    assert {x["code"] for x in result["errors"]} >= {"tax_exceeds_total"}
    assert {x["code"] for x in result["warnings"]} >= {"line_total_mismatch","missing_cost_center"}

def test_03_visual_approval_flow_validates_and_simulates(env):
    _,w,a=env; definition={"min_total":100,"steps":[{"mode":"serial","roles":["reviewer"]},{"mode":"parallel","roles":["admin","reviewer"]}]}
    made=w.create_approval_flow(a,"Flow",definition)
    simulated=w.simulate_approval("a",definition,{"total":150})
    assert made["version"]==1 and simulated["estimated_approvers"]==3
    with pytest.raises(PermissionError): w.create_approval_flow(Actor("a","reviewer"),"x",definition)

def test_04_export_preparation_separates_valid_blocked_and_warning(env):
    service,w,a=env
    warning=service.create_receipt(a,parsed(),"a")["receipt_id"]
    blocked=service.create_receipt(a,parsed(tax=200),"b")["receipt_id"]
    result=w.prepare_export(a,[warning,blocked,"missing"],None)
    assert warning in result["valid_ids"] and len(result["blocked"])==2 and result["status"]=="partial"

def test_05_email_inbox_queues_supported_and_quarantines_unsupported(env):
    _,w,a=env
    ok=w.receive_email(a.tenant_id,"billing@example.com","Receipt",[{"filename":"x.pdf","content_type":"application/pdf","size":5}])
    bad=w.receive_email(a.tenant_id,"spam@example.com","Text",[{"filename":"x.exe","content_type":"application/octet-stream","size":5}])
    assert ok["status"]=="queued" and bad["status"]=="quarantined"
    assert w.emails("other")==[]

def test_06_recurring_expenses_detects_stable_subscriptions_and_feedback(env):
    service,w,a=env
    service.create_receipt(a,parsed("Cloud",10),"a"); service.create_receipt(a,parsed("Cloud",10.5),"b")
    item=w.recurring(a.tenant_id)[0]
    assert item["likely_subscription"] and item["annualized"]==123.0
    w.recurring_feedback(a.tenant_id,"Cloud",False)
    assert not w.recurring(a.tenant_id)[0]["likely_subscription"]

def test_07_currency_ui_supports_dated_manual_rates(env):
    _,w,a=env
    w.set_rate(a,"EUR","CHF",.95,"2026-07-01")
    converted=w.convert(a.tenant_id,100,"EUR","CHF","2026-07-02")
    assert converted["converted"]==95 and converted["source"]=="manual"
    with pytest.raises(KeyError): w.convert("other",100,"EUR","CHF")

def test_08_dashboard_preferences_are_persisted_by_role():
    # Existing advanced preferences back the visual dashboard editor.
    from app.advanced_workspace import AdvancedWorkspace

def get_all_paths(app):
    paths = set()
    for route in app.routes:
        if hasattr(route, 'path'):
            paths.add(route.path)
        elif type(route).__name__ == '_IncludedRouter' and hasattr(route, 'original_router'):
            for sub in route.original_router.routes:
                if hasattr(sub, 'path'):
                    paths.add(sub.path)
    return paths

    service=ProductService(":memory:"); advanced=AdvancedWorkspace(service)
    advanced.save_preferences("a","reviewer",{"dashboard_widgets":["actions","quality"]})
    assert advanced.preferences("a","reviewer")["dashboard_widgets"]==["actions","quality"]
    assert advanced.preferences("a","admin")["dashboard_widgets"]!=["actions","quality"]

def test_09_localization_catalog_and_language_controls_exist():
    html=client.get("/workspace").text; js=client.get("/assets/workspace.js").text
    assert 'id="language"' in html and "const I18N" in js and "Overview" in js

def test_10_permission_matrix_is_admin_only_and_validated(env):
    _,w,a=env
    saved=w.set_permissions(a,"reviewer",["view_image","approve"])
    assert saved["permissions"]==["approve","view_image"]
    with pytest.raises(PermissionError): w.set_permissions(Actor("a","reviewer"),"reviewer",[])
    assert w.permission_matrix("other")["integrator"]==["export"]

def test_11_diagnostics_zip_excludes_sensitive_content(env):
    service,w,a=env; service.create_receipt(a,parsed("SECRET MERCHANT"),"x")
    data=w.diagnostic_zip(a.tenant_id,"1.1.0")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names=set(z.namelist()); combined=b"".join(z.read(n) for n in names)
    assert names=={"health.json","capabilities.json","README.txt"}
    assert b"SECRET MERCHANT" not in combined and b"sk-" not in combined.lower()

def test_12_bidirectional_ocr_link_line_editor_and_all_ui_sections_ship():
    html=client.get("/workspace").text; js=client.get("/assets/workspace.js").text
    for marker in ("fieldLinkMap","lineItemRows","approvalSteps","validationSummary",
                   "exportPreparationResults","inboxAddress","subscriptionCards","rateValue",
                   "widgetEditor","language","permissionMatrix","diagnosticStatus"):
        assert f'id="{marker}"' in html
    for behavior in ("renderFieldLinks","renderLineItems","loadPermissionMatrix","loadDiagnostics"):
        assert behavior in js

def test_13_all_accounting_routes_registered():
    paths = get_all_paths(app)
    assert {"/product/receipts/{receipt_id}/line-items","/product/receipts/{receipt_id}/validation",
            "/product/approval-flows","/product/export-preparations","/product/inbound-emails",
            "/product/recurring-expenses","/product/exchange-rates","/product/currency/convert",
            "/product/permissions","/product/diagnostics","/product/diagnostics/bundle"} <= paths

def test_14_diagnostic_api_is_role_protected():
    assert client.get('/product/diagnostics/bundle',headers={'X-Role':'reviewer'}).status_code==403
    response=client.get('/product/diagnostics/bundle',headers={'X-Role':'admin'})
    assert response.status_code==200 and response.headers['content-type']=='application/zip'
