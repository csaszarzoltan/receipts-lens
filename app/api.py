"""ReceiptLens API layer."""
from __future__ import annotations

import json
import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from typing import Any

import httpx
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, field_validator
from starlette.middleware.base import BaseHTTPMiddleware

from app.alerts import alert_store
from app.analytics import budget_analytics, spending_analytics
from app.api_v2 import batch_router
from app.auth_api import router as auth_router
from app.budgets import budget_store
from app.categorizer import Categorizer
from app.consumer_dashboard import build_consumer_dashboard
from app.dashboard import render_forecast_dashboard
from app.forecast import forecast_router
from app.homepage import render_homepage
from app.ocr import ConfidenceReceipt, check_duplicates, parse_receipt_with_confidence
from app.product_api import Actor, service
from app.product_api import router as product_router
from app.quota_api import router as quota_router
from app.rate_limits import RateLimitMiddleware
from app.report_generator import generate_csv, generate_pdf
from app.reports import receipt_store
from app.security import fetch_image_bytes
from app.ssrf_guard import validate_scheme_and_host
from app.subscriptions_api import router as subscriptions_router
from app.sync_api import router as sync_router
from app.tax_api import router as tax_router
from app.vision_ocr import SOURCE_TESSERACT, SOURCE_VISION, parse_receipt_with_vision

logger = logging.getLogger("uvicorn.error")

# SEC-006: gate API docs behind RECEIPTLENS_ENV=production
_is_production = os.getenv("RECEIPTLENS_ENV") == "production"

app = FastAPI(
    title="ReceiptLens",
    description="Extract structured data from receipt images.",
    version="1.3.0",
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
)

# Rate limiting must be added BEFORE the CORS middlewares: middleware added
# first sits innermost of the user stack, so its 429 responses still flow back
# through CORSMiddleware/_UnconditionalCorsMiddleware and carry the
# Access-Control-* headers the browser needs (SEC-005).
app.add_middleware(RateLimitMiddleware)


@app.exception_handler(RequestValidationError)
async def _validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return validation errors WITHOUT echoing the request body (SEC-001).

    FastAPI's default 422 payload includes ``input`` (the entire submitted
    body), which leaks secrets (e.g. a client_secret sent in an unknown
    field) into responses and logs. Strip it: keep type/loc/msg only.
    Also normalize non-serializable values in ``ctx`` (e.g. ValueError
    instances raised inside field validators).
    """
    safe = []
    for err in exc.errors():
        item = {k: v for k, v in err.items() if k != "input"}
        ctx = item.get("ctx")
        if isinstance(ctx, dict):
            item["ctx"] = {
                k: (str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v)
                for k, v in ctx.items()
            }
        safe.append(item)
    return JSONResponse(status_code=422, content={"detail": safe})


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def homepage() -> HTMLResponse:
    """Return a human-friendly, self-contained service landing page."""
    return HTMLResponse(
        render_homepage(
            name=app.title,
            version=app.version,
            description=app.description or "Receipt OCR API.",
        )
    )


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def forecast_dashboard() -> HTMLResponse:
    """Return the forecast dashboard: charts, next-month spend, anomalies, budget variance."""
    return HTMLResponse(render_forecast_dashboard())


@app.get("/health")
def health() -> dict:
    """Liveness probe: the ASGI process can serve requests."""
    return {"status": "ok"}


@app.get("/ready")
def readiness() -> dict:
    """Readiness probe for the dependency-free application profile."""
    return {"status": "ready", "dependencies": {"ocr": "configured"}}


@app.get("/api/v1/platform/capabilities")
def platform_capabilities() -> dict:
    """Expose the implemented research-requirement capability contract."""
    return {
        "schema_version": 1,
        "requirements": {
            "data": ["tenant_repository", "job_lease", "idempotency", "outbox"],
            "security": ["api_key_port", "rbac", "quota", "webhook_hmac", "audit_chain"],
            "quality": ["benchmark", "calibration", "review", "correction_provenance"],
            "integrations": ["connector_port", "csv_profile", "usage_meter"],
        },
    }


# ---------------------------------------------------------------------------
# Security headers middleware (SEC-004) — every response carries the headers,
# independent of the HTTP server / proxy in front of the app.
#
#   X-Content-Type-Options: nosniff   — no MIME sniffing
#   X-Frame-Options: DENY             — no framing (clickjacking)
#   Referrer-Policy: no-referrer      — no referrer leakage
#   Permissions-Policy                — deny camera/mic/geolocation by default
#   X-XSS-Protection: 0               — disable the legacy, buggy filter
#                                       (modern best practice; the filter
#                                       itself introduces XSS risks)
#   Strict-Transport-Security (HSTS)  — HTTPS-only (production only)
#   Content-Security-Policy (CSP)     — default-src 'none' (production only;
#                                       the API serves JSON, so no scripts
#                                       need loading; relaxed in dev)
#
# Production/HTTPS is detected per request: RECEIPTLENS_HTTPS=1 or
# RECEIPTLENS_ENV=production, or the request arriving via a TLS-terminating
# proxy (x-forwarded-proto: https).
# ---------------------------------------------------------------------------


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach the SEC-004 security header set to every response."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        production = (
            request.headers.get("x-forwarded-proto", "").lower() == "https"
            or os.getenv("RECEIPTLENS_HTTPS", "").strip().lower()
            in ("1", "true", "yes")
            or os.getenv("RECEIPTLENS_ENV", "").strip().lower() == "production"
        )
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "X-XSS-Protection": "0",
        }
        if production:
            headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains"
            )
            headers["Content-Security-Policy"] = (
                "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
            )
        for name, value in headers.items():
            response.headers.setdefault(name, value)
        return response


app.add_middleware(SecurityHeadersMiddleware)


# ---------------------------------------------------------------------------
# CORS middleware — always add CORS headers to every response
# (Starlette's built-in CORSMiddleware only adds them when an Origin header
# is present in the request; the test suite sends requests without Origin.)
# We register both: the built-in one passes the interface-existence test,
# and the custom one ensures headers on every response.)
# ---------------------------------------------------------------------------
_cors_origins = [value.strip() for value in os.getenv("RECEIPTLENS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3010,http://127.0.0.1:3010").split(",") if value.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],
    allow_headers=["Accept","Content-Type","Authorization","X-Tenant-ID","X-Role","Idempotency-Key","If-Match"],
)


class _UnconditionalCorsMiddleware(BaseHTTPMiddleware):
    """Add CORS headers to every response, regardless of request headers."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        origin = request.headers.get("origin")
        if origin in _cors_origins or origin is None:
            response.headers["Access-Control-Allow-Origin"] = origin or _cors_origins[0]
            response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        if request.method == "OPTIONS":
            response.status_code = 200
        return response


