# ReceiptLens

ReceiptLens is a self-hostable receipt intelligence workspace for small businesses and bookkeepers. It turns receipt images into confidence-scored structured data, guides reviewers to uncertain fields, validates accounting readiness, and produces auditable exports without hiding OCR uncertainty.

## What you can do

- Capture receipts by upload, URL, batch, or simulated inbound email.
- Review low-confidence fields alongside the original image and OCR source boxes.
- Correct data with optimistic concurrency and an immutable activity history.
- Validate mandatory fields, tax, line totals, currency, and export readiness.
- Create immutable export preparations and replay-safe CSV export commands.
- Benchmark OCR confidence, publish tenant threshold profiles, and focus the review queue.
- Preview versioned automation rules, activate them deliberately, record runs, and roll back eligible changes.
- Inspect inbound email attachments individually, retry failed OCR, and safely quarantine unsupported or mismatched files.
- Review automation conflicts with a deterministic winning rule before activation.
- Run locally with Tesseract, or opt into vision OCR with an OpenAI-compatible endpoint.

## Product surfaces

The **Next.js workspace** in `frontend/` is the primary user interface. The FastAPI service provides the product API, Swagger documentation, health probes, and the compatibility `/workspace` interface. Tenant and role headers are convenient demo controls, not production authentication.

## Quick start

```bash
# System dependency: install Tesseract OCR first.
python -m venv .venv
. .venv/bin/activate
pip install -e .
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd frontend
npm ci
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

Open `http://127.0.0.1:3000`. API documentation is available at `http://127.0.0.1:8000/docs`.

## Primary workflow

1. Upload or receive receipt documents.
2. Open **Review** and filter by readiness, confidence field, threshold, or amount.
3. Verify extracted values against the source image and correct exceptions.
4. Complete review, create an export preparation, and resolve blockers.
5. Acknowledge warnings explicitly and execute an idempotent CSV export.
6. Inspect receipt history, export runs, quality reports, and reversible automation runs.

## Browser security configuration

Set `RECEIPTLENS_ALLOWED_ORIGINS` to a comma-separated list of trusted frontend origins. The local development default permits `http://localhost:3000`/`http://127.0.0.1:3000` (Next.js dev server) and `http://localhost:3010`/`http://127.0.0.1:3010` (Playwright E2E stack).

## Verification

```bash
pytest -q
ruff check app tests
cd frontend && npm run typecheck && npm run build
```

See `docs/api.md`, `docs/product-workflows.md`, `docs/accounting-export-guide.md`, and `docs/gui-workspace.md` for focused guidance. See `development-report.md` for the exact evidence from the latest development pass.

## Features

