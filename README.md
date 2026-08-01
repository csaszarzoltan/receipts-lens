# ReceiptLens

<p align="center">
  <img alt="ReceiptLens" src="docs/assets/logo.svg" width="120" />
</p>

**ReceiptLens** extracts structured data from receipt images using Tesseract OCR.

Send an image (file upload, public URL, or batch of either) to `POST /v1/parse-receipt` or `POST /v1/parse-receipts` and get back JSON with `vendor`, `total`, `date`, `tax`, `currency`, and `line_items[]`.

v1.3.0 improves repeated daily work with precise task deep links and accessible contextual dialogs for approvals, API keys, saved views, and irreversible retention purge. v1.2.0 added early accounting-readiness badges, filters, and export-blocker tasks. v1.1.1 added the prioritized work queue and atomic receipt workspace save. v1.1.0 adds accounting readiness: line-item editing, validation, approval-flow design, export preparation, email intake, subscriptions, FX, dashboard editing, localization, permission matrix, and private diagnostics. v1.0.0 consolidated the operational and intelligent workspace releases with secure source images, OCR overlays, duplicate review, saved views, notifications, automation rules, history, export runs, preferences, onboarding, and PWA support. v0.8.0 added a complete responsive financial operations workspace with receipt inbox, batch capture, OCR review, approval inbox, reports, integrations, administration, accessibility, and mobile layouts. v0.7.0 added **search, allocation metadata, approvals, retention controls, and portability**. v0.6.0 added **AI-powered categorization**, **budget management**, **spending analytics**, and an **alert system** — transforming ReceiptLens from a receipt scanner into a complete expense management platform.

---

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
- **Receipt operations** — tenant-scoped search, tags, projects, cost centers, threshold approvals, retention purge, and versioned portability export.
- **Precise daily actions** — dashboard tasks deep-link to the exact review receipt, approval, or blocked accounting field instead of opening only a general module.
- **Accessible consequential actions** — approval decisions, API-key creation, saved-view naming, and retention purge use contextual dialogs with inline validation, focus handling, and described consequences.
- **Early accounting readiness** — receipt rows show baseline blocked/warning/exportable state and can be filtered before export preparation.
- **Tested** — 805+ pytest tests across 44 test files; the packaged delivery records the exact passing and skipped counts in `TEST_RESULTS.txt`.

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

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

## License

MIT — see [LICENSE](LICENSE).
