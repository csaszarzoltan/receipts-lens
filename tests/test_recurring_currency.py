"""Recurring spend must not invent subscriptions from receipts it cannot price."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.accounting_workspace import AccountingWorkspace
from app.product_service import Actor, ProductService


def _parsed(vendor, total, currency="HUF", day="2026-07-01"):
    return SimpleNamespace(
        merchant=vendor, date=day, total=total, tax=0.0, currency=currency,
        items=[SimpleNamespace(name="Item", price=total or 0.0)],
        confidence={"vendor": .9, "date": .9, "total": .9, "tax": .9, "currency": .9},
    )


@pytest.fixture
def env():
    service = ProductService(":memory:")
    return service, AccountingWorkspace(service), Actor("a", "admin")


@pytest.mark.test_id("TEST-RL-V02-212")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_vendorless_receipts_do_not_form_an_unknown_subscription(env):
    service, workspace, actor = env
    service.create_receipt(actor, _parsed("", 4400.0), "a")
    service.create_receipt(actor, _parsed("", 4400.0, day="2026-08-01"), "b")
    assert workspace.recurring(actor.tenant_id) == []


@pytest.mark.test_id("TEST-RL-V02-213")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_unknown_totals_are_not_counted_as_zero_charges(env):
    service, workspace, actor = env
    service.create_receipt(actor, _parsed("Cloud", 4400.0), "a")
    service.create_receipt(actor, _parsed("Cloud", None, day="2026-08-01"), "b")
    assert workspace.recurring(actor.tenant_id) == []


@pytest.mark.test_id("TEST-RL-V02-214")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_recurring_record_carries_the_receipts_currency(env):
    service, workspace, actor = env
    service.create_receipt(actor, _parsed("Cloud", 4400.0), "a")
    service.create_receipt(actor, _parsed("Cloud", 4400.0, day="2026-08-01"), "b")
    (record,) = workspace.recurring(actor.tenant_id)
    assert record["currency"] == "HUF"


@pytest.mark.test_id("TEST-RL-V02-215")
@pytest.mark.requirements("FEAT-RL-V02-REQ-061")
@pytest.mark.scenario("AC-RL-V02-42")
def test_same_merchant_in_two_currencies_is_not_mixed(env):
    service, workspace, actor = env
    service.create_receipt(actor, _parsed("Cloud", 4400.0), "a")
    service.create_receipt(actor, _parsed("Cloud", 10.0, currency="USD", day="2026-08-01"), "b")
    assert workspace.recurring(actor.tenant_id) == []
