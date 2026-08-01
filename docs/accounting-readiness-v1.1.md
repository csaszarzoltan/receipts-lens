# ReceiptLens 1.1 Accounting Readiness

This release implements the twelve UI capabilities selected after the consolidated 1.0 workspace. Each feature has a tenant-scoped service, an API contract, a usable workspace view, and focused tests.

## 1. OCR field linking

The accounting view exposes field-link controls for vendor, date, total, tax, currency, and line items. Selecting a field opens the review workspace and focuses its editor. Stored OCR boxes remain available over the source image for visual traceability.

## 2. Line-item editor

The spreadsheet-style editor supports name, quantity, unit price, amount, category, row creation, row deletion, calculated totals, optimistic version checks, and activity history. Invalid negative values and empty names are rejected.

## 3. Approval-flow designer

Admins can build serial and parallel approval steps, assign one or more roles, define a minimum amount, simulate the flow against a sample receipt, and publish a versioned flow. Invalid or empty flows are rejected.

## 4. Accounting validation

Validation checks required fields, negative totals, future or malformed dates, tax greater than total, line-item total mismatches, missing cost centers, and missing export connections. A receipt resolves to `exportable`, `warning`, or `blocked`.

## 5. Export preparation

The three-stage export workspace validates selected receipts and separates exportable, warning, blocked, and missing records. Preparations are retained as tenant-scoped operational history.

## 6. Email inbox

Each workspace receives a deterministic inbound address. The UI lists sender, subject, attachment count, and status. Supported image and PDF metadata is queued; unsupported attachments are quarantined. The present API intentionally stores attachment metadata rather than untrusted binary email bodies.

## 7. Recurring expenses

Repeated merchants with stable amounts are presented as likely subscriptions with occurrence count, monthly average, annualized cost, and observed price change. Users can correct the classification, and the feedback is retained per tenant and merchant.

## 8. Currency conversion

Admins can enter dated manual exchange rates with an explicit source. Conversion selects the latest applicable rate on or before the transaction date. Identity conversion is handled without a stored rate, while missing cross-currency rates produce a clear error.

## 9. Dashboard editor

Users choose which KPI, action, spending, and quality widgets belong to their role-specific dashboard. The selected order and visibility use the existing allowlisted preference store.

## 10. Localization

The workspace has a real translation catalogue entry point, persistent language preference, document-language update, and English/Hungarian navigation labels. The catalogue is intentionally small in 1.1 and can be expanded without changing view logic.

## 11. Permission matrix

Admins can review and change role permissions for images, receipt editing, approvals, exports, deletion, API key administration, automation rules, and audit history. The backend validates both role and permission allowlists and isolates profiles by tenant.

## 12. Diagnostics

The diagnostics panel shows application version, database state, receipt count, failed job count, OCR state, and PWA availability. Admins can download a ZIP containing health and capability metadata. It deliberately excludes receipt content, images, OCR text, credentials, tokens, and API-key material.

## Test coverage

`tests/test_accounting_readiness_ui.py` contains a numbered test for every capability, plus route registration and diagnostic authorization tests. It runs together with all existing API, OCR, product, security, deployment, GUI, and consolidated-workspace tests.