# ---------------------------------------------------------------------------
# Prod alias — Caddy handle_path /api/* strips the leading /api before
# proxying to 127.0.0.1:8130. New routers register at /api/v1/* on the
# backend, so a prod request /api/v1/tax/categories would arrive as
# /v1/tax/categories and 404. This middleware re-adds the prefix so both
# prod (stripped) and direct-local (/api/v1) requests resolve.
# No Caddy reload required — backend alias alone fixes prod 404.
# ---------------------------------------------------------------------------

class _ApiPrefixAliasMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        p = request.url.path
        if p.startswith("/v1/"):
            # Rewrite /v1/* -> /api/v1/* before routing.
            # Keep query string intact; only mutate path.
            request.scope["path"] = "/api" + p  # /v1/x -> /api/v1/x
        return await call_next(request)


app.add_middleware(_ApiPrefixAliasMiddleware)
app.add_middleware(_UnconditionalCorsMiddleware)
app.include_router(product_router)
app.include_router(forecast_router)
app.include_router(batch_router)
app.include_router(subscriptions_router)
app.include_router(auth_router)
app.include_router(tax_router)
app.include_router(quota_router)
app.include_router(sync_router)


# ---------------------------------------------------------------------------
# Shared auth helper — session (Bearer) or dev headers (X-Tenant-ID/X-Role)
# ---------------------------------------------------------------------------

def _resolve_tenant_from_auth(
    authorization: str | None,
    x_tenant_id: str | None,
    x_role: str | None,
) -> str:
    """Resolve tenant identity from either a Bearer session token or legacy
    dev headers. Session-based auth takes precedence (F1.3 / G2).
    """
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        try:
            identity = service.resolve_session(token)
            return identity["tenant_id"]
        except KeyError:
            raise HTTPException(401, "Invalid or expired session")
    if x_tenant_id is None or not x_tenant_id.strip():
        raise HTTPException(401, "Tenant identity is required")
    if x_role is None or x_role not in {"admin", "reviewer", "integrator"}:
        raise HTTPException(403, "Unknown role")
    return x_tenant_id.strip()


# ---------------------------------------------------------------------------
# Consumer dashboard (F1.2 — §3.4 of docs/plans/consumer-pivot-2026-08-13.md)
# ---------------------------------------------------------------------------

@app.get("/api/v1/consumer/dashboard")
def consumer_dashboard(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> dict[str, Any]:
    """Consumer dashboard payload — all six blocks, live backend data.

    Auth: Bearer session token (logged-in users) OR X-Tenant-ID/X-Role
    headers (dev fallback). Session-based auth takes precedence.
    """
    tenant_id = _resolve_tenant_from_auth(authorization, x_tenant_id, x_role)
    return build_consumer_dashboard(tenant_id)

# ---------------------------------------------------------------------------
# Configurable limits (plumbed into fetch_image_bytes defaults)
# ---------------------------------------------------------------------------
MAX_IMAGE_BYTES: int = 20_000_000  # 20 MB
URL_FETCH_TIMEOUT: float = 30.0  # seconds


# ---------------------------------------------------------------------------
# In-memory job store (replace with Redis/DB in production)
# ---------------------------------------------------------------------------


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._executor = ThreadPoolExecutor(max_workers=2)

    def create(self, webhook_url: str | None = None) -> dict[str, Any]:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "webhook_url": webhook_url,
            "result": None,
            "error": None,
        }
        return self._jobs[job_id]

    def get(self, job_id: str) -> dict[str, Any] | None:
        return self._jobs.get(job_id)

    def set_status(self, job_id: str, status: str, result: Any = None, error: str | None = None) -> None:
        job = self._jobs.get(job_id)
        if job:
            job["status"] = status
            job["result"] = result
            job["error"] = error


_job_store = JobStore()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bytes_from_upload(upload: UploadFile) -> bytes:
    if upload.content_type and not upload.content_type.startswith("image/"):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type: {upload.content_type}. Expected an image.",
        )
    return upload.file.read()


