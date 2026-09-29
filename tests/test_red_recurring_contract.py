"""RED contract for F2.1 recurring spend — contract conformance (AC-RC-1 .. AC-RC-6).

Spec: ``docs/plans/recurring-contract-spec.md`` section 2 (``price_trend``),
section 3 (``currency``), section 4 (``period``) and section 5 (the ACs).
The endpoint does NOT honour these yet, so 5 of the 6 tests are RED
(AC-RC-1..5); AC-RC-6 is a regression guard and must stay GREEN.

Style follows ``tests/test_red_recurring_p0_contract.py``: TestClient + dev
headers (X-Tenant-ID / X-Role) + real ProductService(":memory:").

Two properties every fixture below depends on:

1. ASCENDING DATES. ``app/recurring.py:128`` picks the last receipt by
   sorting the ISO ``YYYY-MM-DD`` string, so the amount that must end up in
   ``last_amount``/``delta_pct`` has to be seeded on the LATEST date. Every
   fixture therefore seeds amounts oldest-first onto ``_date_ago(9|6|3)``.
2. LITERAL EXPECTATIONS. The ``delta_pct``/``avg_amount`` values are written
   out by hand from the real formula at ``app/recurring.py:133``
   (``round((round(last,2) - avg_unrounded) / avg_unrounded * 100, 2)``, avg
   over ALL amounts) and are NEVER recomputed inside the test. Asserting a
   value derived from the same expression the code uses would only prove
   the test agrees with itself; a copy-paste typo must be able to fail here.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.api
from app.product_api import Actor
from app.product_service import ProductService

ENDPOINT = "/api/v1/analytics/recurring"

ITEM_KEYS = {
    "merchant",
    "occurrences",
    "frequency",
    "avg_amount",
    "last_amount",
    "delta_pct",
    "price_trend",
}


def _date_ago(days: int) -> str:
    """ISO ``YYYY-MM-DD`` *days* before today (UTC)."""
    return (datetime.now(UTC).date() - timedelta(days=days)).isoformat()


def _parsed(merchant: str, total: float, date: str) -> SimpleNamespace:
    return SimpleNamespace(
        merchant=merchant,
        date=date,
        total=total,
        tax=0.0,
        currency="USD",
        items=[SimpleNamespace(name=merchant, price=total)],
        confidence={
            "vendor": 0.95,
            "date": 0.95,
            "total": 0.95,
            "tax": 0.95,
            "currency": 0.95,
        },
    )


def _seed(service: ProductService, tenant: str, merchant: str, total: float, date: str) -> str:
    actor = Actor(tenant, "admin")
    return service.create_receipt(actor, _parsed(merchant, total, date), f"{merchant}.png")[
        "receipt_id"
    ]


def _isolated_client(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, ProductService]:
    service = ProductService(":memory:")
    monkeypatch.setattr("app.api.service", service)
    monkeypatch.setattr("app.product_api.service", service)
    return TestClient(app.api.app), service


def _seed_series(
    service: ProductService, tenant: str, merchant: str, amounts: list[float]
) -> None:
    """Seed *amounts* oldest-first on 9/6/3 days ago (see module docstring)."""
    for amount, days_ago in zip(amounts, (9, 6, 3), strict=True):
        _seed(service, tenant, merchant, amount, _date_ago(days_ago))


def _get(client: TestClient, tenant: str, query: str = "") -> object:
    headers = {"X-Tenant-ID": tenant, "X-Role": "admin"}
    return client.get(f"{ENDPOINT}{query}", headers=headers)


@pytest.mark.test_id("TEST-RECURCON-001")
@pytest.mark.requirements("REQ-F2-1")
@pytest.mark.scenario("AC-RC-1")
def test_recurring_body_shape_has_currency_and_price_trend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-RC-1: body is exactly ``{period, currency, items}`` and every item
    carries all seven keys with ``price_trend`` in the closed vocabulary."""
    client, service = _isolated_client(monkeypatch)
    _seed_series(service, "recurcon-shape", "Tesco", [100.00, 100.00, 120.00])

    response = _get(client, "recurcon-shape", "?period=90d")
    assert response.status_code == 200
    body = response.json()

    assert set(body) == {"period", "currency", "items"}
    assert body["currency"] == "USD"
    assert body["period"] == "90d"

    items = body["items"]
    assert items, "no recurring item returned for a seeded merchant"
    for item in items:
        assert ITEM_KEYS <= set(item), f"missing keys: {sorted(ITEM_KEYS - set(item))}"
        assert item["price_trend"] in {"up", "down", "flat"}


