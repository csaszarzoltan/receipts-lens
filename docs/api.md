# API Reference

# Böngészős kezdőoldal

A `GET /` egy magyar nyelvű, reszponzív szolgáltatási főoldalt ad vissza. A főoldal az alkalmazás nevét és verzióját dinamikusan a FastAPI metadata alapján jeleníti meg, linket ad a Swagger UI és ReDoc dokumentációhoz, valamint rövid feltöltési példát tartalmaz. A route nem része az OpenAPI sémának, mert emberi navigációs felület, nem integrációs API.



The FastAPI application is exposed as `app.api.app`.

```bash
uvicorn app.main:app --reload
```

## Security headers (SEC-004)

Every response from the API carries the following security headers,
added by an ASGI middleware (`SecurityHeadersMiddleware` in `app/api.py`)
so they apply regardless of the HTTP server / proxy in front of the app
(uvicorn, gunicorn, Caddy, Railway, …):

| Header | Value | Notes |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME sniffing. |
| `X-Frame-Options` | `DENY` | Clickjacking protection — the API must never be framed. |
| `Referrer-Policy` | `no-referrer` | No referrer leakage. |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Denies the sensitive browser features by default. |
| `X-XSS-Protection` | `0` | Disables the legacy browser XSS filter (it is buggy and can itself introduce XSS); modern best practice. |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains` | **Production/HTTPS only** — see below. |
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'; base-uri 'none'` | **Production/HTTPS only** — the API serves JSON, so a defensive default-deny CSP is safe. |

The `Strict-Transport-Security` (HSTS) and `Content-Security-Policy` (CSP)
headers are emitted only when the app is served over HTTPS. HTTPS is detected
per request, in priority order:

1. `X-Forwarded-Proto: https` on the request (TLS-terminating proxy in front),
2. `RECEIPTLENS_HTTPS=1|true|yes` environment variable,
3. `RECEIPTLENS_ENV=production` environment variable.

During local development (`uvicorn app.main:app` without those settings) HSTS
and CSP are not emitted, so browsers don't cache an HSTS policy for
`localhost`. If you terminate TLS at a proxy, set `RECEIPTLENS_HTTPS=1` (or
deploy with `RECEIPTLENS_ENV=production`) and make sure the proxy forwards
`X-Forwarded-Proto`.

The frontend (Next.js, port 8200 in the security-test setup) applies its own
header set — including a browser-facing CSP with `default-src 'self'` and
HSTS — via `frontend/next.config.ts` → `headers()`; see
`frontend/next.config.ts` for the exact policy and its rationale.

## Endpoints

### Rate limits (SEC-005)

OCR-heavy and inbound-ingestion endpoints are rate limited **per tenant + per
client IP** (fixed window). When a limit is exceeded the API answers `429` with
a `Retry-After` header (seconds until the window resets) plus
`X-RateLimit-Limit` / `X-RateLimit-Remaining`. OPTIONS preflight requests and
unlisted routes are not limited.

| Endpoint | Default limit | Window |
|---|---|---|
| `POST /product/receipts/upload` | 60 | 60 s |
| `POST /product/inbound-emails` | 60 | 60 s |
| `POST /v1/parse-receipt` | 60 | 60 s |
| `POST /v1/parse-receipt/async` | 60 | 60 s |
| `POST /v1/parse-receipts` | 60 | 60 s |
| `POST /v1/parse-receipts/async` | 60 | 60 s |
| `POST /api/v1/receipts` | 60 | 60 s |
| `POST /api/v1/receipts/batch` | 60 | 60 s |

Limits are tunable with the `RECEIPTLENS_RATE_LIMITS` environment variable
(`METHOD /path=count/window_seconds`, `;`-separated); e.g.
`RECEIPTLENS_RATE_LIMITS="POST /product/receipts/upload=10/60;POST /v1/parse-receipt=5/60"`.
Any route not listed is not limited. If `login`/`register` endpoints are added
later, add a `POST /auth/login=…` row to the same table. The counter is
in-memory per process; a multi-worker deployment should move it to a shared
store (e.g. Redis).

### `GET /health`

Health-check probe.

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

### `POST /v1/parse-receipt`

Parse a receipt image and return structured JSON with per-field confidence scores.

Send either:
- `file` (multipart upload), or
- `image_url` (form field pointing to a public image URL)

Do not send both at the same time.

#### Request (file upload)

```bash
curl -X POST "http://localhost:8000/v1/parse-receipt" \
  -F "file=@/path/to/receipt.jpg"
```

#### Request (URL)

```bash
curl -X POST "http://localhost:8000/v1/parse-receipt" \
  -F "image_url=https://example.com/receipt.jpg"
```

##### URL fetching contract

When `image_url` is provided the server fetches the image server-side before
running OCR. The fetch is governed by the constraints below.

**Accepted schemes**

Only `http` and `https`. Any other scheme (e.g. `file://`, `ftp://`) is
rejected immediately with a `400` before any network call.

**SSRF protection**

The fetcher validates the URL and its resolved IP address to prevent
server-side request forgery.

| Layer | What is checked | Rejection detail |
|---|---|---|
| Scheme | Must be `http` or `https` | `400 — Failed to fetch image from URL.` |
| Hostname blocklist (exact) | `localhost`, `local.host`, `metadata.google.internal`, `metadata.internal`, `169.254.169.254`, `metadata` | `400 — Failed to fetch image from URL.` |
| Hostname blocklist (substring) | Hostnames containing `local`, `internal`, or `localhost` (case-insensitive, including subdomains such as `foo.local`) | `400 — Failed to fetch image from URL.` |
| Resolved IPs — private | `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` | `400 — Failed to fetch image from URL.` |
| Resolved IPs — loopback | `127.0.0.0/8`, `::1/128` | `400 — Failed to fetch image from URL.` |
| Resolved IPs — link-local | `169.254.0.0/16`, `fe80::/10` | `400 — Failed to fetch image from URL.` |
| Resolved IPs — carrier-grade NAT | `100.64.0.0/10` | `400 — Failed to fetch image from URL.` |
| Resolved IPs — multicast/reserved | `224.0.0.0/4`, `240.0.0.0/4`, `0.0.0.0/8`, `::/128`, `fc00::/7` | `400 — Failed to fetch image from URL.` |

DNS resolution happens **before** any HTTP request. If the hostname resolves
to a blocked address, the request is rejected with no network contact.

**Redirect handling**

- Maximum **5** redirects.
- Each redirect target is re-validated (scheme, hostname blocklist, resolved IPs).
- A redirect to a private or blocked host is rejected with `400`.
- Exceeding the redirect cap returns `400 — Failed to fetch image from URL.`

**Response validation**

| Check | Constraint | Error |
|---|---|---|
| Content-Type | Must start with `image/` | `400 — URL did not return an image` |
| Body size | Max **20 MB** (`MAX_IMAGE_BYTES = 20_000_000`) | `400 — Image exceeds maximum allowed size` |

