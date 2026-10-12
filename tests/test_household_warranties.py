"""Warranty and return deadlines: right dates, kept across restarts, private to the household."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.household_warranties import HouseholdWarranties, add_months
from app.ocr import ConfidenceReceipt
from app.product_service import ProductService

TODAY = date(2026, 10, 11)
client = TestClient(app)


def _headers(tenant: str, role: str = "admin") -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-Role": role}


def _store() -> HouseholdWarranties:
    return HouseholdWarranties(ProductService(":memory:"))


def _add(store: HouseholdWarranties, tenant: str = "hh", **fields):
    body = {"item_name": "Kettle", "purchase_date": "2026-10-01", "return_days": 14, "warranty_months": 24, **fields}
    return store.create(tenant, body, TODAY)


@pytest.mark.test_id("TEST-RL-V02-234")
@pytest.mark.requirements("FEAT-RL-V02-REQ-064")
@pytest.mark.scenario("AC-RL-V02-46")
def test_months_are_added_by_the_calendar_and_clamped_to_the_end_of_a_short_month() -> None:
    assert add_months(date(2026, 10, 11), 24) == date(2028, 10, 11)
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2027, 11, 30), 3) == date(2028, 2, 29)


@pytest.mark.test_id("TEST-RL-V02-235")
@pytest.mark.requirements("FEAT-RL-V02-REQ-064")
@pytest.mark.scenario("AC-RL-V02-46")
def test_a_warranty_gets_both_deadlines_and_the_nearest_one_that_is_still_ahead() -> None:
    item = _add(_store())
    assert item["return_by"] == "2026-10-15"
    assert item["warranty_ends"] == "2028-10-01"
    assert item["return_days_left"] == 4
    assert (item["next_deadline"], item["next_deadline_kind"], item["days_to_next"]) == ("2026-10-15", "return", 4)
    assert item["due_soon"] is True


@pytest.mark.test_id("TEST-RL-V02-236")
@pytest.mark.requirements("FEAT-RL-V02-REQ-064")
@pytest.mark.scenario("AC-RL-V02-46")
def test_a_passed_return_window_is_not_the_next_deadline() -> None:
    item = _add(_store(), purchase_date="2026-08-01")
    assert item["return_days_left"] < 0
    assert (item["next_deadline_kind"], item["warranty_ends"]) == ("warranty", "2028-08-01")
    assert item["due_soon"] is False


@pytest.mark.test_id("TEST-RL-V02-237")
@pytest.mark.requirements("FEAT-RL-V02-REQ-064")
@pytest.mark.scenario("AC-RL-V02-46")
def test_everything_expired_has_no_next_deadline() -> None:
    item = _add(_store(), purchase_date="2020-01-01")
    assert item["next_deadline"] is None and item["days_to_next"] is None and item["due_soon"] is False


@pytest.mark.test_id("TEST-RL-V02-238")
@pytest.mark.requirements("FEAT-RL-V02-REQ-064")
@pytest.mark.scenario("AC-RL-V02-46")
def test_open_items_come_first_by_deadline_and_closed_ones_last() -> None:
    store = _store()
    later = _add(store, item_name="Phone", purchase_date="2026-09-01", return_days=0, warranty_months=24)
    sooner = _add(store, item_name="Shoes", purchase_date="2026-10-05", return_days=14, warranty_months=0)
    done = _add(store, item_name="Lamp", purchase_date="2026-10-10")
    store.update("hh", done["warranty_id"], {"status": "returned"}, TODAY)
    listing = store.list("hh", TODAY)
    assert [i["item_name"] for i in listing["items"]] == ["Shoes", "Phone", "Lamp"]
    assert listing["summary"] == {"active": 2, "due_soon": 1}
    assert later["due_soon"] is False and sooner["due_soon"] is True


@pytest.mark.parametrize("fields", [
    {"item_name": "  "},
    {"purchase_date": "11/10/2026"},
    {"purchase_date": "2030-01-01"},
    {"return_days": -1},
    {"return_days": 400},
    {"warranty_months": 1.5},
    {"warranty_months": True},
    {"return_days": 0, "warranty_months": 0},
])
@pytest.mark.test_id("TEST-RL-V02-239")
@pytest.mark.requirements("FEAT-RL-V02-REQ-064")
@pytest.mark.scenario("AC-RL-V02-47")
def test_invalid_warranties_are_refused(fields) -> None:
    with pytest.raises(ValueError):
        _add(_store(), **fields)


@pytest.mark.test_id("TEST-RL-V02-240")
@pytest.mark.requirements("FEAT-RL-V02-REQ-064")
@pytest.mark.scenario("AC-RL-V02-47")
def test_warranties_survive_a_restart(tmp_path) -> None:
    path = str(tmp_path / "product.db")
    _add(HouseholdWarranties(ProductService(path)), item_name="Washing machine")
    reopened = HouseholdWarranties(ProductService(path))
    assert [i["item_name"] for i in reopened.list("hh", TODAY)["items"]] == ["Washing machine"]


@pytest.mark.test_id("TEST-RL-V02-241")
@pytest.mark.requirements("FEAT-RL-V02-REQ-064")
@pytest.mark.scenario("AC-RL-V02-47")
def test_the_api_adds_lists_updates_and_deletes_for_one_household() -> None:
    created = client.post("/product/warranties", headers=_headers("warranty-api-1"),
                          json={"item_name": "Vacuum", "purchase_date": "2026-10-01", "return_days": 14,
                                "warranty_months": 24, "merchant": "MediaMarkt"})
    assert created.status_code == 201
    warranty_id = created.json()["warranty_id"]
    listing = client.get("/product/warranties", headers=_headers("warranty-api-1")).json()
    assert [i["item_name"] for i in listing["items"]] == ["Vacuum"]

    changed = client.patch(f"/product/warranties/{warranty_id}", headers=_headers("warranty-api-1"),
                           json={"status": "claim"})
    assert changed.json()["status"] == "claim"
    assert changed.json()["merchant"] == "MediaMarkt", "fields not sent stay as they were"

    assert client.delete(f"/product/warranties/{warranty_id}", headers=_headers("warranty-api-1")).status_code == 204
    assert client.get("/product/warranties", headers=_headers("warranty-api-1")).json()["items"] == []


@pytest.mark.test_id("TEST-RL-V02-242")
@pytest.mark.requirements("FEAT-RL-V02-REQ-064")
@pytest.mark.scenario("AC-RL-V02-48")
def test_another_household_cannot_see_change_or_delete_a_warranty() -> None:
    mine = client.post("/product/warranties", headers=_headers("warranty-api-2"),
                       json={"item_name": "Oven", "purchase_date": "2026-10-01", "warranty_months": 24}).json()
    path = f"/product/warranties/{mine['warranty_id']}"
    other = _headers("warranty-api-3")
    assert client.get("/product/warranties", headers=other).json()["items"] == []
    assert client.patch(path, headers=other, json={"status": "archived"}).status_code == 404
    assert client.delete(path, headers=other).status_code == 404
    still = client.get("/product/warranties", headers=_headers("warranty-api-2")).json()["items"]
    assert [i["status"] for i in still] == ["active"]


@pytest.mark.test_id("TEST-RL-V02-243")
@pytest.mark.requirements("FEAT-RL-V02-REQ-064")
@pytest.mark.scenario("AC-RL-V02-48")
def test_a_view_only_member_can_read_but_not_write() -> None:
    body = {"item_name": "TV", "purchase_date": "2026-10-01", "warranty_months": 24}
    assert client.post("/product/warranties", headers=_headers("warranty-api-4", "view_only"), json=body).status_code == 403
    assert client.get("/product/warranties", headers=_headers("warranty-api-4", "view_only")).status_code == 200


@pytest.mark.test_id("TEST-RL-V02-244")
@pytest.mark.requirements("FEAT-RL-V02-REQ-064")
@pytest.mark.scenario("AC-RL-V02-48")
def test_a_warranty_can_only_link_to_the_households_own_receipt() -> None:
    parsed = ConfidenceReceipt(merchant="Shop", date="2026-10-01", items=[], total=10.0, tax=None,
                               currency="HUF", raw_text="", confidence={"merchant": 0.9, "total": 0.9})
    with patch("app.product_api.parse_receipt_with_confidence", return_value=parsed):
        receipt = client.post("/product/receipts/upload", headers=_headers("warranty-api-5"),
                              files={"file": ("r.png", b"image", "image/png")}).json()["receipt_id"]
    body = {"item_name": "Toaster", "purchase_date": "2026-10-01", "warranty_months": 12, "receipt_id": receipt}
    assert client.post("/product/warranties", headers=_headers("warranty-api-5"), json=body).status_code == 201
    assert client.post("/product/warranties", headers=_headers("warranty-api-6"), json=body).status_code == 404


@pytest.mark.test_id("TEST-RL-V02-245")
@pytest.mark.requirements("FEAT-RL-V02-REQ-064")
@pytest.mark.scenario("AC-RL-V02-47")
def test_the_api_reports_invalid_input_as_unprocessable() -> None:
    response = client.post("/product/warranties", headers=_headers("warranty-api-7"),
                           json={"item_name": "Fan", "purchase_date": "soon", "warranty_months": 12})
    assert response.status_code == 422
    assert "ISO date" in response.json()["detail"]