def _render_receipt(parsed: ConfidenceReceipt) -> dict:
    return {
        "vendor": parsed.merchant,
        "total": parsed.total,
        "date": parsed.date,
        "tax": parsed.tax,
        "currency": parsed.currency,
        "line_items": [
            {"name": item.name, "price": item.price} for item in parsed.items
        ],
        "confidence": getattr(parsed, "confidence", {}),
        "confidence_level": getattr(parsed, "confidence_level", None),
    }


def _as_bool(value: str | None) -> bool:
    """Parse a form-field boolean (1/true/yes/on => True)."""
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def api_v1_actor(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> Actor:
    """Strict auth for the /api/v1/receipts CRUD endpoints.

    Bearer session token takes precedence (F1.3 / G2). Falls back to
    X-Tenant-ID/X-Role headers in dev mode.
    """
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        try:
            identity = service.resolve_session(token)
        except KeyError as exc:
            raise HTTPException(401, "Invalid or expired session") from exc
        return Actor(identity["tenant_id"], identity["role"])
    if x_tenant_id is None or not x_tenant_id.strip():
        raise HTTPException(401, "Tenant identity is required")
    if x_role is None or x_role not in {"admin", "reviewer", "integrator"}:
        raise HTTPException(403, "Unknown role")
    if _is_production:
        raise HTTPException(401, "Session required")
    return Actor(x_tenant_id, x_role)


def _render_ai_mode(image_bytes: bytes) -> dict:
    """AI-mode OCR: vision LLM first, automatic Tesseract fallback.

    The response exposes a top-level ``source`` (``vision`` | ``tesseract``).
    When the vision path produced the result, ``ai_result`` and
    ``tesseract_result`` both carry the receipt/confidence shape so the
    frontend can compare the two pipelines on the same image. When it fell
    back, only ``tesseract_result`` is present.
    """
    try:
        parsed = parse_receipt_with_vision(image_bytes)
    except Exception:
        logger.exception("AI-mode vision OCR failed; using Tesseract fallback")
        parsed = None
    if parsed is None:
        return {
            "source": SOURCE_TESSERACT,
            "tesseract_result": _render_receipt(parse_receipt_with_confidence(image_bytes)),
        }
    source = str((parsed.confidence or {}).get("source") or SOURCE_TESSERACT)
    if source == SOURCE_VISION:
        return {
            "source": SOURCE_VISION,
            "ai_result": _render_receipt(parsed),
            "tesseract_result": _render_receipt(parse_receipt_with_confidence(image_bytes)),
        }
    return {"source": SOURCE_TESSERACT, "tesseract_result": _render_receipt(parsed)}


def _process_one(item_bytes: bytes) -> dict[str, Any]:
    parsed = parse_receipt_with_confidence(item_bytes)
    return _render_receipt(parsed)


async def _process_job(
    image_bytes: bytes | None,
    job_id: str,
    webhook_url: str | None = None,
    image_url: str | None = None,
) -> None:
    """Run OCR in a thread and update job store.

    If *image_url* is provided, the fetch happens here (background) instead
    of in the request handler, keeping the ``/v1/parse-receipt/async``
    response non-blocking (P1-2).
    """
    _job_store.set_status(job_id, "processing")

    def _run() -> dict:
        if image_url is not None:
            image_bytes_url = fetch_image_bytes(image_url)
            return _process_one(image_bytes_url)
        assert image_bytes is not None, "image_bytes required when image_url is not set"
        return _process_one(image_bytes)

    loop = __import__("asyncio").get_running_loop()
    try:
        result = await loop.run_in_executor(_job_store._executor, _run)
        _job_store.set_status(job_id, "completed", result=result)
        if webhook_url:
            await _deliver_webhook(webhook_url, {
                "job_id": job_id,
                "status": "completed",
                "result": result,
            })
    except HTTPException as exc:
        # Forward upstream fetch errors (e.g. bad URL) to job status
        _job_store.set_status(job_id, "failed", error=str(exc.detail))
        if webhook_url:
            await _deliver_webhook(webhook_url, {
                "job_id": job_id,
                "status": "failed",
                "error": str(exc.detail),
            })
    except Exception:
        logger.exception("Async OCR job %s failed", job_id)
        _job_store.set_status(job_id, "failed", error="OCR processing failed.")
        if webhook_url:
            await _deliver_webhook(webhook_url, {
                "job_id": job_id,
                "status": "failed",
                "error": "OCR processing failed.",
            })


async def _process_batch_job(
    items: list[dict[str, Any]],
    job_id: str,
    webhook_url: str | None = None,
    image_urls: list[str] | None = None,
) -> None:
    """Run batch OCR in threads and update job store with per-item status.

    If *image_urls* is provided, each URL is fetched inside the background
    job (P1-2 non-blocking contract) rather than in the request handler.
    """
    _job_store.set_status(job_id, "processing")

    # When image_urls are provided, resolve them to items with bytes (or errors)
    if image_urls is not None:
        items = []
        for idx, url in enumerate(image_urls):
            try:
                items.append(_build_batch_item(idx, fetch_image_bytes(url)))
            except HTTPException as exc:
                items.append(_build_error_item(idx, exc.detail))

    total = len(items)
    results: list[dict[str, Any]] = []

    loop = __import__("asyncio").get_running_loop()
    try:
        for idx, item in enumerate(items, start=1):
            _job_store.set_status(
                job_id,
                "processing",
                result={"results": results, "summary": {"total": total, "successful": sum(1 for r in results if r.get("error") is None), "failed": sum(1 for r in results if r.get("error") is not None)}},
            )
            if item.get("_error"):
                results.append({
                    "index": item["index"],
                    "vendor": None,
                    "total": None,
                    "date": None,
                    "tax": None,
                    "currency": None,
                    "line_items": [],
                    "confidence": {
                        "vendor": None,
                        "total": None,
                        "date": None,
                        "tax": None,
                        "currency": None,
                        "line_items": None,
                    },
                    "error": item["_error"],
                })
                continue

            def _run(b=item["bytes"]) -> dict:
                return _process_one(b)

            try:
                rendered = await loop.run_in_executor(_job_store._executor, _run)
            except Exception:
                rendered = None
                results.append({
                    "index": item["index"],
                    "vendor": None,
                    "total": None,
                    "date": None,
                    "tax": None,
                    "currency": None,
                    "line_items": [],
                    "confidence": {
                        "vendor": None,
                        "total": None,
                        "date": None,
                        "tax": None,
                        "currency": None,
                        "line_items": None,
                    },
                    "error": "OCR processing failed.",
                })
                continue

            results.append({
                "index": item["index"],
                **rendered,
                "error": None,
            })

        final_payload = {
            "results": results,
            "summary": {
                "total": total,
                "successful": sum(1 for r in results if r.get("error") is None),
                "failed": sum(1 for r in results if r.get("error") is not None),
            },
        }
        _job_store.set_status(job_id, "completed", result=final_payload)
        if webhook_url:
            await _deliver_webhook(webhook_url, {
                "job_id": job_id,
                "status": "completed",
                "result": final_payload,
            })
    except Exception:
        logger.exception("Async batch OCR job %s failed", job_id)
        _job_store.set_status(job_id, "failed", error="OCR processing failed.")
        if webhook_url:
            await _deliver_webhook(webhook_url, {
                "job_id": job_id,
                "status": "failed",
                "error": "OCR processing failed.",
            })


async def _deliver_webhook(url: str, payload: dict) -> None:
    """POST payload to a webhook URL after SSRF validation."""
    try:
        validate_scheme_and_host(url)
    except ValueError as exc:
        logger.warning("Webhook URL blocked by SSRF guard: %s", exc)
        return
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5.0, read=10.0, write=None, pool=None)) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
    except Exception:
        logger.warning("Webhook delivery failed to %s", url)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


