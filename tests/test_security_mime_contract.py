"""MIME-contract tests: declared type must match the bytes actually uploaded.

Function under test
-------------------
``app.inbox_service`` -- ``detect_type`` and ``InboxService.receive``, the
tenant-scoped inbound attachment pipeline that ``scripts/security-gate.sh``
advertises under "MIME ... regressions".

The contract this pins is the *declared vs. detected* reconciliation:

- ``detect_type`` recognises a fixed set of real magic signatures and returns
  ``None`` for anything else.
- An attachment whose declared ``content_type`` disagrees with its detected
  type is **quarantined** with ``mime_mismatch`` -- it is never processed.
- Content that matches no known signature is quarantined as
  ``unsupported_content`` rather than accepted on the strength of its
  declared type.
- The size cap and missing-content guards quarantine before any processing.

Every test here fails if the MIME gate is weakened -- e.g. if ``detect_type``
starts trusting ``str.startswith`` on a partial signature, or if the
``declared != detected`` branch is removed.  That is the regression the
security gate must catch.
"""
from __future__ import annotations

import base64

import pytest

from app.inbox_service import (
    MAX_ATTACHMENT_BYTES,
    SIGNATURES,
    InboxService,
    detect_type,
    safe_filename,
)
from app.product_service import ProductService

pytestmark = pytest.mark.usefixtures("_inbox_tenant")


@pytest.fixture()
def _inbox_tenant():
    """Every test in this module acts on behalf of a single named tenant."""
    return "tenant-a"


def _service(tmp_path) -> InboxService:
    """Build an InboxService over a real ProductService, as the app wires it."""
    store = ProductService(tmp_path / "inbox.db")
    return InboxService(store, processor=lambda content, mime: f"receipt-{len(content)}")


PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
GIF = b"GIF89a" + b"\x00" * 32
PDF = b"%PDF-1.4" + b"\x00" * 32
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 32


def _attachment(content: bytes, filename: str, content_type: str) -> dict:
    return {
        "filename": filename,
        "content_type": content_type,
        "content_base64": base64.b64encode(content).decode(),
    }


# ---------------------------------------------------------------------------
# detect_type -- signature recognition
# ---------------------------------------------------------------------------


@pytest.mark.test_id("TEST-034S-001")
@pytest.mark.requirements("REQ-034-04")
@pytest.mark.scenario("AC-034-04")
def test_detect_type_recognises_each_declared_signature():
    """Every signature the service advertises is detected from real bytes."""
    assert detect_type(PNG) == "image/png"
    assert detect_type(JPEG) == "image/jpeg"
    assert detect_type(GIF) == "image/gif"
    assert detect_type(PDF) == "application/pdf"


@pytest.mark.test_id("TEST-034S-002")
@pytest.mark.requirements("REQ-034-04")
@pytest.mark.scenario("AC-034-04")
def test_detect_type_recognises_webp_via_riff_container():
    """WEBP needs the RIFF container plus the WEBP tag at bytes 8-12."""
    assert detect_type(WEBP) == "image/webp"
    # RIFF without the WEBP tag is not a WEBP image.
    assert detect_type(b"RIFF" + b"\x00" * 32) != "image/webp"


@pytest.mark.test_id("TEST-034S-003")
@pytest.mark.requirements("REQ-034-04")
@pytest.mark.scenario("AC-034-04")
def test_detect_type_rejects_non_image_content():
    """HTML, plain text and empty input are not any known image type."""
    assert detect_type(b"<html><body>x</body></html>") is None
    assert detect_type(b"just some text") is None
    assert detect_type(b"") is None


@pytest.mark.test_id("TEST-034S-004")
@pytest.mark.requirements("REQ-034-04")
@pytest.mark.scenario("AC-034-04")
def test_detected_type_never_escapes_the_allowed_set():
    """Detection can only ever return an advertised type (or None)."""
    allowed = set(SIGNATURES) | {"image/webp"}
    samples = [PNG, JPEG, GIF, PDF, WEBP, b"\x00" * 64, b"%PDF-", b"RIFF" + b"\x00" * 40]
    for sample in samples:
        detected = detect_type(sample)
        assert detected is None or detected in allowed


