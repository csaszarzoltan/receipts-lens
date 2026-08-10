# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-08-01

### Features

- **Multi-language OCR** — language detection via Tesseract script analysis, locale-aware date parsing (DE, FR, ES, IT, HU, EN), locale-sensitive currency extraction with `_CURRENCY_LOCALE_HINTS` fallback, 6 supported languages (eng, deu, fra, spa, ita, hun).
- **Batch processing** — `BatchProcessor` with `ThreadPoolExecutor` for parallel receipt processing, `BatchJob` model with job lifecycle (pending → running → completed/failed), async batch API endpoint (`POST /api/v1/receipts/batch`), job status polling (`GET /api/v1/receipts/batch/{job_id}`).
- **Accounting export** — `ReceiptExporter` with `ExportProfile` for QuickBooks, Xero, and Generic CSV formats, column mappings per software, CSV formula injection prevention (`_neutralize_csv()`), export API endpoint (`GET /api/v1/receipts/export/{format}`).
- **Receipt normalization** — `NormalizedReceipt` Pydantic schema with `normalize_date()`, `normalize_currency()`, `normalize_receipt()` for cross-border expense intelligence.
- **API v2 endpoints** — batch processing and export endpoints wired into FastAPI with full OpenAPI schemas.
- **CLI subcommands** — `python -m app.cli batch`, `python -m app.cli export`, `python -m app.cli info` for command-line batch processing and export.

### Fixes

- **SyntaxError in product_service.py** — extracted `rid = row["receipt_id"]` to fix nested f-string quotes breaking Python 3.11.
- **Test regressions in test_ocr_coverage.py** — updated `test_no_currency` and `test_empty_text` to match locale fallback behavior (returns "USD" instead of None).

### Tests

- 60+ new tests across 6 test modules: `test_multilang_ocr.py`, `test_normalization.py`, `test_batch_processor.py`, `test_export_profiles.py`, `test_api_v2.py`, `test_cli.py`.
- Full regression suite: 805 passed, 7 skipped, 1 pre-existing TDD stub. 44 test files collected.
- Ruff: 155 pre-existing violations, 0 new.

### Docs

- Created `docs/multi-language-guide.md` — supported languages, Tesseract setup, accuracy tips per language.
- Created `docs/accounting-export-guide.md` — QuickBooks/Xero/Generic CSV formats, column mappings, import instructions.
- Updated `docs/api.md` — batch and export endpoint schemas with request/response examples.
- Updated `README.md` — multi-language OCR, batch processing, accounting export features added.

## Unreleased

### Forecast
- **Forecast engine** — next-period spend forecasting with per-category and overall predictions using trailing moving average + linear trend extrapolation, confidence bounds (±1.96× residual std), and an injectable LLM narrative seam.
- **Anomaly detection** — flag category-period spend deviations via z-score or MAD (median absolute deviation) with leave-one-out baselines.
- **Budget variance projection** — project each budget's end-of-period spend from the current period's run rate and report expected overage with on_track / warning / over_budget status.
- **REST endpoints** — `GET /forecasts` (overall + per-category forecast), `GET /forecasts/anomalies` (detected spending anomalies), `GET /forecasts/budget-variance` (projected budget overage).
- **Dashboard** — server-rendered forecast dashboard at `GET /dashboard` with inline SVG bar chart, per-category forecast cards, flagged anomalies table, and budget variance table. No JavaScript or remote assets.
- **CLI** — `receipts-lens forecast --period monthly` outputs next-period spend, confidence bounds, and trend per category.
- 78 forecast tests added (ForecastEngine, AnomalyDetector, BudgetVarianceProjector, REST routes, CLI). Full suite: 884 passed, 7 skipped, 0 failed.

### Product workflows
- Added a responsive receipt upload workspace at `/workspace`.
- Added tenant-scoped receipt history, retry, cancellation, review, and optimistic correction workflows.
- Added team membership, role checks, and one-time API key creation with digest-only storage.
- Added accounting connection metadata, mapping validation, export records, and a trust dashboard.
- Added a SQLite-backed application service with optional persistent storage through `RECEIPTLENS_PRODUCT_DB`.
- Added end-to-end and negative tests for all six product research requirements.



