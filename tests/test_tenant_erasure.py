from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.product_service import Actor, ProductService


def parsed(vendor="ACME", total=125.0):
    return SimpleNamespace(merchant=vendor, date="2026-07-01", total=total, tax=5.0,
        currency="USD", items=[SimpleNamespace(name="Item", price=total)],
        confidence={"vendor": .99, "total": .99, "date": .99})


@pytest.fixture
def svc():
    return ProductService(":memory:")


@pytest.fixture
def admin():
    return Actor("tenant-a", "admin")


def tenant_row_count(svc, tenant_id):
    return {table: svc._db.execute(f'SELECT COUNT(*) FROM "{table}" WHERE tenant_id=?', (tenant_id,)).fetchone()[0]
            for table in svc._tenant_tables()}


def test_erase_removes_every_tenant_row_and_keeps_other_tenants(svc, admin):
    svc.create_receipt(admin, parsed(), "a1.png")
    svc.create_receipt(admin, parsed("Shop"), "a2.png")
    other = Actor("tenant-b", "admin")
    keep = svc.create_receipt(other, parsed(), "b.png")["receipt_id"]
    before_other = tenant_row_count(svc, "tenant-b")

    result = svc.erase_tenant(admin, "ERASE")

    assert result["erased"] is True and result["tenant_id"] == "tenant-a"
    assert sum(result["deleted"].values()) > 0
    assert not any(tenant_row_count(svc, "tenant-a").values())
    assert tenant_row_count(svc, "tenant-b") == before_other
    assert svc.search_receipts(other)["items"][0]["receipt_id"] == keep


def test_erase_covers_receipt_images_stored_as_blobs(svc, admin):
    receipt_id = svc.create_receipt(admin, parsed(), "a.png")["receipt_id"]
    assert "receipt_assets" in svc._tenant_tables()
    svc._db.execute(
        "INSERT INTO receipt_assets(receipt_id,tenant_id,content,content_type,filename,sha256,boxes,created_at)"
        " VALUES(?,?,?,?,?,?,?,?)",
        (receipt_id, "tenant-a", b"img", "image/png", "a.png", "x", "[]", "2026-07-01T00:00:00+00:00"),
    )
    svc.erase_tenant(admin, "ERASE")
    assert svc._db.execute("SELECT COUNT(*) FROM receipt_assets WHERE tenant_id='tenant-a'").fetchone()[0] == 0


def test_erase_requires_admin_role(svc, admin):
    svc.create_receipt(admin, parsed(), "a.png")
    with pytest.raises(PermissionError):
        svc.erase_tenant(Actor("tenant-a", "reviewer"), "ERASE")
    assert svc.search_receipts(admin)["total"] == 1


def test_household_owner_can_erase_and_manage_privacy(svc):
    # Magic-link sessions carry role "owner"; the owner is the tenant's administrator.
    owner = Actor("tenant-a", "owner")
    svc.create_receipt(owner, parsed(), "a.png")
    svc.set_retention(owner, 60)
    assert svc.purge_expired(owner)["retention_days"] == 60
    assert svc.erase_tenant(owner, "ERASE")["erased"] is True
    assert svc.search_receipts(owner)["total"] == 0


def test_adult_member_cannot_erase_or_change_privacy(svc, admin):
    svc.create_receipt(admin, parsed(), "a.png")
    adult = Actor("tenant-a", "adult")
    with pytest.raises(PermissionError):
        svc.erase_tenant(adult, "ERASE")
    with pytest.raises(PermissionError):
        svc.set_retention(adult, 60)
    with pytest.raises(PermissionError):
        svc.purge_expired(adult)
    assert svc.search_receipts(admin)["total"] == 1


def test_erase_requires_literal_erase_confirmation(svc, admin):
    svc.create_receipt(admin, parsed(), "a.png")
    # The tenant id alone is not confirmation, and neither is a blank or lowercase word.
    for wrong in ("tenant-a", "", "erase"):
        with pytest.raises(ValueError):
            svc.erase_tenant(admin, wrong)
    assert svc.search_receipts(admin)["total"] == 1


def test_erase_route_is_registered():
    paths = set()
    for route in app.routes:
        if hasattr(route, "path"):
            paths.add(route.path)
        elif type(route).__name__ == "_IncludedRouter" and hasattr(route, "original_router"):
            paths.update(sub.path for sub in route.original_router.routes if hasattr(sub, "path"))
    assert "/product/privacy/erase" in paths


def test_erase_route_rejects_non_admin_and_bad_confirmation_without_deleting():
    # Both rejections happen before any row is touched, so these calls are
    # safe against the default product database.
    client = TestClient(app)
    reviewer = {"X-Tenant-ID": "erase-probe", "X-Role": "reviewer"}
    assert client.post("/product/privacy/erase", json={"confirmation": "ERASE"},
                       headers=reviewer).status_code == 403
    admin_headers = {"X-Tenant-ID": "erase-probe", "X-Role": "admin"}
    assert client.post("/product/privacy/erase", json={"confirmation": "erase-probe"},
                       headers=admin_headers).status_code == 422
    assert client.post("/product/privacy/erase", json={}, headers=admin_headers).status_code == 422
