"""ReceiptLens forecast dashboard — server-rendered HTML.

Follows the same dependency-free, no-JS pattern as ``app.homepage``:
pure Python string formatting, inline CSS, no remote assets.
"""
from __future__ import annotations

from html import escape


def _bar_svg(values: list[float], width: int = 480, height: int = 120) -> str:
    """Render a minimal inline SVG bar chart for a list of values."""
    if not values:
        return '<p style="color:var(--muted)">No data to chart.</p>'
    max_val = max(values) if max(values) > 0 else 1.0
    bar_w = max(8, (width - 20) // len(values))
    bars = []
    for i, v in enumerate(values):
        h = max(2, int((v / max_val) * (height - 20)))
        x = 10 + i * (bar_w + 2)
        y = height - h - 10
        bars.append(
            f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" '
            f'rx="3" fill="var(--accent)" opacity="0.85"/>'
        )
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'style="width:100%;max-width:{width}px">'
        + "".join(bars)
        + "</svg>"
    )


def render_forecast_dashboard() -> str:
    """Render the forecast dashboard page.

    Calls the forecast engine singletons directly (synchronous, in-process)
    so the page is fully self-contained — no API round-trip required.
    """
    from app.forecast import anomaly_detector, budget_variance_projector, forecast_engine

    forecast_data = forecast_engine.forecast(period="monthly")
    anomaly_data = anomaly_detector.detect_anomalies()
    variance_data = budget_variance_projector.project_variance(period="monthly")

    # Build chart data from per-category forecasts (excluding Overall for the chart)
    cat_forecasts = [f for f in forecast_data.get("forecasts", []) if f["category"] != "Overall"]
    overall_entry = next(
        (f for f in forecast_data.get("forecasts", []) if f["category"] == "Overall"), None
    )
    chart_values = [f["next_period_total"] for f in cat_forecasts]
    chart_labels = [f["category"] for f in cat_forecasts]

    # Flagged anomalies
    flagged = [a for a in anomaly_data.get("anomalies", []) if a.get("flagged")]

    # Budget projections
    projections = variance_data.get("projections", [])

    # --- HTML ---
    forecast_cards = ""
    for f in forecast_data.get("forecasts", []):
        trend_icon = "↑" if f["trend"] > 0 else ("↓" if f["trend"] < 0 else "→")
        forecast_cards += (
            f'<div class="card">'
            f"<h3>{escape(f['category'])}</h3>"
            f'<p class="big-number">${f["next_period_total"]:,.2f}</p>'
            f'<p class="muted">Expected next month</p>'
            f'<p class="muted">Confidence: ${f["confidence_low"]:,.2f} – '
            f'${f["confidence_high"]:,.2f}</p>'
            f'<p>Trend: {trend_icon} {f["trend"]:+.2f}/period</p>'
            f"</div>"
        )

    anomaly_rows = ""
    for a in flagged[:10]:
        anomaly_rows += (
            f"<tr>"
            f"<td>{escape(a['period'])}</td>"
            f"<td>{escape(a['category'])}</td>"
            f"<td>${a['actual']:,.2f}</td>"
            f"<td>${a['expected']:,.2f}</td>"
            f'<td class="score">{a["score"]:.2f}</td>'
            f"</tr>"
        )
    if not flagged:
        anomaly_rows = '<tr><td colspan="5" style="text-align:center;color:var(--muted)">No flagged anomalies detected.</td></tr>'

    budget_rows = ""
    for p in projections:
        status_cls = p["status"].replace("_", "-")
        overage = p["expected_overage"]
        overage_str = f"+${overage:,.2f}" if overage > 0 else f"-${abs(overage):,.2f}"
        budget_rows += (
            f"<tr>"
            f"<td>{escape(p['category'])}</td>"
            f"<td>${p['budgeted']:,.2f}</td>"
            f"<td>${p['projected_spend']:,.2f}</td>"
            f'<td class="{status_cls}">{overage_str}</td>'
            f'<td class="{status_cls}">{p["status"].replace("_", " ").title()}</td>'
            f"</tr>"
        )
    if not projections:
        budget_rows = '<tr><td colspan="5" style="text-align:center;color:var(--muted)">No budgets configured.</td></tr>'

    overall_html = ""
    if overall_entry:
        overall_html = (
            f'<div class="card highlight">'
            f"<h2>Next Month Overall Spend</h2>"
            f'<p class="big-number">${overall_entry["next_period_total"]:,.2f}</p>'
            f'<p class="muted">Confidence: ${overall_entry["confidence_low"]:,.2f} – '
            f'${overall_entry["confidence_high"]:,.2f}</p>'
            f"</div>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ReceiptLens — Forecast Dashboard</title>
  <style>
    :root {{ color-scheme: light dark; --accent:#2563eb; --surface:#ffffff;
      --ink:#182033; --muted:#5c667a; --line:#dfe5ef; --ok:#16803c;
      --warn:#d97706; --danger:#dc2626; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;
      color:var(--ink); background:#f4f7fb; }}
    main {{ width:min(1080px,calc(100% - 32px)); margin:32px auto 56px; }}
    .hero {{ background:var(--surface); border:1px solid var(--line);
      border-radius:18px; box-shadow:0 8px 26px rgba(35,50,85,.08); padding:36px; }}
    h1 {{ margin:0 0 8px; font-size:clamp(1.8rem,5vw,2.8rem); letter-spacing:-.03em; }}
    h2 {{ margin-top:0; font-size:1.3rem; }}
    h3 {{ margin:0 0 4px; font-size:1rem; }}
    p {{ margin:4px 0; }}
    .muted {{ color:var(--muted); font-size:0.9rem; }}
    .big-number {{ font-size:2rem; font-weight:800; margin:8px 0; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
      gap:18px; margin-top:20px; }}
    .card {{ background:var(--surface); border:1px solid var(--line);
      border-radius:14px; padding:20px; box-shadow:0 4px 16px rgba(35,50,85,.06); }}
    .card.highlight {{ border-color:var(--accent); background:#eef4ff; }}
    table {{ width:100%; border-collapse:collapse; margin-top:12px; }}
    th, td {{ text-align:left; padding:8px 12px; border-bottom:1px solid var(--line); }}
    th {{ font-weight:600; font-size:0.85rem; text-transform:uppercase; color:var(--muted); }}
    .score {{ font-weight:700; color:var(--danger); }}
    .on-track {{ color:var(--ok); font-weight:600; }}
    .warning {{ color:var(--warn); font-weight:600; }}
    .over-budget {{ color:var(--danger); font-weight:600; }}
    .chart-section {{ margin-top:24px; }}
    nav {{ margin-bottom:20px; }}
    nav a {{ color:var(--accent); text-decoration:none; font-weight:600; }}
    nav a:hover {{ text-decoration:underline; }}
    footer {{ margin-top:24px; color:var(--muted); text-align:center; font-size:0.85rem; }}
    @media (prefers-color-scheme:dark) {{
      :root {{ --surface:#151c2c; --ink:#edf2ff; --muted:#b3bdd0; --line:#2d3850; }}
      body {{ background:#0d1320; }}
      .card.highlight {{ background:#1a2744; border-color:#4a7df7; }}
    }}
  </style>
</head>
<body>
<main>
  <nav><a href="/">&larr; Home</a></nav>

  <header class="hero">
    <h1>Forecast Dashboard</h1>
    <p class="muted">Next-period spend forecast, anomaly detection, and budget variance projection.</p>
  </header>

  {overall_html}

  <section class="chart-section">
    <div class="card">
      <h2>Category Spend Forecast</h2>
      {_bar_svg(chart_values)}
      <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:8px">
        {"".join(f'<span class="muted">{escape(label)}: ${v:,.2f}</span>' for label, v in zip(chart_labels, chart_values))}
      </div>
    </div>
  </section>

  <section>
    <h2 style="margin-top:28px">Per-Category Forecasts</h2>
    <div class="grid">
      {forecast_cards}
    </div>
  </section>

  <section>
    <h2 style="margin-top:28px">Flagged Anomalies</h2>
    <div class="card">
      <table>
        <thead><tr><th>Period</th><th>Category</th><th>Actual</th><th>Expected</th><th>Score</th></tr></thead>
        <tbody>{anomaly_rows}</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2 style="margin-top:28px">Budget Variance (Monthly)</h2>
    <div class="card">
      <table>
        <thead><tr><th>Category</th><th>Budgeted</th><th>Projected</th><th>Overage</th><th>Status</th></tr></thead>
        <tbody>{budget_rows}</tbody>
      </table>
    </div>
  </section>

  <footer>ReceiptLens Forecast Dashboard &bull; <a href="/docs">API Docs</a></footer>
</main>
</body>
</html>"""
