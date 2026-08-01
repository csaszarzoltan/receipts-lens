# ReceiptLens GUI workspace

Version 0.8.0 replaces the upload-only page with a responsive financial operations workspace at `/workspace`.

## Implemented workflows

1. **Application shell:** persistent navigation, workspace and role context, global search, notifications, responsive mobile drawer, skip link, focus states, high-contrast mode, and compact tables.
2. **Receipt inbox:** tenant-scoped search, status/tag/amount filters, quick filters, stable pagination, selection, bulk metadata assignment, and bulk approval requests.
3. **Capture:** drag and drop, multi-file selection, mobile camera hint, clipboard image capture, per-item previews, progress, retry-safe queue state, and actionable status text.
4. **OCR review:** split receipt/data view, confidence semantics, field editing, zoom, rotation, previous/next navigation, save versus complete, and `Ctrl+Enter` completion.
5. **Approval inbox:** contextual vendor, amount, project, policy, timestamp, approval/rejection, notes, and policy creation.
6. **Dashboard:** operational KPIs, next actions, spending bars, quality counters, service status, and retention visibility.
7. **Reports:** totals, average and largest receipt, category breakdown, and downloadable versioned JSON portability export.
8. **Integration center:** CSV, QuickBooks, and Xero connection creation, visual field mapping summary, status, and connection testing.
9. **Administration:** member list/invitation, API-key creation with one-time secret display, retention configuration, purge confirmation, portability export, language, compact mode, and high contrast.
10. **Responsive and accessible behavior:** semantic headings and landmarks, keyboard navigation, live toast region, text-plus-color statuses, visible focus, touch-friendly controls, and dedicated breakpoints.

## Supporting API additions

- `GET /product/approvals`
- `GET /product/connections`
- `GET /product/members`
- `GET /assets/workspace.css`
- `GET /assets/workspace.js`

All data-list endpoints are tenant scoped. Static assets are served from a strict allowlist.

## Deliberate product boundaries

- The QuickBooks and Xero cards manage and test connection metadata. Live third-party OAuth and remote posting remain adapter responsibilities because no external credentials are stored by this repository.
- The review panel renders a trustworthy structured receipt preview. Source-image persistence and OCR bounding boxes are not fabricated because the current privacy-oriented upload service does not persist images or return coordinates.
- Automatic camera edge detection and durable offline binary upload require a native/PWA capture pipeline. The responsive camera input and in-session queue are implemented without silently retaining sensitive receipt images in browser storage.
- English is exposed as a preference target, while the shipped interface remains Hungarian until a reviewed translation catalogue is added.

## Test coverage

`tests/test_workspace_gui.py` verifies every GUI area, accessibility/responsive contracts, strict static-asset routing, tenant-scoped supporting APIs, approval context joins, and configured retention on the dashboard. Existing product, API, OCR, security, research, report, and deployment tests remain part of the full regression suite.

## v1.3.0 interaction updates

- Dashboard task buttons preserve the complete task URL instead of stripping record and field context.
- Review tasks open the requested receipt.
- Approval tasks scroll and focus the requested decision card.
- Export-blocker tasks open receipt organization and focus the blocked cost-center or project field when supported.
- Approval decisions use an accessible modal, and rejection requires an inline-validated reason.
- API-key creation and saved-view naming use labelled fields and inline errors.
- Retention purge uses a dedicated irreversible-action dialog with explicit typed confirmation.
- Saved views now preserve the accounting-readiness filter.

These changes reduce navigation ambiguity and remove browser-native business prompts while retaining the existing static HTML and vanilla JavaScript architecture.
