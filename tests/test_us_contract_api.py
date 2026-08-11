"""API-level acceptance coverage for the approved US-001..US-009 workflow."""
from fastapi.testclient import TestClient
from app.api import app


def test_us_004_review_query_rejects_unknown_confidence_field():
    client = TestClient(app)
    response = client.get(
        "/product/review-items?confidence_field=unknown&confidence_below=0.8",
        headers={"X-Tenant-ID": "bdd-api", "X-Role": "admin"},
    )
    assert response.status_code == 422


def test_us_005_active_quality_profile_is_tenant_scoped():
    client = TestClient(app)
    response = client.get(
        "/product/quality/confidence-profiles/active",
        headers={"X-Tenant-ID": "new-quality-tenant", "X-Role": "admin"},
    )
    assert response.status_code == 200
    assert response.json() == {"profile": None}


def test_us_002_export_command_requires_idempotency_key():
    client = TestClient(app)
    response = client.post(
        "/product/export-commands",
        json={"preparation_id": "missing", "acknowledged_warning_receipt_ids": []},
        headers={"X-Tenant-ID": "bdd-api", "X-Role": "admin"},
    )
    assert response.status_code == 422
