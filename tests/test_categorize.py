"""Pre-development interface + behavioral tests for Categorizer API.

Covers P0-1: keyword/regex categorizer + optional LLM fallback.

Layout (follows repo pre-tester conventions):
  * Interface tests  — import, signature/type-hint, class-existence checks.
    These MUST pass immediately (stubs exist with correct signatures).
  * Behavioral tests — real acceptance-criteria assertions that will fail
    with NotImplementedError until the feature is implemented.

Run with:
    pytest tests/test_categorize.py -v
"""
from __future__ import annotations

import inspect

import pytest
from starlette.testclient import TestClient

from app import api
from app.categorizer import CategorizationResult, Categorizer

# ============================================================================
# Fixtures / helpers
# ============================================================================


@pytest.fixture
def categorizer() -> Categorizer:
    return Categorizer()


@pytest.fixture
def client() -> TestClient:
    return TestClient(api.app)


def _route_paths() -> set[str]:
    return {getattr(r, "path", None) for r in api.app.routes}


# ============================================================================
# INTERFACE TESTS — must pass immediately
# ============================================================================


class TestCategorizerInterface:
    """P0-1: Categorizer class import and signature checks."""

    def test_categorizer_importable(self) -> None:
        assert Categorizer is not None

    def test_categorization_result_importable(self) -> None:
        assert CategorizationResult is not None

    def test_categorizer_has_categorize_method(self) -> None:
        assert hasattr(Categorizer, "categorize")
        assert callable(Categorizer.categorize)

    def test_categorizer_categorize_signature(self) -> None:
        """categorize(vendor, total=None, line_items=None) -> CategorizationResult"""
        sig = inspect.signature(Categorizer.categorize)
        params = list(sig.parameters)
        assert "vendor" in params
        assert "total" in params
        assert "line_items" in params
        assert sig.return_annotation in (CategorizationResult, "CategorizationResult")

    def test_categorizer_has_categorize_batch(self) -> None:
        assert hasattr(Categorizer, "categorize_batch")
        assert callable(Categorizer.categorize_batch)

    def test_categorize_endpoint_exists(self) -> None:
        """POST /api/v1/categorize should be registered."""
        assert "/api/v1/categorize" in _route_paths()


# ============================================================================
# BEHAVIORAL TESTS — fail until implementation
# ============================================================================


class TestCategorizeBehavioral:
    """Real acceptance criteria that fail with NotImplementedError."""

    def test_known_merchant_returns_category(self, categorizer: Categorizer) -> None:
        """AC1-3: STARBUCKS → 'Meals & Entertainment'."""
        result = categorizer.categorize(vendor="STARBUCKS COFFEE")
        assert result.category == "Meals & Entertainment"
        assert result.confidence == "high"

    def test_known_merchant_shell_returns_transportation(
        self, categorizer: Categorizer
    ) -> None:
        """AC1-3: SHELL → 'Transportation'."""
        result = categorizer.categorize(vendor="SHELL GAS STATION")
        assert result.category == "Transportation"
        assert result.confidence == "high"

    def test_unknown_merchant_returns_uncategorized(
        self, categorizer: Categorizer
    ) -> None:
        """AC1-4: Unknown vendor → 'Uncategorized', confidence 'low'."""
        result = categorizer.categorize(vendor="RANDOM SHOP 42")
        assert result.category == "Uncategorized"
        assert result.confidence == "low"

    def test_empty_line_items_accepted(self, categorizer: Categorizer) -> None:
        """AC1-6: Empty line_items is accepted (optional field)."""
        result = categorizer.categorize(
            vendor="STARBUCKS", line_items=[]
        )
        assert result.category == "Meals & Entertainment"

    def test_categorize_endpoint_missing_vendor_422(self, client: TestClient) -> None:
        """AC1-5: Missing vendor field returns 422."""
        resp = client.post("/api/v1/categorize", json={"total": 5.75})
        assert resp.status_code == 422

    def test_categorize_endpoint_unknown_vendor_low_confidence(
        self, client: TestClient
    ) -> None:
        """Unknown vendor via endpoint returns 200 with 'Uncategorized'."""
        resp = client.post(
            "/api/v1/categorize",
            json={"vendor": "UNKNOWN SHOP", "total": 10.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["category"] == "Uncategorized"
        assert data["confidence"] == "low"

    def test_llm_fallback_on_no_rule_match(self, categorizer: Categorizer) -> None:
        """AC1-7: When LLM_API_KEY is set and no rule matches, call httpx."""
        import os
        original = os.environ.get("LLM_API_KEY")
        os.environ["LLM_API_KEY"] = "test-key"
        try:
            _ = categorizer.categorize(vendor="OBSCURE VENUE")
        finally:
            if original:
                os.environ["LLM_API_KEY"] = original
            else:
                del os.environ["LLM_API_KEY"]

    def test_llm_fallback_no_key_returns_uncategorized(
        self, categorizer: Categorizer
    ) -> None:
        """AC1-8: When LLM_API_KEY is not set, unknown → Uncategorized."""
        import os
        original = os.environ.get("LLM_API_KEY")
        if "LLM_API_KEY" in os.environ:
            del os.environ["LLM_API_KEY"]
        try:
            result = categorizer.categorize(vendor="MYSTERY VENDOR")
            assert result.category == "Uncategorized"
        finally:
            if original:
                os.environ["LLM_API_KEY"] = original

    def test_llm_fallback_httpx_failure_graceful(
        self, categorizer: Categorizer
    ) -> None:
        """AC1-9: httpx timeout/error → Uncategorized gracefully."""
        import os
        original = os.environ.get("LLM_API_KEY")
        os.environ["LLM_API_KEY"] = "test-key"
        os.environ["LLM_BASE_URL"] = "http://localhost:1/invalid"
        try:
            result = categorizer.categorize(vendor="UNREACHABLE VENDOR")
            # Should not raise — should fall back gracefully
            assert result.category == "Uncategorized"
        finally:
            if original:
                os.environ["LLM_API_KEY"] = original
            else:
                del os.environ["LLM_API_KEY"]
            os.environ.pop("LLM_BASE_URL", None)

    def test_categorize_endpoint_known_merchant(
        self, client: TestClient
    ) -> None:
        """Endpoint integration: known merchant returns expected category."""
        resp = client.post(
            "/api/v1/categorize",
            json={"vendor": "STARBUCKS COFFEE", "total": 5.75},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["category"] == "Meals & Entertainment"
        assert "confidence" in data