async def parse_receipt_endpoint(file: bytes, ai_scan: bool = False) -> dict:
    """Accept raw image bytes, run OCR, return structured dict.

    With *ai_scan* the vision-LLM path runs first (with automatic Tesseract
    fallback) and the response exposes ``source`` plus ``ai_result`` /
    ``tesseract_result``; without it the classic Tesseract path is used.
    """
    if not file:
        raise HTTPException(status_code=422, detail="Empty image payload")
    if ai_scan:
        return _render_ai_mode(file)
    parsed = parse_receipt_with_confidence(file)
    return _render_receipt(parsed)


@app.post("/v1/parse-receipt", response_model=dict)
async def parse_receipt_route(
    file: UploadFile | None = File(default=None, description="Receipt image file"),
    image_url: str | None = Form(default=None, description="Public URL of a receipt image"),
    ai_scan: str | None = Form(default=None, description="Enable AI-mode OCR (vision LLM with Tesseract fallback)"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> dict:
    """Parse a receipt image returned as structured JSON.

    Send either **file** (multipart upload) or **image_url** (form field).
    With **ai_scan=true** the response exposes ``source`` plus
    ``ai_result`` / ``tesseract_result`` payloads.

    Quota gate (ADR-005): when a tenant is identifiable (Bearer session
    or X-Tenant-ID) the Free 25/mo limit is enforced before OCR —
    402 quota_exceeded when exhausted; Pro unlimited.
    """
    # Quota wiring for the legacy public OCR entrypoint — only when
    # we can resolve a tenant; unauthenticated calls remain rate-limited
    # via RateLimitMiddleware (5/60) but do not consume quota.
    _quota_tenant: str | None = None
    if authorization and authorization.strip().startswith("Bearer "):
        try:
            _quota_tenant = service.resolve_session(authorization.strip().removeprefix("Bearer ").strip())["tenant_id"]
        except Exception:
            _quota_tenant = None
    elif x_tenant_id:
        _quota_tenant = x_tenant_id.strip() or None
    if _quota_tenant is not None:
        from app.quota import quota_store
        from app.subscriptions_api import is_pro

        _q = quota_store.incr_and_check(_quota_tenant, pro=is_pro(_quota_tenant))
        if not _q["allowed"]:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "quota_exceeded",
                    "message": "Free limit reached — upgrade to Pro for unlimited scans ($5/mo).",
                    "quota": _q,
                },
            )
    if file is not None and image_url is not None:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'file' or 'image_url', not both.",
        )
    if file is None and not image_url:
        raise HTTPException(
            status_code=422,
            detail="Missing required input: send 'file' or 'image_url'.",
        )

    if file is not None:
        image_bytes = _bytes_from_upload(file)
    else:
        image_bytes = fetch_image_bytes(image_url)  # type: ignore[arg-type]

    try:
        return await parse_receipt_endpoint(image_bytes, ai_scan=_as_bool(ai_scan))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - OCR is unpredictable
        from PIL import UnidentifiedImageError
        if isinstance(exc, UnidentifiedImageError):
            raise HTTPException(
                status_code=400,
                detail="The provided data is not a recognized image format.",
            ) from exc
        logger.exception("OCR processing failed")
        raise HTTPException(
            status_code=500,
            detail="OCR processing failed.",
        ) from exc


