from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.product_service import Actor, ProductConflict, ProductService

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



def parsed(vendor="ACME", total=125.0, currency="USD"):
    return SimpleNamespace(merchant=vendor,date="2026-07-01",total=total,tax=5.0,
        currency=currency,items=[SimpleNamespace(name="Item",price=total)],
        confidence={"vendor":.99,"total":.99,"date":.99})

@pytest.fixture
def svc(): return ProductService(":memory:")

@pytest.fixture
def admin(): return Actor("tenant-a","admin")

def test_search_is_tenant_scoped_and_filters(svc,admin):
    svc.create_receipt(admin,parsed("Alpha",50),"a.png")
    svc.create_receipt(admin,parsed("Beta",150),"b.png")
    svc.create_receipt(Actor("tenant-b","admin"),parsed("Secret",999),"x.png")
    result=svc.search_receipts(admin,query="beta",min_total=100)
    assert result["total"]==1 and result["items"][0]["receipt"]["vendor"]=="Beta"

def test_search_validates_pagination(svc,admin):
    with pytest.raises(ValueError): svc.search_receipts(admin,limit=0)

def test_metadata_is_normalized_and_filterable(svc,admin):
    rid=svc.create_receipt(admin,parsed(),"a.png")["receipt_id"]
    meta=svc.set_metadata(admin,rid,[" Travel ","travel","Client-A"],"Apollo","CC-42")
    assert meta["tags"]==["Client-A","Travel"]
    assert svc.search_receipts(admin,tag="travel")["total"]==1

def test_metadata_cannot_cross_tenants(svc,admin):
    rid=svc.create_receipt(admin,parsed(),"a.png")["receipt_id"]
    with pytest.raises(KeyError): svc.set_metadata(Actor("other","admin"),rid,["x"],None,None)

def test_approval_policy_and_decision(svc,admin):
    policy=svc.create_approval_policy(admin,"Manager review",100,"usd")
    rid=svc.create_receipt(admin,parsed(total=125),"a.png")["receipt_id"]
    request=svc.request_approval(admin,rid)
    assert request["required"] and request["policy_id"]==policy["policy_id"]
    decision=svc.decide_approval(Actor("tenant-a","reviewer"),request["approval_id"],"approved","ok")
    assert decision["status"]=="approved"
    with pytest.raises(ProductConflict): svc.decide_approval(admin,request["approval_id"],"rejected")

def test_approval_not_required_below_threshold(svc,admin):
    svc.create_approval_policy(admin,"High value",500)
    rid=svc.create_receipt(admin,parsed(total=50),"a.png")["receipt_id"]
    assert svc.request_approval(admin,rid)["status"]=="not_required"

def test_policy_requires_admin(svc):
    with pytest.raises(PermissionError):
        svc.create_approval_policy(Actor("t","reviewer"),"x",10)

def test_retention_purges_only_expired_tenant_data(svc,admin):
    old=svc.create_receipt(admin,parsed(),"old.png")["receipt_id"]
    fresh=svc.create_receipt(admin,parsed(),"fresh.png")["receipt_id"]
    other=svc.create_receipt(Actor("tenant-b","admin"),parsed(),"other.png")["receipt_id"]
    old_date=(datetime.now(timezone.utc)-timedelta(days=40)).isoformat()
    svc._db.execute("UPDATE receipts SET created_at=? WHERE receipt_id=?",(old_date,old))
    svc.set_retention(admin,30)
    result=svc.purge_expired(admin)
    assert result["purged"]==1
    assert svc.search_receipts(admin)["total"]==1
    assert svc.search_receipts(Actor("tenant-b","admin"))["items"][0]["receipt_id"]==other

def test_retention_bounds_and_role(svc,admin):
    with pytest.raises(ValueError): svc.set_retention(admin,0)
    with pytest.raises(PermissionError): svc.set_retention(Actor("tenant-a","reviewer"),30)

def test_portability_export_is_scoped_and_versioned(svc,admin):
    svc.create_receipt(admin,parsed(),"a.png")
    svc.create_receipt(Actor("tenant-b","admin"),parsed("Other"),"b.png")
    export=svc.portability_export(admin)
    assert export["schema_version"]==1 and export["tenant_id"]=="tenant-a"
    assert len(export["receipts"])==1

def test_new_routes_are_registered():
    paths = get_all_paths(app)
    assert {"/product/receipts","/product/approval-policies","/product/privacy/export"} <= paths

def test_http_validation_and_not_found():
    client=TestClient(app)
    assert client.get("/product/receipts?limit=0").status_code==422
    assert client.put("/product/receipts/missing/metadata",json={"tags":[]}).status_code==404
    assert client.put("/product/privacy/retention",json={"retention_days":0}).status_code==422
