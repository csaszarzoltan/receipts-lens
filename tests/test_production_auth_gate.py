"""Production auth-gate regression for consumer dashboard (RED).

`_resolve_tenant_from_auth` (app/api.py) has no production gate, unlike
`api_v1_actor` which rejects header auth with 401 when `_is_production`.
These tests pin the expected contract: header auth must be rejected in
production, work in dev, and Bearer sessions must take precedence.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.api


def _get_dashboard(client: TestClient, headers: dict[str, str]):
    return client.get("/api/v1/consumer/dashboard", headers=headers)


@pytest.mark.test_id("TEST-PRODAUTH-001")
@pytest.mark.requirements("REQ-API-1")
@pytest.mark.scenario("AC-API-1")
def test_header_auth_rejected_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api._is_production", True)
    client = TestClient(app.api.app)
    response = _get_dashboard(
        client, {"X-Tenant-ID": "hh-attacker", "X-Role": "admin"}
    )
    assert response.status_code == 401


@pytest.mark.test_id("TEST-PRODAUTH-002")
@pytest.mark.requirements("REQ-API-1")
@pytest.mark.scenario("AC-API-1")
def test_header_auth_allowed_in_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api._is_production", False)
    client = TestClient(app.api.app)
    response = _get_dashboard(
        client, {"X-Tenant-ID": "hh-attacker", "X-Role": "admin"}
    )
    assert response.status_code != 401


@pytest.mark.test_id("TEST-PRODAUTH-003")
@pytest.mark.requirements("REQ-API-1")
@pytest.mark.scenario("AC-API-1")
def test_bearer_session_works_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api._is_production", True)
    monkeypatch.setattr(
        "app.api.service.resolve_session",
        lambda token: {"tenant_id": "hh-test", "role": "admin"},
    )
    client = TestClient(app.api.app)
    response = _get_dashboard(client, {"Authorization": "Bearer good-token"})
    assert response.status_code != 401


@pytest.mark.test_id("TEST-PRODAUTH-004")
@pytest.mark.requirements("REQ-API2-6")
@pytest.mark.scenario("AC-API2-6")
def test_job_status_requires_auth_and_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    jobs = {
        "hh-own": {
            "job_id": "hh-own",
            "status": "completed",
            "result": {"total": 10.0},
            "tenant_id": "hh-own",
        },
        "hh-other": {
            "job_id": "hh-other",
            "status": "completed",
            "result": {"total": 999.0},
            "tenant_id": "hh-other",
        },
    }
    monkeypatch.setattr("app.api._job_store.get", lambda job_id: jobs.get(job_id))
    monkeypatch.setattr(
        "app.api.service.resolve_session",
        lambda token: {"tenant_id": "hh-own", "role": "admin"},
    )
    client = TestClient(app.api.app)

    no_auth = client.get("/api/v1/jobs/hh-own")
    assert no_auth.status_code == 401

    own = client.get("/api/v1/jobs/hh-own", headers={"Authorization": "Bearer good-token"})
    assert own.status_code == 200
    assert own.json()["result"]["total"] == 10.0

    other = client.get("/api/v1/jobs/hh-other", headers={"Authorization": "Bearer good-token"})
    assert other.status_code != 200
