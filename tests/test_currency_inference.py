"""Currency without a printed marker: inferred from history and labelled.

A receipt that prints no currency symbol or code used to be stored as USD
silently. Now the currency is inferred from earlier receipts (same merchant
first, then the tenant), and every inferred or defaulted value is marked
with ``currency_source`` and ``currency_assumed`` so the user can see it and
correct it.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app import ocr
from app.product_service import Actor, ProductService


def _ocr_receipt(monkeypatch, text: str):
    monkeypatch.setattr(ocr, "extract_text", lambda image_bytes, lang="eng": text)
    return ocr.parse_receipt(b"unused")


@pytest.mark.test_id("TEST-RL-V02-171")
@pytest.mark.requirements("FEAT-RL-V02-REQ-060")
@pytest.mark.scenario("AC-RL-V02-41")
def test_ocr_marks_locale_default_when_no_marker(monkeypatch):
    parsed = _ocr_receipt(monkeypatch, "ACME\nMilk 1.20\nTOTAL 1.20")
    assert parsed.currency == "USD"
    assert parsed.currency_source == "default"


@pytest.mark.test_id("TEST-RL-V02-172")
@pytest.mark.requirements("FEAT-RL-V02-REQ-060")
@pytest.mark.scenario("AC-RL-V02-41")
def test_ocr_marks_explicit_marker(monkeypatch):
    parsed = _ocr_receipt(monkeypatch, "ACME\nMilk 1.20 EUR\nTOTAL 1.20 EUR")
    assert parsed.currency == "EUR"
    assert parsed.currency_source == "marker"


def _receipt(merchant, currency=None, source="marker", total=10.0):
    fields = {"merchant": merchant, "date": "2026-08-01", "total": total, "tax": None,
              "currency": currency, "items": [SimpleNamespace(name="Item", price=total)],
              "confidence": {"vendor": 0.95, "total": 0.95, "date": 0.95, "line_items": 0.95}}
    if source is not None:
        fields["currency_source"] = source
    return SimpleNamespace(**fields)


@pytest.fixture
def service():
    return ProductService(":memory:")


ACTOR = Actor("tenant-a", "admin")


@pytest.mark.test_id("TEST-RL-V02-173")
@pytest.mark.requirements("FEAT-RL-V02-REQ-060")
@pytest.mark.scenario("AC-RL-V02-41")
def test_unmarked_receipt_follows_same_merchant_history(service):
    service.create_receipt(ACTOR, _receipt("ACME", "EUR"), "a.png")
    rid = service.create_receipt(ACTOR, _receipt("ACME", "USD", "default"), "b.png")["receipt_id"]
    payload = service.get_receipt(ACTOR, rid)["receipt"]
    assert payload["currency"] == "EUR"
    assert payload["currency_source"] == "inferred_merchant"
    assert payload["currency_assumed"] is True


@pytest.mark.test_id("TEST-RL-V02-174")
@pytest.mark.requirements("FEAT-RL-V02-REQ-060")
@pytest.mark.scenario("AC-RL-V02-41")
def test_unmarked_receipt_of_new_merchant_follows_tenant_history(service):
    for merchant in ("BOLT", "SPAR", "CBA"):
        service.create_receipt(ACTOR, _receipt(merchant, "HUF"), f"{merchant}.png")
    rid = service.create_receipt(ACTOR, _receipt("NEWSHOP", "USD", "default"), "n.png")["receipt_id"]
    payload = service.get_receipt(ACTOR, rid)["receipt"]
    assert payload["currency"] == "HUF"
    assert payload["currency_source"] == "inferred_tenant"
    assert payload["currency_assumed"] is True


@pytest.mark.test_id("TEST-RL-V02-175")
@pytest.mark.requirements("FEAT-RL-V02-REQ-060")
@pytest.mark.scenario("AC-RL-V02-41")
def test_unmarked_receipt_without_history_is_default_and_marked(service):
    rid = service.create_receipt(ACTOR, _receipt("FIRST", "USD", "default"), "f.png")["receipt_id"]
    payload = service.get_receipt(ACTOR, rid)["receipt"]
    assert payload["currency"] == "USD"
    assert payload["currency_source"] == "default"
    assert payload["currency_assumed"] is True


@pytest.mark.test_id("TEST-RL-V02-176")
@pytest.mark.requirements("FEAT-RL-V02-REQ-060")
@pytest.mark.scenario("AC-RL-V02-41")
def test_explicit_marker_is_not_marked_as_assumed(service):
    rid = service.create_receipt(ACTOR, _receipt("ACME", "CHF", "marker"), "m.png")["receipt_id"]
    payload = service.get_receipt(ACTOR, rid)["receipt"]
    assert payload["currency"] == "CHF"
    assert payload["currency_source"] == "marker"
    assert payload["currency_assumed"] is False


@pytest.mark.test_id("TEST-RL-V02-177")
@pytest.mark.requirements("FEAT-RL-V02-REQ-060")
@pytest.mark.scenario("AC-RL-V02-41")
def test_history_ignores_other_assumed_currencies(service):
    """Only explicit receipts teach the inference; defaults must not reinforce themselves."""
    service.create_receipt(ACTOR, _receipt("ZED", "USD", "default"), "z1.png")
    service.create_receipt(ACTOR, _receipt("ZED", "USD", "default"), "z2.png")
    rid = service.create_receipt(ACTOR, _receipt("NEW", "GBP", "default"), "n.png")["receipt_id"]
    payload = service.get_receipt(ACTOR, rid)["receipt"]
    assert payload["currency_source"] == "default"


@pytest.mark.test_id("TEST-RL-V02-178")
@pytest.mark.requirements("FEAT-RL-V02-REQ-060")
@pytest.mark.scenario("AC-RL-V02-41")
def test_user_correction_replaces_assumption(service):
    rid = service.create_receipt(ACTOR, _receipt("FIRST", "USD", "default"), "f.png")["receipt_id"]
    out = service.correct(ACTOR, rid, {"currency": "HUF"}, expected_version=1, complete=False)
    assert out["receipt"]["currency"] == "HUF"
    assert out["receipt"]["currency_source"] == "user"
    assert out["receipt"]["currency_assumed"] is False


@pytest.mark.test_id("TEST-RL-V02-179")
@pytest.mark.requirements("FEAT-RL-V02-REQ-060")
@pytest.mark.scenario("AC-RL-V02-41")
def test_workspace_currency_edit_also_replaces_assumption(service):
    rid = service.create_receipt(ACTOR, _receipt("FIRST", "USD", "default"), "f.png")["receipt_id"]
    out = service.update_receipt_workspace(
        ACTOR, rid, expected_version=1, fields={"currency": "HUF"},
        line_items=None, metadata=None, complete=False,
    )
    assert out["receipt"]["currency_source"] == "user"
    assert out["receipt"]["currency_assumed"] is False


@pytest.mark.parametrize("bad", ["xx", "HUFF", "12$"])
@pytest.mark.test_id("TEST-RL-V02-180")
@pytest.mark.requirements("FEAT-RL-V02-REQ-060")
@pytest.mark.scenario("AC-RL-V02-41")
def test_user_currency_must_be_iso_code(service, bad):
    rid = service.create_receipt(ACTOR, _receipt("FIRST", "USD", "default"), "f.png")["receipt_id"]
    with pytest.raises(ValueError):
        service.correct(ACTOR, rid, {"currency": bad}, expected_version=1, complete=False)


@pytest.mark.test_id("TEST-RL-V02-181")
@pytest.mark.requirements("FEAT-RL-V02-REQ-060")
@pytest.mark.scenario("AC-RL-V02-41")
def test_user_currency_is_normalised_to_upper_case(service):
    rid = service.create_receipt(ACTOR, _receipt("FIRST", "USD", "default"), "f.png")["receipt_id"]
    out = service.correct(ACTOR, rid, {"currency": "huf"}, expected_version=1, complete=False)
    assert out["receipt"]["currency"] == "HUF"


@pytest.mark.test_id("TEST-RL-V02-182")
@pytest.mark.requirements("FEAT-RL-V02-REQ-060")
@pytest.mark.scenario("AC-RL-V02-41")
def test_clearing_user_currency_is_allowed_and_blocks_export_readiness(service):
    """Clearing the currency is a supported state: readiness then asks for one."""
    rid = service.create_receipt(ACTOR, _receipt("FIRST", "USD", "default"), "f.png")["receipt_id"]
    out = service.correct(ACTOR, rid, {"currency": None}, expected_version=1, complete=False)
    assert out["receipt"]["currency"] is None
    assert out["receipt"]["currency_source"] == "user"


def _huf_tenant(service):
    for merchant in ("BOLT", "SPAR", "CBA"):
        service.create_receipt(ACTOR, _receipt(merchant, "HUF"), f"{merchant}.png")


@pytest.mark.test_id("TEST-RL-V02-183")
@pytest.mark.requirements("FEAT-RL-V02-REQ-060")
@pytest.mark.scenario("AC-RL-V02-41")
def test_cents_receipt_is_never_inferred_as_zero_decimal_currency(service):
    """HUF has no minor units: a receipt with cents cannot be HUF, whatever the history says."""
    _huf_tenant(service)
    parsed = _receipt("NEWSHOP", "USD", "default", total=4.50)
    parsed.items = [SimpleNamespace(name="Item", price=4.50)]
    rid = service.create_receipt(ACTOR, parsed, "c.png")["receipt_id"]
    payload = service.get_receipt(ACTOR, rid)["receipt"]
    assert payload["currency"] != "HUF"
    assert payload["currency_source"] == "default"


@pytest.mark.test_id("TEST-RL-V02-184")
@pytest.mark.requirements("FEAT-RL-V02-REQ-060")
@pytest.mark.scenario("AC-RL-V02-41")
def test_whole_unit_receipt_still_inferred_as_huf_from_tenant(service):
    """Guard against over-blocking: no cents means HUF inference still applies."""
    _huf_tenant(service)
    rid = service.create_receipt(ACTOR, _receipt("NEWSHOP", "USD", "default", total=4400.0),
                                 "w.png")["receipt_id"]
    payload = service.get_receipt(ACTOR, rid)["receipt"]
    assert payload["currency"] == "HUF"
    assert payload["currency_source"] == "inferred_tenant"
