"""REQ-UX-04/06/19; AC-UX-04/06/19 behavior regressions."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from tempfile import SpooledTemporaryFile
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile

from app import consumer_dashboard, product_api
from app.advanced_workspace import AdvancedWorkspace
from app.api import app
from app.ocr import ConfidenceReceipt
from app.product_service import Actor, ProductConflict, ProductService


def receipt():
    return ConfidenceReceipt(
        merchant="Shop",
        date="2026-10-12",
        items=[],
        total=10,
        tax=0,
        currency="HUF",
        raw_text="shop",
        confidence={"total": 0.9},
    )


def test_req_ux04_ac_ux04_filters_before_pagination():
    s = ProductService()
    a = Actor("search-ux", "admin")
    for i in range(55):
        r = s.create_receipt(a, receipt(), str(i))
        s.correct(a, r["receipt_id"], {"date": "2026-09-01"}, 1, False)
    r = s.create_receipt(a, receipt(), "target")
    s._db.execute(
        "UPDATE receipts SET payload=json_set(payload,'$.category','Food') WHERE receipt_id=?",
        (r["receipt_id"],),
    )
    s._db.commit()
    result = s.search_receipts(
        a, category="Food", date_from="2026-10-01", date_to="2026-10-31", limit=1
    )
    assert result["total"] == 1
    assert result["items"][0]["receipt_id"] == r["receipt_id"]
    assert "Food" in result["categories"]
    assert not s.search_receipts(Actor("other", "admin"), category="Food")["items"]
    with pytest.raises(ValueError):
        s.search_receipts(a, date_from="2026-99-01")


def test_req_ux06_ac_ux06_atomic_persisted_replay_and_conflict(tmp_path):
    path = tmp_path / "uploads.sqlite"
    s = ProductService(path)
    a = Actor("upload-ux", "admin")
    calls = []

    def create():
        calls.append(1)
        return s.create_receipt(a, receipt(), "receipt.png")

    first = s.idempotent_upload(a, "same-key", "fingerprint", create)
    assert s.idempotent_upload(a, "same-key", "fingerprint", create) == first
    assert len(calls) == 1
    restarted = ProductService(path)
    assert (
        restarted.idempotent_upload(
            a, "same-key", "fingerprint", lambda: pytest.fail("reprocessed")
        )
        == first
    )
    with pytest.raises(ProductConflict):
        restarted.idempotent_upload(a, "same-key", "different", create)
    assert (
        restarted.idempotent_upload(
            Actor("other", "admin"), "same-key", "different", lambda: {"receipt_id": "other"}
        )["receipt_id"]
        == "other"
    )


def test_req_ux06_ac_ux06_failure_rolls_back_nested_writes(tmp_path):
    s = ProductService(tmp_path / "rollback.sqlite")
    a = Actor("failure-ux", "admin")

    def fail():
        s.create_receipt(a, receipt(), "receipt.png")
        raise RuntimeError("after receipt created")

    with pytest.raises(RuntimeError):
        s.idempotent_upload(a, "retry", "fp", fail)
    assert s.search_receipts(a)["total"] == 0
    assert s.idempotent_upload(
        a, "retry", "fp", lambda: s.create_receipt(a, receipt(), "receipt.png")
    )["receipt_id"]


def test_req_ux06_ac_ux06_parallel_connections(tmp_path):
    path = tmp_path / "parallel.sqlite"
    a = Actor("parallel-ux", "admin")
    services = [ProductService(path), ProductService(path)]

    def run(s):
        return s.idempotent_upload(
            a, "parallel", "fp", lambda: s.create_receipt(a, receipt(), "image")
        )

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(run, services))
    assert results[0]["receipt_id"] == results[1]["receipt_id"]
    assert services[0].search_receipts(a)["total"] == 1


def test_req_ux06_ac_ux06_http_replay_does_not_repeat_ocr():
    s = ProductService()
    w = AdvancedWorkspace(s)
    actor = Actor("http-ux", "admin")

    async def upload(data=b"image"):
        with SpooledTemporaryFile() as stream:
            stream.write(data)
            stream.seek(0)
            file = UploadFile(
                stream, filename="same.png", headers=Headers({"content-type": "image/png"})
            )
            return await product_api.upload_receipt(
                file=file, ai_scan=None, current=actor, idempotency_key="http-replay"
            )

    with (
        patch.object(product_api, "service", s),
        patch.object(product_api, "advanced", w),
        patch("app.product_api.parse_receipt_with_confidence", return_value=receipt()) as ocr,
    ):
        first = asyncio.run(upload())
        replay = asyncio.run(upload())
        assert first["receipt_id"] == replay["receipt_id"]
        assert ocr.call_count == 1
        with pytest.raises(HTTPException) as exc:
            asyncio.run(upload(b"other"))
        assert exc.value.status_code == 409


def test_req_ux19_ac_ux19_empty_dashboard_currency_is_explicit():
    s = ProductService()
    w = AdvancedWorkspace(s)
    with patch.object(product_api, "service", s), patch.object(product_api, "advanced", w):
        empty = consumer_dashboard.build_consumer_dashboard("currency-ux", date(2026, 10, 12))
        assert empty["household"]["currency"] is None
        assert empty["monthly_by_category"]["currency"] is None
        w.save_preferences("currency-ux", "admin", {"language": "hu", "base_currency": "HUF"})
        chosen = consumer_dashboard.build_consumer_dashboard("currency-ux", date(2026, 10, 12))
        assert chosen["household"]["currency"] == "HUF"
        assert chosen["monthly_by_category"]["currency"] == "HUF"
        w.save_preferences("currency-ux", "admin", {"language": "en"})
        assert (
            consumer_dashboard.build_consumer_dashboard("currency-ux", date(2026, 10, 12))[
                "household"
            ]["currency"]
            == "HUF"
        )


def test_req_ux16_ac_ux16_category_suggestions_are_confirmed_and_tenant_scoped():
    s = ProductService()
    a = Actor("categories-ux", "admin")
    old = s.create_receipt(a, receipt(), "old")
    s.correct(a, old["receipt_id"], {"category": "Groceries"}, 1, True)
    new = s.create_receipt(a, receipt(), "new")
    assert s.get_receipt(a, new["receipt_id"])["suggested_category"] == "Groceries"
    assert "category" not in s.get_receipt(a, new["receipt_id"])["receipt"]
    assert s.suggest_category(Actor("other", "admin"), "Shop") is None
    s.correct(a, new["receipt_id"], {"category": "Other"}, 1, True)
    assert s.get_receipt(a, old["receipt_id"])["receipt"]["category"] == "Groceries"


def test_req_ux17_ac_ux17_summary_frequency_is_persisted_and_validated():
    w = AdvancedWorkspace(ProductService())
    assert (
        w.save_preferences("notify-ux", "admin", {"insight_frequency": "weekly"})[
            "insight_frequency"
        ]
        == "weekly"
    )
    assert w.preferences("notify-ux", "admin")["insight_frequency"] == "weekly"
    with pytest.raises(ValueError):
        w.save_preferences("notify-ux", "admin", {"insight_frequency": "hourly"})


def test_req_ux17_ac_ux17_weekly_evaluation_honors_preference():
    from app import insight_api

    s = ProductService()
    w = AdvancedWorkspace(s)
    w.save_preferences("frequency-ux", "admin", {"insight_frequency": "weekly"})
    with (
        patch.object(product_api, "advanced", w),
        patch.object(insight_api, "_insight_tenant", return_value=("frequency-ux", "admin")),
        patch.object(insight_api, "_evaluate_tenant", return_value=[]) as evaluate,
    ):
        insight_api.evaluate_insights(insight_api.EvaluateRequest(tenant_id="frequency-ux"))
        insight_api.evaluate_insights(insight_api.EvaluateRequest(tenant_id="frequency-ux"))
        assert evaluate.call_count == 1
        w.save_preferences("frequency-ux", "admin", {"insight_frequency": "never"})
        insight_api.evaluate_insights(insight_api.EvaluateRequest(tenant_id="frequency-ux"))
        assert evaluate.call_count == 1


def test_req_ux11_ac_ux11_exact_review_link_works_beyond_first_page():
    s = ProductService()
    a = Actor("review-ux", "admin")
    p = receipt()
    p.confidence = {"total": 0.2}
    for _ in range(51):
        s.create_receipt(a, p, "other")
    target = s.create_receipt(a, p, "target")
    result = s.list_reviews(a, receipt_id=target["receipt_id"], readiness="needs_review")
    assert result["total"] == 1
    assert result["items"][0]["receipt_id"] == target["receipt_id"]


def test_req_ux16_ac_ux16_chosen_category_drives_dashboard():
    s = ProductService()
    w = AdvancedWorkspace(s)
    a = Actor("category-dashboard-ux", "admin")
    row = s.create_receipt(a, receipt(), "category")
    s.correct(a, row["receipt_id"], {"category": "Groceries"}, 1, True)
    with patch.object(product_api, "service", s), patch.object(product_api, "advanced", w):
        data = consumer_dashboard.build_consumer_dashboard(a.tenant_id, date(2026, 10, 12))
        assert data["monthly_by_category"]["categories"][0]["key"] == "Groceries"


def test_req_ux06_ac_ux06_shared_connection_does_not_expose_partial_upload():
    import threading
    from concurrent.futures import TimeoutError

    s = ProductService()
    a = Actor("partial-ux", "admin")
    started = threading.Event()
    release = threading.Event()
    reading = threading.Event()

    def process():
        s.create_receipt(a, receipt(), "partial")
        started.set()
        assert release.wait(3)
        raise RuntimeError("rollback")

    def write():
        with pytest.raises(RuntimeError):
            s.idempotent_upload(a, "partial", "fp", process)

    def read():
        reading.set()
        return s.search_receipts(a)["total"]

    with ThreadPoolExecutor(2) as pool:
        writer = pool.submit(write)
        assert started.wait(3)
        reader = pool.submit(read)
        assert reading.wait(3)
        try:
            with pytest.raises(TimeoutError):
                reader.result(timeout=0.05)
        finally:
            release.set()
        writer.result(timeout=3)
        assert reader.result(timeout=3) == 0


def test_req_ux19_ac_ux19_dashboard_uses_current_roles_explicit_currency():
    s = ProductService()
    w = AdvancedWorkspace(s)
    w.save_preferences("roles-currency-ux", "owner", {"base_currency": "EUR"})
    w.save_preferences("roles-currency-ux", "adult", {"base_currency": "HUF"})
    with patch.object(product_api, "service", s), patch.object(product_api, "advanced", w):
        result = consumer_dashboard.build_consumer_dashboard(
            "roles-currency-ux", date(2026, 10, 12), role="adult"
        )
        assert result["monthly_by_category"]["currency"] == "HUF"


def test_req_ux17_ac_ux17_manual_evaluation_can_bypass_cadence():
    from app import insight_api

    s = ProductService()
    w = AdvancedWorkspace(s)
    w.save_preferences("manual-frequency-ux", "admin", {"insight_frequency": "weekly"})
    with (
        patch.object(product_api, "advanced", w),
        patch.object(insight_api, "_insight_tenant", return_value=("manual-frequency-ux", "admin")),
        patch.object(insight_api, "_evaluate_tenant", return_value=[]) as evaluate,
    ):
        insight_api.evaluate_insights(insight_api.EvaluateRequest(tenant_id="manual-frequency-ux"))
        insight_api.evaluate_insights(
            insight_api.EvaluateRequest(tenant_id="manual-frequency-ux", force=True)
        )
        assert evaluate.call_count == 2


def test_req_ux06_ac_ux06_retention_removes_replayed_receipt_content():
    from datetime import UTC, datetime

    s = ProductService()
    a = Actor("purge-upload-ux", "admin")
    original = s.idempotent_upload(
        a, "purge-key", "fp", lambda: s.create_receipt(a, receipt(), "old.png")
    )
    s.purge_expired(a, datetime(2099, 1, 1, tzinfo=UTC))
    encoded = s._db.execute(
        "SELECT result FROM upload_commands WHERE tenant_id=?", (a.tenant_id,)
    ).fetchone()[0]
    assert "Shop" not in encoded
    with pytest.raises(ProductConflict):
        s.idempotent_upload(a, "purge-key", "fp", lambda: pytest.fail("recreated purged receipt"))


def test_req_ux06_ac_ux06_commit_failure_is_rolled_back():
    import sqlite3

    s = ProductService()
    a = Actor("commit-failure-ux", "admin")
    with (
        patch.object(
            s._db, "commit", side_effect=sqlite3.OperationalError("simulated commit failure")
        ),
        pytest.raises(sqlite3.OperationalError),
    ):
        s.idempotent_upload(
            a, "commit-failure", "fp", lambda: s.create_receipt(a, receipt(), "image")
        )
    assert not s._db.in_transaction
    assert s.search_receipts(a)["total"] == 0
    assert s.idempotent_upload(
        a, "commit-failure", "fp", lambda: s.create_receipt(a, receipt(), "image")
    )["receipt_id"]


def test_req_ux19_ac_ux19_migration_verifier_preserves_source_and_legacy_rows(tmp_path):
    import hashlib
    import importlib.util
    from pathlib import Path

    source = tmp_path / "original.sqlite"
    store = ProductService(source)
    store.create_receipt(Actor("migration-test", "admin"), receipt(), "receipt.png")
    with store._db:
        store._db.execute("DROP TABLE upload_commands")
        store._db.execute("DROP TABLE product_migrations")
    store._db.close()
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    path = Path(__file__).resolve().parents[1] / "scripts" / "verify-ux-migration.py"
    spec = importlib.util.spec_from_file_location("verify_ux_migration", path)
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    result = verifier.verify(source)
    assert result["legacy_rows_unchanged"]
    assert result["integrity_ok"]
    assert result["receipts_preserved"] == 1
    assert result["private_copy_removed"]
    assert before == hashlib.sha256(source.read_bytes()).hexdigest()
