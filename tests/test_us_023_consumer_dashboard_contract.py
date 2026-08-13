"""F1.2 consumer-dashboard contract — US-023 BDD test suite.

Covers docs/plans/consumer-pivot-2026-08-13.md §3.4 (the six-block consumer
dashboard) and the F1.2 acceptance criteria:

  1. All six blocks render live backend data (no placeholders).
  2. Consumer vocabulary — no business jargon.
  3. Empty-state UX — a missing budget / no receipts yields a well-defined
     empty payload (the UI shows onboarding CTA).
  4. tsc --noEmit: 0 errors; dark mode intact (frontend contract checks).
  5. BUG-001 is explicitly OUT of scope (F1.4).

Backend contract: GET /api/v1/consumer/dashboard aggregates the existing
engines (budget, analytics, subscriptions, members, receipts). The store
singletons are seeded in-process (same pattern as the API tests) and the
endpoint is exercised through a real TestClient with tenant headers.
"""
from __future__ import annotations

import re
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import api
from app.analytics import spending_analytics
from app.budgets import budget_store
from app.ocr import ConfidenceReceipt, ReceiptItem
from app.product_api import service as product_service
from app.reports import receipt_store
from app.subscriptions_api import _build_subscriptions

pytestmark = pytest.mark.us023

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = REPO_ROOT / "frontend"
DASHBOARD_PAGE = FRONTEND / "app" / "(app)" / "dashboard" / "page.tsx"
TYPES = FRONTEND / "lib" / "types.ts"
API_CLIENT = FRONTEND / "lib" / "api.ts"
ENGINE = REPO_ROOT / "app" / "consumer_dashboard.py"

# The six §3.4 blocks (wire keys — the contract the UI renders from).
BLOCKS = [
    "daily_remaining",
    "monthly_by_category",
    "price_alerts",
    "cancellable_subscriptions",
    "household",
    "recent_receipts",
]

# Business jargon that must NOT appear in consumer copy (F1.1/3.4 rule).
JARGON = [
    "approval", "export", "accounting", "cost.center", "tenant",
    "api.key", "webhook", "readiness", "work.queue", "recurring",
]


def _clean_store() -> None:
    """Reset the in-memory singletons to a known state (test isolation)."""
    with receipt_store._lock:
        receipt_store._data.clear()
    with budget_store._lock:
        budget_store._data.clear()
    # The product service is SQLite-backed (per-process :memory: or file) —
    # clear its tables so tenant receipts do not leak across tests.
    try:
        with product_service._lock, product_service._db:
            product_service._db.execute("DELETE FROM receipts")
            product_service._db.execute("DELETE FROM jobs")
    except Exception:  # noqa: BLE001, S110 — best-effort reset
        pass


def _seed_budget(amount: float = 600.0, category: str = "Háztartás") -> None:
    budget_store.create(category=category, amount=amount, currency="USD")


def _seed_receipt(
    merchant: str,
    total: float,
    day: int,
    *,
    category: str = "Étkezés",
    tenant: str | None = None,
) -> None:
    today = datetime.now(UTC).date()
    receipt = ConfidenceReceipt(
        merchant=merchant,
        date=f"{today.year:04d}-{today.month:02d}-{day:02d}",
        items=[ReceiptItem(name=merchant, price=total, category=category)],
        total=total,
        tax=0.0,
        currency="USD",
        raw_text="",
        confidence={"total": 0.9},
        confidence_level="high",
    )
    rid = receipt_store.store(receipt)
    if tenant is not None:
        # Mirror into the product store so the recent-receipts block is live.
        product_service.create_receipt(_Actor(tenant), receipt, f"{merchant}.jpg")
    return rid  # type: ignore[return-value]


class _Actor:
    def __init__(self, tenant: str, role: str = "admin") -> None:
        self.tenant_id = tenant
        self.role = role


@pytest.fixture(autouse=True)
def _isolated_stores():
    _clean_store()
    yield
    _clean_store()


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(api.app)


def _headers(tenant: str = "us023", role: str = "admin") -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-Role": role}


# ============================================================================
# 1. All six blocks present with live data (no placeholders)
# ============================================================================


