"""NAV eNyugta app exports are imported as certain receipts; secrets in the file are never kept."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.enyugta_import import EnyugtaError, parse_export

client = TestClient(app)
NS = "http://schemas.nav.gov.hu/ERECEIPT/1.1/export"


def _element(number="NY-2026-0001", supplier="KISBOLT KFT", gross="3267.00", issued="2026-10-05T10:30:00Z",
             extra="") -> str:
    parts = ["<exportCounter>1</exportCounter><elementVersion>1</elementVersion>",
             "<documentClass>RECEIPT</documentClass>", "<searchKey>U0VDUkVULVNFQVJDSy1LRVk=</searchKey>",
             "<privateKey>UFJJVkFURS1LRVktTUFURVJJQUw=</privateKey>"]
    if supplier:
        parts.append(f"<supplierName>{supplier}</supplierName>")
    if number:
        parts.append(f"<documentNumber>{number}</documentNumber>")
    if gross:
        parts.append(f"<documentGrossAmountHUF>{gross}</documentGrossAmountHUF>")
    if issued:
        parts.append(f"<issueEndDateTime>{issued}</issueEndDateTime>")
    return f"<exportElements>{''.join(parts)}{extra}</exportElements>"


def _file(*elements: str, ns: str = NS) -> bytes:
    body = "".join(elements)
    return (f'<?xml version="1.0" encoding="utf-8"?><ExportEnvelope xmlns="{ns}">'
            f"<exportTimestamp>2026-10-11T08:00:00Z</exportTimestamp><numberOfElements>{len(elements)}</numberOfElements>"
            f"<exportVersion>1</exportVersion><exportName>export</exportName>{body}</ExportEnvelope>").encode()


def _post(tenant: str, content: bytes, role: str = "admin"):
    return client.post("/product/enyugta-import", headers={"X-Tenant-ID": tenant, "X-Role": role},
                       files={"file": ("export.xml", content, "application/xml")})


def _receipts(tenant: str) -> list[dict]:
    items = client.get("/product/review-items?readiness=completed", headers={"X-Tenant-ID": tenant, "X-Role": "admin"})
    return [i["receipt"] for i in items.json()["items"]]


@pytest.mark.test_id("TEST-RL-V02-266")
@pytest.mark.requirements("FEAT-RL-V02-REQ-066")
@pytest.mark.scenario("AC-RL-V02-55")
def test_an_export_element_gives_seller_total_and_the_hungarian_day() -> None:
    receipts, skipped = parse_export(_file(_element(issued="2026-10-05T22:30:00Z")))
    assert skipped == []
    assert [(r.supplier, r.gross_huf, r.day, r.document_number) for r in receipts] == [
        ("KISBOLT KFT", 3267.0, "2026-10-06", "NY-2026-0001")], "22:30 UTC is already the next day in Budapest"


@pytest.mark.test_id("TEST-RL-V02-267")
@pytest.mark.requirements("FEAT-RL-V02-REQ-066")
@pytest.mark.scenario("AC-RL-V02-55")
def test_either_published_namespace_is_read() -> None:
    old = "http://schemas.nav.gov.hu/ERECEIPT/1.0/export"
    assert len(parse_export(_file(_element(), ns=old))[0]) == 1


@pytest.mark.test_id("TEST-RL-V02-268")
@pytest.mark.requirements("FEAT-RL-V02-REQ-066")
@pytest.mark.scenario("AC-RL-V02-55")
def test_elements_that_are_not_receipts_or_are_unreadable_are_reported_not_guessed() -> None:
    report = "<exportElements><exportCounter>2</exportCounter><reportClass>CASHFLOW</reportClass></exportElements>"
    receipts, skipped = parse_export(_file(_element(), report, _element(gross="lots"), _element(issued="yesterday")))
    assert len(receipts) == 1
    assert [(s["index"], s["reason"]) for s in skipped] == [(2, "not_a_receipt"), (3, "unreadable"), (4, "unreadable")]


@pytest.mark.parametrize(("raw", "message"), [
    (b"not xml at all", "not valid XML"),
    (b"<Other/>", "ExportEnvelope"),
    (b'<!DOCTYPE x [<!ENTITY a "aaaa">]><ExportEnvelope/>', "DTD"),
    (b"x" * 5_000_001, "larger than 5 MB"),
    (_file(), "no exported elements"),
])
@pytest.mark.test_id("TEST-RL-V02-269")
@pytest.mark.requirements("FEAT-RL-V02-REQ-066")
@pytest.mark.scenario("AC-RL-V02-56")
def test_a_file_that_is_not_an_export_is_refused_with_a_reason(raw, message) -> None:
    with pytest.raises(EnyugtaError, match=message):
        parse_export(raw)


@pytest.mark.test_id("TEST-RL-V02-270")
@pytest.mark.requirements("FEAT-RL-V02-REQ-066")
@pytest.mark.scenario("AC-RL-V02-57")
def test_import_creates_confirmed_forint_receipts_without_any_key_material() -> None:
    result = _post("eny-1", _file(_element(), _element(number="NY-2", supplier="TESCO", gross="12990")))
    assert result.status_code == 201
    assert result.json() == {"imported": 2, "duplicates": 0, "skipped": [], "elements": 2}
    receipts = {r["vendor"]: r for r in _receipts("eny-1")}
    assert (receipts["KISBOLT KFT"]["total"], receipts["KISBOLT KFT"]["currency"], receipts["KISBOLT KFT"]["date"]) == (
        3267.0, "HUF", "2026-10-05")
    assert receipts["KISBOLT KFT"]["currency_assumed"] is False
    stored = json.dumps(receipts)
    assert "PRIVATE-KEY" not in stored and "UFJJVkFURS1" not in stored and "U0VDUkVU" not in stored


@pytest.mark.test_id("TEST-RL-V02-271")
@pytest.mark.requirements("FEAT-RL-V02-REQ-066")
@pytest.mark.scenario("AC-RL-V02-57")
def test_importing_the_same_file_twice_adds_nothing() -> None:
    content = _file(_element())
    assert _post("eny-2", content).json()["imported"] == 1
    again = _post("eny-2", content).json()
    assert (again["imported"], again["duplicates"]) == (0, 1)
    assert len(_receipts("eny-2")) == 1


@pytest.mark.test_id("TEST-RL-V02-272")
@pytest.mark.requirements("FEAT-RL-V02-REQ-066")
@pytest.mark.scenario("AC-RL-V02-57")
def test_a_receipt_without_a_document_number_is_still_recognised_the_second_time() -> None:
    content = _file(_element(number=None))
    assert _post("eny-3", content).json()["imported"] == 1
    assert _post("eny-3", content).json()["duplicates"] == 1


@pytest.mark.test_id("TEST-RL-V02-273")
@pytest.mark.requirements("FEAT-RL-V02-REQ-066")
@pytest.mark.scenario("AC-RL-V02-58")
def test_the_same_document_number_in_another_household_is_a_separate_receipt() -> None:
    content = _file(_element())
    assert _post("eny-4", content).json()["imported"] == 1
    assert _post("eny-5", content).json()["imported"] == 1


@pytest.mark.test_id("TEST-RL-V02-274")
@pytest.mark.requirements("FEAT-RL-V02-REQ-066")
@pytest.mark.scenario("AC-RL-V02-58")
def test_a_view_only_member_cannot_import_and_a_bad_file_is_unprocessable() -> None:
    assert _post("eny-6", _file(_element()), role="view_only").status_code == 403
    response = _post("eny-6", b"nope")
    assert response.status_code == 422 and "not valid XML" in response.json()["detail"]
