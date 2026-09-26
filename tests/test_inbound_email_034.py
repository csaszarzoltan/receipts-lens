"""SPEC-034 bizonyíték: e-mailben érkező nyugták fogadása (inbound inbox).

A SPEC 13. fejezete (elfogadási terv) írja elő ezt a fájlt: a 8 REQ
mindegyikéhez tartozik futtatható bizonyíték, különben a SPEC nem
zárható le. A termékkód adott, ez a fájl igazítja hozzá a szerződést
(forwarding-cím, állapotok, izoláció, auth, hibakezelés, limitek).
"""
from __future__ import annotations

import base64
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.product_api import service

PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
PDF_B64 = base64.b64encode(b"%PDF-1.4 test").decode()
HELLO_B64 = base64.b64encode(b"hello").decode()

A = {"X-Tenant-ID": "tenant-a", "X-Role": "admin"}
B = {"X-Tenant-ID": "tenant-b", "X-Role": "admin"}

client = TestClient(app)


def _att(filename: str = "r.png", ctype: str = "image/png", b64: str = PNG_B64) -> dict[str, str]:
    """Build one attachment payload dict."""
    return {"filename": filename, "content_type": ctype, "content_base64": b64}


def _post(headers: dict[str, str], atts: list[dict[str, str]]) -> dict[str, Any]:
    """POST an inbound email, assert 201, return the body."""
    r = client.post("/product/inbound-emails", headers=headers, json={"sender": "s@x.hu", "subject": "t", "attachments": atts})
    assert r.status_code == 201
    return r.json()


@pytest.fixture(autouse=True)
def _clean_inbox() -> Iterator[None]:
    """Reset inbox state pre/post test via the service._db connection object.

    The module-level inbox_service shares service._db, so truncating the
    inbound_emails / inbound_email_attachments tables resets every store
    without touching any developer database file.
    """
    with service._db:
        service._db.execute("DELETE FROM inbound_email_attachments")
        service._db.execute("DELETE FROM inbound_emails")
    yield
    with service._db:
        service._db.execute("DELETE FROM inbound_email_attachments")
        service._db.execute("DELETE FROM inbound_emails")


@pytest.mark.test_id("TEST-INBOUN-001")
@pytest.mark.requirements("REQ-034-01")
@pytest.mark.scenario("AC-034-01")
def test_list_returns_forwarding_address_for_own_tenant() -> None:
    """REQ-034-01 / AC-034-01: a lista a saját tenant forwarding-címét adja."""
    r = client.get("/product/inbound-emails", headers=A)
    assert r.status_code == 200
    assert r.json()["address"] == "receipts+tenant-a@receiptlens.local"
    assert r.json()["items"] == []


@pytest.mark.test_id("TEST-INBOUN-002")
@pytest.mark.requirements("REQ-034-02")
@pytest.mark.scenario("AC-034-02")
def test_status_and_attachment_states_are_visible() -> None:
    """REQ-034-02 / AC-034-02: a detail mutatja az email- és attachment-státuszt.

    A REQ azt kéri, hogy a felhasználó tudja, LÉTREJÖTT-E nyugta — ezért a
    konkrét ``completed`` értéket állítjuk, nem egy szuperhalmazt.
    """
    body = _post(A, [_att()])
    d = client.get(f"/product/inbound-emails/{body['email_id']}", headers=A).json()
    assert d["status"] == "completed"
    assert d["attachments"][0]["status"] == "completed"
    assert "receipt_id" in d["attachments"][0]
    assert d["sender"] == "s@x.hu"
    assert d["subject"] == "t"


@pytest.mark.test_id("TEST-INBOUN-003")
@pytest.mark.requirements("REQ-034-03")
@pytest.mark.scenario("AC-034-03")
def test_supported_image_attachment_completes() -> None:
    """REQ-034-03 / AC-034-03: a támogatott képfeldolgozás completed lesz."""
    body = _post(A, [_att()])
    assert body["status"] == "completed"
    assert body["attachments"][0]["status"] == "completed"


@pytest.mark.test_id("TEST-INBOUN-004")
@pytest.mark.requirements("REQ-034-04")
@pytest.mark.scenario("AC-034-04")
def test_missing_content_fails() -> None:
    """REQ-034-04 / AC-034-04: üres tartalom failed/content_missing lesz."""
    body = _post(A, [_att(b64="")])
    att = body["attachments"][0]
    assert att["status"] == "failed"
    assert att["error_code"] == "content_missing"


@pytest.mark.test_id("TEST-INBOUN-005")
@pytest.mark.requirements("REQ-034-04")
@pytest.mark.scenario("AC-034-04")
def test_unsupported_content_quarantined() -> None:
    """REQ-034-04 / AC-034-04: nem támogatott tartalom quarantined lesz."""
    body = _post(A, [_att("n.txt", "text/plain", HELLO_B64)])
    att = body["attachments"][0]
    assert att["status"] == "quarantined"
    assert att["error_code"] == "unsupported_content"


@pytest.mark.test_id("TEST-INBOUN-006")
@pytest.mark.requirements("REQ-034-04")
@pytest.mark.scenario("AC-034-04")
def test_too_large_attachment_quarantined(monkeypatch: pytest.MonkeyPatch) -> None:
    """REQ-034-04 / AC-034-04: túl nagy melléklet quarantined/attachment_too_large."""
    monkeypatch.setattr("app.inbox_service.MAX_ATTACHMENT_BYTES", 10)
    body = _post(A, [_att()])
    att = body["attachments"][0]
    assert att["status"] == "quarantined"
    assert att["error_code"] == "attachment_too_large"