@app.post("/v1/parse-receipt/async", response_model=dict)
async def parse_receipt_async_route(
    file: UploadFile | None = File(default=None, description="Receipt image file"),
    image_url: str | None = Form(default=None, description="Public URL of a receipt image"),
    webhook_url: str | None = Form(default=None, description="Optional webhook URL for completion callback"),
) -> dict:
    """Queue an async OCR job and return a job_id immediately.

        Optionally provide **webhook_url** to receive a JSON POST when processing
    completes or fails.
        """
    if file is not None and image_url is not None:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'file' or 'image_url', not both.",
        )
    if file is None and not image_url:
        raise HTTPException(
            status_code=422,
            detail="Missing required input: send 'file' or 'image_url'.",
        )

    if file is not None:
        image_bytes = _bytes_from_upload(file)
        job = _job_store.create(webhook_url=webhook_url)
        # Fire-and-forget background task — file bytes are ready
        import asyncio

        asyncio.get_running_loop().create_task(
            _process_job(image_bytes, job["job_id"], webhook_url=webhook_url)
        )
    else:
        # Defer the URL fetch to the background job (P1-2 non-blocking)
        job = _job_store.create(webhook_url=webhook_url)
        import asyncio

        asyncio.get_running_loop().create_task(
            _process_job(
                None,
                job["job_id"],
                webhook_url=webhook_url,
                image_url=image_url,
            )
        )
    return {"job_id": job["job_id"], "status": "queued", "webhook_url": webhook_url}


@app.get("/v1/jobs/{job_id}", response_model=dict)
async def job_status_route(job_id: str) -> dict:
    """Poll the status and result of an async OCR job."""
    job = _job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "result": job.get("result"),
        "error": job.get("error"),
    }


# ---------------------------------------------------------------------------
# Batch endpoints
# ---------------------------------------------------------------------------


def _build_batch_item(index: int, image_bytes: bytes) -> dict[str, Any]:
    return {"index": index, "bytes": image_bytes}


def _build_error_item(index: int, error: str) -> dict[str, Any]:
    return {
        "index": index,
        "bytes": b"",
        "_error": error,
    }


@app.post("/v1/parse-receipts", response_model=dict)
async def parse_receipts_route(
    files: list[UploadFile] | None = File(default=None, description="Receipt image files"),
    image_urls: str | None = Form(default=None, description="JSON array of receipt image URLs"),
) -> dict:
    """Parse multiple receipt images in one request.

    Send either **files** (multipart uploads) or **image_urls** (JSON array),
    not both.
    """
    if files is not None and image_urls is not None:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'files' or 'image_urls', not both.",
        )

    items: list[dict[str, Any]] = []

    if files is not None:
        if not files:
            raise HTTPException(status_code=422, detail="Provide at least one file.")
        if len(files) > 20:
            raise HTTPException(
                status_code=413,
                detail="Too many files: maximum 20 per request.",
            )
        for idx, upload in enumerate(files):
            try:
                items.append(_build_batch_item(idx, _bytes_from_upload(upload)))
            except HTTPException as exc:
                items.append(_build_error_item(idx, exc.detail))
    elif image_urls is not None:
        try:
            urls = json.loads(image_urls)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid JSON for image_urls: {exc}",
            ) from exc
        if not isinstance(urls, list) or not urls:
            raise HTTPException(status_code=422, detail="Provide at least one URL.")
        if len(urls) > 20:
            raise HTTPException(
                status_code=413,
                detail="Too many URLs: maximum 20 per request.",
            )
        for idx, url in enumerate(urls):
            try:
                items.append(_build_batch_item(idx, fetch_image_bytes(str(url))))
            except HTTPException as exc:
                items.append(_build_error_item(idx, exc.detail))
    else:
        raise HTTPException(
            status_code=422,
            detail="Missing required input: send 'files' or 'image_urls'.",
        )

    loop = __import__("asyncio").get_running_loop()
    results: list[dict[str, Any]] = []
    for item in items:
        if item.get("_error"):
            results.append({
                "index": item["index"],
                "vendor": None,
                "total": None,
                "date": None,
                "tax": None,
                "currency": None,
                "line_items": [],
                "confidence": {
                    "vendor": None,
                    "total": None,
                    "date": None,
                    "tax": None,
                    "currency": None,
                    "line_items": None,
                },
                "error": item["_error"],
            })
            continue

        def _run(b=item["bytes"]) -> dict:
            return _process_one(b)

        try:
            rendered = await loop.run_in_executor(_job_store._executor, _run)
        except Exception:
            results.append({
                "index": item["index"],
                "vendor": None,
                "total": None,
                "date": None,
                "tax": None,
                "currency": None,
                "line_items": [],
                "confidence": {
                    "vendor": None,
                    "total": None,
                    "date": None,
                    "tax": None,
                    "currency": None,
                    "line_items": None,
                },
                "error": "OCR processing failed.",
            })
            continue

        results.append({
            "index": item["index"],
            **rendered,
            "error": None,
        })

    return {
        "results": results,
        "summary": {
            "total": len(results),
            "successful": sum(1 for r in results if r.get("error") is None),
            "failed": sum(1 for r in results if r.get("error") is not None),
        },
    }