@pytest.mark.test_id("TEST-RECURCON-002")
@pytest.mark.requirements("REQ-F2-1")
@pytest.mark.scenario("AC-RC-2")
def test_recurring_price_trend_boundary_is_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-RC-2: the 10% band is closed — ``delta_pct == 10.0`` is ``flat``,
    one cent more is ``up``; mirrored below, ``-10.0`` is ``flat``, one cent
    more negative is ``down``; an all-zero mean short-circuits to ``0.0``.

    Every row is compared against a hand-written literal triple, so the whole
    table is visible in the single assertion diff. The pre-change code has no
    ``price_trend`` key at all, so this fails on the trend column.
    """
    client, service = _isolated_client(monkeypatch)

    # (label, ascending amounts, expected avg_amount, expected delta_pct,
    #  expected price_trend) — all literals, per app/recurring.py:133.
    cases: list[tuple[str, list[float], float, float, str]] = [
        ("clearly_above", [100.00, 100.00, 120.00], 106.67, 12.5, "up"),
        ("exactly_on_tie", [9.50, 9.50, 11.00], 10.0, 10.0, "flat"),
        ("one_cent_over_tie", [9.50, 9.50, 11.01], 10.0, 10.06, "up"),
        ("one_cent_under_tie", [9.50, 9.50, 10.99], 10.0, 9.94, "flat"),
        ("mirror_on_tie", [21.00, 21.00, 18.00], 20.0, -10.0, "flat"),
        ("one_cent_under_mirror", [21.00, 21.00, 17.99], 20.0, -10.04, "down"),
        ("zero_mean", [0.00, 0.00, 0.00], 0.0, 0.0, "flat"),
    ]

    actual: list[tuple[str, float, float, str]] = []
    for label, amounts, _avg, _delta, _trend in cases:
        tenant = f"recurcon-pt-{label}"
        _seed_series(service, tenant, "Tesco", amounts)
        response = _get(client, tenant, "?period=90d")
        assert response.status_code == 200, f"{label}: HTTP {response.status_code}"
        items = response.json()["items"]
        assert [i["merchant"] for i in items] == ["Tesco"], f"{label}: {items}"
        item = items[0]
        actual.append(
            (label, item["avg_amount"], item["delta_pct"], item.get("price_trend"))
        )

    expected = [(label, avg, delta, trend) for label, _a, avg, delta, trend in cases]
    assert actual == expected


@pytest.mark.test_id("TEST-RECURCON-003")
@pytest.mark.requirements("REQ-F2-1")
@pytest.mark.scenario("AC-RC-3")
def test_recurring_period_filters_instead_of_merely_echoing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-RC-3: ``period`` must change the ANSWER, not just the echoed label.

    One receipt today, one 45 days ago. ``?period=30d`` must see only the
    recent one; ``?period=90d`` must see both. The pre-change route discards
    ``period`` (``app/api.py:1522-1529``) and both windows return 2, so the
    first assertion below is the one that fails.
    """
    client, service = _isolated_client(monkeypatch)
    tenant = "recurcon-period"
    _seed(service, tenant, "Tesco", 10.0, _date_ago(45))
    _seed(service, tenant, "Tesco", 10.0, _date_ago(0))

    short = _get(client, tenant, "?period=30d")
    assert short.status_code == 200
    short_items = short.json()["items"]
    assert [i["merchant"] for i in short_items] == ["Tesco"]
    assert short_items[0]["occurrences"] == 1

    long = _get(client, tenant, "?period=90d")
    assert long.status_code == 200
    long_items = long.json()["items"]
    assert [i["merchant"] for i in long_items] == ["Tesco"]
    assert long_items[0]["occurrences"] == 2