**Timeouts**

| Phase | Limit |
|---|---|
| Connect | 10 s |
| Read | 30 s (`URL_FETCH_TIMEOUT = 30.0`) |

Network errors (timeouts, connection refused, DNS failures) return
`400 — Failed to fetch image from URL.`

**Error responses summary**

| Status | `detail` | Trigger |
|---|---|---|
| `400` | `Invalid image URL.` | Malformed URL (e.g. missing host) |
| `400` | `Failed to fetch image from URL.` | Unsupported scheme, blocked hostname/IP, DNS failure, connection error, timeout, too many redirects |
| `400` | `URL did not return an image` | Response Content-Type is not `image/*` |
| `400` | `Image exceeds maximum allowed size` | Response body exceeds 20 MB |
| `400` | `The provided data is not a recognized image format.` | Downloaded bytes are not a valid image (PIL error) |
| `400` | `Provide either 'file' or 'image_url', not both.` | Both `file` and `image_url` supplied |
| `422` | `Missing required input: send 'file' or 'image_url'.` | Neither `file` nor `image_url` supplied |
| `500` | `OCR processing failed.` | Unexpected OCR error (no internals leaked) |

> **Security note:** All error messages are controlled strings. Raw IP
> addresses, exception messages, and internal paths are never included in
> HTTP responses.

##### Example requests (URL)

```bash
# Valid URL
curl -X POST "http://localhost:8000/v1/parse-receipt" \
  -F "image_url=https://example.com/receipt.jpg"

# Blocked: file:// scheme → 400
curl -s -X POST "http://localhost:8000/v1/parse-receipt" \
  -F "image_url=file:///etc/passwd" | python -m json.tool
# {"detail":"Failed to fetch image from URL."}

# Blocked: metadata IP → 400
curl -s -X POST "http://localhost:8000/v1/parse-receipt" \
  -F "image_url=http://169.254.169.254/latest/meta-data/" | python -m json.tool
# {"detail":"Failed to fetch image from URL."}

# Blocked: non-image response → 400
curl -s -X POST "http://localhost:8000/v1/parse-receipt" \
  -F "image_url=https://example.com/page.html" | python -m json.tool
# {"detail":"URL did not return an image"}

# Blocked: empty input → 422
curl -s -X POST "http://localhost:8000/v1/parse-receipt" | python -m json.tool
# {"detail":"Missing required input: send 'file' or 'image_url'."}
```

#### Response

```json
{
  "vendor": "STORE NAME",
  "total": 42.50,
  "date": "2025-03-14",
  "tax": 3.40,
  "currency": "USD",
  "line_items": [
    { "name": "ITEM", "price": 9.99 }
  ],
  "confidence": {
    "vendor": 0.88,
    "total": 0.95,
    "date": 0.80,
    "tax": 0.70,
    "currency": 0.99,
    "line_items": 0.85
  }
}
```

#### AI mode (`ai_scan=true`)

Add the form field `ai_scan=true` to run the LLM vision path first, with
automatic Tesseract fallback. The response then exposes a top-level `source`
(`"vision"` | `"tesseract"`) plus `ai_result` / `tesseract_result` payloads,
each carrying the same receipt/confidence shape as the regular response.
See [docs/ai-vision-ocr.md](ai-vision-ocr.md) for setup (env vars
`LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` / `VISION_OCR_ENABLED` /
`VISION_OCR_TIMEOUT`) and behavior.

```bash
curl -X POST "http://localhost:8000/v1/parse-receipt" \
  -F "file=@/path/to/receipt.jpg" \
  -F "ai_scan=true"
```

Without `VISION_OCR_ENABLED` / `LLM_API_KEY` the response falls back to
Tesseract (verified output shape):

```json
{
  "source": "tesseract",
  "tesseract_result": {
    "vendor": "STORE NAME",
    "total": 42.50,
    "date": "2025-03-14",
    "tax": 3.40,
    "currency": "USD",
    "line_items": [
      { "name": "ITEM", "price": 9.99 }
    ],
    "confidence": {
      "vendor": 0.88,
      "total": 0.95,
      "date": 0.80,
      "tax": 0.70,
      "currency": 0.99,
      "line_items": 0.85
    }
  }
}
```

When the vision path produces the result, `source` is `"vision"` and
`ai_result` (vision extraction) is present alongside `tesseract_result`
(classic pipeline on the same image) for comparison. The regular flow (no
`ai_scan`) never leaks these AI-mode fields.

### `POST /v1/parse-receipt/async`

Queue an async OCR job and return immediately with a `job_id`.

Parameters:

- `file` (multipart upload)
- `image_url` (form field)
- `webhook_url` (optional form field) — URL to POST the result to when processing completes or fails.

```bash
curl -X POST "http://localhost:8000/v1/parse-receipt/async" \
  -F "file=@/path/to/receipt.jpg"
```

Response:

```json
{
  "job_id": "uuid",
  "status": "queued",
  "webhook_url": null
}
```

### `GET /v1/jobs/{job_id}`

Poll the status and result of an async OCR job.

```bash
curl "http://localhost:8000/v1/jobs/abc123"
```

Response:

```json
{
  "job_id": "abc123",
  "status": "completed",
  "result": { ... same shape as /v1/parse-receipt ... },
  "error": null
}
```

### `POST /v1/parse-receipts`

Parse multiple receipt images in a single request. Accepts either multiple
`files` uploads or a JSON `image_urls` array, not both.

#### Request (file uploads)

```bash
curl -X POST "http://localhost:8000/v1/parse-receipts" \
  -F "files=@/path/to/receipt1.jpg" \
  -F "files=@/path/to/receipt2.jpg"
```

#### Request (URLs)

```bash
curl -X POST "http://localhost:8000/v1/parse-receipts" \
  -F 'image_urls=["https://example.com/receipt1.jpg","https://example.com/receipt2.jpg"]'
```

> The same URL fetching contract (scheme restrictions, SSRF protection,
> redirect limits, content-type and size checks) described above for
> `/v1/parse-receipt` applies to every URL in the array.

#### Response

```json
{
  "results": [
    {
      "index": 0,
      "vendor": "STORE A",
      "total": 12.50,
      "date": "2025-03-14",
      "tax": 1.00,
      "currency": "USD",
      "line_items": [
        { "name": "ITEM", "price": 9.99 }
      ],
      "confidence": {
        "vendor": 0.88,
        "total": 0.95,
        "date": 0.80,
        "tax": 0.70,
        "currency": 0.99,
        "line_items": 0.85
      },
      "error": null
    },
    {
      "index": 1,
      "vendor": null,
      "total": null,
      "date": null,
      "tax": null,
      "currency": null,
      "line_items": [],
      "confidence": {
        "vendor": null,
        "total": null,
        "date": null,
        "tax": null,
        "currency": null,
        "line_items": null
      },
      "error": "Failed to fetch image from URL: ..."
    }
  ],
  "summary": {
    "total": 2,
    "successful": 1,
    "failed": 1
  }
}
```

