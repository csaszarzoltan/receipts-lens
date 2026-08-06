# API Reference

# Böngészős kezdőoldal

A `GET /` egy magyar nyelvű, reszponzív szolgáltatási főoldalt ad vissza. A főoldal az alkalmazás nevét és verzióját dinamikusan a FastAPI metadata alapján jeleníti meg, linket ad a Swagger UI és ReDoc dokumentációhoz, valamint rövid feltöltési példát tartalmaz. A route nem része az OpenAPI sémának, mert emberi navigációs felület, nem integrációs API.



The FastAPI application is exposed as `app.api.app`.

```bash
uvicorn app.main:app --reload
```

## Endpoints

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

## Stored receipt endpoints

- `POST /api/v1/receipts` accepts `{"image_url": "https://..."}`, validates and downloads the image, runs OCR, stores the result, and returns HTTP 201 with `receipt_id` and parsed fields.
- `GET /api/v1/receipts` lists the current in-memory store.
- `GET /api/v1/receipts/{receipt_id}` returns one receipt or HTTP 404.

The current store is process-local and is cleared when the server restarts. It is intended for development and demonstration, not durable production storage.

## Environment Variables (v0.6.0)

| Variable | Default | Description |
|---|---|---|
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
