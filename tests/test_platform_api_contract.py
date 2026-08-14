"""Public operational API contracts introduced by research requirements."""
from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


def test_readiness_and_capabilities_are_typed_and_versioned() -> None:
    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
    caps = client.get("/api/v1/platform/capabilities")
    assert caps.status_code == 200
    body = caps.json()
    assert body["schema_version"] == 1
    assert set(body["requirements"]) == {"data", "security", "quality", "integrations"}