### `POST /v1/parse-receipts/async`

Queue an async batch OCR job. Same inputs as `POST /v1/parse-receipts`,
plus optional `webhook_url` for completion callback.

```bash
curl -X POST "http://localhost:8000/v1/parse-receipts/async" \
  -F "files=@/path/to/receipt1.jpg" \
  -F "files=@/path/to/receipt2.jpg"
```

Returns `job_id` immediately. Poll with `GET /v1/jobs/{job_id}`.

> The same URL fetching contract described above for `/v1/parse-receipt`
> applies to each URL. Fetching happens in the background job (non-blocking).

### `POST /api/v1/categorize`

AI-powered receipt categorization by vendor name. Uses keyword/regex rules (offline, always available) with optional LLM enrichment when `LLM_API_KEY` is set.

```bash
curl -X POST http://localhost:8000/api/v1/categorize \
  -H "Content-Type: application/json" \
  -d '{"vendor": "Starbucks Coffee", "total": 5.75}'
```

Response:

```json
{
  "category": "Meals & Entertainment",
  "confidence": "high",
  "matched_rule": "starbucks",
  "subcategory": "Coffee Shops"
}
```

See [docs/categorization.md](categorization.md) for full details.

### `POST /api/v1/budgets`

Create a new budget definition.

```bash
curl -X POST http://localhost:8000/api/v1/budgets \
  -H "Content-Type: application/json" \
  -d '{"category": "Meals & Entertainment", "amount": 500}'
```

### `GET /api/v1/budgets`

List all budget definitions with computed spend fields.

### `GET /api/v1/budgets/{id}`

Get a single budget by id.

### `PUT /api/v1/budgets/{id}`

Update an existing budget.

### `DELETE /api/v1/budgets/{id}`

Delete a budget.

### `GET /api/v1/analytics/spending`

Aggregate spending by category, merchant, day, or month.

```bash
curl "http://localhost:8000/api/v1/analytics/spending?date_from=2026-07-01&date_to=2026-07-31&group_by=category"
```

### `GET /api/v1/analytics/budgets`

Compare budget definitions against current spending.

```bash
curl "http://localhost:8000/api/v1/analytics/budgets?period=monthly"
```

### `GET /api/v1/alerts`

List active (non-acknowledged) alerts.

```bash
curl http://localhost:8000/api/v1/alerts
```

### `POST /api/v1/alerts/{alert_id}/acknowledge`

Acknowledge an alert (dismisses it from the active list).

## Subscription endpoints

### `GET /api/v1/subscriptions`

List active subscriptions with next renewal date, monthly cost, and price-change trend. Subscriptions are derived from merchants with at least 2 stored receipts (recurring-expense analysis); the frequency is inferred from the number of occurrences (12+ monthly, 5–11 quarterly, 2–4 annual).

```bash
curl http://localhost:8000/api/v1/subscriptions
```

```json
{
  "subscriptions": [
    {
      "id": "sub-001",
      "merchant": "Spotify",
      "occurrences": 6,
      "frequency": "quarterly",
      "renewal_date": "2026-11-03",
      "amount": 10.99,
      "monthly_cost": 3.66,
      "annualized": 131.88,
      "trend": "stable",
      "price_increase": false,
      "likely_subscription": true
    },
    {
      "id": "sub-002",
      "merchant": "Netflix",
      "occurrences": 6,
      "frequency": "quarterly",
      "renewal_date": "2026-09-15",
      "amount": 12.99,
      "monthly_cost": 3.5,
      "annualized": 125.88,
      "trend": "up",
      "price_increase": true,
      "likely_subscription": false
    }
  ],
  "summary": {
    "total": 2,
    "monthly_total": 7.16
  }
}
```

### `GET /api/v1/subscriptions/{subscription_id}/cancel-guide`

Return merchant-specific cancellation steps for a subscription's merchant. Curated guides exist for the top streaming/subscription merchants; unknown merchants fall back to a generic guide (`"merchant": "generic"`, `"url": null`).

```bash
curl http://localhost:8000/api/v1/subscriptions/sub-002/cancel-guide
```

```json
{
  "subscription_id": "sub-002",
  "merchant": "Netflix",
  "steps": [
    "Go to netflix.com/cancelplan and sign in to your account.",
    "Click 'Finish Cancellation' on the membership page.",
    "Follow the confirmation prompts (you may be asked for a reason).",
    "Keep using Netflix until the end of the current billing period.",
    "Check your email for a cancellation confirmation."
  ],
  "url": "https://www.netflix.com/cancelplan"
}
```

### `GET /api/v1/subscriptions/trend-data`

Return time-series spending data for the subscription dashboard trend chart.
Aggregates receipt amounts across recurring merchants by month (or quarter /
year) and computes an overall trend direction.

#### Query parameters

| Parameter | Type   | Default    | Description                                                        |
|-----------|--------|------------|--------------------------------------------------------------------|
| `period`  | string | `monthly`  | Granularity: `monthly`, `quarterly`, or `annual`                   |

#### Example

```bash
curl "http://localhost:8000/api/v1/subscriptions/trend-data?period=monthly"
```

#### Response

```json
{
  "monthly": [
    {"month": "2026-08", "amount": 45.97},
    {"month": "2026-07", "amount": 41.97},
    {"month": "2026-06", "amount": 38.98}
  ],
  "annual_total": 516.50,
  "trend_direction": "increasing",
  "avg_monthly": 42.04
}
```

| Field              | Type   | Description                                                          |
|--------------------|--------|----------------------------------------------------------------------|
| `monthly`          | array  | Time-series entries sorted newest-first; each has `month` (string) and `amount` (float) |
| `annual_total`     | float  | Sum of all monthly totals                                            |
| `trend_direction`  | string | `increasing`, `decreasing`, or `stable` (based on first-half vs second-half comparison) |
| `avg_monthly`      | float  | Average monthly spend across all months with data                    |

When `period` is `quarterly`, months are grouped into `YYYY-Q1` … `YYYY-Q4`
buckets. When `annual`, grouped by `YYYY`. An empty workspace returns empty
arrays and zeroes.

### `GET /api/v1/subscriptions/renewal-timeline`

Return upcoming renewals sorted by renewal date with a countdown of days
until each renewal. The subscription list is built from the same
recurring-expense analysis as `GET /subscriptions`.

#### Example

```bash
curl "http://localhost:8000/api/v1/subscriptions/renewal-timeline"
```

#### Response