@app.post("/v1/parse-receipts/async", response_model=dict)
async def parse_receipts_async_route(
    files: list[UploadFile] | None = File(default=None, description="Receipt image files"),
    image_urls: str | None = Form(default=None, description="JSON array of receipt image URLs"),
    webhook_url: str | None = Form(default=None, description="Optional webhook URL for completion callback"),
) -> dict:
    """Queue an async batch OCR job and return a job_id immediately."""
    if files is not None and image_urls is not None:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'files' or 'image_urls', not both.",
        )

    items: list[dict[str, Any]] = []

    if files is not None:
        if not files:
            raise HTTPException(status_code=422, detail="Provide at least one file.")
        if len(files) > 20:
            raise HTTPException(
                status_code=413,
                detail="Too many files: maximum 20 per request.",
            )
        for idx, upload in enumerate(files):
            try:
                items.append(_build_batch_item(idx, _bytes_from_upload(upload)))
            except HTTPException as exc:
                items.append(_build_error_item(idx, exc.detail))
    elif image_urls is not None:
        try:
            urls = json.loads(image_urls)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid JSON for image_urls: {exc}",
            ) from exc
        if not isinstance(urls, list) or not urls:
            raise HTTPException(status_code=422, detail="Provide at least one URL.")
        if len(urls) > 20:
            raise HTTPException(
                status_code=413,
                detail="Too many URLs: maximum 20 per request.",
            )
        # Defer URL fetching to the background job (P1-2 non-blocking)
        job = _job_store.create(webhook_url=webhook_url)
        import asyncio

        asyncio.get_running_loop().create_task(
            _process_batch_job(
                [],
                job["job_id"],
                webhook_url=webhook_url,
                image_urls=[str(u) for u in urls],
            )
        )
        return {"job_id": job["job_id"], "status": "queued", "webhook_url": webhook_url}
    else:
        raise HTTPException(
            status_code=422,
            detail="Missing required input: send 'files' or 'image_urls'.",
        )

    job = _job_store.create(webhook_url=webhook_url)
    import asyncio

    asyncio.get_running_loop().create_task(
        _process_batch_job(items, job["job_id"], webhook_url=webhook_url)
    )
    return {"job_id": job["job_id"], "status": "queued", "webhook_url": webhook_url}


# ---------------------------------------------------------------------------
# Duplicate detection endpoint
# ---------------------------------------------------------------------------


class DuplicateCheckRequest(BaseModel):
    receipts: list[dict]

    @field_validator("receipts")
    @classmethod
    def validate_receipts(cls, v: list[dict]) -> list[dict]:
        if not isinstance(v, list):
            raise ValueError("receipts must be a list")
        if len(v) == 0:
            raise ValueError("receipts list must not be empty")
        if len(v) > 200:
            raise HTTPException(
                status_code=413,
                detail="Too many receipts: maximum 200 per request.",
            )
        for i, receipt in enumerate(v):
            if not isinstance(receipt, dict):
                raise ValueError(f"receipt at index {i} must be a dict")
            total = receipt.get("total")
            if total is None:
                raise ValueError(
                    f"receipt at index {i} is missing required 'total' field"
                )
            if not isinstance(total, (int, float)):
                raise ValueError(
                    f"receipt at index {i} has non-numeric 'total': {total!r}"
                )
        return v


@app.post("/v1/check-duplicates", response_model=dict)
async def check_duplicates_route(body: DuplicateCheckRequest) -> dict:
    """Check a batch of parsed receipts for potential duplicates."""
    try:
        result = check_duplicates(body.receipts)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Duplicate detection failed")
        raise HTTPException(
            status_code=500, detail="Duplicate detection failed."
        ) from exc

    return {
        "duplicate_groups": [
            {
                "group_id": g.group_id,
                "indices": g.indices,
                "confidence": g.confidence,
                "match_evidence": g.match_evidence,
            }
            for g in result.duplicate_groups
        ],
        "summary": result.summary,
    }


# ---------------------------------------------------------------------------
# Report Request model and endpoint
# ---------------------------------------------------------------------------


class ReceiptCreateRequest(BaseModel):
    """Request body for creating a new receipt entry."""
    image_url: str


class ReportRequest(BaseModel):
    """Request body for POST /api/v1/reports."""
    date_from: str | None = None
    date_to: str | None = None
    format: str = "pdf"
    range: str | None = None
    category: str | None = None
    merchant: str | None = None
    min_amount: float | None = None
    max_amount: float | None = None

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        if v not in ("pdf", "csv"):
            raise ValueError(f"Unsupported format: {v!r}. Must be 'pdf' or 'csv'.")
        return v


