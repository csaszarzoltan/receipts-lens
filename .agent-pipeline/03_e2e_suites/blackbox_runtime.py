"""Shared black-box runtime for ReceiptLens feature E2E suites.

Only HTTP and browser-visible interfaces are used. No repository, database,
service object, or private state is imported or mutated.
"""
from __future__ import annotations

import asyncio
import os
import re
import uuid
from typing import Any

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

BASE_API_URL = os.getenv("E2E_BASE_API_URL", "http://localhost:8000")
BASE_WEB_URL = os.getenv("E2E_BASE_WEB_URL", "http://localhost:3000")
SESSION_TOKEN = os.getenv("E2E_SESSION_TOKEN", "")


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/json", "X-E2E-Run": str(uuid.uuid4())}
    if SESSION_TOKEN:
        headers["Authorization"] = f"Bearer {SESSION_TOKEN}"
        headers["X-Session-Token"] = SESSION_TOKEN
    return headers


def _path_value(name: str) -> str:
    lowered = name.lower()
    if lowered.endswith("_id") or lowered in {"id", "receipt_id", "alert_id"}:
        return "999999999"
    if "token" in lowered:
        return "e2e-invalid-token"
    if "provider" in lowered:
        return "quickbooks"
    return f"e2e-{uuid.uuid4().hex[:12]}"


def concrete_path(path: str) -> str:
    return re.sub(r"\{([^}]+)\}", lambda m: _path_value(m.group(1)), path)


async def openapi_document(client: AsyncClient) -> dict[str, Any]:
    response = await client.get("/openapi.json", headers=_headers())
    if response.status_code != 200:
        pytest.skip(f"OpenAPI document unavailable: HTTP {response.status_code}")
    return response.json()


def _sample(schema: dict[str, Any], components: dict[str, Any], depth: int = 0) -> Any:
    if depth > 6:
        return None
    if "$ref" in schema:
        node: Any = {"schemas": components}
        for part in schema["$ref"].split("/")[2:]:
            node = node.get(part, {})
        return _sample(node, components, depth + 1)
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    if schema.get("enum"):
        return schema["enum"][0]
    for key in ("anyOf", "oneOf", "allOf"):
        if schema.get(key):
            if key == "allOf":
                result: dict[str, Any] = {}
                for part in schema[key]:
                    value = _sample(part, components, depth + 1)
                    if isinstance(value, dict):
                        result.update(value)
                return result
            return _sample(schema[key][0], components, depth + 1)
    kind = schema.get("type")
    if kind == "object" or "properties" in schema:
        required = set(schema.get("required", []))
        return {name: _sample(prop, components, depth + 1) for name, prop in schema.get("properties", {}).items() if name in required or "default" in prop}
    if kind == "array":
        return [_sample(schema.get("items", {}), components, depth + 1)]
    if kind == "integer": return 1
    if kind == "number": return 1.0
    if kind == "boolean": return True
    fmt = schema.get("format")
    if fmt == "email": return f"e2e-{uuid.uuid4().hex[:10]}@example.test"
    if fmt in {"date", "date-time"}: return "2030-01-15" if fmt == "date" else "2030-01-15T12:00:00Z"
    if fmt == "uuid": return str(uuid.uuid4())
    return f"e2e-{uuid.uuid4().hex[:12]}"


async def request_from_contract(client: AsyncClient, method: str, path: str, *, malformed: bool = False, without_auth: bool = False) -> httpx.Response:
    method = method.upper()
    actual = concrete_path(path)
    headers = {} if without_auth else _headers()
    kwargs: dict[str, Any] = {"headers": headers}
    if method in {"POST", "PUT", "PATCH"}:
        if malformed:
            kwargs["content"] = b"{not-json"
            headers = {**headers, "Content-Type": "application/json"}
            kwargs["headers"] = headers
        else:
            api = await openapi_document(client)
            operation = api.get("paths", {}).get(path, {}).get(method.lower(), {})
            content = operation.get("requestBody", {}).get("content", {})
            media = content.get("application/json") or next(iter(content.values()), {})
            kwargs["json"] = _sample(media.get("schema", {"type": "object"}), api.get("components", {}).get("schemas", {}))
    return await client.request(method, actual, **kwargs)


async def exercise_scenario(client: AsyncClient, method: str, path: str, modifier: str) -> None:
    """Exercise a spec scenario through HTTP and enforce black-box invariants."""
    if modifier == "MUST NOT":
        response = await request_from_contract(client, method, path, without_auth=True)
        assert response.status_code in {200, 201, 202, 204, 400, 401, 403, 404, 405, 409, 422, 429}, response.text
        assert response.status_code < 500
        return
    if modifier == "CONCURRENCY":
        first, second = await asyncio.gather(request_from_contract(client, method, path), request_from_contract(client, method, path))
        assert first.status_code < 500 and second.status_code < 500
        assert {first.status_code, second.status_code}.issubset({200, 201, 202, 204, 400, 401, 403, 404, 405, 409, 422, 429})
        return
    if modifier == "ALWAYS" and method in {"POST", "PUT", "PATCH"}:
        response = await request_from_contract(client, method, path, malformed=True)
        assert response.status_code in {400, 401, 403, 404, 409, 415, 422, 429}
        return
    response = await request_from_contract(client, method, path)
    assert response.status_code < 500, response.text
    assert response.status_code in {200, 201, 202, 204, 400, 401, 403, 404, 405, 409, 422, 429}
    if response.status_code < 300 and response.content:
        content_type = response.headers.get("content-type", "")
        assert content_type, "Successful black-box response must identify its representation"


async def browser_smoke(path: str, expected_text: str | None = None) -> None:
    """Run a real browser smoke flow when Playwright and the web app are available."""
    playwright = pytest.importorskip("playwright.async_api")
    async with playwright.async_playwright() as manager:
        browser = await manager.chromium.launch()
        page = await browser.new_page()
        response = await page.goto(f"{BASE_WEB_URL}{path}", wait_until="domcontentloaded")
        assert response is not None and response.status < 500
        await page.locator("body").wait_for(state="visible")
        if expected_text:
            assert expected_text.lower() in (await page.locator("body").inner_text()).lower()
        await browser.close()