```json
{
  "renewals": [
    {
      "subscription_id": "sub-001",
      "merchant": "Netflix",
      "amount": 15.99,
      "renewal_date": "2026-08-12",
      "days_until": 4
    },
    {
      "subscription_id": "sub-002",
      "merchant": "Spotify",
      "amount": 10.99,
      "renewal_date": "2026-09-01",
      "days_until": 24
    }
  ]
}
```

| Field              | Type   | Description                                                |
|--------------------|--------|------------------------------------------------------------|
| `subscription_id`  | string | Stable per-request id (`sub-001`, `sub-002`, …)            |
| `merchant`         | string | Vendor name as detected from receipts                      |
| `amount`           | float  | Most recent charge amount                                  |
| `renewal_date`     | string | Next renewal date (ISO `YYYY-MM-DD`)                       |
| `days_until`       | int    | Number of days from today until the renewal date (can be 0 or negative if overdue) |

Results are sorted by `renewal_date` ascending (earliest first).

### `POST /api/v1/subscriptions/{subscription_id}/email-alert`

Toggle the per-subscription email alert preference. When enabled, the
daily scheduler (`daily_scheduler()` in `app/subscription_alerts.py`)
includes this subscription in its renewal and price-hike email scans.

The subscription id must match the `sub-NNN` pattern (`sub-001`,
`sub-002`, …). Invalid ids return `404`.

Preferences are stored in-memory (survive across requests within a
process, but not across restarts).

#### Request body

```json
{"enabled": true}
```

| Field     | Type | Required | Description                     |
|-----------|------|----------|---------------------------------|
| `enabled` | bool | Yes      | `true` to enable, `false` to disable |

#### Example

