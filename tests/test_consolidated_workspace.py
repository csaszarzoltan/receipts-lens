"""Acceptance tests for the merged v0.9/v1.0 workspace release."""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.advanced_workspace import AdvancedWorkspace
from app.api import app
from app.product_service import Actor, ProductService

client = TestClient(app)


def parsed(vendor="SBB Rail", total=120.0, currency="CHF", confidence=.95):
    return SimpleNamespace(
        merchant=vendor, date="2026-08-01", total=total, tax=8.0, currency=currency,
        items=[SimpleNamespace(name="Ticket", price=total)],
        confidence={k:confidence for k in ("vendor","date","total","tax","currency","line_items")},
    )

@pytest.fixture
def bundle():
    service=ProductService(":memory:")
    advanced=AdvancedWorkspace(service)
    actor=Actor("tenant-a","admin")
    return service,advanced,actor


def test_source_asset_is_tenant_scoped_and_preserves_boxes(bundle):
    service,advanced,actor=bundle
    rid=service.create_receipt(actor,parsed(),"r.png")["receipt_id"]
    boxes=[{"text":"SBB","confidence":.9,"x":.1,"y":.1,"width":.2,"height":.1}]
    advanced.store_asset(actor.tenant_id,rid,b"PNGDATA","image/png","r.png",boxes)
    asset=advanced.asset(actor.tenant_id,rid)
    assert asset and asset.content==b"PNGDATA" and asset.boxes==boxes
    assert advanced.asset("other",rid) is None


def test_saved_views_validate_filter_contract_and_isolate_tenants(bundle):
    _,advanced,actor=bundle
    view=advanced.create_view(actor.tenant_id,"High value",{"min_total":500},pinned=True)
    assert advanced.views(actor.tenant_id)[0]["filters"]=={"min_total":500}
    assert advanced.views("other")==[]
    assert advanced.delete_view(actor.tenant_id,view["view_id"])
    with pytest.raises(ValueError): advanced.create_view(actor.tenant_id,"Bad",{"sql":"DROP"})


def test_notifications_support_read_archive_and_read_all(bundle):
    _,advanced,actor=bundle
    first=advanced.notify(actor.tenant_id,"review","Review","Needs review","r1")
    advanced.notify(actor.tenant_id,"export","Export","Failed","r2")
    advanced.update_notification(actor.tenant_id,first["notification_id"],True,True)
    active=advanced.notifications(actor.tenant_id)
    assert len(active)==1 and not active[0]["read"]
    assert advanced.mark_all_read(actor.tenant_id)==1


def test_automation_preview_and_application(bundle):
    service,advanced,actor=bundle
    service.create_approval_policy(actor,"Manager",100,"CHF")
    rid=service.create_receipt(actor,parsed(),"r.png")["receipt_id"]
    advanced.create_rule(actor.tenant_id,"SBB travel",{"vendor_contains":"SBB","currency":"CHF"},
                         {"tags":["rail"],"project":"Travel","request_approval":True})
    assert advanced.rule_preview(actor.tenant_id,{"vendor_contains":"SBB"})==1
    applied=advanced.apply_rules(actor,rid,parsed_payload(service,actor,rid))
    assert len(applied)==1
    found=service.search_receipts(actor,tag="rail")["items"][0]
    assert found["metadata"]["project"]=="Travel"
    assert service.list_approvals(actor,"pending")[0]["receipt_id"]==rid


def parsed_payload(service,actor,rid):
    return service.search_receipts(actor)["items"][0]["receipt"]


def test_duplicate_comparison_and_decision_removes_candidate(bundle):
    service,advanced,actor=bundle
    service.create_receipt(actor,parsed("SBB",120),"a.png")
    service.create_receipt(actor,parsed("SBB Rail",120),"b.png")
    candidate=advanced.duplicates(actor)[0]
    assert candidate["confidence"]==1.0
    advanced.decide_duplicate(actor.tenant_id,candidate["left_id"],candidate["right_id"],"different")
    assert advanced.duplicates(actor)==[]


def test_history_preferences_and_export_runs(bundle):
    _,advanced,actor=bundle
    advanced.record_history(actor,"r1","receipt.corrected",{"total":1},{"total":2})
    assert advanced.history(actor.tenant_id,"r1")[0]["after"]=={"total":2}
    prefs=advanced.save_preferences(actor.tenant_id,actor.role,{"language":"en","compact":True,"evil":1})
    assert prefs=={"language":"en","compact":True}
    run=advanced.record_export(actor.tenant_id,"csv",3,2,["missing field"])
    assert run["status"]=="partial" and advanced.exports(actor.tenant_id)[0]["exported"]==2


def test_advanced_gui_sections_and_pwa_assets_are_shipped():
    html=client.get("/workspace").text
    for marker in ("savedViewSelect","reviewImage","ocrOverlay","showHistory","duplicates",
                   "automations","notificationPanel","exportHistory","onboarding","networkState"):
        assert marker in html
    assert client.get("/assets/manifest.webmanifest").status_code==200
    assert client.get("/assets/service-worker.js").status_code==200


def test_new_api_routes_are_registered():
    paths = get_all_paths(app)
    expected={
        "/product/receipts/{receipt_id}/image","/product/receipts/{receipt_id}/ocr-boxes",
        "/product/receipts/{receipt_id}/history","/product/saved-views",
        "/product/notifications","/product/automation-rules","/product/duplicates",
        "/product/preferences","/product/export-runs",
    }
    assert expected <= paths


def test_asset_api_rejects_cross_tenant_access(monkeypatch):
    from app import product_api

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

    service=ProductService(":memory:"); advanced=AdvancedWorkspace(service); actor=Actor("a","admin")
    rid=service.create_receipt(actor,parsed(),"r.png")["receipt_id"]
    advanced.store_asset("a",rid,b"abc","image/png","r.png")
    monkeypatch.setattr(product_api,"advanced",advanced)
    assert client.get(f"/product/receipts/{rid}/image",headers={"X-Tenant-ID":"b"}).status_code==404
    ok=client.get(f"/product/receipts/{rid}/image",headers={"X-Tenant-ID":"a"})
    assert ok.status_code==200 and ok.content==b"abc" and ok.headers["cache-control"]=="private, no-store"


def test_workspace_javascript_contains_real_workflows():
    js=client.get("/assets/workspace.js").text
    for contract in ("loadSavedViews","loadDuplicates","loadRules","loadNotifications",
                     "loadReviewAsset","loadBoxes","serviceWorker.register","beforeinstallprompt"):
        assert contract in js
