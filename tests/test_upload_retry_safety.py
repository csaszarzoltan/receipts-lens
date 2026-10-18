"""I3: OCR runs outside the write lock; a failed or repeated upload costs one quota unit at most."""
import asyncio
import threading
from tempfile import SpooledTemporaryFile
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile

from app import product_api
from app.advanced_workspace import AdvancedWorkspace
from app.ocr import ConfidenceReceipt
from app.product_service import Actor, ProductConflict, ProductService
from app.quota import QuotaStore, quota_store


def _service(tmp_path):
    return ProductService(str(tmp_path / "p.db"))


def _actor():
    return Actor("t1", "owner")


def test_prepare_runs_without_holding_the_write_lock(tmp_path):
    s = _service(tmp_path)
    a = _actor()
    seen = {}

    def prepare():
        # While the "OCR" runs, another writer must be able to take the lock.
        done = threading.Event()

        def other():
            seen["ok"] = s.idempotent_upload(a, "other", "f2", lambda: {"v": 2})
            done.set()

        t = threading.Thread(target=other)
        t.start()
        seen["finished_during_prepare"] = done.wait(2)
        t.join()
        return "parsed"

    out = s.idempotent_upload(a, "k1", "f1", lambda p: {"v": p}, prepare=prepare)
    assert out == {"v": "parsed"}
    assert seen["finished_during_prepare"] is True
    assert seen["ok"] == {"v": 2}


def test_discard_called_once_when_create_fails_and_retry_succeeds(tmp_path):
    s = _service(tmp_path)
    a = _actor()
    discards = []

    def boom(_):
        raise RuntimeError("write failed")

    with pytest.raises(RuntimeError):
        s.idempotent_upload(a, "k", "f", boom, prepare=lambda: 1, discard=lambda: discards.append(1))
    assert discards == [1]
    out = s.idempotent_upload(a, "k", "f", lambda p: {"ok": p}, prepare=lambda: 1,
                              discard=lambda: discards.append(2))
    assert out == {"ok": 1} and discards == [1]


def test_replay_skips_prepare_and_race_discards(tmp_path):
    s = _service(tmp_path)
    a = _actor()
    s.idempotent_upload(a, "k", "f", lambda p: {"first": True}, prepare=lambda: 1)
    calls = []
    again = s.idempotent_upload(a, "k", "f", lambda p: {"second": True},
                                prepare=lambda: calls.append("prepare"), discard=lambda: calls.append("discard"))
    assert again == {"first": True} and calls == []
    with pytest.raises(ProductConflict):
        s.idempotent_upload(a, "k", "other", lambda p: {}, prepare=lambda: calls.append("p"))
    assert calls == []


def test_quota_refund_floor_and_counts():
    q = QuotaStore(limit=2)
    q.incr_and_check("t")
    q.incr_and_check("t")
    q.refund("t")
    assert q.get_quota("t")["used"] == 1
    q.refund("t")
    q.refund("t")
    assert q.get_quota("t")["used"] == 0


def _receipt():
    return ConfidenceReceipt(merchant="Shop", date="2026-10-12", items=[], total=10, tax=0,
                             currency="HUF", raw_text="shop", confidence={"total": 0.9})


def _upload(actor, key, data=b"image"):
    async def go():
        with SpooledTemporaryFile() as stream:
            stream.write(data)
            stream.seek(0)
            file = UploadFile(stream, filename="a.png", headers=Headers({"content-type": "image/png"}))
            return await product_api.upload_receipt(file=file, ai_scan=None, current=actor, idempotency_key=key)
    return asyncio.run(go())


def test_http_failed_ocr_and_replay_cost_at_most_one_quota_unit():
    s = ProductService()
    w = AdvancedWorkspace(s)
    actor = Actor("i3-quota", "admin")
    quota_store.reset(actor.tenant_id)
    with (patch.object(product_api, "service", s), patch.object(product_api, "advanced", w)):
        with patch("app.product_api.parse_receipt_with_confidence", side_effect=RuntimeError("ocr down")):
            for _ in range(3):  # three failed attempts with the same key
                with pytest.raises(HTTPException) as exc:
                    _upload(actor, "i3-key")
                assert exc.value.status_code == 422
        assert quota_store.get_quota(actor.tenant_id)["used"] == 0
        with patch("app.product_api.parse_receipt_with_confidence", return_value=_receipt()):
            first = _upload(actor, "i3-key")
            replay = _upload(actor, "i3-key")
        assert first["receipt_id"] == replay["receipt_id"]
        assert quota_store.get_quota(actor.tenant_id)["used"] == 1
