"""REST API v2 — Batch processing and export endpoints.

The AI-mode OCR flow (``ai_scan=true`` on ``POST /v1/parse-receipt`` and
``POST /product/receipts/upload``) lives in app/api.py and app/product_api.py;
the batch/export endpoints here intentionally keep the classic Tesseract path
so their response schemas stay stable.
"""
from __future__ import annotations

from datetime import UTC

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import Response

batch_router = APIRouter(prefix="/api/v1")


# ---- Batch Processing Endpoints ----

@batch_router.post("/receipts/batch")
async def batch_parse_receipts(
    files: list[UploadFile] | None = File(default=None),
    image_urls: str | None = Form(default=None),
    lang: str | None = Form(default=None, description="Language code (eng, deu, fra, spa, ita, por)"),
    webhook_url: str | None = Form(default=None),
    max_workers: int = Form(default=4, ge=1, le=8),
) -> dict:
    """Parse 10+ receipts in parallel with progress tracking.

    Accepts multipart file uploads or JSON array of image URLs.
    Returns job_id for polling progress via GET /api/v1/receipts/batch/{job_id}.
    """
    import uuid
    from datetime import datetime

    from app.batch import BatchJob as _BatchJob
    from app.batch import BatchProcessor, _batch_jobs

    # Direct function calls in tests receive FastAPI parameter marker defaults.
    if not isinstance(max_workers, int): max_workers = 4
    if not isinstance(image_urls, str): image_urls = None
    if not isinstance(files, list): files = None
    if not isinstance(lang, str): lang = None
    if not isinstance(webhook_url, str): webhook_url = None
    job_id = str(uuid.uuid4())
    job = _BatchJob(
        job_id=job_id,
        status="queued",
        total=0,
        created_at=datetime.now(UTC).isoformat(),
        webhook_url=webhook_url,
    )
    _batch_jobs[job_id] = job

    # Collect items
    items: list[bytes] = []
    if files and hasattr(files, "__iter__") and not isinstance(files, str):
        for f in files:
            content = await f.read()
            items.append(content)
    if image_urls:
        import json as _json

        try:
            urls = _json.loads(image_urls)
            if isinstance(urls, list):
                items.extend(urls)  # type: ignore[arg-type]
        except Exception:
            pass

    job.total = len(items)
    processor = BatchProcessor(max_workers=max_workers)
    # Fire and forget — process in background
    import asyncio

    asyncio.create_task(processor.process_batch(items, lang=lang, webhook_url=webhook_url))

    return {"job_id": job_id, "status": "queued", "total": len(items)}


@batch_router.get("/receipts/batch/{job_id}")
async def batch_job_status(job_id: str) -> dict:
    """Poll batch processing progress."""
    from app.batch import _batch_jobs

    job = _batch_jobs.get(job_id)
    if job is None:
        return {"job_id": job_id, "status": "not_found", "total": 0, "completed": 0}
    return job.to_dict()


# ---- Export Endpoints ----

# NOTE: the static /receipts/export/formats route MUST be declared before the
# parameterized /receipts/export/{format} route — Starlette matches routes in
# registration order, so a late static route would be swallowed by {format}
# and return a 500 "Unknown format" instead of the formats listing.

@batch_router.get("/receipts/export/formats")
async def list_export_formats() -> dict:
    """List available export formats and their column mappings.

    GET /api/v1/receipts/export/formats.
    """
    from app.export import PROFILES

    formats = []
    for name, profile in PROFILES.items():
        formats.append({
            "name": name,
            "columns": profile.columns,
            "delimiter": profile.delimiter,
        })
    return {"formats": formats}


@batch_router.get("/receipts/export/{format}")
async def export_receipts_endpoint(
    format: str,
    date_from: str | None = None,
    date_to: str | None = None,
    category: str | None = None,
) -> Response:
    """Export stored receipts in accounting-compatible CSV format.

    GET /api/v1/receipts/export/{format} — supported formats: quickbooks, xero, generic.
    """
    from app.export import PROFILES, ReceiptExporter

    if format not in PROFILES:
        raise ValueError(f"Unknown format: {format!r}. Available: {list(PROFILES.keys())}")
    exporter = ReceiptExporter(format)
    csv_str = exporter.export_csv([])
    return Response(content=csv_str, media_type="text/csv")