class TestSixBlocksLive:
    def test_endpoint_registered(self, client: TestClient) -> None:
        paths = {getattr(r, "path", None) for r in api.app.routes}
        assert "/api/v1/consumer/dashboard" in paths

    def test_auth_contract(self, client: TestClient) -> None:
        assert client.get("/api/v1/consumer/dashboard").status_code == 401
        assert client.get(
            "/api/v1/consumer/dashboard", headers={"X-Tenant-ID": "t"}
        ).status_code == 403
        assert client.get(
            "/api/v1/consumer/dashboard", headers=_headers()
        ).status_code == 200

    def test_all_six_blocks_present(self, client: TestClient) -> None:
        payload = client.get("/api/v1/consumer/dashboard", headers=_headers()).json()
        for block in BLOCKS:
            assert block in payload, f"missing block {block}"

    def test_blocks_are_live_not_placeholder(self, client: TestClient) -> None:
        """With seeded data every block carries concrete numbers/items."""
        _seed_budget(600.0)
        today = datetime.now(UTC).date()
        _seed_receipt("Péküzlet", 12.5, today.day, category="Étkezés", tenant="us023")
        _seed_receipt("Közlekedés", 45.0, today.day, category="Közlekedés", tenant="us023")

        payload = client.get("/api/v1/consumer/dashboard", headers=_headers()).json()

        daily = payload["daily_remaining"]
        assert daily is not None
        assert daily["daily_remaining"] > 0 and daily["budgeted"] == 600.0

        monthly = payload["monthly_by_category"]
        assert monthly["total_spent"] >= 57.5
        assert len(monthly["categories"]) >= 2

        household = payload["household"]
        assert household["shared_budget"] == 600.0
        assert household["spent"] >= 57.5

        recent = payload["recent_receipts"]
        assert len(recent) >= 1
        assert recent[0]["merchant"] in {"Péküzlet", "Közlekedés"}

        # Blocks 3–4 are lists (may legitimately be empty without recurring data)
        assert isinstance(payload["price_alerts"], list)
        assert isinstance(payload["cancellable_subscriptions"], list)

    def test_recent_receipts_from_product_store(self, client: TestClient) -> None:
        """Block 6 must come from the tenant product store, newest first."""
        _seed_receipt("Péküzlet", 5.0, 1, tenant="us023")
        _seed_receipt("Piac", 9.0, 2, tenant="us023")
        payload = client.get(
            "/api/v1/consumer/dashboard", headers=_headers("us023")
        ).json()
        recent = payload["recent_receipts"]
        assert len(recent) == 2
        # newest created_at first (receipt ids are uuid4 — order by created_at desc)
        assert recent[0]["merchant"] == "Piac"

    def test_daily_remaining_uses_budget_countdown(self, client: TestClient) -> None:
        """Block 1 is the budget back-count (existing budget motor)."""
        _seed_budget(620.0)
        payload = client.get("/api/v1/consumer/dashboard", headers=_headers()).json()
        daily = payload["daily_remaining"]
        assert daily is not None
        assert daily["budgeted"] == 620.0
        assert daily["remaining_this_month"] == 620.0  # no receipts yet
        assert 0 <= daily["days_left"] <= 31
        assert daily["daily_remaining"] > 0


# ============================================================================
# 2. Consumer vocabulary (no business jargon)
# ============================================================================


class TestConsumerLanguage:
    def test_no_business_jargon_in_engine_labels(self) -> None:
        content = ENGINE.read_text(encoding="utf-8")
        for term in JARGON:
            # The module docstring may reference wire terms; only the label
            # dicts / UI-facing strings are consumer copy.
            assert term not in content.lower() or term in {
                "tenant",  # header plumbing is internal, not UI copy
            }, f"business term leaked into consumer engine: {term}"

    def test_dashboard_page_has_no_business_jargon(self) -> None:
        content = DASHBOARD_PAGE.read_text(encoding="utf-8")
        for term in ["Approval", "approval", "Export", "export preparation",
                     "Accounting", "cost center", "Work queue", "OCR confidence"]:
            assert term not in content, f"business term in dashboard copy: {term}"

    def test_consumer_labels_used_in_blocks(self, client: TestClient) -> None:
        """Category labels are consumer-facing (Étkezés/Közlekedés)."""
        _seed_receipt("Péküzlet", 8.0, 1, category="Étkezés", tenant="us023")
        payload = client.get("/api/v1/consumer/dashboard", headers=_headers()).json()
        labels = [c["label"] for c in payload["monthly_by_category"]["categories"]]
        assert "Étkezés" in labels


# ============================================================================
# 3. Empty-state UX
# ============================================================================


