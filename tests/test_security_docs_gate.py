"""SEC-006: API docs are gated behind RECEIPTLENS_ENV.

Security test report 2026-08-12, SEC-006:

    /docs (Swagger UI), /redoc and /openapi.json were publicly served on
    127.0.0.1:8100. In production this exposes the full API surface to
    attackers.

Contract (matching the Mealmind precedent that hid /api/docs + /api/redoc
in prod):

  * When ``RECEIPTLENS_ENV=production`` is set at app-import time, the
    FastAPI app is created with ``docs_url=None``, ``redoc_url=None`` and
    ``openapi_url=None`` — the routes are absent and requests return 404.
  * For every other value (unset, ``development``, ``dev``, ...) the docs
    stay enabled exactly as before: /docs, /redoc and /openapi.json return
    200 and the homepage still links to them.
  * The behaviour is decided at import time (module-level), matching how
    the rest of ``app.api`` reads configuration via ``os.getenv``.

The module-level import makes subprocess-based reload tests the only
deterministic way to assert the prod gate (``importlib.reload`` re-runs the
module body, but the FastAPI app object and the ``app.api`` symbol
reference held by ``app.main`` / TestClient would be stale — a subprocess
imports fresh and exercises the real server entry point).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _probe(env_override: dict | None = None) -> dict:
    """Import ``app.api`` in a fresh subprocess under *env* and probe the docs routes.

    Returns ``{"docs": <status>, "redoc": <status>, "openapi": <status>,
    "homepage_docs_link": <bool>}``. The probe runs against the real ASGI app
    via ``fastapi.testclient`` inside the subprocess, so it exercises the
    exact code path uvicorn would serve in production.
    """
    script = (
        "import json, os; "
        "from fastapi.testclient import TestClient; "
        "from app.api import app; "
        "c = TestClient(app); "
        "print(json.dumps({"
        "'docs': c.get('/docs').status_code, "
        "'redoc': c.get('/redoc').status_code, "
        "'openapi': c.get('/openapi.json').status_code, "
        "'homepage_docs_link': 'href=\"/docs\"' in c.get('/').text"
        "}))"
    )
    env = dict(os.environ)
    env.pop("RECEIPTLENS_ENV", None)
    if env_override:
        env.update(env_override)
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_docs_enabled_by_default() -> None:
    """With no RECEIPTLENS_ENV, Swagger/ReDoc/OpenAPI stay public (dev default)."""
    result = _probe(None)
    assert result["docs"] == 200, result
    assert result["redoc"] == 200, result
    assert result["openapi"] == 200, result
    assert result["homepage_docs_link"] is True, result


def test_docs_enabled_in_development_env() -> None:
    """RECEIPTLENS_ENV=development keeps the docs enabled (explicit dev)."""
    result = _probe({"RECEIPTLENS_ENV": "development"})
    assert result["docs"] == 200, result
    assert result["redoc"] == 200, result
    assert result["openapi"] == 200, result
    assert result["homepage_docs_link"] is True, result


def test_docs_disabled_in_production_env() -> None:
    """RECEIPTLENS_ENV=production removes /docs, /redoc and /openapi.json."""
    result = _probe({"RECEIPTLENS_ENV": "production"})
    assert result["docs"] == 404, result
    assert result["redoc"] == 404, result
    assert result["openapi"] == 404, result


def test_homepage_does_not_link_to_docs_in_production() -> None:
    """In prod the landing page must not advertise routes that no longer exist."""
    result = _probe({"RECEIPTLENS_ENV": "production"})
    assert result["homepage_docs_link"] is False, result
