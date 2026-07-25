"""Pre-development interface + behavioral tests for Budget CRUD API.

Covers P0-2: Budget CRUD POST/PUT/GET/DELETE /api/v1/budgets.

Layout:
  * Interface tests  — import, signature, class-existence checks.
    These MUST pass immediately (stubs exist with correct signatures).
  * Behavioral tests — real acceptance-criteria assertions that will fail
    with NotImplementedError until the feature is implemented.

Run with:
    pytest tests/test_budgets.py -v
"""
from __future__ import annotations

import inspect

import pytest
from starlette.testclient import TestClient

from app import api
from app.budgets import BudgetPeriod, BudgetRecord, BudgetStore, budget_store

# ============================================================================
# Fixtures / helpers
# ============================================================================


@pytest.fixture
def store() -> BudgetStore:
    return BudgetStore()


@pytest.fixture
def client() -> TestClient:
    return TestClient(api.app)


def _route_paths() -> set[str]:
    return {getattr(r, "path", None) for r in api.app.routes}


# ============================================================================
# INTERFACE TESTS — must pass immediately
# ============================================================================


class TestBudgetStoreInterface:
    """P0-2: BudgetStore class import and signature checks."""

    def test_budget_store_importable(self) -> None:
        assert BudgetStore is not None

    def test_budget_record_importable(self) -> None:
        assert BudgetRecord is not None

    def test_budget_period_enum(self) -> None:
        assert BudgetPeriod.WEEKLY.value == "weekly"
        assert BudgetPeriod.MONTHLY.value == "monthly"
        assert BudgetPeriod.YEARLY.value == "yearly"

    def test_budget_store_singleton_exists(self) -> None:
        assert budget_store is not None
        assert isinstance(budget_store, BudgetStore)

    def test_budget_store_has_create_method(self) -> None:
        assert hasattr(BudgetStore, "create")
        assert callable(BudgetStore.create)

    def test_budget_store_create_signature(self) -> None:
        """create(category, amount, **kwargs) -> BudgetRecord"""
        sig = inspect.signature(BudgetStore.create)
        params = list(sig.parameters)
        assert "category" in params
        assert "amount" in params

    def test_budget_store_has_get_method(self) -> None:
        assert hasattr(BudgetStore, "get")
        assert callable(BudgetStore.get)

    def test_budget_store_has_list_method(self) -> None:
        assert hasattr(BudgetStore, "list")
        assert callable(BudgetStore.list)

    def test_budget_store_has_update_method(self) -> None:
        assert hasattr(BudgetStore, "update")
        assert callable(BudgetStore.update)

    def test_budget_store_has_delete_method(self) -> None:
        assert hasattr(BudgetStore, "delete")
        assert callable(BudgetStore.delete)

    def test_budget_endpoints_exist(self) -> None:
        """All budget CRUD routes should be registered."""
        paths = _route_paths()
        assert "/api/v1/budgets" in paths  # POST + GET (list)

    def test_budget_by_id_endpoint_exists(self) -> None:
        paths = _route_paths()
        assert any(
            p and "/api/v1/budgets/" in p and "{id}" in p
            for p in paths
        )


# ============================================================================
# BEHAVIORAL TESTS — fail until implementation
# ============================================================================


class TestBudgetStoreBehavioral:
    """Real acceptance criteria that fail with NotImplementedError."""

    def test_create_budget_valid(self, store: BudgetStore) -> None:
        """AC2-1: Create budget with valid data returns BudgetRecord."""
        record = store.create(
            category="Meals & Entertainment",
            amount=500.0,
            currency="USD",
            period="monthly",
        )
        assert record is not None
        assert record.category == "Meals & Entertainment"
        assert record.amount == 500.0
        assert record.budget_id is not None

    def test_create_budget_negative_amount_raises(self, store: BudgetStore) -> None:
        """AC2-2: Amount <= 0 should raise ValueError (→ 422)."""
        with pytest.raises((ValueError, AssertionError)):
            store.create(category="Test", amount=-10.0)

    def test_create_budget_invalid_period_raises(self, store: BudgetStore) -> None:
        """AC2-3: Invalid period should raise ValueError (→ 422)."""
        with pytest.raises((ValueError, AssertionError)):
            store.create(
                category="Test", amount=100.0, period="decade"
            )

    def test_create_budget_invalid_threshold_raises(self, store: BudgetStore) -> None:
        """AC2-4: alert_threshold outside 0.0-1.0 should raise ValueError."""
        with pytest.raises((ValueError, AssertionError)):
            store.create(
                category="Test", amount=100.0, alert_threshold=1.5
            )

    def test_update_budget_existing(self, store: BudgetStore) -> None:
        """AC2-5: Update existing budget fields."""
        record = store.create(category="Test", amount=100.0)
        updated = store.update(record.budget_id, amount=200.0)
        assert updated is not None
        assert updated.amount == 200.0

    def test_update_budget_nonexistent_returns_none(self, store: BudgetStore) -> None:
        """AC2-6: Update non-existent budget returns None (→ 404)."""
        result = store.update("nonexistent-id", amount=200.0)
        assert result is None

    def test_delete_budget_existing(self, store: BudgetStore) -> None:
        """AC2-7: Delete existing budget returns True."""
        record = store.create(category="Test", amount=100.0)
        assert store.delete(record.budget_id) is True

    def test_delete_budget_nonexistent_returns_false(self, store: BudgetStore) -> None:
        """AC2-8: Delete non-existent budget returns False (→ 404)."""
        assert store.delete("nonexistent-id") is False

    def test_list_budgets_returns_all(self, store: BudgetStore) -> None:
        """AC2-9: List budgets includes all created budgets."""
        a = store.create(category="Food", amount=200.0)
        b = store.create(category="Transport", amount=100.0)
        all_budgets = store.list()
        ids = [r.budget_id for r in all_budgets]
        assert a.budget_id in ids
        assert b.budget_id in ids

    def test_get_budget_by_id(self, store: BudgetStore) -> None:
        """AC2-10: Get by id returns correct record."""
        record = store.create(category="Shopping", amount=300.0)
        fetched = store.get(record.budget_id)
        assert fetched is not None
        assert fetched.category == "Shopping"
        assert fetched.amount == 300.0