@pytest.mark.test_id("TEST-RECURCON-004")
@pytest.mark.requirements("REQ-F2-1")
@pytest.mark.scenario("AC-RC-4")
def test_recurring_rejects_unparseable_period(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-RC-4: an unparseable/out-of-range ``period`` is 422, not a silent
    fallback to 90 days under a false label."""
    client, service = _isolated_client(monkeypatch)
    _seed(service, "recurcon-422", "Tesco", 10.0, _date_ago(3))

    for bad in ("7x", "0d", "-5d", "abc"):
        response = _get(client, "recurcon-422", f"?period={bad}")
        assert response.status_code == 422, f"period={bad} -> {response.status_code}"
        assert "items" not in response.json(), f"period={bad} leaked items"


@pytest.mark.test_id("TEST-RECURCON-005")
@pytest.mark.requirements("REQ-F2-1")
@pytest.mark.scenario("AC-RC-5")
def test_recurring_auth_and_empty_state_keep_new_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-RC-5: 401 without credentials; an empty tenant is 200 with
    ``items == []`` AND ``currency`` present (not 404)."""
    client, _ = _isolated_client(monkeypatch)

    assert client.get(f"{ENDPOINT}?period=90d").status_code == 401

    empty = _get(client, "recurcon-empty", "?period=90d")
    assert empty.status_code == 200
    body = empty.json()
    assert body["items"] == []
    assert body["currency"] == "USD"


@pytest.mark.test_id("TEST-RECURCON-006")
@pytest.mark.requirements("REQ-F2-1")
@pytest.mark.scenario("AC-RC-6")
def test_recurring_change_does_not_regress_existing_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-RC-6: the new work must not move the pre-existing numbers.

    All three receipts are inside the default 90d window, so the new filtering
    must leave ``occurrences``/``avg_amount``/``delta_pct`` at their
    pre-change values (100.00, 100.00, 120.00 -> 3 / 106.67 / 12.5), an
    all-zero series keeps ``delta_pct == 0.0`` with a flat trend, and
    ``/analytics/savings-summary`` — which consumes ``RecurringAnalytics`` at
    ``app/savings.py:171`` — still answers 200. This test is GREEN before the
    change and must stay green after it.
    """
    client, service = _isolated_client(monkeypatch)
    tenant = "recurcon-regress"
    _seed_series(service, tenant, "Tesco", [100.00, 100.00, 120.00])
    _seed_series(service, tenant, "ZeroMart", [0.00, 0.00, 0.00])

    response = _get(client, tenant)
    assert response.status_code == 200
    by_merchant = {item["merchant"]: item for item in response.json()["items"]}
    assert sorted(by_merchant) == ["Tesco", "ZeroMart"]

    tesco = by_merchant["Tesco"]
    assert tesco["occurrences"] == 3
    assert tesco["avg_amount"] == 106.67
    assert tesco["last_amount"] == 120.0
    assert tesco["delta_pct"] == 12.5

    zero = by_merchant["ZeroMart"]
    assert zero["delta_pct"] == 0.0
    # The new key, once emitted, must be the flat one the spec prescribes for
    # a zero mean; absent before the change, so this line cannot go RED here
    # (AC-RC-2 already pins "flat" unconditionally).
    assert zero["price_trend"] == "flat"

    headers = {"X-Tenant-ID": tenant, "X-Role": "admin"}
    savings = client.get("/api/v1/analytics/savings-summary?period=90d", headers=headers)
    assert savings.status_code == 200
