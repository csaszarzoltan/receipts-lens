"""A household that has not chosen a currency is offered its own, never a blanket USD."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.ocr import ConfidenceReceipt

client = TestClient(app)


def _headers(tenant: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-Role": "admin"}


def _upload(tenant: str, currency: str, source: str) -> None:
    parsed = ConfidenceReceipt(
        merchant="Shop", date="2026-10-01", items=[], total=10.0, tax=None, currency=currency,
        raw_text="", confidence={"merchant": 0.9, "total": 0.9}, currency_source=source,
    )
    with patch("app.product_api.parse_receipt_with_confidence", return_value=parsed):
        created = client.post("/product/receipts/upload", headers=_headers(tenant),
                              files={"file": ("r.png", b"image", "image/png")})
    assert created.status_code == 201


def _base(tenant: str) -> str:
    return client.get("/product/preferences", headers=_headers(tenant)).json()["base_currency"]


def _source(tenant: str) -> str:
    return client.get("/product/preferences", headers=_headers(tenant)).json()["base_currency_source"]


@pytest.mark.test_id("TEST-RL-V02-230")
@pytest.mark.requirements("FEAT-RL-V02-REQ-063")
@pytest.mark.scenario("AC-RL-V02-45")
def test_a_household_without_receipts_still_defaults_to_usd() -> None:
    assert _base("hh-currency-empty") == "USD"
    assert _source("hh-currency-empty") == "default", "the UI may then offer the language's currency"


@pytest.mark.test_id("TEST-RL-V02-231")
@pytest.mark.requirements("FEAT-RL-V02-REQ-063")
@pytest.mark.scenario("AC-RL-V02-45")
def test_the_currency_printed_on_most_receipts_becomes_the_default() -> None:
    _upload("hh-currency-huf", "HUF", "marker")
    _upload("hh-currency-huf", "HUF", "marker")
    _upload("hh-currency-huf", "EUR", "marker")
    assert _base("hh-currency-huf") == "HUF"
    assert _source("hh-currency-huf") == "receipts"


@pytest.mark.test_id("TEST-RL-V02-232")
@pytest.mark.requirements("FEAT-RL-V02-REQ-063")
@pytest.mark.scenario("AC-RL-V02-45")
def test_guessed_currencies_do_not_teach_the_default() -> None:
    _upload("hh-currency-guess", "EUR", "default")
    assert _base("hh-currency-guess") == "USD"


@pytest.mark.test_id("TEST-RL-V02-233")
@pytest.mark.requirements("FEAT-RL-V02-REQ-063")
@pytest.mark.scenario("AC-RL-V02-45")
def test_a_chosen_currency_wins_and_other_settings_do_not_freeze_the_guess() -> None:
    _upload("hh-currency-saved", "HUF", "marker")
    client.put("/product/preferences", headers=_headers("hh-currency-saved"), json={"payload": {"compact": True}})
    assert _base("hh-currency-saved") == "HUF"
    # The guess was not written down by the unrelated save, so a later receipt mix can still move it...
    stored = client.get("/product/preferences", headers=_headers("hh-currency-saved")).json()
    assert stored["compact"] is True
    # ...but an explicit choice is permanent.
    client.put("/product/preferences", headers=_headers("hh-currency-saved"), json={"payload": {"base_currency": "EUR"}})
    _upload("hh-currency-saved", "HUF", "marker")
    assert _base("hh-currency-saved") == "EUR"
    assert _source("hh-currency-saved") == "saved"
