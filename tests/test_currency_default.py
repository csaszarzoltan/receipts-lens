"""Currency provenance on read: receipts saved before provenance existed must not look verified (I6, UX-19)."""
import json
from types import SimpleNamespace

from app.product_service import Actor, ProductService


def parsed(vendor="TESCO EXPRESS", total=4786.0, currency="HUF"):
    return SimpleNamespace(
        merchant=vendor, date=None, total=total, tax=0.0, currency=currency,
        items=[SimpleNamespace(name="Item", price=total)],
        confidence={k: .95 for k in ("vendor", "date", "total", "tax", "currency", "line_items")},
    )


def strip_provenance(service, receipt_id):
    """Turn a stored row into the shape of a pre-provenance legacy row."""
    row = service._db.execute("SELECT payload FROM receipts WHERE receipt_id=?", (receipt_id,)).fetchone()
    payload = json.loads(row[0])
    payload.pop("currency_source", None)
    payload.pop("currency_assumed", None)
    payload["currency"] = "USD"
    service._db.execute("UPDATE receipts SET payload=? WHERE receipt_id=?", (json.dumps(payload), receipt_id))
    return payload


def test_legacy_receipt_without_provenance_reads_as_unverified():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "admin")
    rid = service.create_receipt(actor, parsed(), "a.png")["receipt_id"]
    strip_provenance(service, rid)

    receipt = service.get_receipt(actor, rid)["receipt"]
    assert receipt["currency"] == "USD"
    assert receipt["currency_source"] == "unverified"
    assert receipt["currency_assumed"] is True


def test_legacy_receipt_in_search_results_reads_as_unverified():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "admin")
    rid = service.create_receipt(actor, parsed(), "a.png")["receipt_id"]
    strip_provenance(service, rid)

    items = service.search_receipts(actor, status="completed")["items"]
    assert items[0]["receipt"]["currency_source"] == "unverified"
    assert items[0]["receipt"]["currency_assumed"] is True


def test_read_marking_does_not_write_back_to_the_database():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "admin")
    rid = service.create_receipt(actor, parsed(), "a.png")["receipt_id"]
    stored = strip_provenance(service, rid)

    service.get_receipt(actor, rid)
    service.search_receipts(actor, status="completed")
    service.search_receipts(actor, status="needs_review")
    row = service._db.execute("SELECT payload FROM receipts WHERE receipt_id=?", (rid,)).fetchone()
    assert json.loads(row[0]) == stored


def test_receipt_with_marker_provenance_is_unchanged():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "admin")
    rid = service.create_receipt(actor, parsed(currency="HUF"), "a.png")["receipt_id"]

    receipt = service.get_receipt(actor, rid)["receipt"]
    assert receipt["currency_source"] == "marker"
    assert receipt["currency_assumed"] is False


def test_receipt_without_a_currency_marker_keeps_no_currency_until_confirmed():
    """I13: the locale default is a guess; it is flagged and not stored as a value."""
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "admin")
    guessed = parsed(currency="USD")
    guessed.currency_source = "default"

    receipt = service.create_receipt(actor, guessed, "a.png")["receipt"]
    assert receipt["currency"] is None
    assert receipt["currency_source"] == "default"
    assert receipt["currency_assumed"] is True


def test_confirming_the_currency_by_hand_stores_it():
    service = ProductService(":memory:")
    actor = Actor("tenant-a", "admin")
    guessed = parsed(currency="USD")
    guessed.currency_source = "default"
    created = service.create_receipt(actor, guessed, "a.png")
    service.update_receipt_workspace(actor, created["receipt_id"], 1, {"currency": "HUF"}, None, None, False)

    receipt = service.get_receipt(actor, created["receipt_id"])["receipt"]
    assert receipt["currency"] == "HUF"
    assert receipt["currency_source"] == "user"