### Homepage
- Added a responsive, self-contained Hungarian landing page at `GET /`.
- Added direct Swagger UI, ReDoc and health links, supported-operation summaries and a Windows upload example.
- Added deterministic homepage, navigation and metadata-escaping tests.



### Research requirements
- Added a durable tenant-scoped SQLite reference data plane with job leases, idempotency, optimistic locking and transactional outbox.
- Added authentication, RBAC, quota, signed webhook and tamper-evident audit primitives.
- Added deterministic OCR benchmark, calibration, review and correction provenance services.
- Added accounting connector and usage-metering ports plus readiness/capability endpoints.



### Subscription alerts
- **Renewal tracking** — `extract_next_renewal_date()` computes the next renewal from a last-known date and recurrence frequency (monthly / quarterly / annual), rolling forward to the first date on or after today with day-of-month clamping for short months (Jan 31 → Feb 28).
- **Price-increase detection** — `detect_price_increase()` flags a subscription when the most recent charge exceeds the rolling average of prior charges by more than a configurable threshold (default 10 %).
- **Cancellation guides** — `CancelGuide` with curated steps + account links for 22 merchant entries across 21 distinct brands (Netflix, Spotify, Disney+, Amazon Prime, Max/HBO Max, Hulu, Audible, YouTube Premium, Microsoft 365, Adobe, ChatGPT, Apple Music/TV+/iCloud+, Dropbox, Google One, Notion, Figma, Canva, Headspace, Crunchyroll) and a generic fallback for unknown merchants.
- **REST endpoints** — `GET /api/v1/subscriptions` (active subscriptions with renewal date, monthly cost, annualized spend, trend) and `GET /api/v1/subscriptions/{id}/cancel-guide` (merchant-specific steps; deterministic merchant resolution for unresolvable ids, generic fallback otherwise). Mounted via the router in `app/subscriptions_api.py`.
- **Email notifications** — `send_email_notification()` delivers renewal/price alerts via SMTP when a config dict is provided; delivery additionally requires `RECEIPTLENS_SMTP_ENABLED=1` (env gate — the process never dials out implicitly). No config / no host / gate off → returns `False` silently.
- **Alert types** — `SUBSCRIPTION_RENEWAL` (info) and `PRICE_INCREASE` (warning) added to `AlertStore`, with `schedule_renewal_alerts()` (fires N days before renewal, default 3) and `create_price_increase_alert()`.
- **Subscriptions UI** — new Subscriptions page (`frontend/app/(app)/subscriptions/page.tsx`): summary cards (count, monthly total), upcoming renewals within 14 days, price-change cards, full table with trend indicators, cancel-guide modal, and a persisted Email alerts toggle through `PUT /product/preferences` (`email_alerts` key).
- Only new runtime dependencies: none — implementation uses the existing stdlib + FastAPI stack (all deps already pinned in `pyproject.toml`).

### AI Vision OCR
- **LLM vision extraction** — `VisionOcrProvider` sends the receipt image (base64 data URL, MIME sniffed from magic bytes) to an OpenAI-compatible vision chat-completions endpoint and returns structured receipt JSON; model asked for `merchant` / `date` / `total` / `tax` / `currency` / `line_items` with `temperature: 0.0`.
- **Automatic Tesseract fallback** — `parse_receipt_with_vision()` returns the same `ConfidenceReceipt` shape as the classic pipeline; the producing path is marked via `confidence["source"]` (`"vision"` | `"tesseract"`). Fallback when disabled / no API key / timeout / API error / non-JSON response (one retry for transient failures: timeout, connection error, HTTP 5xx).
- **Cost guard** — vision path is OFF by default: requires `VISION_OCR_ENABLED` (1/true/yes/on) AND `LLM_API_KEY`. Config mirrors `app/categorizer.py`: `LLM_API_KEY` / `LLM_BASE_URL` (default `https://api.openai.com/v1`) / `LLM_MODEL` (default `gpt-4o-mini`), plus `VISION_OCR_TIMEOUT` (default 30.0 s).
- **AI-mode API fields** — `ai_scan=true` form field on `POST /v1/parse-receipt` and `POST /product/receipts/upload` exposes top-level `source` plus `ai_result` / `tesseract_result` payloads (both pipelines on the same image); regular flow unchanged (no breaking changes). Batch/export endpoints intentionally keep the classic path.
- **Frontend AI Scan** — accessible `AiScanToggle` (role=switch) in the upload flow, `AiResultPanel` with source badge, per-field confidence and friendly Tesseract fallback notice, `uploadReceiptWithAi()` client, and a contract-shaped dev mock behind `NEXT_PUBLIC_USE_MOCK_AI=1`.
- Only new runtime dependency: `httpx>=0.27` (pinned in `pyproject.toml`).

