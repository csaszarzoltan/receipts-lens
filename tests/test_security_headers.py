"""SEC-004: Security headers on API responses.

Security test report 2026-08-12 (SEC-004) requires the following headers on
every API response:

- ``X-Content-Type-Options: nosniff``
- ``X-Frame-Options: DENY`` (or SAMEORIGIN)
- ``Strict-Transport-Security`` (HSTS) — production/HTTPS only
- ``Referrer-Policy``
- ``Content-Security-Policy`` (CSP) — production/HTTPS only (the API serves
  JSON, so a defensive default-src 'none' CSP is safe; relaxed in dev)
- ``Permissions-Policy``
- ``X-XSS-Protection: 0`` (modern best practice: disables the legacy,
  buggy filter; document why in docs/api.md)

The headers are emitted by an ASGI middleware in ``app/api.py`` so that every
response (including error responses, 404s, CORS preflights) carries them,
independent of the HTTP server / proxy in front of the app.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.api import app

# Headers that must be present on EVERY API response in every environment.
# Exact values are validated per-header below; this list names the
# unconditional presence contract.
ALWAYS_REQUIRED_NAMES = [
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "permissions-policy",
    "x-xss-protection",
]

# Headers that must exist when the app runs in production/HTTPS mode.
HTTPS_ONLY_NAMES = [
    "strict-transport-security",
    "content-security-policy",
]

# Response-producing paths that should carry the headers: a JSON API route,
# a 404 (no matching route), and an OPTIONS preflight (middleware must run
# even on non-app responses).
SAMPLE_PATHS = [
    ("/api/v1/platform/capabilities", 200),
    ("/definitely-not-a-real-route", 404),
]


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Environment handling
# ---------------------------------------------------------------------------


@pytest.fixture
def prod_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the app into production/HTTPS mode for HSTS/CSP assertions."""
    monkeypatch.setenv("RECEIPTLENS_ENV", "production")
    monkeypatch.setenv("RECEIPTLENS_HTTPS", "1")


@pytest.fixture
def clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default local/dev mode: no HSTS, no CSP."""
    monkeypatch.delenv("RECEIPTLENS_HTTPS", raising=False)
    monkeypatch.delenv("RECEIPTLENS_ENV", raising=False)


# ---------------------------------------------------------------------------
# Headers present on every response
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path,status", SAMPLE_PATHS)
def test_always_headers_present(
    client: TestClient, clear_env: None, path: str, status: int
) -> None:
    """Every response carries the always-on security headers (SEC-004)."""
    for method in ("get", "options"):
        resp = getattr(client, method)(path)
        assert resp.status_code in (status, 200, 405), (
            f"{method.upper()} {path} -> {resp.status_code}"
        )
        missing = [h for h in ALWAYS_REQUIRED_NAMES if h not in resp.headers]
        assert not missing, f"{method.upper()} {path} missing headers: {missing}"


def test_nosniff_value(client: TestClient, clear_env: None) -> None:
    resp = client.get("/api/v1/platform/capabilities")
    assert resp.headers["x-content-type-options"] == "nosniff"


def test_frame_options_deny(client: TestClient, clear_env: None) -> None:
    resp = client.get("/api/v1/platform/capabilities")
    assert resp.headers["x-frame-options"] == "DENY"


def test_referrer_policy_value(client: TestClient, clear_env: None) -> None:
    resp = client.get("/api/v1/platform/capabilities")
    assert resp.headers["referrer-policy"] == "no-referrer"


def test_permissions_policy_present(client: TestClient, clear_env: None) -> None:
    resp = client.get("/api/v1/platform/capabilities")
    assert "permissions-policy" in resp.headers
    # The header must not grant anything dangerous by default.
    assert "geolocation" not in resp.headers["permissions-policy"].lower() or (
        "geolocation=()" in resp.headers["permissions-policy"]
    )


def test_xss_protection_disabled(client: TestClient, clear_env: None) -> None:
    """Legacy X-XSS-Protection is set to 0 (modern best practice)."""
    resp = client.get("/api/v1/platform/capabilities")
    assert resp.headers["x-xss-protection"] == "0"


# ---------------------------------------------------------------------------
# HSTS — production/HTTPS only
# ---------------------------------------------------------------------------


def test_hsts_present_in_production(client: TestClient, prod_env: None) -> None:
    resp = client.get("/api/v1/platform/capabilities")
    assert resp.headers["strict-transport-security"].startswith(
        "max-age="
    ), resp.headers.get("strict-transport-security")


def test_hsts_absent_in_dev(client: TestClient, clear_env: None) -> None:
    resp = client.get("/api/v1/platform/capabilities")
    assert "strict-transport-security" not in resp.headers


# ---------------------------------------------------------------------------
# CSP — production/HTTPS only
# ---------------------------------------------------------------------------


def test_csp_present_in_production(client: TestClient, prod_env: None) -> None:
    resp = client.get("/api/v1/platform/capabilities")
    assert "content-security-policy" in resp.headers


def test_csp_absent_in_dev(client: TestClient, clear_env: None) -> None:
    resp = client.get("/api/v1/platform/capabilities")
    assert "content-security-policy" not in resp.headers


def test_csp_is_defensive_in_production(
    client: TestClient, prod_env: None
) -> None:
    """JSON API CSP must not allow script execution from anywhere."""
    csp = client.get("/api/v1/platform/capabilities").headers[
        "content-security-policy"
    ]
    assert "default-src 'none'" in csp, csp


# ---------------------------------------------------------------------------
# Frontend (Next.js) header contract — config-level assertions
# ---------------------------------------------------------------------------


def test_frontend_config_defines_security_headers() -> None:
    """frontend/next.config.ts must export a headers() function with the
    SEC-004 header set (applied by Next.js to every page/asset response)."""
    import re
    from pathlib import Path

    cfg = Path(__file__).resolve().parents[1] / "frontend" / "next.config.ts"
    assert cfg.exists(), "frontend/next.config.ts missing"
    text = cfg.read_text(encoding="utf-8")

    assert "headers:" in text, "next.config.ts must define headers()"
    # Every required header name must be configured for the frontend.
    for header_name in (
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Referrer-Policy",
        "Permissions-Policy",
        "Content-Security-Policy",
        "Strict-Transport-Security",
        "X-XSS-Protection",
    ):
        assert header_name.lower() in text.lower(), (
            f"frontend next.config.ts missing {header_name}"
        )
    # CSP must be a non-trivial policy: it must contain a default-src
    # directive (regardless of how the config structures key/value).
    assert "default-src" in text, "frontend CSP must be a non-trivial policy"
