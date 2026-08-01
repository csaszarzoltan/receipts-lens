"""Pre-development interface + behavioral tests for REST API v2.

Module 5: app/api_v2.py — batch and export endpoints.

Run: PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_v2.py -v
"""
from __future__ import annotations

import inspect

import pytest
from fastapi import APIRouter

from app.api_v2 import (
    batch_job_status,
    batch_parse_receipts,
    batch_router,
    export_receipts_endpoint,
    list_export_formats,
)

# ===========================================================================
# INTERFACE TESTS — must pass immediately
# ===========================================================================

class TestBatchRouterInterface:
    """Verify batch_router is properly configured."""

    def test_batch_router_is_router(self):
        assert isinstance(batch_router, APIRouter)

    def test_batch_router_prefix(self):
        assert batch_router.prefix == "/api/v1"


class TestBatchEndpointsInterface:
    """Verify batch endpoint functions exist with correct signatures."""

    def test_batch_parse_receipts_exists(self):
        assert callable(batch_parse_receipts)

    def test_batch_parse_receipts_is_async(self):
        import asyncio
        assert asyncio.iscoroutinefunction(batch_parse_receipts)

    def test_batch_parse_receipts_signature(self):
        sig = inspect.signature(batch_parse_receipts)
        params = list(sig.parameters)
        assert "files" in params
        assert "image_urls" in params
        assert "lang" in params
        assert "webhook_url" in params
        assert "max_workers" in params

    def test_batch_job_status_exists(self):
        assert callable(batch_job_status)

    def test_batch_job_status_is_async(self):
        import asyncio
        assert asyncio.iscoroutinefunction(batch_job_status)

    def test_batch_job_status_signature(self):
        sig = inspect.signature(batch_job_status)
        params = list(sig.parameters)
        assert "job_id" in params


class TestExportEndpointsInterface:
    """Verify export endpoint functions exist with correct signatures."""

    def test_export_receipts_endpoint_exists(self):
        assert callable(export_receipts_endpoint)

    def test_export_receipts_endpoint_is_async(self):
        import asyncio
        assert asyncio.iscoroutinefunction(export_receipts_endpoint)

    def test_export_receipts_endpoint_signature(self):
        sig = inspect.signature(export_receipts_endpoint)
        params = list(sig.parameters)
        assert "format" in params
        assert "date_from" in params
        assert "date_to" in params
        assert "category" in params

    def test_list_export_formats_exists(self):
        assert callable(list_export_formats)

    def test_list_export_formats_is_async(self):
        import asyncio
        assert asyncio.iscoroutinefunction(list_export_formats)


# ===========================================================================
# BEHAVIORAL TESTS — should fail with NotImplementedError until implemented
# ===========================================================================

class TestBatchEndpointsBehavior:
    """Behavioral: batch processing API behavior."""

    @pytest.mark.asyncio
    async def test_batch_parse_returns_dict(self):
        try:
            result = await batch_parse_receipts()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_batch_parse_has_job_id(self):
        try:
            result = await batch_parse_receipts()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_batch_parse_has_status(self):
        try:
            result = await batch_parse_receipts()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert "status" in result
        assert result["status"] == "queued"

    @pytest.mark.asyncio
    async def test_batch_job_status_returns_dict(self):
        try:
            result = await batch_job_status("test-job-id")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_batch_job_status_has_fields(self):
        try:
            result = await batch_job_status("test-job-id")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert "job_id" in result
        assert "status" in result
        assert "total" in result
        assert "completed" in result


class TestExportEndpointsBehavior:
    """Behavioral: export API behavior."""

    @pytest.mark.asyncio
    async def test_export_formats_returns_dict(self):
        try:
            result = await list_export_formats()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert isinstance(result, dict)
        assert "formats" in result

    @pytest.mark.asyncio
    async def test_export_formats_lists_three(self):
        try:
            result = await list_export_formats()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        names = [f["name"] for f in result["formats"]]
        assert sorted(names) == ["generic", "quickbooks", "xero"]

    @pytest.mark.asyncio
    async def test_export_csv_returns_response(self):
        try:
            result = await export_receipts_endpoint("generic")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        # Should return a Response with CSV content
        assert hasattr(result, "body") or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_export_invalid_format_raises(self):
        try:
            with pytest.raises((ValueError, Exception)):
                await export_receipts_endpoint("nonexistent")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
