"""DEPLOY-3 FU: body-only tenant az insights/evaluate úton.

A modul-docstring "Bearer > header > body" sorrendet ígér és az
EvaluateRequest tartalmaz tenant_id-t, de evaluate_insights a
_header_tenant Depends-et használja, így body-only hívás 401-et ad.
Döntés: body-t is figyelembe venni (docstring szerint).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)

EVALUATE_URL = "/api/v1/insights/evaluate"
TENANT_BODY_ONLY = "fu-body-only-tenant"


def test_evaluate_accepts_body_only_tenant():
    """Body-only tenant_id header nélkül is 200-at ad (docstring szerint)."""
    resp = client.post(EVALUATE_URL, json={"tenant_id": TENANT_BODY_ONLY})
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert isinstance(body["cards"], list)