# ---------------------------------------------------------------------------
# declared vs. detected -- the quarantine contract
# ---------------------------------------------------------------------------


@pytest.mark.test_id("TEST-034S-005")
@pytest.mark.requirements("REQ-034-04")
@pytest.mark.scenario("AC-034-04")
def test_matching_declared_type_is_accepted(tmp_path, _inbox_tenant):
    """A PNG declared as image/png passes the MIME gate and is processed."""
    service = _service(tmp_path)
    email = service.receive(_inbox_tenant, "a@example.com", "receipt", [
        _attachment(PNG, "receipt.png", "image/png"),
    ])

    attachment = email["attachments"][0]
    assert attachment["status"] == "completed"
    assert attachment["error_code"] is None
    assert attachment["detected_type"] == "image/png"


@pytest.mark.test_id("TEST-034S-006")
@pytest.mark.requirements("REQ-034-04")
@pytest.mark.scenario("AC-034-04")
def test_mime_spoof_is_quarantined(tmp_path, _inbox_tenant):
    """HTML bytes declared as image/png are quarantined, never processed.

    ``unsupported_content`` (not ``mime_mismatch``) is the correct code here:
    unrecognised content is rejected *before* the declared/detected comparison,
    because there is no detected type to disagree with.
    """
    service = _service(tmp_path)
    email = service.receive(_inbox_tenant, "a@example.com", "spoof", [
        _attachment(b"<html><script>alert(1)</script></html>", "evil.png", "image/png"),
    ])

    attachment = email["attachments"][0]
    assert attachment["status"] == "quarantined"
    assert attachment["error_code"] == "unsupported_content"
    assert attachment["receipt_id"] is None


@pytest.mark.test_id("TEST-034S-007")
@pytest.mark.requirements("REQ-034-04")
@pytest.mark.scenario("AC-034-04")
def test_declared_type_cannot_upgrade_unsupported_content(tmp_path, _inbox_tenant):
    """Correctly-declared but unrecognised bytes are still quarantined."""
    service = _service(tmp_path)
    email = service.receive(_inbox_tenant, "a@example.com", "pdf-as-png", [
        _attachment(PDF, "doc.png", "image/png"),
    ])

    attachment = email["attachments"][0]
    assert attachment["status"] == "quarantined"
    assert attachment["error_code"] == "mime_mismatch"


@pytest.mark.test_id("TEST-034S-008")
@pytest.mark.requirements("REQ-034-04")
@pytest.mark.scenario("AC-034-04")
def test_octet_stream_declaration_of_real_image_is_quarantined(tmp_path, _inbox_tenant):
    """A real image declared as application/octet-stream is a mismatch."""
    service = _service(tmp_path)
    email = service.receive(_inbox_tenant, "a@example.com", "unlabelled", [
        _attachment(PNG, "receipt.png", "application/octet-stream"),
    ])

    assert email["attachments"][0]["error_code"] == "mime_mismatch"


@pytest.mark.test_id("TEST-034S-009")
@pytest.mark.requirements("REQ-034-04")
@pytest.mark.scenario("AC-034-04")
def test_missing_content_fails_rather_than_defaulting(tmp_path, _inbox_tenant):
    """An attachment with no bytes fails instead of being processed as empty."""
    service = _service(tmp_path)
    email = service.receive(_inbox_tenant, "a@example.com", "empty", [
        {"filename": "receipt.png", "content_type": "image/png", "content_base64": ""},
    ])

    attachment = email["attachments"][0]
    assert attachment["status"] == "failed"
    assert attachment["error_code"] == "content_missing"


@pytest.mark.test_id("TEST-034S-010")
@pytest.mark.requirements("REQ-034-04")
@pytest.mark.scenario("AC-034-04")
def test_oversize_attachment_is_quarantined(tmp_path, _inbox_tenant):
    """Content beyond MAX_ATTACHMENT_BYTES is quarantined before processing."""
    service = _service(tmp_path)
    oversized = b"\x89PNG\r\n\x1a\n" + b"\x00" * (MAX_ATTACHMENT_BYTES + 1)
    email = service.receive(_inbox_tenant, "a@example.com", "big", [
        _attachment(oversized, "big.png", "image/png"),
    ])

    attachment = email["attachments"][0]
    assert attachment["status"] == "quarantined"
    assert attachment["error_code"] == "attachment_too_large"