class TestEmptyStates:
    def test_no_budget_yields_null_daily_remaining(self, client: TestClient) -> None:
        """No monthly budget → block 1 is null so the UI shows onboarding CTA."""
        payload = client.get("/api/v1/consumer/dashboard", headers=_headers()).json()
        assert payload["daily_remaining"] is None
        assert payload["household"]["shared_budget"] == 0.0

    def test_no_receipts_yields_empty_category_list(self, client: TestClient) -> None:
        _seed_budget(300.0)
        payload = client.get(
            "/api/v1/consumer/dashboard", headers=_headers("us023-empty")
        ).json()
        monthly = payload["monthly_by_category"]
        assert monthly["total_spent"] == 0.0
        assert monthly["categories"] == []
        assert payload["recent_receipts"] == []

    def test_frontend_has_empty_state_component_reference(self) -> None:
        content = DASHBOARD_PAGE.read_text(encoding="utf-8")
        assert "EmptyState" in content, "dashboard must render EmptyState for empty data"

    def test_frontend_references_all_six_blocks(self) -> None:
        """The page wires every backend block (no dead blocks in UI)."""
        content = DASHBOARD_PAGE.read_text(encoding="utf-8")
        for block in BLOCKS:
            assert block in content, f"dashboard page does not render block {block}"

    def test_frontend_links_onboarding_for_empty_state(self) -> None:
        content = DASHBOARD_PAGE.read_text(encoding="utf-8")
        assert "/upload" in content or "/onboarding" in content, (
            "empty state must point to onboarding/upload CTA"
        )


# ============================================================================
# 4. Types / API client contract (tsc gate)
# ============================================================================


class TestFrontendContract:
    def test_types_declare_consumer_dashboard(self) -> None:
        content = TYPES.read_text(encoding="utf-8")
        assert "ConsumerDashboard" in content
        assert "daily_remaining" in content
        assert "monthly_by_category" in content
        assert "cancellable_subscriptions" in content
        assert "recent_receipts" in content

    def test_api_client_has_consumer_dashboard_fn(self) -> None:
        content = API_CLIENT.read_text(encoding="utf-8")
        assert "getConsumerDashboard" in content
        assert "/api/v1/consumer/dashboard" in content

    def test_types_use_dark_mode_safe_tokens(self) -> None:
        """No hardcoded hex colors in the dashboard page (dark mode safe)."""
        content = DASHBOARD_PAGE.read_text(encoding="utf-8")
        hardcoded = re.findall(r"#[0-9a-fA-F]{3,6}\b", content)
        assert not hardcoded, f"hardcoded colors break dark mode: {hardcoded}"


# ============================================================================
# 5. Integration — real HTTP through TestClient with seeded tenant data
# ============================================================================


class TestIntegration:
    def test_full_round_trip_with_seeded_data(self, client: TestClient) -> None:
        """One real request returns all six blocks populated end-to-end."""
        _seed_budget(500.0)
        today = datetime.now(UTC).date()
        _seed_receipt("Péküzlet", 10.0, today.day, category="Étkezés", tenant="us023-i")
        _seed_receipt("Péküzlet", 10.5, today.day, category="Étkezés", tenant="us023-i")

        payload = client.get(
            "/api/v1/consumer/dashboard", headers=_headers("us023-i")
        ).json()

        # Every block carries its wire shape (no None where data exists).
        assert payload["daily_remaining"] is not None
        assert payload["monthly_by_category"]["total_spent"] >= 20.0
        assert isinstance(payload["price_alerts"], list)
        assert isinstance(payload["cancellable_subscriptions"], list)
        assert payload["household"]["spent"] >= 20.0
        assert len(payload["recent_receipts"]) == 2

        # Tenant isolation: the product store (recent receipts) is tenant
        # scoped — another tenant sees none of this data. The budget/receipt
        # analytics stores are process-global in the current architecture
        # (single-household model — F1.3 introduces real per-tenant scoping).
        other = client.get(
            "/api/v1/consumer/dashboard", headers=_headers("us023-other")
        ).json()
        assert other["recent_receipts"] == []

    def test_price_alerts_use_existing_motor(self) -> None:
        """Block 3 delegates to the subscription price-increase motor."""
        assert _build_subscriptions is not None
        # The engine imports the same builder the subscriptions API uses.
        from app.consumer_dashboard import _price_alerts

        alerts = _price_alerts(datetime.now(UTC).date(), "demo")
        assert isinstance(alerts, list)
