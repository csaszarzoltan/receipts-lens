"""External-interface fixtures for the ReceiptLens black-box E2E suites."""
from __future__ import annotations
import os
import pytest
from httpx import AsyncClient
from blackbox_runtime import BASE_API_URL

@pytest.fixture
async def async_client():
    """HTTP client pointed at a running ReceiptLens deployment.

    Start the API before running E2E tests, or set E2E_BASE_API_URL.
    No production module or database is imported by this fixture.
    """
    async with AsyncClient(base_url=BASE_API_URL, timeout=30.0, follow_redirects=False) as client:
        try:
            response = await client.get("/health")
        except Exception as exc:
            pytest.skip(f"ReceiptLens API is not reachable at {BASE_API_URL}: {exc}")
        if response.status_code >= 500:
            pytest.fail(f"ReceiptLens health endpoint failed: {response.status_code}")
        yield client