- **Receipt OCR** — runs Tesseract 5 on uploaded images with automatic pre-processing (grayscale, upscale, contrast, sharpen).
- **Structured output** — parses merchant, date, line items, subtotal, tax, and total from raw OCR text with regex heuristics.
- **Confidence scores** — every field includes a `confidence` float between 0.0 and 1.0, derived from Tesseract `image_to_data` accuracy metrics.
- **OCR pipeline library** — use `app.ocr` and `app.preprocessing` as a Python library, no server required. See [Library Usage](#library-usage).
- **Image preprocessing** — automatic EXIF orientation correction, deskew via projection profiles, adaptive thresholding, and contrast/sharpen enhancements. All stages configurable.
- **Magic byte validation** — rejects non-image files before PIL decode (JPEG, PNG, TIFF, BMP, WEBP, GIF).
- **Typed exceptions** — `InvalidImageError`, `UnsupportedImageFormatError`, and `CorruptImageError` map to HTTP 400/415/422.
- **Async processing** — queue long-running OCR jobs with `POST /v1/parse-receipt/async`, poll with `GET /v1/jobs/{job_id}`, and receive a webhook callback on completion.
- **Batch processing (API)** — parse multiple receipts in one call with `POST /v1/parse-receipts` for file uploads or `image_urls`, plus async batch jobs via `POST /v1/parse-receipts/async`. Enhanced batch endpoint at `POST /api/v1/receipts/batch` with language selection and parallel workers.
- **Multi-language OCR** — supports English, German, French, Spanish, Italian, and Portuguese. Locale-aware decimal separators, date formats, and currency defaults. Auto-detection via `detect_language()`. See [docs/multi-language-guide.md](docs/multi-language-guide.md).
- **AI Vision OCR (AI Scan)** — optional LLM vision extraction for blurry photos, handwritten amounts, and unusual layouts, with automatic Tesseract fallback when the vision path is unavailable or fails. Enabled via `VISION_OCR_ENABLED` + `LLM_API_KEY`; `ai_scan=true` on upload endpoints. See [docs/ai-vision-ocr.md](docs/ai-vision-ocr.md).
- **Batch processing CLI** — `receipts-lens batch --dir ./receipts --lang deu --export quickbooks` processes a directory of receipt images in parallel with configurable workers. See [CLI Usage](#cli-usage).
- **Accounting export** — export parsed receipts to QuickBooks, Xero, or generic CSV formats via `GET /api/v1/receipts/export/{format}` or CLI. Column mappings and import instructions in [docs/accounting-export-guide.md](docs/accounting-export-guide.md).
- **URL-based input** — pass a public image URL instead of uploading a file. Works in single, batch, and async modes.
- **SSRF guard** — URL validation and DNS-resolution checks block requests to private/reserved IP ranges (RFC 1918, link-local, metadata endpoints). Follows redirects safely through the same validation.
- **Duplicate detection** — `POST /v1/check-duplicates` compares parsed receipts by vendor similarity and total proximity, returning candidate groups with confidence scores.
- **Configurable resource limits** — `MAX_IMAGE_BYTES` (20 MB) and `URL_FETCH_TIMEOUT` (30 s) cap image downloads (constants in `app/api.py`).
- **Flexible input** — accepts a multipart `file` upload or an `image_url` form field, in single or batch mode.
- **FastAPI service** — async endpoint with `/health`, OpenAPI docs, and strict type hints.
- **Health endpoint** — `GET /health` returns `{"status":"ok"}` for load-balancer probes.
- **AI categorization** — `POST /api/v1/categorize` auto-classifies receipts by vendor name using keyword/regex rules. Optional LLM enrichment via OpenAI-compatible API. See [docs/categorization.md](docs/categorization.md).
- **Budget management** — full CRUD for per-category monthly budgets with real-time spending tracking. Endpoints at `POST/GET/PUT/DELETE /api/v1/budgets`. See [docs/budgets-and-analytics.md](docs/budgets-and-analytics.md).
- **Spending analytics** — aggregate spending by category, merchant, day, or month. Compare budgets vs actuals. Endpoints at `GET /api/v1/analytics/spending` and `GET /api/v1/analytics/budgets`.
- **Alert system** — automatic threshold-based alerts when spending approaches or exceeds budget limits. Also detects unusual spending patterns. Endpoints at `GET /api/v1/alerts` and `POST /api/v1/alerts/{id}/acknowledge`. See [docs/alerts.md](docs/alerts.md).
- **Subscription intelligence** — proactive email alerts for upcoming renewals (7-day window), price-hike detection (>10% over rolling average), spending trend dashboard (inline SVG chart with trend direction), renewal timeline with countdown, per-subscription email alert toggle, and merchant-specific cancellation guides for 20+ brands. Daily scheduler scans all subscriptions and sends alerts via SMTP when configured. Endpoints at `GET /api/v1/subscriptions`, `GET /api/v1/subscriptions/trend-data`, `GET /api/v1/subscriptions/renewal-timeline`, `POST/GET /api/v1/subscriptions/{id}/email-alert`, and `GET /api/v1/subscriptions/{id}/cancel-guide`. Requires `RECEIPTLENS_SMTP_ENABLED=1` + SMTP config for email delivery. See [docs/subscription-alerts.md](docs/subscription-alerts.md).
- **Forecast engine** — next-period spend forecasting with per-category and overall predictions, confidence bounds, anomaly detection (z-score / MAD), and budget variance projection. REST endpoints at `GET /forecasts`, `GET /forecasts/anomalies`, `GET /forecasts/budget-variance`. Dashboard at `GET /dashboard`. CLI: `receipts-lens forecast --period monthly`.
- **Receipt operations** — tenant-scoped search, tags, projects, cost centers, threshold approvals, retention purge, and versioned portability export.
- **Precise daily actions** — dashboard tasks deep-link to the exact review receipt, approval, or blocked accounting field instead of opening only a general module.
- **Accessible consequential actions** — approval decisions, API-key creation, saved-view naming, and retention purge use contextual dialogs with inline validation, focus handling, and described consequences.
- **Early accounting readiness** — receipt rows show baseline blocked/warning/exportable state and can be filtered before export preparation.
- **Tested** — 1266 pytest tests (1256 passed, 10 skipped) across 52 test files; the packaged delivery records the exact passing and skipped counts in `TEST_RESULTS.txt`.

---

## Research requirements implementation

The capabilities specified in `docs/research/REQUIREMENTS_01` through `REQUIREMENTS_04` now have executable reference implementations:

- `app/platform.py`: durable tenant data plane, jobs, idempotency and outbox;
- `app/governance.py`: authentication port, role checks, quota, webhook signatures and audit chain;
- `app/quality.py`: benchmark, confidence calibration, review and correction provenance;
- `app/integrations.py`: accounting connector contract, safe CSV export and usage metering.

See `docs/research/REQUIREMENTS_IMPLEMENTATION_REPORT.md` for deployment boundaries.

## Product workspace and workflows

ReceiptLens now includes a browser-based upload workspace at `/workspace` and tenant-aware APIs for receipt history, review corrections, teams, API keys, accounting connections, exports, and the trust dashboard. See [docs/product-workflows.md](docs/product-workflows.md), [docs/gui-workspace.md](docs/gui-workspace.md), [docs/accounting-readiness-v1.1.md](docs/accounting-readiness-v1.1.md), [docs/NEXT_VERSION_PRODUCT_UX_REQUIREMENTS.md](docs/NEXT_VERSION_PRODUCT_UX_REQUIREMENTS.md), and [docs/IMPLEMENTATION_DELIVERY_REPORT_V1.3.md](docs/IMPLEMENTATION_DELIVERY_REPORT_V1.3.md) for workflows, requirements, delivery scope, persistence, endpoints, and production boundaries.

## Webes főoldal

A szerver gyökércíme (`http://127.0.0.1:8000/`) egy önálló, reszponzív információs főoldalt jelenít meg. A főoldalon látható a ReceiptLens verziója és állapota, a támogatott műveletek áttekintése, egy PowerShell feltöltési példa, valamint közvetlen hivatkozás a `/docs`, `/redoc` és `/health` oldalakra. A főoldal nem használ JavaScriptet vagy külső webes erőforrást.

## Windows quickstart

A részletes magyar Windows telepítési, tesztelési és használati útmutató: [docs/WINDOWS_GUIDE_HU.md](docs/WINDOWS_GUIDE_HU.md).

## Getting Started

### Prerequisites

- Python 3.11+
- Tesseract OCR 5.x with the English language pack

### Installation

```bash
# System dependency (Tesseract binary)
# Debian/Ubuntu:
sudo apt install tesseract-ocr tesseract-ocr-eng

# macOS:
brew install tesseract

# Python dependencies
pip install -e .
# Installs: pillow, pytesseract, fastapi, uvicorn, pydantic, httpx, python-multipart
```

### Running the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The server listens on `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive OpenAPI playground.

### AI Scan setup (optional)

AI Scan is **off by default** — it sends receipt images to a paid LLM vision
endpoint, so enable it explicitly:

```bash
export LLM_API_KEY="sk-..."
export LLM_BASE_URL="https://api.openai.com/v1"  # OpenAI-compatible endpoint root (default)
export LLM_MODEL="gpt-4o-mini"                   # vision-capable model (default)
export VISION_OCR_ENABLED=1                      # cost guard — required to enable
export VISION_OCR_TIMEOUT=30.0                   # seconds (default)
```

Any OpenAI-compatible vision endpoint works (Azure OpenAI, Together,
OpenRouter, local vLLM/llama.cpp, ...). With the vision path enabled, send
`ai_scan=true` as a form field to `POST /v1/parse-receipt` or
`POST /product/receipts/upload`; the response then exposes `source`
(`"vision"` | `"tesseract"`) plus `ai_result` / `tesseract_result` payloads.
Without `VISION_OCR_ENABLED` / `LLM_API_KEY`, `ai_scan=true` requests fall
back to Tesseract (`"source": "tesseract"`) — no API key is required, only
vision results are. Full guide: [docs/ai-vision-ocr.md](docs/ai-vision-ocr.md).

```bash
# AI-mode upload with the vision path enabled
curl -X POST "http://localhost:8000/v1/parse-receipt" \
  -F "file=@/path/to/receipt.jpg" \
  -F "ai_scan=true"
```

---

## Deployment

### Live instance

ReceiptLens is deployed on Railway at:

**https://receiptslens-production.up.railway.app**

Health check: `GET https://receiptslens-production.up.railway.app/health` → `{"status":"ok"}`

Interactive API docs: **https://receiptslens-production.up.railway.app/docs**

---

### Deploy to Railway (primary)

Railway builds from the `infra/Dockerfile` and sets `PORT` automatically.

#### Prerequisites

- A [Railway](https://railway.app) account
- The [Railway CLI](https://docs.railway.app/develop/cli) (`npm i -g @railway/cli`)
- Your own fork or clone of the repo

#### One-click deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new?template=https://github.com/csaszarzoltan/receiptslens)

Clicking the button above creates a new Railway project linked to the upstream repo.
After deploy completes, Railway assigns a `.railway.app` domain — use `railway domain` to view it.

#### Manual deploy (CLI)

```bash
# 1. Clone the repository
git clone https://github.com/csaszarzoltan/receiptslens.git
cd receiptslens

# 2. Install Railway CLI and log in
npm i -g @railway/cli
railway login

# 3. Create a new project or link to an existing one
railway init
# or: railway link

# 4. Set required environment variables (if any — see table below)
railway variables --set PORT=8000

# 5. Deploy
railway up --dockerfile-path infra/Dockerfile

# 6. Get the public URL
railway domain
```

Railway automatically:
- Builds the Docker image using `infra/Dockerfile`
- Runs `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}` as the start command
- Polls `GET /health` for readiness (30 s timeout)
- Restarts the service on failure (up to 3 retries)

---

### Deploy to Fly.io (alternative)

Fly.io requires a `fly.toml` — one is not shipped with this repo. To deploy manually:

#### Prerequisites

- A [Fly.io](https://fly.io) account
- The [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/) (`flyctl`)

#### Steps

```bash
# 1. Clone the repository
git clone https://github.com/csaszarzoltan/receiptslens.git
cd receiptslens

# 2. Launch a new Fly app (creates fly.toml interactively)
flyctl launch --no-deploy

# 3. Set the Dockerfile path (answer "infra/Dockerfile" when prompted)
#    Or edit fly.toml to add:
#    [build]
#      dockerfile = "infra/Dockerfile"

# 4. Set environment variables
flyctl secrets set PORT=8000

# 5. Deploy
flyctl deploy

# 6. Open the app
flyctl open
```

The Fly.io `Dockerfile` pipeline picks up `infra/Dockerfile` automatically when `flyctl launch` is configured with the correct build section.

---

### Self-host with Docker

```bash
# Build the image (uses the multi-stage infra/Dockerfile)
docker build -t receiptslens -f infra/Dockerfile .

# Run the container (default port 8000)
docker run -p 8000:8000 receiptslens

# Override the port if needed
docker run -p 8080:8080 -e PORT=8080 receiptslens
```

The image is based on `python:3.11-slim` and includes Tesseract 5 OCR with the English language pack.
Image size is approximately 692 MB.

---

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `PORT` | No | `8000` | Server port for uvicorn. Railway sets this automatically; override for local or custom deployments. |
| `LLM_API_KEY` | No | *(empty)* | API key for the OpenAI-compatible endpoint. Used by AI Vision OCR (AI Scan) and AI categorization. |
| `LLM_BASE_URL` | No | `https://api.openai.com/v1` | Base URL of the OpenAI-compatible API. |
| `LLM_MODEL` | No | `gpt-4o-mini` | Vision-capable model name used by AI Scan. |
| `VISION_OCR_ENABLED` | No | *(off)* | Cost guard for AI Vision OCR — set to `1`/`true`/`yes`/`on` to enable the LLM vision path. Without it, `ai_scan=true` requests fall back to Tesseract. |
| `VISION_OCR_TIMEOUT` | No | `30.0` | Timeout in seconds for vision-LLM requests (float). |
| `RECEIPTLENS_SMTP_ENABLED` | No | *(off)* | Set to `1` to allow SMTP delivery of subscription alerts. SMTP connection settings are passed to `send_email_notification()` as a config dict (host / port / user / password / from_addr / to_addr) — see [docs/subscription-alerts.md](docs/subscription-alerts.md). |

The following variables are **declared in deployment configs** but not yet wired in the application code.
They are reserved for future use:

| Variable | Status | Default | Description |
|---|---|---|---|
| `CORS_ORIGINS` | Planned | — | Comma-separated allowed CORS origins |
| `AUTH_TOKEN` | Planned | — | Bearer token for API authentication |
| `TESSDATA_PREFIX` | Planned | auto-detected | Path to Tesseract data directory |

**Configurable constants** (edit `app/api.py` directly):

| Constant | Default | Description |
|---|---|---|
| `MAX_IMAGE_BYTES` | 20,000,000 (20 MB) | Maximum image download size from URLs |
| `URL_FETCH_TIMEOUT` | 30.0 s | Timeout for remote image fetches |

---

### Usage against the live API

All localhost examples in this document work identically against the live URL. Replace `http://localhost:8000` with the Railway URL:

```bash
curl -X POST "https://receiptslens-production.up.railway.app/v1/parse-receipt" \
  -F "file=@receipt.jpg"
```

```python
import requests

resp = requests.post(
    "https://receiptslens-production.up.railway.app/v1/parse-receipt",
    files={"file": open("receipt.jpg", "rb")},
)
print(resp.json())
```

Check service health:

```bash
curl https://receiptslens-production.up.railway.app/health
# {"status":"ok"}
```

Browse the interactive API docs at **https://receiptslens-production.up.railway.app/docs**.

---

## CLI Usage

ReceiptLens ships with a command-line tool for batch processing and export.

```bash
# Install (already done with `pip install -e .`)
receipts-lens --help
```

### Batch process a directory

```bash
# Process all images in ./receipts with English (default)
receipts-lens batch --dir ./receipts

# German receipts, export to QuickBooks CSV
receipts-lens batch --dir ./receipts-de --lang deu --export quickbooks --output results.csv

# 8 parallel workers, recursive subdirectory scan
receipts-lens batch --dir ./receipts --workers 8 --recursive --verbose
```

### Export to accounting CSV

```bash
# Export to QuickBooks format
receipts-lens export --format quickbooks

# Export to Xero format with date filter
receipts-lens export --format xero --date-from 2026-01-01 --date-to 2026-06-30

# Show supported languages and formats
receipts-lens info
```

| Option         | Default      | Description                                      |
|----------------|--------------|--------------------------------------------------|
| `--dir`        | (required)   | Directory of receipt images                      |
| `--lang`       | `eng`        | Tesseract language code                          |
| `--workers`    | `4`          | Parallel OCR threads (1–8)                       |
| `--export`     | `generic`    | Export profile: `generic`, `quickbooks`, `xero`  |
| `--output`     | `results.csv`| Output CSV file path                             |
| `--verbose`    | off          | Print progress details                           |
| `--recursive`  | off          | Scan subdirectories                              |

## Library Usage

ReceiptLens works as a Python library without starting the server. All functions accept raw image bytes.

### Basic OCR

```python
from app.ocr import extract_text

with open("receipt.jpg", "rb") as f:
    text = extract_text(f.read())
print(text)
```

### Structured parsing

```python
from app.ocr import parse_receipt

with open("receipt.jpg", "rb") as f:
    receipt = parse_receipt(f.read())

print("vendor :", receipt.merchant)
print("date   :", receipt.date)
print("total  :", receipt.total)
print("tax    :", receipt.tax)
print("items  :", [(i.name, i.price) for i in receipt.items])
```

### With confidence scores

```python
from app.ocr import parse_receipt_with_confidence

with open("receipt.jpg", "rb") as f:
    result = parse_receipt_with_confidence(f.read())

for field, score in result.confidence.items():
    print(f"{field}: {score:.2f}")
```

### Preprocessing only

```python
from app.preprocessing import preprocess_image

with open("receipt.jpg", "rb") as f:
    image = preprocess_image(f.read(), deskew=True)
# Returns a PIL.Image.Image ready for custom processing
```

### Error handling

```python
from app.ocr import extract_text
from app.exceptions import InvalidImageError

try:
    result = extract_text(b"not an image")
except InvalidImageError as e:
    print(f"Bad input: {e}")
except ValueError as e:
    print(f"Decode error: {e}")
```

### Preprocessing options

| Option | Default | Description |
|---|---|---|
| `deskew` | `True` | Detect and correct skew via projection profiles (±5° range, 0.5° steps) |

The preprocessing pipeline runs these stages in order:

1. EXIF orientation correction
2. Grayscale conversion
3. Deskew (optional)
4. Upscale 1.5x (LANCZOS)
5. Adaptive thresholding (block size 15, C=10; global fallback for images >2M pixels)
6. Contrast enhancement (2.0x)
7. Sharpen

### Supported image formats

JPEG, PNG, TIFF (II/MM), BMP, WEBP, GIF — validated by magic bytes before PIL decode.

---

## API Endpoints

### Sync parsing

```bash
curl -X POST "http://localhost:8000/v1/parse-receipt" \
  -F "file=@/path/to/receipt.jpg"
```

```bash
curl -X POST "http://localhost:8000/v1/parse-receipt" \
  -F "image_url=https://example.com/receipt.jpg"
```

### Batch parsing

```bash
curl -X POST "http://localhost:8000/v1/parse-receipts" \
  -F "files=@/path/to/receipt1.jpg" \
  -F "files=@/path/to/receipt2.jpg"
```

```bash
curl -X POST "http://localhost:8000/v1/parse-receipts" \
  -F "image_urls=[\"https://example.com/receipt1.jpg\",\"https://example.com/receipt2.jpg\"]"
```

### Async parsing

```bash
curl -X POST "http://localhost:8000/v1/parse-receipt/async" \
  -F "file=@/path/to/receipt.jpg"
  # returns { "job_id": "uuid", "status": "queued" }
```

### Async batch parsing

```bash
curl -X POST "http://localhost:8000/v1/parse-receipts/async" \
  -F "files=@/path/to/receipt1.jpg" \
  -F "files=@/path/to/receipt2.jpg"
  # returns { "job_id": "uuid", "status": "queued" }
```

Poll for the result:

```bash
curl "http://localhost:8000/v1/jobs/{job_id}"
```

Optional webhook:

```bash
curl -X POST "http://localhost:8000/v1/parse-receipt/async" \
  -F "file=@/path/to/receipt.jpg" \
  -F "webhook_url=https://your-app.com/ocr-callback"
```

### Duplicate detection

```bash
curl -X POST "http://localhost:8000/v1/check-duplicates" \
  -H "Content-Type: application/json" \
  -d '{
    "receipts": [
      {"vendor": "Store A", "total": 42.50, "date": "2025-03-14"},
      {"vendor": "Store A", "total": 42.50, "date": "2025-03-15"}
    ]
  }'
```

Returns groups of potentially duplicate receipts with similarity scores.

---

## Using image_url

ReceiptLens can fetch receipt images directly from a public URL instead of requiring a multipart file upload. This is useful for cloud-hosted images, webhooks, or when you want to avoid transferring large files in the request.

### Single receipt

Send `image_url` as a form field to `POST /v1/parse-receipt`:

```bash
curl -X POST "http://localhost:8000/v1/parse-receipt" \
  -F "image_url=https://example.com/receipt.jpg"
```

### Batch receipts

Send `image_urls` as a JSON-encoded array to `POST /v1/parse-receipts`:

```bash
curl -X POST "http://localhost:8000/v1/parse-receipts" \
  -F "image_urls=[\"https://example.com/receipt1.jpg\",\"https://example.com/receipt2.jpg\"]"
```

### Async receipt

Send `image_url` as a form field to `POST /v1/parse-receipt/async`:

```bash
curl -X POST "http://localhost:8000/v1/parse-receipt/async" \
  -F "image_url=https://example.com/receipt.jpg"
```

### URL constraints

| Constraint | Value |
|---|---|
| **Connect timeout** | 10 seconds |
| **Read timeout** | 30 seconds |
| **Redirects** | Automatically followed (max 5) |
| **Allowed protocols** | `http://` and `https://` (httpx default) |
| **Maximum inputs** | 1 URL (single endpoint), 1–20 URLs (batch) |
| **Mixed input** | Cannot combine `file` upload + `image_url` in the same request |
| **SSRF protection** | Blocks private/reserved IPs, metadata endpoints, and localhost hostnames |

### Error behavior

- **Invalid or unreachable URL** — returns `400 Bad Request` with detail: `Failed to fetch image from URL: <error message>`.
- **Both `file` and `image_url` provided** — returns `400 Bad Request`: `Provide either 'file' or 'image_url', not both.`
- **Neither `file` nor `image_url` provided** — returns `422`: `Missing required input: send 'file' or 'image_url'.`
- **URL returns non-image content-type** — returns `400 Bad Request`: `URL did not return an image`.
- **Image exceeds max size** — returns `400 Bad Request`: `Image exceeds maximum allowed size`.
- **Batch: invalid `image_urls` JSON** — returns `422` with JSON decode error details.
- **Batch: more than 20 URLs** — returns `413 Payload Too Large`.

In batch mode, individual URL failures are returned per-item in the `results` array (with an `error` field and null values for all other fields) without failing the entire request. The `summary` block counts `successful` and `failed` items.

---

## Response Schema

```jsonc
{
  "vendor": "STORE NAME",      // merchant / store name
  "total": 42.50,              // receipt total
  "date": "2025-03-14",        // ISO-8601 date
  "tax": 3.40,                 // tax amount (best-effort)
  "currency": "USD",           // ISO-4217 currency code
  "line_items": [              // parsed individual items
    { "name": "ITEM", "price": 9.99 }
  ],
  "confidence": {              // per-field confidence (0.0 - 1.0)
    "vendor": 0.88,
    "total": 0.95,
    "date": 0.80,
    "tax": 0.70,
    "currency": 0.99,
    "line_items": 0.85
  }
}
```

Batch responses wrap individual results in a top-level `results` array with a `summary` block.

---

## Tests

```bash
pytest
ruff check .
```

---

## Documentation

- [API Reference](docs/api.md) — endpoints, URL fetching contract, SSRF protection, error responses
- [OCR Pipeline](docs/ocr-pipeline.md) — architecture, preprocessing stages, configuration, error handling, tips
- [AI Vision OCR (AI Scan)](docs/ai-vision-ocr.md) — LLM vision extraction, setup, fallback behavior, API responses
- [Subscription Alerts](docs/subscription-alerts.md) — renewal detection, price-increase detection, cancellation guides, email alerts, Subscriptions UI

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

## License

MIT — see [LICENSE](LICENSE).

## Exception-to-export workflow (development pass)

ReceiptLens now exposes the approved bookkeeping workflow through the Next.js workspace:

1. Forward or upload receipt images. Email attachments are tracked independently and unsafe or mismatched content is quarantined.
2. Open **Review** to prioritize low-confidence fields, inspect source evidence, and correct structured values without changing the original image.
3. Use **Settings → Diagnostics → OCR quality** to evaluate labelled cases and publish tenant-scoped confidence thresholds.
4. Preview and activate automation rules before applying them, inspect each run, and roll back eligible receipts without overwriting later edits.
5. Open **Export → Prepare** to create a versioned validation snapshot. Blocked receipts stay out of the artifact, warnings require acknowledgement, and repeated commands use an idempotency key.

The implementation remains provider-neutral. QuickBooks and Xero production OAuth posting are intentionally deferred; the current export artifact is deterministic CSV. For local development, start FastAPI on port 8000 and the Next.js workspace on port 3000. If the workspace reports a load error, verify the backend, tenant headers, and `NEXT_PUBLIC_API_BASE_URL`, then use the visible **Retry** action.

## QuickBooks Online sandbox workflow

The provider foundation supports tenant-bound OAuth state, AES-GCM token storage, immutable account mappings, durable replay-safe export items, reconciliation, and source-currency/tax projections. Install project dependencies, set `RECEIPTLENS_CREDENTIAL_KEY` to URL-safe Base64 for 32 random bytes, start FastAPI and the Next.js frontend, then open **Integrations**. This phase is sandbox-oriented and does not claim production Intuit certification. See `docs/quickbooks-online.md` for the operational contract and troubleshooting boundaries.

### Connected workflow API completion
The Integrations QuickBooks action now calls the tenant-scoped OAuth-start endpoint and redirects only to its fixed Intuit authorization URL. Accounting projection refresh and role-limited provider preview endpoints are available for server-integrated screens. A configured 32-byte URL-safe Base64 `RECEIPTLENS_CREDENTIAL_KEY` is required; absent configuration fails closed with HTTP 503.

### Provider connection administration
Provider connections can now be listed tenant-safely, inspected, disconnected with active ciphertext deletion, and assigned immutable mapping versions through the `/product/provider-connections` and `/product/connections/{id}/mappings` APIs. Historical connection metadata remains after disconnect while active credentials are removed.

## Dokumentáció

- [Engineering Standards](docs/engineering-standards.md) — kötelező olvasmány kódírás előtt
- [Döntések / tanulságok](docs/decisions/) — javított hibák és anti-minták
- [Specifikációk](docs/specs/) — feature-ök kanonikus követelményei

- [Módszertan](docs/METHODOLOGY.md) — a lab fejlesztési módszertana (kötelező olvasmány)