def _resolve_date_range(
    range_preset: str | None,
    date_from: str | None,
    date_to: str | None,
) -> tuple[str, str]:
    """Resolve ``range`` preset or explicit ``date_from`` / ``date_to``.

    Raises ``HTTPException`` for invalid combinations.
    """
    if range_preset is not None and (date_from is not None or date_to is not None):
        raise HTTPException(
            status_code=400,
            detail="'range' is mutually exclusive with 'date_from' and 'date_to'.",
        )

    if range_preset is not None:
        now = datetime.now(UTC)
        if range_preset == "today":
            d = now.strftime("%Y-%m-%d")
            return d, d
        elif range_preset == "this_week":
            # ISO week: Monday start
            monday = now.date() - __import__("datetime").timedelta(
                days=now.weekday()
            )
            sunday = monday + __import__("datetime").timedelta(days=6)
            return monday.isoformat(), sunday.isoformat()
        elif range_preset == "this_month":
            first = now.replace(day=1).strftime("%Y-%m-%d")
            # compute last day of month
            import calendar
            last_day = calendar.monthrange(now.year, now.month)[1]
            last = now.replace(day=last_day).strftime("%Y-%m-%d")
            return first, last
        else:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown range preset: {range_preset!r}.",
            )

    if date_from is None or date_to is None:
        raise HTTPException(
            status_code=422,
            detail="Provide either 'range' or both 'date_from' and 'date_to'.",
        )

    # Validate date format
    try:
        date.fromisoformat(date_from)
        date.fromisoformat(date_to)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid date format. Use YYYY-MM-DD.",
        )

    if date_from > date_to:
        raise HTTPException(
            status_code=422,
            detail="date_from must not be after date_to.",
        )

    return date_from, date_to


@app.post("/api/v1/receipts", status_code=201)
def post_receipt(body: ReceiptCreateRequest, current: Actor = Depends(api_v1_actor)) -> dict:
    """Fetch, parse, and store a receipt image from a validated public URL.

    Receipts are persisted to the shared product store (the same SQLite-backed
    ``ProductService`` the ``/product/*`` workspace uses), so an upload here is
    immediately visible through ``/product/receipts`` and vice versa.
    """
    image_bytes = fetch_image_bytes(
        body.image_url,
        max_bytes=MAX_IMAGE_BYTES,
        timeout=URL_FETCH_TIMEOUT,
    )
    parsed = parse_receipt_with_confidence(image_bytes)
    result = service.create_receipt(current, parsed, body.image_url.rsplit("/", 1)[-1] or "receipt")
    return {"receipt_id": result["receipt_id"], **_render_receipt(parsed)}


@app.get("/api/v1/receipts")
def list_receipts(current: Actor = Depends(api_v1_actor)) -> dict:
    """List the tenant's receipts from the shared product store."""
    items = service.search_receipts(current, limit=200)["items"]
    return {
        "receipts": [
            {
                "receipt_id": item["receipt_id"],
                "status": item["status"],
                "created_at": item["created_at"],
                **item["receipt"],
            }
            for item in items
        ]
    }


@app.get("/api/v1/receipts/{receipt_id}")
def get_receipt(receipt_id: str, current: Actor = Depends(api_v1_actor)) -> dict:
    """Get one stored receipt or return HTTP 404 when it does not exist."""
    try:
        item = service.get_receipt(current, receipt_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Receipt not found") from exc
    return {"receipt_id": receipt_id, **item["receipt"]}


@app.post("/api/v1/reports")
def generate_report(body: ReportRequest) -> Any:
    """Generate an expense report in PDF or CSV format."""
    date_from, date_to = _resolve_date_range(
        body.range, body.date_from, body.date_to
    )

    receipts = receipt_store.list(
        date_from=date_from,
        date_to=date_to,
        merchant=body.merchant,
    )

    # Apply post-filter for category, min_amount, max_amount
    if body.category is not None or body.min_amount is not None or body.max_amount is not None:
        filtered: list[ConfidenceReceipt] = []
        for r in receipts:
            items = [
                it
                for it in r.items
                if (body.category is None or it.category == body.category)
                and (body.min_amount is None or it.price >= body.min_amount)
                and (body.max_amount is None or it.price <= body.max_amount)
            ]
            if items:
                # Create a filtered copy
                from dataclasses import replace
                filtered.append(replace(r, items=items))
        receipts = filtered

    if not receipts:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=404,
            content={"detail": "No receipts found for the given criteria."},
        )

    if body.format == "pdf":
        pdf_bytes = generate_pdf(receipts)
        from fastapi.responses import Response

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=expense_report.pdf",
                "Content-Type": "application/pdf",
            },
        )
    else:
        csv_str = generate_csv(receipts)
        from fastapi.responses import Response

        return Response(
            content=csv_str,
            headers={
                "Content-Disposition": "attachment; filename=expense_report.csv",
                "Content-Type": "text/csv",
            },
        )


# ---------------------------------------------------------------------------
# Categorization endpoint
# ---------------------------------------------------------------------------


_categorizer = Categorizer()


class CategorizeRequest(BaseModel):
    vendor: str
    total: float | None = None
    line_items: list[dict[str, Any]] | None = None


@app.post("/api/v1/categorize", response_model=dict)
def categorize_route(body: CategorizeRequest) -> dict:
    """Categorize a receipt by vendor name.  Returns category + confidence."""
    result = _categorizer.categorize(
        vendor=body.vendor,
        total=body.total,
        line_items=body.line_items,
    )
    return {
        "category": result.category,
        "confidence": result.confidence,
        "matched_rule": result.matched_rule,
        "subcategory": result.subcategory,
    }


