"""Acceptance tests for the human-friendly ReceiptLens landing page."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.api import app

import pytest

client = TestClient(app)


@pytest.mark.test_id("TEST-HOME-001")
@pytest.mark.requirements("REQ-HOMEPAGE-01")
@pytest.mark.scenario("A szerződéshez tartozó viselkedés.")
def test_root_returns_self_contained_html_homepage() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    assert "ReceiptLens" in html
    assert app.version in html
    assert "Service status" in html
    assert 'href="/docs"' in html
    assert 'href="/redoc"' in html
    assert "Receipt processing" in html
    assert "Batch processing" in html
    assert "Budgets &amp; analytics" in html
    assert "curl.exe" in html
    assert "/v1/parse-receipt" in html
    assert "<script" not in html.lower()
    assert "https://" not in html.lower()


@pytest.mark.test_id("TEST-HOME-002")
@pytest.mark.requirements("REQ-HOMEPAGE-01")
@pytest.mark.scenario("A szerződéshez tartozó viselkedés.")
def test_homepage_links_resolve() -> None:
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.test_id("TEST-HOME-003")
@pytest.mark.requirements("REQ-HOMEPAGE-01")
@pytest.mark.scenario("A szerződéshez tartozó viselkedés.")
def test_homepage_escapes_dynamic_application_metadata() -> None:
    from app.homepage import render_homepage

    html = render_homepage(name='<script>alert(1)</script>', version='1&2', description='<b>x</b>')
    assert '<script>' not in html
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in html
    assert '1&amp;2' in html
    assert '&lt;b&gt;x&lt;/b&gt;' in html
