"""Acceptance tests for the human-friendly ReceiptLens landing page."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


def test_root_returns_self_contained_html_homepage() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    assert "ReceiptLens" in html
    assert app.version in html
    assert "Szolgáltatás állapota" in html
    assert 'href="/docs"' in html
    assert 'href="/redoc"' in html
    assert "Nyugta feldolgozása" in html
    assert "Kötegelt feldolgozás" in html
    assert "Költségkeretek és analitika" in html
    assert "curl.exe" in html
    assert "/v1/parse-receipt" in html
    assert "<script" not in html.lower()
    assert "https://" not in html.lower()


def test_homepage_links_resolve() -> None:
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}


def test_homepage_escapes_dynamic_application_metadata() -> None:
    from app.homepage import render_homepage

    html = render_homepage(name='<script>alert(1)</script>', version='1&2', description='<b>x</b>')
    assert '<script>' not in html
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in html
    assert '1&amp;2' in html
    assert '&lt;b&gt;x&lt;/b&gt;' in html
