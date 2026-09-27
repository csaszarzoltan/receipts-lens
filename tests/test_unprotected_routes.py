"""Unprotected route regression (RED): two /v1 endpoints accept no auth.

`parse_receipts_route` and `check_duplicates_route` both sit under the /v1
prefix but resolve no tenant identity, so any caller can run a batch OCR (or
a cross-tenant duplicate comparison) against the shared resource pool. Their
sibling `parse_receipt_route` already takes the three auth headers — these
tests pin the same contract for the two stragglers.

Note: the body validators run before the handler, so the tests post payloads
that would otherwise reach the route; auth must be what rejects them, not
validation.

`parse_receipt_endpoint` is deliberately NOT covered: it is not registered
on the app (no route maps to it), so it is unreachable dead code rather than
a live exposure.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.api


def _client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(
        "app.api.service.resolve_session",
        lambda token: {"tenant_id": "hh-test", "role": "admin"},
    )
    return TestClient(app.api.app)


@pytest.mark.test_id("TEST-UNPROT-002")
@pytest.mark.requirements("REQ-API-3")
@pytest.mark.scenario("AC-API-3")
def test_parse_receipts_batch_requires_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch)
    response = client.post(
        "/api/v1/parse-receipts",
        files={"files": ("r.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    assert response.status_code == 401


@pytest.mark.test_id("TEST-UNPROT-003")
@pytest.mark.requirements("REQ-API-3")
@pytest.mark.scenario("AC-API-3")
def test_check_duplicates_requires_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch)
    response = client.post(
        "/api/v1/check-duplicates",
        json={"receipts": [{"id": "a", "total": 10.0}]},
    )
    assert response.status_code == 401

