# ReceiptLens 1.0 consolidated workspace

ReceiptLens 1.0 merges the originally planned 0.9 operational release and 1.0 intelligence release into one tested package.

## Delivered capabilities

### Source evidence and OCR traceability

Uploaded receipt images are stored in the tenant-scoped SQLite product database with content type, original filename, SHA-256 digest, and retention-aware deletion. The review workspace can switch between the original image and the structured representation, zoom and rotate it, and request normalized OCR word boxes. Stored images are returned with `Cache-Control: private, no-store` and cannot be read across tenants.

### Duplicate review

The duplicate inbox compares stored receipts using normalized merchant, exact canonical total, and transaction date. Reviewers can mark pairs as the same or different. Decisions are persisted and remove resolved pairs from the inbox; the action also appears in receipt history.

### Saved views

Receipt filters can be named, pinned, shared, applied, and deleted. The server validates the filter allowlist rather than accepting executable query fragments. Views are tenant scoped.

### Notification center

The application now has an in-app notification inbox with unread counts, read status, archive state, mark-all-read support, subject links, and tenant isolation. Low-confidence uploads create review notifications automatically.

### Automation rules

Rules support merchant substring, currency, minimum amount, and maximum amount conditions. Actions can apply tags, project, cost center, and request approval. Users can preview the number of matching historical receipts before creating a rule. Active rules run after upload.

### Activity history

Creation, correction, and duplicate decisions are recorded with time, actor role, and before/after values where applicable. The review screen exposes the timeline without placing image bytes in history.

### Export center

Connection-based export runs record requested, exported, failed, partial, and completed outcomes. The reports screen lists export history next to the existing portability download.

### Preferences and role-oriented dashboard

Language target, compact mode, high contrast, onboarding completion, and dashboard widget preferences are persisted by tenant and role. Preferences are filtered to a fixed allowlist.

### PWA and onboarding

The workspace ships with a web app manifest, install prompt, online/offline indicator, service worker, shell caching, and first-run checklist. Product API responses and receipt images are deliberately excluded from service-worker caching. Sensitive receipt binaries are therefore not persisted in the offline shell cache.

## API additions

- `GET /product/receipts/{receipt_id}/image`
- `GET /product/receipts/{receipt_id}/ocr-boxes`
- `GET /product/receipts/{receipt_id}/history`
- `GET|POST /product/saved-views`
- `DELETE /product/saved-views/{view_id}`
- `GET /product/notifications`
- `PATCH /product/notifications/{notification_id}`
- `POST /product/notifications/read-all`
- `GET|POST /product/automation-rules`
- `POST /product/automation-rules/preview`
- `GET /product/duplicates`
- `POST /product/duplicates/decision`
- `GET|PUT /product/preferences`
- `GET|POST /product/export-runs`

## Security and privacy properties

- Every advanced data query includes tenant identity.
- Receipt image responses are private and non-cacheable.
- Static assets use an explicit allowlist.
- Saved-view filters, rule conditions, rule actions, and preferences use field allowlists.
- The service worker never caches `/product/` requests.
- Retention purge removes source images and activity records with the receipt.
- Image content is never written to audit or activity history.

## Test strategy

The consolidated suite adds focused tests for source image isolation, OCR-box persistence, saved-view validation, notification lifecycle, rule preview/application, duplicate decisions, history, preferences, export runs, PWA assets, UI contracts, and route registration. These tests run together with the complete OCR, API, security, product, reporting, deployment, and regression suite.