### Fixed
- Replaced placeholder receipt create/list/get endpoints with working in-memory implementations.
- Made `ReceiptStore.get()` lock-protected and added a stable `list_all()` snapshot API.

### Tests and documentation
- Added receipt CRUD runtime acceptance tests.
- Added a tested Hungarian Windows installation and usage guide.
- 69 new vision-OCR tests: `test_vision_ocr.py` (29, provider + fallback chain), `test_api_vision.py` (9, AI-mode API contract), `test_frontend_ai_scan.py` (31, AI Scan UI interface + behavior). Full suite: 1157 passed, 7 skipped, 0 failed across 50 modules; Ruff 0 new rule-level errors vs the pre-feature baseline.
- Added `docs/ai-vision-ocr.md` — AI Scan setup (env vars, cost guard), fallback chain, API response shapes, Python library usage, frontend behavior.
- Updated `README.md` (AI Vision OCR feature, AI Scan getting-started setup, env-var table, docs list) and `docs/api.md` (AI-mode `ai_scan=true` section on `POST /v1/parse-receipt`).

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

## 1.1.1 - 2026-08-01

### Added
- Tenant-scoped, role-aware daily work queue for failed jobs, OCR review, and approvals.
- Atomic receipt workspace update covering fields, line items, metadata, status, version, job status, and audit.
- TDD acceptance tests for workflow ordering, transaction rollback, concurrency, and API behavior.
- Delivery requirements and implementation report.

### Changed
- Dashboard next actions now use the prioritized work queue.
- Review save now performs one atomic workspace request instead of separate receipt and metadata requests.

## 1.2.0 - 2026-08-01

### Added
- Early accounting-readiness state and stable issue details on product receipt queries.
- Receipt-list filtering by blocked, warning, or exportable state.
- Export-blocker tasks in the prioritized daily work queue.
- Accounting-readiness badges and filter controls in the receipt workspace.
- TDD acceptance tests for readiness state, filtering, API behavior, queue behavior, and UI contracts.
- Product/UX analysis and full implementation delivery report in `docs/`.

### Changed
- Receipt filter reset now clears both inputs and select controls.
- Receipt table now surfaces accounting state before users enter export preparation.

## 1.3.0 - 2026-08-01

### Added
- Precise work-queue deep links for review receipts, export blockers, and approval tasks.
- Accessible contextual dialogs for approval decisions, API-key creation, saved-view naming, and retention purge.
- Inline dialog validation, mandatory rejection reasons, and typed confirmation for irreversible purge.
- TDD acceptance coverage for deep links and business-action dialog contracts.
- Updated product analysis, requirements, GUI, API, workflow, accounting-readiness, delivery, and GitHub README documentation.

### Changed
- Dashboard actions retain complete task URLs and navigate to exact records and fields.
- Saved views now preserve the accounting-readiness filter.
- Approval cards can receive programmatic focus after task navigation.

### Removed
- Browser-native business `prompt()` and `confirm()` flows for approval, API-key, saved-view, and purge actions.

## [1.5.0] - 2026-08-10

### Added
- Confidence-filtered review queue with deterministic pagination and sorting.
- Immutable export preparations, tenant-scoped idempotent export commands, run detail, and CSV artifacts.
- Persisted OCR benchmark reports and versioned confidence threshold profiles.
- Versioned automation preview, activation, run history, optimistic rollback preview, and rollback.
- Redacted receipt audit endpoint and nine BDD story regression tests.

### Changed
- Export preparation now snapshots receipt versions and validation results.
- Direct async API tests run in minimal CI without an external pytest async plugin.
- README now provides a concise GitHub product overview and primary workflow.

### Fixed
- API v2 direct-call defaults and the previously failing async endpoint behavioral tests.
- Export preparation inserts remain compatible after additive schema migration.

### Tests and documentation
- Added US-001 through US-009 behavior coverage and updated API/workflow documentation.
