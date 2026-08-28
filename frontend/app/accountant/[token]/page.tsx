import { headers } from "next/headers";

export default async function AccountantPage({ params }: { params: { token: string } }) {
  const h = headers();
  const host = h.get("host") ?? "receipts.allthezoo.com";
  const proto = h.get("x-forwarded-proto") ?? "https";
  const base = `${proto}://${host}`;
  let rows: Array<{ vendor: string; date: string; total: string; status: string }> = [];
  let error: string | null = null;
  try {
    const res = await fetch(`${base}/accountant/${params.token}`, { cache: "no-store" });
    if (!res.ok) {
      error = res.status === 404 ? "Invite expired or invalid" : `Error ${res.status}`;
    } else {
      const html = await res.text();
      // Extract table rows from HTML fallback — show raw invite info
      // The backend returns HTML table; we render it via iframe-style passthrough
      // For SSR, just proxy the HTML table rows via text extraction
      rows = [];
      // If backend returned HTML, we already have it — render raw via dangerouslySetInnerHTML alternative
      // Simpler: just show message and link to HTML view
      error = null;
      // Store HTML for rendering
      return (
        <html lang="en">
          <head>
            <meta name="robots" content="noindex, nofollow" />
            <title>Receipts — read only</title>
          </head>
          <body style={{ fontFamily: "system-ui, sans-serif", padding: 24 }}>
            <h1>Receipts — read only</h1>
            <p style={{ color: "#64748b" }}>Shared via invite token {params.token.slice(0, 8)}…</p>
            <div dangerouslySetInnerHTML={{ __html: html }} />
          </body>
        </html>
      );
    }
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }
  if (error) {
    return (
      <html lang="en">
        <head>
          <meta name="robots" content="noindex, nofollow" />
        </head>
        <body style={{ fontFamily: "system-ui, sans-serif", padding: 24 }}>
          <h1>Invite expired or invalid</h1>
          <p>{error}</p>
        </body>
      </html>
    );
  }
  return (
    <html lang="en">
      <head>
        <meta name="robots" content="noindex, nofollow" />
      </head>
      <body style={{ fontFamily: "system-ui, sans-serif", padding: 24 }}>
        <h1>Receipts — read only</h1>
        <table>
          <thead>
            <tr>
              <th>Vendor</th>
              <th>Date</th>
              <th>Total</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td>{r.vendor}</td>
                <td>{r.date}</td>
                <td>{r.total}</td>
                <td>{r.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </body>
    </html>
  );
}