```bash
curl -X POST "http://localhost:8000/api/v1/subscriptions/sub-001/email-alert" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

#### Response

```json
{"subscription_id": "sub-001", "enabled": true}
```

### `GET /api/v1/subscriptions/{subscription_id}/email-alert`

Read back the current email alert preference for a subscription. Returns
`enabled: false` by default (alerts off unless explicitly toggled on).

```bash
curl "http://localhost:8000/api/v1/subscriptions/sub-001/email-alert"
```

```json
{"subscription_id": "sub-001", "enabled": true}
```

> Both email-alert endpoints accept the tenant/role headers used across the
> product workspace (`x-tenant-id` defaults to `demo`, `x-role` to `admin`).
> The POST endpoint validates the `subscription_id` format and returns `404`
> for non-matching ids; the GET endpoint does not validate the format.

Both subscription endpoints accept the `x-tenant-id` / `x-role` headers used by the product workspace (defaults: `demo` / `admin`). See [docs/subscription-alerts.md](subscription-alerts.md) for detection rules, the daily scheduler, the email-alert toggle, and the Python API.

## Stored receipt endpoints

- `POST /api/v1/receipts` accepts `{"image_url": "https://..."}`, validates and downloads the image, runs OCR, stores the result, and returns HTTP 201 with `receipt_id` and parsed fields.
- `GET /api/v1/receipts` lists the tenant's receipts.
- `GET /api/v1/receipts/{receipt_id}` returns one receipt or HTTP 404.

All three endpoints require the product-workspace auth headers: `X-Tenant-ID`
(required — a missing or blank value returns 401) and `X-Role` (one of
`admin` / `reviewer` / `integrator` — anything else returns 403).

Receipts are stored in the same shared product store that backs the
`/product/*` workspace: an upload through `POST /api/v1/receipts` is
immediately visible in `GET /product/receipts` for the same tenant, and vice
versa. The store is tenant-scoped — a receipt created under one `X-Tenant-ID`
is never listed or fetched under another.

## Environment Variables (v0.6.0)

| Variable | Default | Description |
|---|---|---|
| `RECEIPTLENS_ENV` | `development` | Set to `production` to disable `/docs`, `/redoc` and `/openapi.json` (SEC-006). Any other value keeps docs enabled. |
| `LLM_API_KEY` | (empty) | API key for LLM categorization enrichment |
| `LLM_MODEL` | `gpt-4o-mini` | Model name for OpenAI-compatible endpoint |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | Base URL for OpenAI-compatible API |

## Verified quickstart

```bash
python -c "
from PIL import Image
from app.ocr import parse_receipt
import io
img = Image.new('RGB', (200, 100), color='white')
buf = io.BytesIO()
img.save(buf, format='PNG')
buf.seek(0)
r = parse_receipt(buf.getvalue())
print(r)
"
```

```bash
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/v1/parse-receipt \
  -F 'file=@<(python -c "
from PIL import Image
import io, sys
img = Image.new(\"RGB\", (200, 100), color=\"white\")
buf = io.BytesIO()
img.save(buf, format=\"PNG\")
buf.seek(0)
sys.stdout.buffer.write(buf.read())
")' | python -m json.tool
```

## Product work-queue deep links in v1.3.0

`GET /product/work-queue` returns an `action_url` for every actionable item. Values are workspace-local hash URLs and may include query parameters identifying the exact receipt, approval, or blocked field. Clients should preserve the complete value rather than reducing it to a view name.

Examples:

```text
#review?receipt=<receipt-id>
#receipts?receipt=<receipt-id>&field=cost_center
#approvals?approval=<approval-id>
```

## Batch Processing and Export Endpoints (v2)
## Forecast Endpoints

The forecast engine provides next-period spend forecasting, anomaly detection, and budget variance projection. Routes are defined in `app/forecast.py` and mounted under the `/forecasts` prefix.

### `GET /forecasts`

Return next-period spend forecast (overall + per category).

#### Query parameters

| Parameter    | Type   | Default    | Description                                                       |
|--------------|--------|------------|-------------------------------------------------------------------|
| `period`     | string | `monthly`  | Aggregation period: `weekly`, `monthly`, `yearly`                 |
| `category`   | string | `null`     | Filter to one category (omit for all categories + Overall)        |
| `horizon`    | int    | `1`        | Number of periods ahead to forecast                               |
| `date_from`  | string | `null`     | Start date filter `YYYY-MM-DD`                                    |
| `date_to`    | string | `null`     | End date filter `YYYY-MM-DD`                                      |

#### Example

```bash
curl "http://localhost:8000/forecasts?period=monthly&category=Meals"
```

#### Response

```json
{
  "period": "monthly",
  "currency": "USD",
  "forecasts": [
    {
      "category": "Meals",
      "next_period_total": 8.5,
      "confidence_low": 8.5,
      "confidence_high": 8.5,
      "trend": 0.0,
      "method": "moving_average_trend"
    }
  ],
  "source_range": {
    "date_from": "2026-01-15",
    "date_to": "2026-07-04"
  }
}
```

When `category` is omitted, the response includes one entry per category plus an `Overall` entry aggregating all categories.

Each forecast entry contains:

| Field                | Type   | Description                                                              |
|----------------------|--------|--------------------------------------------------------------------------|
| `category`           | string | Category name (or `"Overall"`)                                           |
| `next_period_total`  | float  | Point estimate for next-period spend                                     |
| `confidence_low`     | float  | Lower 95% confidence bound                                               |
| `confidence_high`    | float  | Upper 95% confidence bound                                               |
| `trend`              | float  | Linear trend slope per period (positive = increasing spend)              |
| `method`             | string | Always `"moving_average_trend"` (trailing MA + least-squares extrapolation) |

### `GET /forecasts/anomalies`

Return detected spending anomalies for the given period.

#### Query parameters

| Parameter    | Type   | Default    | Description                                                       |
|--------------|--------|------------|-------------------------------------------------------------------|
| `period`     | string | `monthly`  | Aggregation period (detector always works over monthly buckets)   |
| `method`     | string | `zscore`   | Scoring method: `zscore` (mean/stddev) or `mad` (median/MAD)     |
| `threshold`  | float  | `2.0`      | Deviation cutoff — entries with `score >= threshold` are flagged  |
| `date_from`  | string | `null`     | Start date filter `YYYY-MM-DD`                                    |
| `date_to`    | string | `null`     | End date filter `YYYY-MM-DD`                                      |

#### Example

```bash
curl "http://localhost:8000/forecasts/anomalies?method=zscore&threshold=2.0"
```

#### Response

```json
{
  "method": "zscore",
  "threshold": 2.0,
  "anomalies": [
    {
      "period": "2026-03",
      "category": "Groceries",
      "expected": 320.50,
      "actual": 510.20,
      "score": 2.45,
      "flagged": true
    }
  ]
}
```

Each anomaly entry contains:

| Field      | Type   | Description                                                        |
|------------|--------|--------------------------------------------------------------------|
| `period`   | string | Period bucket (e.g. `2026-03` for monthly)                        |
| `category` | string | Category name                                                      |
| `expected` | float  | Baseline expected spend (leave-one-out mean for z-score, median for MAD) |
| `actual`   | float  | Actual spend in that period                                        |
| `score`    | float  | Deviation score (>= threshold means flagged)                       |
| `flagged`  | bool   | `true` if `score >= threshold`                                     |

Categories with fewer than 2 periods of data are excluded (no baseline to deviate from).

### `GET /forecasts/budget-variance`

Return projected budget variance with expected overage.

#### Query parameters

| Parameter  | Type   | Default | Description                                                    |
|------------|--------|---------|----------------------------------------------------------------|
| `period`   | string | `null`  | Filter to one period: `weekly`, `monthly`, `yearly` (null = all) |
| `horizon`  | int    | `1`     | Number of periods ahead to project                             |

#### Example

```bash
curl "http://localhost:8000/forecasts/budget-variance?period=monthly"
```

#### Response

```json
{
  "currency": "USD",
  "projections": [
    {
      "budget_id": "b_abc123",
      "category": "Meals & Entertainment",
      "period": "monthly",
      "budgeted": 500.00,
      "projected_spend": 620.00,
      "expected_overage": 120.00,
      "status": "over_budget"
    }
  ]
}
```

Each projection entry contains:

| Field               | Type   | Description                                                              |
|---------------------|--------|--------------------------------------------------------------------------|
| `budget_id`         | string | Budget identifier (matches `BudgetStore` id)                             |
| `category`          | string | Budget category                                                          |
| `period`            | string | Budget period (`weekly`, `monthly`, `yearly`)                            |
| `budgeted`          | float  | Budget amount                                                            |
| `projected_spend`   | float  | Projected spend = `spent / fraction_elapsed × horizon`                   |
| `expected_overage`  | float  | `projected_spend - budgeted` (positive = over budget)                    |
| `status`            | string | `on_track`, `warning` (>= alert threshold), or `over_budget` (>= 100%)  |

Projections use the same item-category matching as `BudgetStore._recompute` so they agree with the dashboard's spent/remaining figures.

### `GET /dashboard`

Server-rendered forecast dashboard (HTML). No JavaScript or remote assets — follows the same self-contained pattern as `GET /`.

```bash
curl "http://localhost:8000/dashboard"
```

Returns an HTML page with:
- Overall next-month spend summary
- Per-category forecast cards with confidence bounds and trend
- Inline SVG bar chart of category forecasts
- Flagged anomalies table
- Budget variance table with on_track / warning / over_budget status

## Batch Processing and Export Endpoints (v2)

These endpoints are defined in `app/api_v2.py` and mounted on the `/api/v1` prefix.

### `POST /api/v1/receipts/batch`

Parse multiple receipts in parallel with language selection and configurable workers.
Accepts multipart `files` uploads or a JSON `image_urls` array.

#### Request parameters (form fields)

| Field         | Type   | Required | Default | Description                                         |
|---------------|--------|----------|---------|-----------------------------------------------------|
| `files`       | file[] | No       | --      | Multipart receipt image uploads                     |
| `image_urls`  | string | No       | --      | JSON array of public image URLs                     |
| `lang`        | string | No       | `eng`   | Language code: `eng`, `deu`, `fra`, `spa`, `ita`, `por` |
| `webhook_url` | string | No       | --      | URL to POST results to on completion                |
| `max_workers` | int    | No       | `4`     | Parallel OCR threads (1--8)                         |

Either `files` or `image_urls` must be provided. Do not send both.

#### Example: file uploads

```bash
curl -X POST "http://localhost:8000/api/v1/receipts/batch" \
  -F "files=@receipt1.jpg" \
  -F "files=@receipt2.jpg" \
  -F "lang=deu" \
  -F "max_workers=8"
```

#### Example: URL array

```bash
curl -X POST "http://localhost:8000/api/v1/receipts/batch" \
  -F 'image_urls=["https://example.com/r1.jpg","https://example.com/r2.jpg"]' \
  -F "lang=fra"
```

#### Response

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "total": 2
}
```

Processing runs in the background. Poll progress with `GET /api/v1/receipts/batch/{job_id}`.

### `GET /api/v1/receipts/batch/{job_id}`

Poll batch processing progress and results.

#### Example

```bash
curl "http://localhost:8000/api/v1/receipts/batch/550e8400-e29b-41d4-a716-446655440000"
```

#### Response (in progress)

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "total": 2,
  "completed": 1,
  "failed": 0,
  "progress": 0.5,
  "results": [
    {
      "index": 0,
      "vendor": "COFFEE SHOP",
      "total": 12.50,
      "date": "2026-03-14",
      "currency": "EUR",
      "line_items": [{"name": "Latte", "price": 5.50}],
      "error": null
    }
  ],
  "errors": [],
  "created_at": "2026-08-01T12:00:00+00:00",
  "webhook_url": null
}
```

#### Response (completed)

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "total": 2,
  "completed": 2,
  "failed": 0,
  "progress": 1.0,
  "results": [ "..." ],
  "errors": [],
  "created_at": "2026-08-01T12:00:00+00:00",
  "webhook_url": null
}
```

#### Response (not found)

```json
{
  "job_id": "unknown-id",
  "status": "not_found",
  "total": 0,
  "completed": 0
}
```

### `GET /api/v1/receipts/export/{format}`

Export receipts to an accounting-compatible CSV format. Returns `text/csv`.

#### Path parameter

| Parameter | Type   | Values                             |
|-----------|--------|------------------------------------|
| `format`  | string | `quickbooks`, `xero`, `generic`    |

#### Query parameters (optional)

| Parameter   | Type   | Description                    |
|-------------|--------|--------------------------------|
| `date_from` | string | Start date filter `YYYY-MM-DD` |
| `date_to`   | string | End date filter `YYYY-MM-DD`   |
| `category`  | string | Category filter                |

#### Example

```bash
curl "http://localhost:8000/api/v1/receipts/export/quickbooks" -o export.csv

curl "http://localhost:8000/api/v1/receipts/export/xero?date_from=2026-01-01&date_to=2026-06-30"
```

#### Response

Returns a CSV file with headers matching the chosen format. See [docs/accounting-export-guide.md](accounting-export-guide.md) for column mappings and import instructions.

```csv
Date,Transaction Type,Num,Name,Memo,Account,Debit,Credit,Currency
2026-03-14,,,,,,,12.50,EUR
```

### `GET /api/v1/receipts/export/formats`

List all available export formats and their column definitions.

#### Example

```bash
curl "http://localhost:8000/api/v1/receipts/export/formats"
```

#### Response

```json
{
  "formats": [
    {
      "name": "quickbooks",
      "columns": ["Date", "Transaction Type", "Num", "Name", "Memo", "Account", "Debit", "Credit", "Currency"],
      "delimiter": ","
    },
    {
      "name": "xero",
      "columns": ["Date", "Contact", "Description", "Quantity", "Unit Price", "Amount", "Tax Rate", "Tax Amount", "Account Code", "Currency Code"],
      "delimiter": ","
    },
    {
      "name": "generic",
      "columns": ["Date", "Merchant", "Category", "Description", "Amount", "Currency", "Tax"],
      "delimiter": ","
    }
  ]
}
```

## Product workspace endpoints (connections, automation rules, export runs)

All product workspace endpoints require the demo auth headers `X-Tenant-ID` (default `demo`) and `X-Role` (`admin` | `reviewer` | `integrator`, default `admin`). A missing tenant header returns `401`; an unknown role returns `403`. These headers are a demo identity mechanism, not a production authentication system.

### `GET /product/connections`

List the accounting connections configured for the tenant.

#### Example

```bash
curl -H "X-Tenant-ID: demo" -H "X-Role: admin" \
  "http://localhost:8000/product/connections"
```

#### Response

```json
{
  "items": [
    {
      "connection_id": "0f5f2b3e-...",
      "name": "CSV Ledger",
      "provider": "csv",
      "mapping": {"vendor": "vendor", "total": "total", "currency": "currency"},
      "active": true
    }
  ]
}
```

Each item carries `connection_id`, `name`, `provider` (`csv` | `quickbooks` | `xero`), `mapping` (field-name mapping, always includes `vendor`, `total`, `currency`) and `active`.

### `POST /product/connections`

Create a new accounting connection.

#### Request body

```json
{
  "name": "CSV Ledger",
  "provider": "csv",
  "mapping": {"vendor": "vendor", "total": "total", "currency": "currency"}
}
```

- `name` — display name (required)
- `provider` — one of `csv`, `quickbooks`, `xero`; anything else returns `422`
- `mapping` — object that must contain at least `vendor`, `total`, `currency`; a missing key returns `422`

#### Example

```bash
curl -X POST -H "Content-Type: application/json" \
  -H "X-Tenant-ID: demo" -H "X-Role: admin" \
  -d '{"name":"CSV Ledger","provider":"csv","mapping":{"vendor":"vendor","total":"total","currency":"currency"}}' \
  "http://localhost:8000/product/connections"
```

#### Response (201)

```json
{
  "connection_id": "0f5f2b3e-...",
  "name": "CSV Ledger",
  "provider": "csv",
  "mapping": {"vendor": "vendor", "total": "total", "currency": "currency"},
  "active": true
}
```

Errors: `422` for an unsupported provider or an incomplete mapping; `403` when the role is not allowed.

### `POST /product/connections/{connection_id}/test`

Validate a stored connection. Returns `404` when the connection does not exist.

```bash
curl -X POST -H "X-Tenant-ID: demo" -H "X-Role: admin" \
  "http://localhost:8000/product/connections/{connection_id}/test"
```

```json
{"connection_id": "0f5f2b3e-...", "status": "ok", "provider": "csv"}
```

### `GET /product/automation-rules`

List the tenant's automation rules, ordered by priority then name.

#### Example

```bash
curl -H "X-Tenant-ID: demo" -H "X-Role: admin" \
  "http://localhost:8000/product/automation-rules"
```

#### Response

```json
{
  "items": [
    {
      "rule_id": "04526a2a-...",
      "name": "SBB travel",
      "conditions": {"vendor_contains": "SBB", "min_total": 20.0},
      "actions": {"tags": ["travel"], "cost_center": "tr-01"},
      "priority": 100,
      "active": true
    }
  ]
}
```

### `POST /product/automation-rules`

Create an automation rule that applies actions to matching receipts.

#### Request body

```json
{
  "name": "SBB travel",
  "conditions": {"vendor_contains": "SBB", "currency": "CHF", "min_total": 20.0, "max_total": 500.0},
  "actions": {"tags": ["travel"], "project": "consulting", "cost_center": "tr-01", "request_approval": true},
  "priority": 100
}
```

#### Supported keys

- `conditions` (all optional): `vendor_contains`, `currency`, `min_total`, `max_total`
- `actions` (all optional): `tags`, `project`, `cost_center`, `request_approval`
- `priority` (optional, default `100`) — lower runs first; ties break by name

#### Example

```bash
curl -X POST -H "Content-Type: application/json" \
  -H "X-Tenant-ID: demo" -H "X-Role: admin" \
  -d '{"name":"SBB travel","conditions":{"vendor_contains":"SBB"},"actions":{"tags":["travel"]}}' \
  "http://localhost:8000/product/automation-rules"
```

#### Response (201)

```json
{
  "rule_id": "04526a2a-...",
  "name": "SBB travel",
  "conditions": {"vendor_contains": "SBB"},
  "actions": {"tags": ["travel"]},
  "priority": 100,
  "active": true
}
```

#### Validation errors (422)

The error message names the offending key(s) and the supported sets, e.g.:

```json
{
  "detail": "invalid rule: unsupported condition key(s) ['bad_key']; supported conditions are ['currency', 'max_total', 'min_total', 'vendor_contains']"
}
```

An empty/whitespace-only `name` returns `422` with `invalid rule: name is required`.

### `POST /product/automation-rules/preview`

Dry-run how many receipts would match the given conditions (no rule is stored).

```bash
curl -X POST -H "Content-Type: application/json" \
  -H "X-Tenant-ID: demo" -H "X-Role: admin" \
  -d '{"name":"preview","conditions":{"vendor_contains":"SBB"},"actions":{"tags":["travel"]}}' \
  "http://localhost:8000/product/automation-rules/preview"
```

```json
{"matching_receipts": 3}
```

### `GET /product/export-runs`

List the tenant's export runs (legacy connection exports plus workflow exports), newest first.

#### Example

```bash
curl -H "X-Tenant-ID: demo" -H "X-Role: admin" \
  "http://localhost:8000/product/export-runs"
```

#### Response

```json
{
  "items": [
    {
      "run_id": "9c1d4f2e-...",
      "tenant_id": "demo",
      "format": "quickbooks",
      "status": "completed",
      "requested": 3,
      "exported": 3,
      "errors": [],
      "created_at": "2026-08-11T12:00:00Z"
    }
  ]
}
```

Each item includes `run_id`, `tenant_id`, `format`, `status`, `requested`/`exported` counts, `errors`, and `created_at`.

### `POST /product/export-runs`

Export a set of completed receipts through a connection. Creates the connection export and records an export run.

#### Request body

```json
{
  "connection_id": "0f5f2b3e-...",
  "receipt_ids": ["r-1", "r-2", "r-3"]
}
```

#### Example

```bash
curl -X POST -H "Content-Type: application/json" \
  -H "X-Tenant-ID: demo" -H "X-Role: admin" \
  -d '{"connection_id":"0f5f2b3e-...","receipt_ids":["r-1","r-2"]}' \
  "http://localhost:8000/product/export-runs"
```

#### Response (201)

```json
{
  "run_id": "9c1d4f2e-...",
  "status": "completed",
  "requested": 2,
  "exported": 2,
  "errors": []
}
```

A missing connection returns `404`-equivalent behavior with the run recorded as failed and `errors` populated.

### `GET /product/export-runs/{run_id}`

Fetch one export run's metadata. Returns `404` when the run does not exist.

```bash
curl -H "X-Tenant-ID: demo" -H "X-Role: admin" \
  "http://localhost:8000/product/export-runs/{run_id}"
```

### `GET /product/export-runs/{run_id}/artifact`

Download the run's CSV artifact. Returns `404` when the run does not exist.

```bash
curl -H "X-Tenant-ID: demo" -H "X-Role: admin" \
  "http://localhost:8000/product/export-runs/{run_id}/artifact" -o export.csv
```

## Review, quality, export, and automation workflow (1.5)

- `GET /product/review-items` accepts `confidence_field`, `confidence_lt`, `readiness`, `sort`, `limit`, and `offset`.
- `POST /product/export-preparations` snapshots validation and receipt versions.
- `POST /product/export-commands` requires `Idempotency-Key` and explicit warning receipt acknowledgements.
- `GET /product/export-runs/{run_id}` and `/artifact` return immutable run metadata and CSV.
- `GET /product/receipts/{receipt_id}/audit` returns tenant-scoped, redacted activity events.
- `POST /product/quality/benchmarks/run`, `GET /product/quality/benchmarks/{id}`, `POST /product/quality/confidence-profiles`, and `GET /product/quality/confidence-profiles/active` manage calibration.
- Versioned automation endpoints support preview, activation, runs, rollback preview, and rollback under `/product/automation-rules` and `/product/automation-runs`.

All product endpoints use `X-Tenant-ID` and `X-Role` demo headers. These headers are not a production identity system. Rate limits apply per tenant + client IP on the OCR and inbound-ingestion endpoints — see the [Rate limits](#rate-limits-sec-005) section at the top of this document.

## Inbound attachment and automation completion (1.6)

Inbound email attachment payloads may include `content_base64`. The service stores validated bytes, detected MIME type, SHA-256, sanitized filename, status, attempt count, receipt link, and a sanitized error code. Use `GET /product/inbound-emails/{email_id}` for details and `POST /product/inbound-emails/{email_id}/attachments/{attachment_id}/retry` for failed attachments. Quarantined attachments cannot be retried.

Versioned rule preview now returns `conflicts`, including receipt, target field, candidate values, priorities, winning rule, and winning value. Rule runs are listed at `GET /product/automation-rules/{rule_id}/runs`.

Configure browser origins with the comma-separated `RECEIPTLENS_ALLOWED_ORIGINS` environment variable. Wildcard credentialed origins are not supported.

## QuickBooks Online connected workflow (OAuth, refresh, revoke)

The QuickBooks Online integration connects a sandbox company through Intuit's OAuth2 Authorization Code flow with PKCE. Client credentials are read from `RECEIPTLENS_QBO_CLIENT_ID` / `RECEIPTLENS_QBO_CLIENT_SECRET`; the redirect URI defaults to `RECEIPTLENS_QBO_REDIRECT_URI` (`/product/connections/quickbooks/oauth/callback`). When the client secret is unset, the OAuth exchange fails fast with `502 oauth_exchange_failed` rather than leaking a placeholder credential.

### OAuth lifecycle

- `POST /product/connections/quickbooks/oauth/start` — admin only (`X-Role: admin`). Body: `{"return_path": "/integrations"}`. Returns `authorization_url` (Intuit's `appcenter.intuit.com/connect/oauth2` endpoint with a single-use, tenant-bound, 10-minute `state` token and an RFC 7636 S256 PKCE `code_challenge`) and `state_expires_at`. Any other `return_path` is rejected (`422`). The PKCE verifier is stored encrypted-side along with the state and is required at exchange time, so the authorize URL can never be replayed against the token endpoint.
- `GET|POST /product/connections/quickbooks/oauth/callback` — the browser redirect target. Query params: `state`, `code`, `realmId` (the QuickBooks company id; required, else `422 realm_required`). The tenant is derived from the single-use state token, so no tenant headers are required on this route. The state is validated **before** any token exchange; the authorization code is exchanged at Intuit's fixed token endpoint together with the stored PKCE verifier, and the resulting tokens are stored AES-GCM encrypted. The state token is consumed on success and can never be replayed. Returns `{"status": "connected", "redirect": "/integrations"}`; never returns token material.
  - `422 oauth_state_invalid` — unknown, expired, or already-consumed state (rejected before any Intuit call).
  - `502 oauth_exchange_failed` — Intuit rejected the exchange (bad/expired code, misconfigured client, missing client secret).

### Connections

- `GET /product/provider-connections` — list tenant connections (`connection_id`, provider, company id/name, health, `reauthorization_required`, timestamps).
- `GET /product/provider-connections/{connection_id}` — single connection detail; `404` when missing.
- `POST /product/connections/{connection_id}/test` — validates the stored access token against the provider and refreshes health/company name. `404` when missing.
- `POST /product/connections/{connection_id}/refresh` — rotates an expiring access token via Intuit's refresh flow. Returns `{"status": "refreshed"}` or `{"status": "not_needed"}` when the token still has >5 minutes of life. On refresh failure the connection is flipped to `reauthorization_required` and `409 reauthorization_required` is returned so the UI can prompt for re-connect. `404` when the connection does not exist.
- `POST /product/connections/{connection_id}/disconnect` — admin only. Performs a best-effort Intuit revoke with the stored refresh token, then deletes the local credentials and marks the connection `disconnected`. Revoke failure does not block the local disconnect (Intuit may already have invalidated the token).

### Mappings

- `POST /product/connections/{connection_id}/mappings` — save an immutable mapping version (`expense_account_ref`, `tax_strategy`, `snapshot_hash`); admin only. `404` when the connection is missing.
- `GET /product/connections/{connection_id}/mappings/current` — latest mapping version for the connection; `404` when none exists.
- `POST /product/provider-mappings/validate` — validates a proposed mapping against the provider's active account references and returns a `snapshot_hash` to pin before saving.

All product endpoints use `X-Tenant-ID` and `X-Role` demo headers (except the OAuth callback, which authenticates via the single-use state token). These headers are not a production identity system.

## Household auth (F1.3, US-024)

The consumer-pivot Family product (docs/plans/consumer-pivot-2026-08-13.md §2.3) needs real, password-less identity. The `X-Tenant-ID` / `X-Role` headers remain usable **in development only** (`RECEIPTLENS_ENV != production`); when a real household session is present it always wins.

### Identity model

- A household = a tenant. Roles: `owner` (Háztartás tulajdonosa), `adult` (Felnőtt tag), `child` (Gyermek / korlátozott tag), `view_only` (Csak megtekintés).
- Sessions are issued by magic-link login or invite acceptance and travel as `Authorization: Bearer <session_token>`. Tokens are stored sha256-hashed; a session lasts 30 days.
- Magic-link tokens last 15 minutes, invite tokens 7 days; both are single-use and invalidated on first use (or expiry).

### `POST /auth/magic-link-request`

Body: `{"email": "..."}`. Creates a single-use magic-link token for the email and delivers it:

- When SMTP is configured (`RECEIPTLENS_SMTP_HOST` set and `RECEIPTLENS_SMTP_ENABLED=1`), the link is sent via the existing `send_email_notification()` channel.
- Otherwise, in dev mode (`RECEIPTLENS_ENV != production`) the response includes `magic_link` and `token` so the UI flow is testable without a mail server. **In production the raw token is never returned** — the response is `{"delivered": false, "detail": "Email delivery is not configured"}`.

`201` with `{email, expires_at, delivered, magic_link?, token?}`. A caller-supplied `household_id` is **not honored** (the field is rejected/ignored): binding a magic link to an arbitrary household without proof of membership would mint an owner session for that household (CRITICAL-1). A fresh household is always derived from the email at verify time; joining an existing household goes through the owner-issued invite flow.

### `POST /auth/magic-link-verify`

Body: `{"token": "..."}`. Consumes the token and establishes a session. `201` with `{session_token, email, household_id, role, expires_at}`. Unknown / expired / already-used tokens: `401`.

### `POST /auth/session/me`

Body: `{"session_token": "..."}`. Resolves a session into `{tenant_id, role, email?, ...}`; `401` on bad/expired session.

### Family invites

- `POST /auth/households/{household_id}/invites` — owner only. Body: `{"email": "...", "role": "adult|child|view_only"}` (role pattern enforced; `owner` is rejected on invites — a household has exactly one owner). Non-owner caller: `403`. The email link embeds the household + invite ids: `{base}/auth/invite?token=...&household={household_id}&invite={invite_id}`. `201` with `{invite_id, email, role, status, expires_at, delivered, magic_link?, token?}` (dev-mode link return same as magic link).
- `GET /auth/households/{household_id}/invites` — owner only. `200` with `{items: [...]}` pending invites.
- `POST /auth/households/{household_id}/invites/{invite_id}/accept` — body: `{"token": "..."}`. Validates the invite token matches the household+invite path **before** the token is consumed (a wrong path returns `401`/`404` without burning the token), creates the membership and signs the user in. `201` with `{session_token, email, household_id, role, expires_at}`. Unknown/expired/used invite: `401`; mismatched path: `401`/`404`.

### Role gates

Write-gated endpoints (`child`/`view_only` get `403`): `POST /product/receipts/upload`, `PATCH /product/review-items/{receipt_id}`, `PATCH /product/receipts/{receipt_id}/workspace`, `PUT /product/receipts/{receipt_id}/metadata`, `PUT /product/receipts/{receipt_id}/line-items`, `POST /product/connections`, `POST /product/exports`, `POST /product/export-runs`, `POST /product/export-commands`, `POST /product/export-preparations`, `POST /product/receipts/{receipt_id}/approval`, `POST /product/jobs/{job_id}/retry`, `POST /product/jobs/{job_id}/cancel`, `POST /product/saved-views`, `DELETE /product/saved-views/{view_id}`, `POST /product/notifications/read-all`, `PATCH /product/notifications/{notification_id}`, `POST /product/automation-rules`, `POST /product/automation-rules/preview`, `POST /product/duplicates/decision`, `PUT /product/preferences`, `POST /product/inbound-emails`, `POST /product/approval-flows`, `POST /product/approval-flows/simulate`, `POST /product/recurring-expenses/feedback`, `POST /product/exchange-rates`, `POST /product/currency/convert`, `PUT /product/permissions`, `POST /product/quality/benchmarks/run`, `POST /product/quality/confidence-profiles`, `POST /product/automation-rules/{id}/preview|activate|runs`, `POST /product/automation-runs/{id}/rollback-preview|rollback`, `POST /product/connections/quickbooks/oauth/start`, `POST /product/connections/{id}/refresh|disconnect|mappings`, `POST /product/provider-mappings/validate`, `POST /product/receipts/{id}/accounting-projection/refresh` — `owner`/`adult` may write; `child`/`view_only` get `403`.
- `POST /product/members` (invite creation) — only the household owner may add members; any other role `403`.
- Legacy `X-Role: admin|reviewer|integrator` dev headers map to the RESTRICTED household roles `adult`/`adult`/`child` — the demo header auth never grants owner-equivalent power (CRITICAL-2): header actors can write receipts but cannot manage the household roster.

### Dev-mode compatibility (AC6)

`actor()` (product workspace) and `api_v1_actor()` (v1) resolve identity in this order: `Authorization: Bearer` session → legacy `X-Tenant-ID`/`X-Role` headers (dev only) → `401` when nothing valid. In production the headers are rejected entirely (`401 Session required`), so the demo auth can never be used against a live deployment.
