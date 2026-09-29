"""RED anti-drift gate for D2 — the dashboard's savings block is not wired yet.

``GET /api/v1/consumer/dashboard`` (app/api.py:316 -> app/consumer_dashboard.py:314
``build_consumer_dashboard``) still returns the pre-D2 eight-key payload. There is
no ``savings`` key, so this test is RED with ``KeyError: "savings"`` until the
implementer adds the block per docs/plans/dashboard-wiring-spec.md Decisions 1-4.

The point of AC-D2-2 is DRIFT, not shape: a second hand-copied aggregation inside
``consumer_dashboard.py`` would satisfy a key-existence check and then silently
disagree with ``GET /api/v1/analytics/savings-summary`` (app/api.py:1538) forever
after. The dashboard block must therefore be a pass-through of the very same
engine, and the only way to prove that is to compare the two live responses field
for field in the SAME test run, with the same tenant and the same period.

Per-key comparison is mandatory: the dashboard block legitimately carries a
SEVENTH key (``recurring``) on top of the six summary keys, so whole-dict equality
is guaranteed to fail even on a correct implementation. Only the six shared keys
are compared.

The fixture straddles the 45-day midpoint of the 90d window on purpose and the
non-zero ``potential_saving`` precondition is asserted BEFORE the parity
comparison, so a fixture that collapsed into one half (guard-tripped to 0.0) can
never let this gate pass vacuously.

Patterns (isolated client, ProductService, ``_parsed`` with a real ``category``,
seed helper) are copied from tests/test_red_savings_store_fix.py — not imported
from it, so this file stays independently readable.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.api
from app.product_api import Actor
from app.product_service import ProductService
from app.reports import receipt_store

HEADERS = {"X-Role": "admin"}
TENANT = "dashwire"

# The six keys the dashboard block and the savings endpoint must agree on.
# ``recurring`` is deliberately absent: it is the dashboard-only extra (spec
# Decision 1), and comparing it here would be a shape check, not a drift check.
SHARED_KEYS = (
    "period",
    "potential_saving",
    "total_spent",
    "avg_by_category",
    "currency",
    "top_candidates",
)


def _date_ago(days: int) -> str:
    return (datetime.now(UTC).date() - timedelta(days=days)).isoformat()


def _parsed(merchant: str, total: float, when: str, category: str) -> SimpleNamespace:
    """Parsed-receipt stand-in that CARRIES a category.

    Same hazard as tests/test_red_savings_store_fix.py:49-70 — drop ``category``
    and ``product_service`` emits ``getattr(i, "category", None) -> None``, every
    line collapses into ``Uncategorized``, and ``avg_by_category`` parity is
    compared against a degenerate key.
    """
    return SimpleNamespace(
        merchant=merchant,
        date=when,
        total=total,
        tax=0.0,
        currency="USD",
        items=[SimpleNamespace(name=merchant, price=total, category=category)],
        confidence={
            "vendor": 0.95,
            "date": 0.95,
            "total": 0.95,
            "tax": 0.95,
            "currency": 0.95,
        },
    )


def _seed(service: ProductService, tenant: str, merchant: str, total: float, when: str) -> str:
    """Seed one receipt through the production write path (ProductService -> SQLite)."""
    actor = Actor(tenant, "admin")
    return service.create_receipt(actor, _parsed(merchant, total, when, "Groceries"), f"{merchant}.png")[
        "receipt_id"
    ]


def _isolated_client(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, ProductService]:
    """Fresh SQLite product store + cleared in-memory store (no cross-test bleed)."""
    service = ProductService(":memory:")
    monkeypatch.setattr("app.api.service", service)
    monkeypatch.setattr("app.product_api.service", service)
    with receipt_store._lock:
        receipt_store._data.clear()
        receipt_store._tenants.clear()
    return TestClient(app.api.app), service


def _seed_straddling(service: ProductService, tenant: str) -> None:
    """AC-D2-2 fixture — one category, both halves of the 90d window populated.

    ``_period_bounds("90d")`` puts the midpoint at ``today - 45``, so:

    * 10.0 (60d) + 30.0 (50d) -> EARLY half, mean 20.0
    * 40.0 (40d) + 40.0 (30d) -> LATE  half, mean 40.0

    ``potential_saving = max(0.0, 40.0 - 20.0) = 20.0`` (spec section 1, both halves
    clearing the ``count >= 2`` guard). Two rows per half are load-bearing: a single
    late row would guard-trip the category and force 0.0, which is the vacuous green
    this test explicitly rules out. Distinct merchants keep ``RecurringAnalytics``
    quiet so ``top_candidates`` stays a stable value on both sides.
    """
    _seed(service, tenant, "WireA1", 10.0, _date_ago(60))
    _seed(service, tenant, "WireA2", 30.0, _date_ago(50))
    _seed(service, tenant, "WireA3", 40.0, _date_ago(40))
    _seed(service, tenant, "WireA4", 40.0, _date_ago(30))


def _stored_payloads(service: ProductService, tenant: str) -> list[dict[str, Any]]:
    rows = service._db.execute(
        "SELECT payload FROM receipts WHERE tenant_id=?", (tenant,)
    ).fetchall()
    return [json.loads(row["payload"]) for row in rows]


def _assert_fixture_landed(service: ProductService, tenant: str, expected_rows: int) -> None:
    """Precondition, read back from SQLite: the fixture really persisted with categories.

    Without this, a silent seed failure is indistinguishable from a correct 0.0.
    """
    payloads = _stored_payloads(service, tenant)
    assert len(payloads) == expected_rows, f"fixture did not persist: {payloads}"
    categories = {item["category"] for p in payloads for item in p["line_items"]}
    assert categories == {"Groceries"}, f"category lost on the write path: {categories}"


def _assert_half_split(service: ProductService, tenant: str, expected_early: int) -> None:
    """Precondition: the fixture really straddles the midpoint, by the engine's predicate.

    ``is_early(d) = 2 * (d - date_from).days < span`` (app/savings.py ``_half_means``,
    spec section 1) instead of a hand-rolled date comparison, so the fixture is
    validated with the same rule the product code applies.
    """
    today = datetime.now(UTC).date()
    date_from, date_to = today - timedelta(days=90), today
    span = (date_to - date_from).days
    early = late = 0
    for payload in _stored_payloads(service, tenant):
        day = date.fromisoformat(str(payload["date"]))
        if not (date_from <= day <= date_to):
            continue
        if 2 * (day - date_from).days < span:
            early += 1
        else:
            late += 1
    assert early == expected_early, f"expected {expected_early} early receipts, got {early}"
    assert late == expected_early, f"expected {expected_early} late receipts, got {late}"


def _headers(tenant: str) -> dict[str, str]:
    return {**HEADERS, "X-Tenant-ID": tenant}


@pytest.mark.test_id("TEST-DASHWIRE-001")
@pytest.mark.requirements("REQ-F2-2b")
@pytest.mark.scenario("AC-D2-2")
def test_dashboard_savings_matches_the_savings_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-D2-2 — the dashboard's savings block equals
    GET /api/v1/analytics/savings-summary for the same tenant+period."""
    client, service = _isolated_client(monkeypatch)
    _seed_straddling(service, TENANT)
    _assert_fixture_landed(service, TENANT, 4)
    _assert_half_split(service, TENANT, expected_early=2)

    summary_response = client.get(
        "/api/v1/analytics/savings-summary?period=90d", headers=_headers(TENANT)
    )
    assert summary_response.status_code == 200, summary_response.text
    summary = summary_response.json()

    # Non-vacuity FIRST: a guard-tripped fixture (0.0) would make every parity
    # comparison below trivially true on both sides.
    assert summary["potential_saving"] != 0, (
        f"fixture produced no saving to compare — parity assertions would be vacuous: {summary}"
    )

    dashboard_response = client.get("/api/v1/consumer/dashboard", headers=_headers(TENANT))
    assert dashboard_response.status_code == 200, dashboard_response.text
    dashboard = dashboard_response.json()

    # The RED: no "savings" key until the block is wired (app/consumer_dashboard.py:317-326).
    savings = dashboard["savings"]

    for key in SHARED_KEYS:
        assert savings[key] == summary[key], f"savings block drifted on {key!r}"

    # AC-D2-2 also binds the echoed period, not just the values.
    assert savings["period"] == "90d" == summary["period"]