@pytest.mark.test_id("TEST-INBOUN-007")
@pytest.mark.requirements("REQ-034-04")
@pytest.mark.scenario("AC-034-04")
def test_mime_mismatch_quarantined() -> None:
    """REQ-034-04 / AC-034-04: deklarált/detektált MIME-eltérés quarantined."""
    body = _post(A, [_att(ctype="image/jpeg")])
    att = body["attachments"][0]
    assert att["status"] == "quarantined"
    assert att["error_code"] == "mime_mismatch"


@pytest.mark.test_id("TEST-INBOUN-008")
@pytest.mark.requirements("REQ-034-05")
@pytest.mark.scenario("AC-034-05")
def test_foreign_tenant_email_not_visible() -> None:
    """REQ-034-05 / AC-034-05: másik tenant levele nem látható."""
    body = _post(A, [_att()])
    ids = [e["email_id"] for e in client.get("/product/inbound-emails", headers=B).json()["items"]]
    assert body["email_id"] not in ids
    assert client.get(f"/product/inbound-emails/{body['email_id']}", headers=B).status_code == 404


@pytest.mark.test_id("TEST-INBOUN-009")
@pytest.mark.requirements("REQ-034-06")
@pytest.mark.scenario("AC-034-06")
def test_unauthenticated_401() -> None:
    """REQ-034-06 / AC-034-06: header nélkül GET és POST is 401-et ad."""
    assert client.get("/product/inbound-emails").status_code == 401
    r = client.post("/product/inbound-emails", json={"sender": "s@x.hu", "subject": "t", "attachments": []})
    assert r.status_code == 401


@pytest.mark.test_id("TEST-INBOUN-010")
@pytest.mark.requirements("REQ-034-07")
@pytest.mark.scenario("AC-034-07")
def test_pdf_fails_not_succeeds() -> None:
    """REQ-034-07 / AC-034-07: a PDF nem sikeres, hanem failed lesz."""
    body = _post(A, [_att("d.pdf", "application/pdf", PDF_B64)])
    att = body["attachments"][0]
    assert att["status"] == "failed"
    assert att["error_code"] == "pdf_processing_unavailable"


@pytest.mark.test_id("TEST-INBOUN-011")
@pytest.mark.requirements("REQ-034-07")
@pytest.mark.scenario("AC-034-07")
def test_quarantined_retry_rejected_422() -> None:
    """REQ-034-07 / AC-034-07: a quarantined attachment retry-ja 422."""
    body = _post(A, [_att("n.txt", "text/plain", HELLO_B64)])
    aid = body["attachments"][0]["attachment_id"]
    r = client.post(f"/product/inbound-emails/{body['email_id']}/attachments/{aid}/retry", headers=A)
    assert r.status_code == 422


@pytest.mark.test_id("TEST-INBOUN-012")
@pytest.mark.requirements("REQ-034-08")
@pytest.mark.scenario("AC-034-08")
def test_too_many_attachments_422() -> None:
    """REQ-034-08 / AC-034-08: 21 melléklet 422-t ad (limit 20)."""
    atts = [_att(f"{i}.png") for i in range(21)]
    r = client.post("/product/inbound-emails", headers=A, json={"sender": "s@x.hu", "subject": "t", "attachments": atts})
    assert r.status_code == 422


@pytest.mark.test_id("TEST-INBOUN-013")
@pytest.mark.requirements("REQ-034-08")
@pytest.mark.scenario("AC-034-08")
def test_duplicate_submit_does_not_duplicate_state() -> None:
    """REQ-034-08 / AC-034-08: ismételt POST nem duplikálja az állapotot."""
    first = _post(A, [_att()])
    second = _post(A, [_att()])
    assert first["email_id"] != second["email_id"]
    ids = [e["email_id"] for e in client.get("/product/inbound-emails", headers=A).json()["items"]]
    assert sorted(ids) == sorted({first["email_id"], second["email_id"]})


@pytest.mark.test_id("TEST-INBOUN-014")
@pytest.mark.requirements("REQ-034-08")
@pytest.mark.scenario("AC-034-08")
def test_retry_increments_attempt() -> None:
    """REQ-034-08 / AC-034-08: sikeres attachment retry-je attempt 2-re lép."""
    body = _post(A, [_att()])
    aid = body["attachments"][0]["attachment_id"]
    r = client.post(f"/product/inbound-emails/{body['email_id']}/attachments/{aid}/retry", headers=A)
    assert r.status_code == 200
    assert r.json()["attempt"] == 2


@pytest.mark.test_id("TEST-INBOUN-015")
@pytest.mark.requirements("REQ-034-06")
@pytest.mark.scenario("AC-034-06")
def test_readonly_role_cannot_receive() -> None:
    """REQ-034-06 / AC-034-06: olvasó szerep nem fogadhat e-mailt (403).

    WRITE_ROLES csak {"owner", "adult"}; a "view_only" household role
    nincs benne, így a POST 403-mal elutasítandó.
    """
    ro = {"X-Tenant-ID": "tenant-a", "X-Role": "view_only"}
    r = client.post("/product/inbound-emails", headers=ro, json={"sender": "s@x.hu", "subject": "t", "attachments": [_att()]})
    assert r.status_code == 403