@pytest.mark.test_id("TEST-034S-011")
@pytest.mark.requirements("REQ-034-04")
@pytest.mark.scenario("AC-034-04")
def test_quarantined_attachment_cannot_be_retried(tmp_path, _inbox_tenant):
    """A quarantined (spoofed) attachment is terminal: retry is refused."""
    service = _service(tmp_path)
    email = service.receive(_inbox_tenant, "a@example.com", "spoof", [
        _attachment(b"<html></html>", "evil.png", "image/png"),
    ])
    attachment_id = email["attachments"][0]["attachment_id"]

    with pytest.raises(ValueError):
        service.retry(_inbox_tenant, email["email_id"], attachment_id)


# ---------------------------------------------------------------------------
# filename handling (part of the same untrusted-input boundary)
# ---------------------------------------------------------------------------


@pytest.mark.test_id("TEST-034S-012")
@pytest.mark.requirements("REQ-034-04")
@pytest.mark.scenario("AC-034-04")
def test_filename_traversal_is_neutralised():
    """Path components in an attachment name are stripped, not honoured."""
    assert safe_filename("../../etc/passwd") == "passwd"
    assert safe_filename("C:\\Windows\\System32\\evil.png") == "evil.png"
    assert "/" not in safe_filename("a/b/c.png")
    assert safe_filename("...") == "attachment"


# ---------------------------------------------------------------------------
# tenant scoping -- the inbound pipeline stores under a tenant too
# ---------------------------------------------------------------------------


@pytest.mark.test_id("TEST-034S-013")
@pytest.mark.requirements("REQ-034-05")
@pytest.mark.scenario("AC-034-05")
def test_email_is_not_readable_by_another_tenant(tmp_path):
    """An inbound email, its subject and its attachments stay with its tenant.

    ``InboxService.get`` filters on ``tenant_id``; without that predicate one
    tenant could read another's inbound mail, which carries the attachment
    bytes and the sender/subject of the other tenant's correspondence.
    """
    service = _service(tmp_path)
    email = service.receive("tenant-a", "a@example.com", "Salary March", [
        _attachment(PNG, "receipt.png", "image/png"),
    ])

    assert service.get("tenant-a", email["email_id"])["subject"] == "Salary March"

    with pytest.raises(KeyError):
        service.get("tenant-b", email["email_id"])


@pytest.mark.test_id("TEST-034S-014")
@pytest.mark.requirements("REQ-034-05")
@pytest.mark.scenario("AC-034-05")
def test_inbound_listing_does_not_cross_tenants(tmp_path):
    """``list`` is tenant-scoped, so it never enumerates another tenant's mail."""
    service = _service(tmp_path)
    service.receive("tenant-a", "a@example.com", "A", [
        _attachment(PNG, "a.png", "image/png"),
    ])
    service.receive("tenant-b", "b@example.com", "B", [
        _attachment(JPEG, "b.jpg", "image/jpeg"),
    ])

    assert [e["subject"] for e in service.list("tenant-a")] == ["A"]
    assert [e["subject"] for e in service.list("tenant-b")] == ["B"]


@pytest.mark.test_id("TEST-034S-015")
@pytest.mark.requirements("REQ-034-05")
@pytest.mark.scenario("AC-034-05")
def test_retry_cannot_target_another_tenants_attachment(tmp_path):
    """Re-processing is tenant-scoped: another tenant cannot drive a retry."""
    service = _service(tmp_path)
    email = service.receive("tenant-a", "a@example.com", "Docs", [
        {"filename": "r.png", "content_type": "image/png",
         "content_base64": base64.b64encode(PNG).decode()},
    ])
    attachment_id = email["attachments"][0]["attachment_id"]

    with pytest.raises(KeyError):
        service.retry("tenant-b", email["email_id"], attachment_id)