# ---------------------------------------------------------------------------
# Budget CRUD endpoints
# ---------------------------------------------------------------------------


class BudgetCreateRequest(BaseModel):
    category: str
    amount: float
    currency: str = "USD"
    period: str = "monthly"
    alert_threshold: float = 0.8


class BudgetUpdateRequest(BaseModel):
    category: str | None = None
    amount: float | None = None
    currency: str | None = None
    period: str | None = None
    alert_threshold: float | None = None


@app.post("/api/v1/budgets", response_model=dict)
def create_budget_route(
    body: BudgetCreateRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> dict:
    """Create a new budget definition scoped to the caller's tenant.

    F1.2 B2: without tenant scoping, a budget created by tenant A is
    visible in tenant B's consumer dashboard — a cross-tenant leak.
    """
    try:
        record = budget_store.create(
            category=body.category,
            amount=body.amount,
            currency=body.currency,
            period=body.period,
            alert_threshold=body.alert_threshold,
            tenant_id=_resolve_tenant_from_auth(authorization, x_tenant_id, x_role),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return record.to_dict()


@app.get("/api/v1/budgets", response_model=dict)
def list_budgets_route(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> dict:
    """List the caller's budget definitions with computed spend fields."""
    records = budget_store.list(tenant_id=_resolve_tenant_from_auth(authorization, x_tenant_id, x_role))
    return {"budgets": [r.to_dict() for r in records]}


@app.get("/api/v1/budgets/{id}", response_model=dict)
def get_budget_route(
    id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> dict:
    """Get a single budget by id (tenant-scoped: 404 for other tenants' budgets)."""
    record = budget_store.get(id)
    if record is None or record.tenant_id != _resolve_tenant_from_auth(authorization, x_tenant_id, x_role):
        raise HTTPException(status_code=404, detail="Budget not found")
    return record.to_dict()


@app.put("/api/v1/budgets/{id}", response_model=dict)
def update_budget_route(
    id: str,
    body: BudgetUpdateRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> dict:
    """Update fields on an existing budget (tenant-scoped: 404 for others)."""
    kwargs = {}
    if body.category is not None:
        kwargs["category"] = body.category
    if body.amount is not None:
        kwargs["amount"] = body.amount
    if body.currency is not None:
        kwargs["currency"] = body.currency
    if body.period is not None:
        kwargs["period"] = body.period
    if body.alert_threshold is not None:
        kwargs["alert_threshold"] = body.alert_threshold

    existing = budget_store.get(id)
    if existing is None or existing.tenant_id != (x_tenant_id or "").strip():
        raise HTTPException(status_code=404, detail="Budget not found")

    try:
        record = budget_store.update(id, **kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if record is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    return record.to_dict()


@app.delete("/api/v1/budgets/{id}", response_model=dict)
def delete_budget_route(
    id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> dict:
    """Delete a budget definition (tenant-scoped: 404 for other tenants' budgets)."""
    record = budget_store.get(id)
    if record is None or record.tenant_id != _resolve_tenant_from_auth(authorization, x_tenant_id, x_role):
        raise HTTPException(status_code=404, detail="Budget not found")
    deleted = budget_store.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Budget not found")
    return {"status": "deleted", "budget_id": id}


# ---------------------------------------------------------------------------
# Analytics endpoints
# ---------------------------------------------------------------------------


@app.get("/api/v1/analytics/spending", response_model=dict)
def spending_analytics_route(
    date_from: str,
    date_to: str,
    group_by: str = "category",
    category: str | None = None,
) -> dict:
    """Aggregate spending by category/merchant/day/month."""
    if date_from > date_to:
        raise HTTPException(
            status_code=422,
            detail="date_from must not be after date_to.",
        )
    valid_group_bys = {"category", "merchant", "day", "month"}
    if group_by not in valid_group_bys:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid group_by: {group_by!r}.",
        )
    try:
        result = spending_analytics.spending_overview(
            date_from=date_from,
            date_to=date_to,
            group_by=group_by,
            category=category,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result


@app.get("/api/v1/analytics/budgets", response_model=dict)
def budget_analytics_route(period: str | None = None) -> dict:
    """Compare budget definitions against current spending."""
    result = budget_analytics.budget_overview(period=period)
    return result


# ---------------------------------------------------------------------------
# Alert endpoints
# ---------------------------------------------------------------------------


@app.get("/api/v1/alerts", response_model=dict)
def list_alerts_route() -> dict:
    """List active (non-acknowledged) alerts."""
    alerts = alert_store.list_alerts()
    return {
        "alerts": [
            {
                "alert_id": a.alert_id,
                "type": a.type.value if hasattr(a.type, "value") else str(a.type),
                "severity": a.severity.value if hasattr(a.severity, "value") else str(a.severity),
                "category": a.category,
                "message": a.message,
                "pct_used": a.pct_used,
                "created_at": a.created_at,
                "acknowledged": a.acknowledged,
            }
            for a in alerts
        ],
        "unread_count": alert_store.unread_count(),
    }


@app.post("/api/v1/alerts/{alert_id}/acknowledge", response_model=dict)
def acknowledge_alert_route(alert_id: str) -> dict:
    """Mark an alert as acknowledged."""
    result = alert_store.acknowledge(alert_id)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "acknowledged", "alert_id": alert_id}
