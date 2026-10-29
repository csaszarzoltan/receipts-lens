import json

import pytest

from app import ocr
from app.product_service import Actor, ProductService

SECRET_SESSION = "SECRET-SESSION-TOKEN-VALUE"
SECRET_KEY_HASH = "SECRET-API-KEY-HASH-VALUE"


@pytest.fixture
def svc():
    return ProductService(":memory:")


@pytest.fixture
def admin():
    return Actor("tenant-a", "admin")


def _insert_member_and_secrets(svc, tenant_id):
    svc._db.execute(
        "INSERT INTO members(member_id,tenant_id,email,role,active) VALUES(?,?,?,?,?)",
        (f"m-{tenant_id}", tenant_id, f"{tenant_id}@example.test", "adult", 1),
    )
    svc._db.execute(
        "INSERT INTO sessions(session_token,email,tenant_id,role,expires_at,created_at,display_name)"
        " VALUES(?,?,?,?,?,?,?)",
        (f"{SECRET_SESSION}-{tenant_id}", f"{tenant_id}@example.test", tenant_id, "owner",
         "2030-01-01", "2026-01-01", None),
    )
    svc._db.execute(
        "INSERT INTO api_keys(key_id,tenant_id,name,secret_hash,revoked,created_at) VALUES(?,?,?,?,?,?)",
        (f"k-{tenant_id}", tenant_id, "ci", f"{SECRET_KEY_HASH}-{tenant_id}", 0, "2026-01-01"),
    )


def test_export_includes_tenant_tables_and_keeps_legacy_keys(svc, admin):
    _insert_member_and_secrets(svc, "tenant-a")
    _insert_member_and_secrets(svc, "tenant-b")
    export = svc.portability_export(admin)

    assert export["schema_version"] == 1
    assert "receipts" in export and "approvals" in export
    members = export["tables"]["members"]
    assert [m["email"] for m in members] == ["tenant-a@example.test"]


def test_export_never_contains_credentials_or_digests(svc, admin):
    _insert_member_and_secrets(svc, "tenant-a")
    export = svc.portability_export(admin)
    text = json.dumps(export)

    assert SECRET_SESSION not in text
    assert SECRET_KEY_HASH not in text
    assert "session_token" not in text
    assert "secret_hash" not in text
    # Operational session state is not exported at all; API key metadata is.
    assert "sessions" not in export["tables"]
    assert export["tables"]["api_keys"][0]["name"] == "ci"


def test_export_skips_binary_receipt_images_but_keeps_metadata(svc, admin):
    svc._db.execute(
        "INSERT INTO receipt_assets(receipt_id,tenant_id,content,content_type,filename,sha256,boxes,created_at)"
        " VALUES(?,?,?,?,?,?,?,?)",
        ("r1", "tenant-a", b"\x89PNG-binary", "image/png", "r1.png", "abc", "[]", "2026-01-01"),
    )
    export = svc.portability_export(admin)
    rows = export["tables"]["receipt_assets"]
    assert rows and rows[0]["filename"] == "r1.png"
    assert all("content" not in row for row in rows)
    json.dumps(export)  # must stay JSON-serializable


def test_ocr_caches_are_cleared_on_erase():
    ocr._PREPROCESS_CACHE.clear()
    ocr._TESS_CACHE.clear()
    ocr._cache_put(ocr._PREPROCESS_CACHE, b"image-bytes", "preprocessed")
    ocr._cache_put(ocr._TESS_CACHE, (b"image-bytes", "eng"), "tess-output")
    ocr.clear_caches()
    assert len(ocr._PREPROCESS_CACHE) == 0
    assert len(ocr._TESS_CACHE) == 0
