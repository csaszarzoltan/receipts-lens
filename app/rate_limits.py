"""Per-tenant + per-IP rate limiting for OCR-heavy and ingestion endpoints (SEC-005).

Attack surface (security test report 2026-08-12, SEC-005):

- ``POST /product/receipts/upload``  — expensive OCR (2x Tesseract in AI mode)
- ``POST /product/inbound-emails``  — any tenant can spam
- ``POST /v1/parse-receipt*``        — unauthenticated OCR entrypoints
- ``POST /api/v1/receipts``          — the same OCR cost via the /api/v1 namespace
- login/register — do not exist yet; add a ``POST /auth/login`` row to
  ``DEFAULT_LIMITS`` (or the ``RECEIPTLENS_RATE_LIMITS`` env) when they land.

Design: an in-process fixed-window counter keyed by ``(route, tenant, client IP)``,
enforced by a Starlette middleware. On exceeding the limit the middleware returns
HTTP 429 with ``Retry-After`` (seconds until the window resets) plus
``X-RateLimit-Limit`` / ``X-RateLimit-Remaining``. The store is in-memory per
process — consistent with the repo's existing "in-memory job store" pattern; a
multi-worker deployment should move this to Redis (documented in docs/api.md).

Defaults are deliberately generous for a small deployment and tunable via the
``RECEIPTLENS_RATE_LIMITS`` environment variable::

    RECEIPTLENS_RATE_LIMITS="POST /product/receipts/upload=10/60;POST /v1/parse-receipt=5/60"

Format: ``METHOD path=count/window_seconds`` separated by ``;``. Any route not
listed is not limited.
"""
from __future__ import annotations

import os
import time
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# (limit, window_seconds) per route key "METHOD /path". The window for the
# unauthenticated OCR endpoints is per-IP only (no tenant header present).
DEFAULT_LIMITS: dict[str, tuple[int, int]] = {
    "POST /product/receipts/upload": (60, 60),
    "POST /product/inbound-emails": (60, 60),
    "POST /v1/parse-receipt": (60, 60),
    "POST /v1/parse-receipt/async": (60, 60),
    "POST /v1/parse-receipts": (60, 60),
    "POST /v1/parse-receipts/async": (60, 60),
    "POST /api/v1/receipts": (60, 60),
    "POST /api/v1/receipts/batch": (60, 60),
}

# Max tracked buckets; beyond this the oldest windows are pruned so a hostile
# tenant/IP fan-out cannot grow memory without bound.
_MAX_BUCKETS = 10_000


def _parse_env_limits() -> dict[str, tuple[int, int]]:
    raw = os.getenv("RECEIPTLENS_RATE_LIMITS", "").strip()
    if not raw:
        return dict(DEFAULT_LIMITS)
    out: dict[str, tuple[int, int]] = {}
    for item in raw.split(";"):
        item = item.strip()
        if not item:
            continue
        route, _, spec = item.partition("=")
        count, _, window = spec.strip().partition("/")
        out[route.strip()] = (int(count), int(window))
    return out


_limits: dict[str, tuple[int, int]] = _parse_env_limits()
_buckets: dict[tuple[str, str], tuple[int, int]] = {}  # (route_key, identity) -> (bucket_start, count)
_time = time.time  # injectable clock for tests


def set_limits(limits: dict[str, tuple[int, int]] | None) -> None:
    """Override the active limits table (tests) or restore env/defaults (None)."""
    global _limits
    _limits = dict(DEFAULT_LIMITS) if limits is None else {k: tuple(v) for k, v in limits.items()}


def reset() -> None:
    """Drop all counters (tests)."""
    _buckets.clear()


def _check(route_key: str, tenant: str, ip: str) -> tuple[bool, int]:
    """Return (allowed, retry_after_seconds) for one request attempt."""
    spec = _limits.get(route_key)
    if spec is None:
        return True, 0
    limit, window = spec
    identity = f"{tenant or '-'}|{ip}"
    key = (route_key, identity)
    now = _time()
    bucket_start = int(now // window) * window
    current = _buckets.get(key)
    if current is None or current[0] != bucket_start:
        _buckets[key] = (bucket_start, 1)
        _prune(now, window)
        return True, 0
    _, count = current
    if count >= limit:
        retry_after = max(1, int(bucket_start + window - now) + 1)
        return False, retry_after
    _buckets[key] = (bucket_start, count + 1)
    return True, 0


def _remaining(route_key: str, tenant: str, ip: str) -> int:
    spec = _limits.get(route_key)
    if spec is None:
        return -1
    limit, window = spec
    key = (route_key, f"{tenant or '-'}|{ip}")
    now = _time()
    bucket_start = int(now // window) * window
    current = _buckets.get(key)
    if current is None or current[0] != bucket_start:
        return limit
    return max(0, limit - current[1])


def _prune(now: float, window: int) -> None:
    if len(_buckets) <= _MAX_BUCKETS:
        return
    horizon = now - max(w for _, w in _limits.values())
    for key, (start, _count) in list(_buckets.items()):
        if start + horizon < now:
            del _buckets[key]
    if len(_buckets) > _MAX_BUCKETS:
        _buckets.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Return 429 with Retry-After when a route's per-tenant+per-IP quota is spent.

    OPTIONS preflight requests and unlisted paths pass through untouched. The
    limiter returns a Response directly (never raises HTTPException) so the
    response still flows back through the CORS middlewares, which add the
    Access-Control-* headers.
    """

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        if request.method == "OPTIONS":
            return await call_next(request)
        route_key = f"{request.method} {request.url.path}"
        if route_key not in _limits:
            return await call_next(request)
        tenant = (request.headers.get("X-Tenant-ID") or "").strip()
        ip = request.client.host if request.client else "unknown"
        allowed, retry_after = _check(route_key, tenant, ip)
        if not allowed:
            remaining = _remaining(route_key, tenant, ip)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(_limits[route_key][0]),
                    "X-RateLimit-Remaining": str(remaining),
                },
            )
        response = await call_next(request)
        remaining = _remaining(route_key, tenant, ip)
        response.headers.setdefault("X-RateLimit-Limit", str(_limits[route_key][0]))
        response.headers.setdefault("X-RateLimit-Remaining", str(remaining))
        return response
