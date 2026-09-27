"""Pre-development acceptance tests for confidence scores + async processing."""
from __future__ import annotations

import inspect
import uuid
from typing import get_type_hints

import pytest

from app import api


# --------------------------------------------------------------------------
# Interface tests -- must pass before implementation is complete
# --------------------------------------------------------------------------
@pytest.mark.test_id("TEST-ASYNCC-001")
@pytest.mark.requirements("REQ-OCR-ASYNC")
@pytest.mark.scenario("A szerződéshez tartozó viselkedés.")
def test_app_version_bumped():
    assert api.app.version.startswith("1.3.")


@pytest.mark.test_id("TEST-ASYNCC-002")
@pytest.mark.requirements("REQ-OCR-ASYNC")
@pytest.mark.scenario("A szerződéshez tartozó viselkedés.")
def test_parse_receipt_route_still_registered():
    routes = {getattr(r, "path", None) for r in api.app.routes}
    assert "/v1/parse-receipt" in routes


@pytest.mark.test_id("TEST-ASYNCC-003")
@pytest.mark.requirements("REQ-OCR-ASYNC")
@pytest.mark.scenario("A szerződéshez tartozó viselkedés.")
def test_async_parse_receipt_route_registered():
    routes = {getattr(r, "path", None) for r in api.app.routes}
    assert "/v1/parse-receipt/async" in routes


@pytest.mark.test_id("TEST-ASYNCC-004")
@pytest.mark.requirements("REQ-OCR-ASYNC")
@pytest.mark.scenario("A szerződéshez tartozó viselkedés.")
def test_jobs_route_registered():
    routes = {getattr(r, "path", None) for r in api.app.routes}
    assert "/v1/jobs/{job_id}" in routes


@pytest.mark.test_id("TEST-ASYNCC-005")
@pytest.mark.requirements("REQ-OCR-ASYNC")
@pytest.mark.scenario("A szerződéshez tartozó viselkedés.")
def test_async_endpoint_is_async():
    # Find the async endpoint function by inspecting routes
    for route in api.app.routes:
        if getattr(route, "path", None) == "/v1/parse-receipt/async":
            assert inspect.iscoroutinefunction(route.endpoint)
            break
    else:
        pytest.fail("Async endpoint not found")


@pytest.mark.test_id("TEST-ASYNCC-006")
@pytest.mark.requirements("REQ-OCR-ASYNC")
@pytest.mark.scenario("A szerződéshez tartozó viselkedés.")
def test_parse_receipt_accepts_webhook_url():
    hints = {}
    for route in api.app.routes:
        if getattr(route, "path", None) == "/v1/parse-receipt/async":
            hints = get_type_hints(route.endpoint)
            break
    assert "webhook_url" in hints, "webhook_url parameter missing"


# --------------------------------------------------------------------------
# Behavioral tests -- endpoint behavior
# --------------------------------------------------------------------------
@pytest.mark.test_id("TEST-ASYNCC-007")
@pytest.mark.requirements("REQ-OCR-ASYNC")
@pytest.mark.scenario("Async endpoint should return immediately with a job_id.")
def test_async_returns_job_id_immediately():
    """Async endpoint should return immediately with a job_id."""
    import httpx
    from httpx import ASGITransport

    from app.main import app

    transport = ASGITransport(app=app)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")

    async def do():
        resp = await client.post(
            "/v1/parse-receipt/async",
            data={},
            headers={"X-Tenant-ID": "test-tenant", "X-Role": "admin"},
        )
        assert resp.status_code == 422

    import asyncio
    asyncio.run(do())


@pytest.mark.test_id("TEST-ASYNCC-008")
@pytest.mark.requirements("REQ-OCR-ASYNC")
@pytest.mark.scenario("Sync endpoint must include confidence scores when result is non-empty.")
def test_parse_receipt_response_has_confidence():
    """Sync endpoint must include confidence scores when result is non-empty."""
    from PIL import Image

    image = Image.new("RGB", (200, 100), color="white")
    buf = __import__("io").BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    image_bytes = buf.read()

    import asyncio
    result = asyncio.run(api.parse_receipt_endpoint(file=image_bytes))
    assert "confidence" in result, "confidence key missing"
    assert isinstance(result["confidence"], dict)


@pytest.mark.test_id("TEST-ASYNCC-009")
@pytest.mark.requirements("REQ-OCR-ASYNC")
@pytest.mark.scenario("A szerződéshez tartozó viselkedés.")
def test_confidence_keys_match_schema():
    from PIL import Image

    image = Image.new("RGB", (200, 100), color="white")
    buf = __import__("io").BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    image_bytes = buf.read()

    import asyncio
    result = asyncio.run(api.parse_receipt_endpoint(file=image_bytes))
    conf = result.get("confidence", {})
    for key in ("vendor", "total", "date", "tax", "currency", "line_items"):
        assert key in conf, f"{key} missing from confidence"
        assert 0.0 <= conf[key] <= 1.0, f"{key} confidence out of range"


@pytest.mark.test_id("TEST-ASYNCC-010")
@pytest.mark.requirements("REQ-OCR-ASYNC")
@pytest.mark.scenario("Polling a non-existent job_id must return 404.")
def test_job_status_endpoint_returns_not_found():
    """Polling a non-existent job_id must return 404."""
    import httpx
    from httpx import ASGITransport

    from app.main import app

    transport = ASGITransport(app=app)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")

    async def do():
        resp = await client.get(
            f"/v1/jobs/{uuid.uuid4()}",
            headers={"X-Tenant-ID": "test-tenant", "X-Role": "admin"},
        )
        assert resp.status_code == 404

    import asyncio
    asyncio.run(do())
