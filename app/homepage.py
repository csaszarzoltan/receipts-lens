"""Self-contained, dependency-free HTML landing page for ReceiptLens."""
from __future__ import annotations

import os
from html import escape


def _is_production() -> bool:
    """Check if running in production mode (docs gated)."""
    return os.getenv("RECEIPTLENS_ENV") == "production"


def render_homepage(*, name: str, version: str, description: str) -> str:
    """Render the public landing page using escaped application metadata.

    The page intentionally has no JavaScript or remote assets. This keeps the
    API service usable offline and avoids introducing an additional frontend
    build pipeline for a small informational entry page.
    """
    safe_name = escape(name)
    safe_version = escape(version)
    safe_description = escape(description)

    # SEC-006: in production, don't link to /docs or /redoc
    prod = _is_production()

    docs_button = (
        '<a class="button secondary" href="/docs">Swagger UI</a>'
        if not prod else ""
    )
    redoc_button = (
        '<a class="button secondary" href="/redoc">ReDoc megnyitása</a>'
        if not prod else ""
    )

    footer_docs_link = (
        '<a href="/docs">/docs</a>' if not prod else ""
    )
    return f"""<!doctype html>
<html lang="hu">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{safe_description}">
  <title>{safe_name} {safe_version}</title>
  <style>
    :root {{ color-scheme: light dark; --accent:#2563eb; --surface:#ffffff;
      --ink:#182033; --muted:#5c667a; --line:#dfe5ef; --ok:#16803c; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;
      color:var(--ink); background:#f4f7fb; }}
    main {{ width:min(1080px,calc(100% - 32px)); margin:32px auto 56px; }}
    .hero,.card {{ background:var(--surface); border:1px solid var(--line);
      border-radius:18px; box-shadow:0 8px 26px rgba(35,50,85,.08); }}
    .hero {{ padding:36px; }}
    h1 {{ margin:0 0 8px; font-size:clamp(2rem,6vw,3.5rem); letter-spacing:-.04em; }}
    h2 {{ margin-top:0; font-size:1.3rem; }}
    p {{ color:var(--muted); }}
    .version {{ display:inline-block; padding:4px 10px; border-radius:999px;
      background:#e8f0ff; color:#174ea6; font-weight:700; }}
    .status {{ display:flex; align-items:center; gap:9px; margin:22px 0; font-weight:700; }}
    .dot {{ width:11px; height:11px; border-radius:50%; background:var(--ok);
      box-shadow:0 0 0 5px rgba(22,128,60,.13); }}
    .actions {{ display:flex; flex-wrap:wrap; gap:12px; }}
    .button {{ display:inline-block; padding:11px 16px; border-radius:10px;
      background:var(--accent); color:white; text-decoration:none; font-weight:700; }}
    .button.secondary {{ color:var(--accent); background:#edf3ff; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(245px,1fr));
      gap:18px; margin-top:20px; }}
    .card {{ padding:24px; }}
    ul {{ padding-left:20px; }} li {{ margin:7px 0; }}
    code {{ font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }}
    pre {{ overflow:auto; margin:0; padding:18px; border-radius:12px;
      color:#e8edf7; background:#101827; white-space:pre-wrap; }}
    footer {{ margin-top:24px; color:var(--muted); text-align:center; }}
    @media (prefers-color-scheme:dark) {{
      :root {{ --surface:#151c2c; --ink:#edf2ff; --muted:#b3bdd0; --line:#2d3850; }}
      body {{ background:#0d1320; }} .version {{ background:#23365c; color:#c9dcff; }}
      .button.secondary {{ background:#23365c; color:#d9e7ff; }}
    }}
  </style>
</head>
<body>
<main>
  <header class="hero">
    <span class="version">v{safe_version}</span>
    <h1>{safe_name}</h1>
    <p>{safe_description} A szolgáltatás nyugtaképekből strukturált adatokat készít,
      és API-n keresztül biztosít feldolgozási, riportálási és elemzési műveleteket.</p>
    <div class="status" aria-label="Szolgáltatás állapota: működik">
      <span class="dot" aria-hidden="true"></span>
      <span>Szolgáltatás állapota: működik</span>
    </div>
    <nav class="actions" aria-label="API dokumentáció">
      <a class="button" href="/dashboard">Forecast dashboard</a>
      <a class="button secondary" href="/workspace">Open workspace</a>
      {docs_button}
      {redoc_button}
      <a class="button secondary" href="/health">Health check</a>
    </nav>
  </header>

  <section class="grid" aria-label="Támogatott műveletek">
    <article class="card"><h2>Nyugta feldolgozása</h2><p>Egy kép feltöltése vagy biztonságosan
      ellenőrzött publikus kép-URL feldolgozása, strukturált mezőkkel és confidence értékekkel.</p></article>
    <article class="card"><h2>Kötegelt feldolgozás</h2><p>Több nyugta szinkron vagy aszinkron
      feldolgozása, job státusszal és opcionális webhookkal.</p></article>
    <article class="card"><h2>Riportok és kategorizálás</h2><p>CSV/PDF riport, automatikus
      kategorizálás és duplikált nyugták ellenőrzése.</p></article>
    <article class="card"><h2>Költségkeretek és analitika</h2><p>Budget CRUD, költési összesítések,
      trendek és küszöbérték-alapú riasztások.</p></article>
    <article class="card"><h2><a href="/dashboard" style="color:inherit;text-decoration:none">Előrejelzések</a></h2>
      <p>Következő havi kiadás előrejelzés, anomália-detekció és költségvetési
      eltérés-projekciók.</p></article>
  </section>

  <section class="card" style="margin-top:20px">
    <h2>Rövid példa nyugtafeltöltésre</h2>
    <p>PowerShellben a beépített <code>curl.exe</code> használata ajánlott:</p>
    <pre><code>curl.exe -X POST "http://127.0.0.1:8000/v1/parse-receipt" `
  -F "file=@C:\\Receipts\\receipt.jpg"</code></pre>
  </section>
  <footer>ReceiptLens API • részletes kipróbálás: {footer_docs_link}</footer>
</main>
</body>
</html>"""
