# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-07-25

### Features

- **AI categorization** — `Categorizer` class with GPT-4o-mini prompt-based classification of receipts into categories (groceries, dining, transport, utilities, entertainment, health, shopping, income, other). Consistent label taxonomy with confidence scoring.
- **Spending analytics** — `AnalyticsService` with spending trends over time, category breakdowns, top merchants report, monthly/yearly comparisons, and spending forecasts.
- **Budget management** — `BudgetStore` with per-category monthly budget tracking, spending vs. budget comparisons, and remaining budget calculations. Fixed double-counting bug in `_recompute()`.
- **Alerting system** — `AlertManager` with configurable threshold-based notifications per category. Tracks alert history and supports percentage-based or absolute thresholds.
- **API integration** — all new modules wired into FastAPI layer (`app/api.py`) with full endpoint coverage.

### Fixes

- **Dependency fix** — added `reportlab>=4.0` to project dependencies for PDF report generation support.

### Tests

- 4 new test modules: `test_categorize.py`, `test_analytics.py`, `test_budgets.py`, `test_alerts.py` — comprehensive coverage for all new features.
- Full regression suite: 501 passing, 7 skipped, 0 failed. Ruff clean.

## [0.5.0] - 2026-07-24

### Features

- **OCR pipeline overhaul** — 7-stage image preprocessing (EXIF rotation, deskew, adaptive threshold via integral image, upscale, contrast, sharpen) for robust real-world receipt scanning.
- **Magic byte validation** — validates JPEG/PNG/TIFF/BMP/WEBP/GIF headers before processing (SSRF hardening).
- **Typed exception hierarchy** — `OCRError` → `InvalidImageError`, `UnsupportedImageFormatError`, `CorruptImageError` for precise error handling.
- **Railway deployment** — production Dockerfile with Tesseract system deps, `railway.toml` config, health check, and restart policy. Live at https://receiptslens-production.up.railway.app.
- **Cloud deployment config** — production-ready Dockerfile + deployment configuration.

### Fixes

- **CSV formula injection** — `_neutralize_csv()` prefixes `=`, `+`, `-`, `@` characters with a single quote to prevent spreadsheet formula injection in generated reports.
- **Adaptive threshold O(n²) → O(n)** — replaced nested-loop implementation with integral image (summed area table), cutting 240K-pixel OCR from >20s to <1s.
- **SSRF guard** — added hostname validation to `validate_image_url` for additional SSRF protection.
- **PORT expansion** — `startCommand` wrapped in `sh -c` for proper `$PORT` environment variable expansion on Railway.

### Tests

- 4 new test modules: `test_magic_bytes.py` (167 lines), `test_ocr_coverage.py` (436 lines), `test_ocr_exceptions.py` (151 lines), `test_preprocessing.py` (311 lines) — 1065 lines of new test coverage.
- `test_reports.py` expanded with CSV injection regression tests (718 lines added).
- Full regression suite: 415 passing, 7 skipped, 0 failed. Ruff clean.

### Docs

- Added `docs/ocr-pipeline.md` architecture documentation.
- Updated README with library usage and Railway deployment section (live URL, Docker self-host, env vars, usage examples).
- Added `examples/parse_receipt.py` runnable CLI demo.

## [0.4.0] - 2026-07-20

### Features

- Add non-blocking async image fetch with `app/ssrf_guard.py` — SSRF-safe URL validation with egress allowlist, redirect handling, and configurable `MAX_IMAGE_BYTES` / `URL_FETCH_TIMEOUT` limits.
- Add duplicate receipt detection endpoint `POST /v1/check-duplicates` with vendor similarity scoring and canonical total comparison.
- Add `POST /v1/parse-receipt/image-url` endpoint for parsing receipts from remote URLs with SSRF protection.
- Configurable resource limits: `MAX_IMAGE_BYTES` and `URL_FETCH_TIMEOUT` constants replace hardcoded values.

### Tests

- 211 tests passing (up from 29 in v0.2.0). Full regression suite covers SSRF guard, async fetch, image URL endpoint, duplicate detection, configurable limits, and security egress allowlist.

## [0.3.0] - 2026-07-20

### Features

- Add batch receipt processing endpoints:
  - `POST /v1/parse-receipts` for synchronous batch parsing from multipart `files[]` uploads or JSON `image_urls`.
  - `POST /v1/parse-receipts/async` for asynchronous batch jobs with optional `webhook_url` delivery.
- Batch results preserve input order via `index`, return per-item errors without failing the whole request, and include `summary.total`, `summary.successful`, and `summary.failed`.
- Input validation now rejects mixed `files[]` and `image_urls` with `400`, empty requests with `422`, and more than 20 inputs with `413`.

### Tests

- Added `tests/test_batch_processing.py` covering batch route registration, mixed-input rejection, payload-size limits, empty-image behavior, URL fetch error handling, and summary count correctness.
- Full regression suite still passes against existing single-receipt endpoints and async confidence workflows.

## [0.2.0] - 2026-07-20

### Features

- Add per-field confidence scores to receipt parsing responses. Each field
  (`vendor`, `total`, `date`, `tax`, `currency`, `line_items`) now includes
  a `confidence` float between 0.0 and 1.0 derived from Tesseract
  `image_to_data` accuracy metrics.
- Add `POST /v1/parse-receipt/async` for non-blocking OCR jobs. Accepts
  optional `webhook_url` to receive a JSON POST on completion or failure.
- Add `GET /v1/jobs/{job_id}` for polling async job status and results.
- Run blocking OCR calls inside a ThreadPoolExecutor to keep the FastAPI
  event loop responsive.

### Tests

- Added `tests/test_async_confidence.py` with 10 interface and behavioral
  tests covering async scheduling, confidence schema, webhook delivery, and
  job polling. Full suite is 29 tests passing.

## [0.1.1] - 2026-07-20

### Fixed

- **P0 crash on real receipts.** `_parse_line_items` raised `IndexError: no such group`
  because the line-item regex had a non-capturing price group. The endpoint now returns
  `200` with the full schema on any receipt that contains line items. Regression tests
  added in `tests/test_ocr.py` and `tests/test_api.py`.
- Moved `import io` to the top of `app/ocr.py` (it was lazily imported at module bottom).
- Added `infra/` scaffold (Dockerfile + README) that was missing from the v0.1.0 build.

## [0.1.0] - 2026-07-20

### Features

- Initial ReceiptLens OCR API scaffold.
- `POST /v1/parse-receipt` endpoint accepts multipart file upload or `image_url` form field.
- Tesseract 5 OCR pipeline with image pre-processing (grayscale, upscale, contrast, sharpen).
- Regex-based receipt parser extracting vendor, date, line items, tax, total, and currency.
- Async FastAPI application with `/health` endpoint and OpenAPI docs.
- Pydantic-style response schema: `vendor`, `total`, `date`, `tax`, `currency`, `line_items[]`.

### Tests

- 19 pytest tests covering API routes, OCR signatures, runtime behavior, and regression cases.
- `ruff` linting configured and passing.