@pytest.mark.test_id("TEST-DASHWIRE-002")
@pytest.mark.requirements("REQ-F2-2b")
@pytest.mark.scenario("AC-D2-1")
def test_dashboard_key_sets_are_exactly_the_contracted_ones(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-D2-1 — the wire shape is EXACTLY nine top-level keys + seven savings keys.

    Both assertions are ``==`` on the whole ``set(...)``, not ``issubset``/``in``:
    an extra key is as much a contract break as a missing one, and a subset
    check would have passed against the pre-D2 eight-key payload — which is the
    regression this gate exists to catch.

    The seventh savings key is ``savings_candidates`` (app/consumer_dashboard.py:326),
    NOT ``recurring``: docs/plans/dashboard-wiring-spec.md:25/36 still names
    ``recurring``, which is stale relative to the implemented key. A payload
    carrying the spec's literal ``recurring`` is a failure here on purpose.
    """
    client, service = _isolated_client(monkeypatch)
    _seed_straddling(service, TENANT)
    _assert_fixture_landed(service, TENANT, 4)

    response = client.get(
        "/api/v1/consumer/dashboard?period=90d", headers=_headers(TENANT)
    )
    assert response.status_code == 200, response.text
    dashboard = response.json()

    assert set(dashboard.keys()) == {
        "generated_at",
        "tenant",
        "daily_remaining",
        "monthly_by_category",
        "price_alerts",
        "cancellable_subscriptions",
        "household",
        "recent_receipts",
        "savings",
    }, f"top-level key set drifted: {sorted(dashboard.keys())}"

    assert set(dashboard["savings"].keys()) == {
        "period",
        "potential_saving",
        "total_spent",
        "avg_by_category",
        "currency",
        "top_candidates",
        "savings_candidates",
    }, f"savings sub-key set drifted: {sorted(dashboard['savings'].keys())}"


@pytest.mark.test_id("TEST-DASHWIRE-003")
@pytest.mark.scenario("AC-D2-3")
@pytest.mark.requirements("REQ-F2-2b")
def test_dashboard_potential_saving_is_windowed_by_the_period_param(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-D2-3 — the period param actually re-windows the savings engine.

    Literal expectations, deliberately NOT recomputed from the engine, so this
    is a value contract rather than a tautology:

    * 90d: _period_bounds midpoint at today-45 -> early {10.0, 30.0} mean 20.0,
      late {40.0, 40.0} mean 40.0 -> ``max(0, 40.0 - 20.0) = 20.0``.
    * 30d: the 60d-ago and 50d-ago records fall outside the window entirely, so
      ``Groceries`` has one early line and one late line. Both fail the
      ``len(early) >= 2 and len(late) >= 2`` guard (app/savings.py:174-176), and a
      guard-tripped category contributes 0.0 -> ``potential_saving == 0.0``.

    ``savings["period"]`` echoes the REQUESTED value in both calls, so a route
    that ignored ``?period=`` and hard-coded 90d would show 90d on the 30d call
    while still returning 20.0 — caught by the pair of assertions, not either.
    """
    client, service = _isolated_client(monkeypatch)
    _seed_straddling(service, TENANT)
    _assert_fixture_landed(service, TENANT, 4)

    wide = client.get("/api/v1/consumer/dashboard?period=90d", headers=_headers(TENANT))
    assert wide.status_code == 200, wide.text
    wide_savings = wide.json()["savings"]
    assert wide_savings["potential_saving"] == 20.0, wide_savings
    assert wide_savings["period"] == "90d", wide_savings

    narrow = client.get("/api/v1/consumer/dashboard?period=30d", headers=_headers(TENANT))
    assert narrow.status_code == 200, narrow.text
    narrow_savings = narrow.json()["savings"]
    assert narrow_savings["potential_saving"] == 0.0, narrow_savings
    assert narrow_savings["period"] == "30d", narrow_savings


@pytest.mark.test_id("TEST-DASHWIRE-004")
@pytest.mark.scenario("AC-D2-4")
@pytest.mark.requirements("REQ-F2-2b")
def test_dashboard_rejects_invalid_period_with_no_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-D2-4 — an unparseable or out-of-range ``period`` is 422, never a payload.

    Four shapes are covered in one loop: non-numeric suffix (``7x``), non-numeric
    body (``abc``), zero days (``0d``) and days past the 3650 ceiling
    (``99999d``). ``build_consumer_dashboard`` is NOT reached for any of them, so
    the response must carry no ``savings`` block and no dashboard envelope at all
    — a route that validated late (or fell back to 90 days the way
    ``app/savings.py:16-31`` does) would answer 200 with 90-day data under a
    ``7x`` label, which is the hazard this gate exists to catch.
    """
    client, service = _isolated_client(monkeypatch)
    _seed_straddling(service, TENANT)
    _assert_fixture_landed(service, TENANT, 4)

    for bad_period in ("7x", "0d", "99999d", "abc"):
        response = client.get(
            f"/api/v1/consumer/dashboard?period={bad_period}", headers=_headers(TENANT)
        )
        assert response.status_code == 422, (
            f"period={bad_period!r} answered {response.status_code}: {response.text}"
        )
        body = response.json()
        assert "savings" not in body, f"period={bad_period!r} leaked a savings block: {body}"
        assert "generated_at" not in body, (
            f"period={bad_period!r} leaked a partial dashboard envelope: {body}"
        )


@pytest.mark.test_id("TEST-DASHWIRE-005")
@pytest.mark.scenario("AC-D2-5")
@pytest.mark.requirements("REQ-F2-2b")
def test_dashboard_auth_gate_empty_state_and_tenant_isolation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-D2-5 — 401 without identity, a real zeroed block for an empty tenant,
    and no bleed of one tenant's receipts into another's savings block.

    (a) The new ``savings`` block must not have moved or weakened the auth gate
        at ``app/api.py:288-310``: no ``Authorization`` and no ``X-Tenant-ID``
        is still 401.

    (b) A tenant that has never written a receipt gets the FULL key set with
        zeroed values — not a missing key, not ``None``. ``potential_saving``
        is ``0`` and ``total_spent`` is ``0``; both are compared with ``== 0``,
        which does not distinguish int from float, so the assertion survives
        either engine spelling.

    (c) Isolation is asserted from BOTH sides. iso-a carries the straddling
        fixture and really does have 20.0 of savings to leak; iso-b — a different
        tenant, also empty — must see none of it. Asserting only iso-b's zeros
        would be vacuous without the iso-a non-vacuity check, and the merchant
        scan catches a leak of iso-a's rows even if the aggregates happened to
        come out zero.
    """
    client, service = _isolated_client(monkeypatch)

    # (a) unauthenticated.
    anonymous = client.get("/api/v1/consumer/dashboard")
    assert anonymous.status_code == 401, anonymous.text

    # (b) a brand-new tenant with zero receipts.
    empty_response = client.get(
        "/api/v1/consumer/dashboard", headers=_headers("iso-empty")
    )
    assert empty_response.status_code == 200, empty_response.text
    assert _stored_payloads(service, "iso-empty") == [], "empty tenant is not empty"
    empty_savings = empty_response.json()["savings"]
    assert empty_savings["potential_saving"] == 0, empty_savings
    assert empty_savings["total_spent"] == 0, empty_savings
    assert empty_savings["avg_by_category"] == {}, empty_savings
    assert empty_savings["top_candidates"] == [], empty_savings
    assert empty_savings["savings_candidates"] == [], empty_savings

    # (c) isolation: seeded tenant iso-a vs a different, empty tenant iso-b.
    _seed_straddling(service, "iso-a")
    _assert_fixture_landed(service, "iso-a", 4)
    _assert_half_split(service, "iso-a", expected_early=2)

    seeded_response = client.get("/api/v1/consumer/dashboard", headers=_headers("iso-a"))
    assert seeded_response.status_code == 200, seeded_response.text
    seeded_savings = seeded_response.json()["savings"]
    assert seeded_savings["potential_saving"] == 20.0, seeded_savings

    other_response = client.get("/api/v1/consumer/dashboard", headers=_headers("iso-b"))
    assert other_response.status_code == 200, other_response.text
    other_savings = other_response.json()["savings"]
    assert other_savings["savings_candidates"] == [], other_savings
    assert other_savings["potential_saving"] == 0, other_savings
    assert _stored_payloads(service, "iso-b") == [], "iso-b is not empty"

    other_blob = json.dumps(other_response.json())
    for merchant in ("WireA1", "WireA2", "WireA3", "WireA4"):
        assert merchant not in other_blob, f"iso-a merchant {merchant!r} leaked into iso-b"
