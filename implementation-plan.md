# Implementation Plan

## Executive Summary
This pass is a **completion pass**, not another foundation pass. The previous development phase added tested domain modules for OAuth state and encrypted credentials, mapping versions, replay-safe provider links, reconciliation comparison, and Decimal currency/tax projections, but its own report marks every US-010 through US-018 story PARTIAL because the HTTP APIs, live provider orchestration, retry scheduler, full UI screens, role enforcement, and browser verification are missing.

The selected scope is three coherent completion features: (A) wire the existing QuickBooks services into secure API endpoints and a real connection/mapping UI, (B) finish durable asynchronous export, retry, run detail, and reconciliation, and (C) integrate accounting projection, tax blockers, and provider payload preview into Receipt Detail and Export Preparation. All nine existing stories, US-010 through US-018, remain the contract. No new product surface is added beyond the routes already approved.

This scope is bounded for one development pass because the domain foundations already exist. The developer must extend and harden those modules rather than replace them. A story is PASS only when its complete GUI flow and every acceptance criterion work through the API and UI, not merely at service level.

## Current-State Validation
- The research remains actionable: accounting integration is table stakes; matching/reconciliation, currency, and tax mistakes are validated pain points; the recommended sequence is one provider sandbox before Xero.
- The project contains the planned foundation modules: `app/credential_store.py`, `connection_service.py`, `quickbooks_connector.py`, `provider_export_service.py`, `reconciliation_service.py`, and `accounting_projection.py`.
- `tests/test_us_010_018_provider_workflow.py` verifies core service behavior, but `development-report.md` explicitly marks US-010..018 PARTIAL and lists missing API wiring, live Intuit exchange/refresh, Retry-After scheduling, attachment upload, mapping/accounting/run/reconciliation screens, real sandbox verification, and browser evidence.
- `frontend/app/(app)/integrations/page.tsx` contains a polished onboarding card, but its Connect button is intentionally informational. There are no QuickBooks detail, mapping, accounting projection, provider run item, reconciliation, or payload-preview screens.
- `pyproject.toml` includes `cryptography>=43`; no additional runtime dependency is required. Existing `httpx`, FastAPI, SQLite, SWR, Next.js, Playwright, and axe are sufficient.
- Existing lab scripts are present. The BDD gate maps US-010..018 structurally; it must be strengthened to require at least one API or E2E test per acceptance criterion, not only a story-name substring.

## Research Priorities
| Priority | Need | Decision | Reason |
|---|---|---|---|
| P0 | Complete one accounting provider end to end | Select | Highest market value and already partially implemented. |
| P0 | Retry-safe export and reconciliation | Select | Directly addresses duplicate and opaque-sync risk. |
| P0 | Currency/tax provenance in the daily UI | Select | Direct evidence of costly currency and tax mistakes. |
| P1 | Xero | Defer | QuickBooks must be production-shaped and verified first. |
| P1 | Production identity | Defer | Important release blocker, but separate from completing this sandbox workflow. |
| P2 | Billing | Defer | Requires beta telemetry and product activation data. |

## Selected Scope for This Pass
### Feature A: Complete QuickBooks connected workflow
Finish US-010, US-011, and US-012 through real FastAPI endpoints, Intuit OAuth exchange/refresh/revoke, role and tenant checks, mapping references and immutable versions, and Integrations/connection-detail UI.

### Feature B: Durable export, retry, and reconciliation
Finish US-013, US-014, and US-015 through queued item processing, retry scheduling, attachment upload, run and item APIs, failed-item retry, remote verification, and run/reconciliation UI.

### Feature C: Accounting projection and payload approval
Finish US-016, US-017, and US-018 by integrating source/reporting amounts, dated rates, tax validation, mapping blockers, readiness, snapshot-bound provider preview, role enforcement, and the required Receipt Detail/Export Preparation UI.

## Deferred Scope and Rationale
1. **Xero connector:** next provider phase after all US-010..018 stories are PASS.
2. **Production Intuit certification and launch:** release phase after sandbox evidence and operational review.
3. **Production identity/SSO:** dedicated tenancy/identity phase; header identity remains visibly non-production.
4. **Automatic FX-rate provider:** requires licensing, outage, caching, and provenance policy; manual tenant rates remain.
5. **Provider webhooks/bidirectional edits:** polling reconciliation completes this pass; inbound synchronization is later.
6. **Jurisdiction-specific tax advice:** requires accountant-reviewed country rules and legal wording.
7. **PostgreSQL migration:** provider repositories must stay adapter-ready, but SQLite remains reference storage.
8. **Billing and quotas:** wait for connected-export activation and support-cost metrics.
9. **Legacy workspace removal:** separate frontend consolidation phase.

## User Stories (BDD)
```json
[
  {
    "id": "US-010",
    "epic": "Complete QuickBooks connected workflow",
    "role": "tenant administrator",
    "action": "connect a QuickBooks Online sandbox company through OAuth",
    "benefit": "approved receipts can be posted without copying CSV files",
    "story": "As a tenant administrator, I want to connect a QuickBooks Online sandbox company through OAuth, so that approved receipts can be posted without copying CSV files.",
    "gui_flow": [
      "Administrator opens Integrations \u2192 sees QuickBooks Online marked Not connected",
      "Administrator selects Connect QuickBooks \u2192 sees a disclosure of requested scopes and data use",
      "Administrator selects Continue to Intuit \u2192 browser is redirected to the provider authorization URL with state and PKCE parameters",
      "Provider callback returns \u2192 ReceiptLens validates state, stores encrypted tokens, and shows the selected company name",
      "Administrator selects Test connection \u2192 sees Connected, company identifier suffix, and last-tested timestamp",
      "Administrator opens Export Preparation \u2192 QuickBooks Online is available as a destination"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "an admin starts a connection for tenant A",
        "when": "the OAuth callback returns matching state, realm identifier, and authorization code",
        "then": "one active tenant-A connection is stored and the callback redirects to `/integrations?connected=quickbooks` without exposing tokens"
      },
      {
        "type": "given",
        "text": "an OAuth state belongs to tenant A",
        "when": "a tenant-B callback or a replay uses that state",
        "then": "the callback returns 400, stores no token, and records a redacted security event"
      },
      {
        "type": "given",
        "text": "the provider token exchange times out",
        "when": "the callback is processed",
        "then": "the connection remains disconnected, the UI shows `Connection could not be completed`, and Retry creates a new state"
      }
    ]
  },
  {
    "id": "US-011",
    "epic": "Complete QuickBooks connected workflow",
    "role": "tenant administrator",
    "action": "inspect and refresh the accounting connection",
    "benefit": "expired credentials do not interrupt an export unexpectedly",
    "story": "As a tenant administrator, I want to inspect and refresh the accounting connection, so that expired credentials do not interrupt an export unexpectedly.",
    "gui_flow": [
      "Administrator opens Integrations \u2192 sees connection health, scope summary, and token expiry status",
      "Administrator selects Test connection \u2192 ReceiptLens requests provider company information",
      "Successful response appears \u2192 status changes to Healthy with a UTC timestamp",
      "Administrator selects Refresh authorization when consent is stale \u2192 a new OAuth flow begins",
      "Administrator returns from provider \u2192 the existing connection is updated rather than duplicated",
      "Administrator selects Disconnect \u2192 a confirmation dialog explains queued exports will stop"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "an access token expires and a valid refresh token exists",
        "when": "the connection test runs",
        "then": "ReceiptLens refreshes once, retries once, and returns Healthy without exposing either token"
      },
      {
        "type": "given",
        "text": "a refresh response rotates the refresh token",
        "when": "the new token set is stored",
        "then": "the previous encrypted token material is replaced and cannot be retrieved through any API response"
      },
      {
        "type": "given",
        "text": "the provider returns invalid_grant",
        "when": "the connection test runs",
        "then": "the connection becomes Reauthorization required, no repeated refresh loop occurs, and the UI offers Reconnect"
      }
    ]
  },
  {
    "id": "US-012",
    "epic": "Complete QuickBooks connected workflow",
    "role": "integrator",
    "action": "map ReceiptLens fields to QuickBooks purchase fields and validate the mapping",
    "benefit": "posting failures are caught before an export run",
    "story": "As a integrator, I want to map ReceiptLens fields to QuickBooks purchase fields and validate the mapping, so that posting failures are caught before an export run.",
    "gui_flow": [
      "Integrator opens QuickBooks connection detail \u2192 sees the Mapping tab",
      "Integrator chooses expense account, payment account, tax treatment, vendor fallback, and attachment behavior",
      "Integrator selects Validate mapping \u2192 server checks required fields and provider references",
      "Valid mapping appears \u2192 each row shows Ready and the Save mapping button enables",
      "Integrator saves \u2192 mapping version and editor role appear in the audit panel",
      "Integrator opens Export Preparation \u2192 preflight uses the saved mapping version"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "a mapping references active provider accounts and defines every required target",
        "when": "the integrator validates and saves it",
        "then": "a new immutable mapping version is stored and returned with `valid=true`"
      },
      {
        "type": "given",
        "text": "the provider account list changes after a mapping was saved",
        "when": "preflight validates the mapping",
        "then": "the affected receipts are blocked with `mapping_reference_inactive` and a deep link to Mapping"
      },
      {
        "type": "given",
        "text": "a required purchase account is blank",
        "when": "the integrator selects Validate mapping",
        "then": "the API returns 422 with field `expense_account_ref` and Save remains disabled"
      }
    ]
  },
  {
    "id": "US-013",
    "epic": "Durable export, retry, and reconciliation",
    "role": "bookkeeper",
    "action": "post a prepared batch to QuickBooks exactly once",
    "benefit": "retries cannot create duplicate purchases",
    "story": "As a bookkeeper, I want to post a prepared batch to QuickBooks exactly once, so that retries cannot create duplicate purchases.",
    "gui_flow": [
      "Bookkeeper opens Export Preparation \u2192 selects exportable receipts and QuickBooks Online",
      "Bookkeeper runs Preflight \u2192 sees Ready, Warning, and Blocked groups plus mapping version",
      "Bookkeeper acknowledges warning receipts \u2192 Export ready items enables",
      "Bookkeeper selects Export ready items \u2192 a queued run appears with progress",
      "Worker posts each receipt with deterministic idempotency metadata \u2192 item rows update independently",
      "Run completes \u2192 summary shows Created, Already exported, Failed, and Needs reconciliation counts"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "50 valid prepared receipts and a healthy sandbox connection",
        "when": "the export command executes twice with the same idempotency key",
        "then": "exactly 50 provider purchases exist and both calls return the same ReceiptLens run identifier"
      },
      {
        "type": "given",
        "text": "one receipt already has a successful provider link",
        "when": "a different export command includes it",
        "then": "that receipt is reported Already exported and no second provider create request is made"
      },
      {
        "type": "given",
        "text": "the provider returns HTTP 429 with Retry-After for an item",
        "when": "the worker processes the run",
        "then": "the item is retried no more than three times, other items continue, and terminal failure remains retryable"
      }
    ]
  },
  {
    "id": "US-014",
    "epic": "Durable export, retry, and reconciliation",
    "role": "bookkeeper",
    "action": "inspect every provider result and retry only failed items",
    "benefit": "partial failures can be recovered without reposting successful receipts",
    "story": "As a bookkeeper, I want to inspect every provider result and retry only failed items, so that partial failures can be recovered without reposting successful receipts.",
    "gui_flow": [
      "Bookkeeper opens Export Runs \u2192 sees destination, state, counts, and created timestamp",
      "Bookkeeper opens a partial run \u2192 sees one row per receipt and provider result",
      "Bookkeeper filters Failed \u2192 successful rows remain unchanged and hidden",
      "Bookkeeper opens a failed row \u2192 sees redacted provider error, attempt count, and next action",
      "Bookkeeper selects Retry failed items \u2192 a confirmation lists only retryable item identifiers",
      "Retry completes \u2192 rows update and the aggregate run state recalculates"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "a run contains 42 created, 5 already exported, and 3 retryable failures",
        "when": "the detail endpoint is read",
        "then": "all 50 immutable item records are returned with matching aggregate counts"
      },
      {
        "type": "given",
        "text": "a receipt changed after the original preparation",
        "when": "the user retries its failed item",
        "then": "the retry is rejected as `receipt_version_changed` and creates no provider request"
      },
      {
        "type": "given",
        "text": "a provider error contains request headers or tokens",
        "when": "the error is persisted and displayed",
        "then": "credentials are removed, the provider request ID is retained, and the payload is limited to 2 KB"
      }
    ]
  },
  {
    "id": "US-015",
    "epic": "Durable export, retry, and reconciliation",
    "role": "accountant",
    "action": "reconcile a ReceiptLens receipt with its QuickBooks purchase and attachment",
    "benefit": "I can prove what the accounting system accepted",
    "story": "As a accountant, I want to reconcile a ReceiptLens receipt with its QuickBooks purchase and attachment, so that I can prove what the accounting system accepted.",
    "gui_flow": [
      "Accountant opens a successful run item \u2192 sees ReceiptLens and provider identifiers",
      "Accountant selects Verify in QuickBooks \u2192 ReceiptLens retrieves the purchase by provider identifier",
      "Comparison panel opens \u2192 amount, currency, date, vendor, account, tax, and attachment state are shown side by side",
      "Matching values show Verified \u2192 mismatches show Needs attention with field names",
      "Accountant selects Mark resolved after correcting the provider record \u2192 verification runs again",
      "Verified result is written to receipt and run audit history with a UTC timestamp"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "provider and ReceiptLens values match for all compared fields",
        "when": "verification runs",
        "then": "the item becomes verified and records a provider sync token plus verified_at timestamp"
      },
      {
        "type": "given",
        "text": "the provider purchase exists but total differs by more than 0.01 in source currency",
        "when": "verification runs",
        "then": "the item becomes needs_reconciliation with field `total` and cannot be marked verified manually"
      },
      {
        "type": "given",
        "text": "the provider purchase was deleted",
        "when": "verification runs",
        "then": "the item becomes missing_remote, the original successful link remains in audit history, and Recreate stays disabled until a new preflight"
      }
    ]
  },
  {
    "id": "US-016",
    "epic": "Accounting projection and payload approval",
    "role": "cross-border bookkeeper",
    "action": "preserve original currency and conversion evidence from receipt through provider export",
    "benefit": "foreign receipts are not silently posted in the wrong currency",
    "story": "As a cross-border bookkeeper, I want to preserve original currency and conversion evidence from receipt through provider export, so that foreign receipts are not silently posted in the wrong currency.",
    "gui_flow": [
      "Bookkeeper opens Receipt Detail \u2192 sees Original amount, Original currency, and tenant reporting currency",
      "Bookkeeper selects Currency details \u2192 sees exchange-rate value, date, source, and conversion status",
      "Bookkeeper edits original currency \u2192 existing conversion becomes Stale and readiness recalculates",
      "Bookkeeper selects Refresh conversion \u2192 server resolves the configured dated rate",
      "Updated conversion appears \u2192 original values remain unchanged and converted values are visually secondary",
      "Bookkeeper opens Export Preflight \u2192 provider currency capability and conversion decision are explicit"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "a EUR receipt belongs to a CHF reporting tenant and a dated EUR/CHF rate exists",
        "when": "conversion is calculated",
        "then": "the original EUR amount remains unchanged and the CHF amount, rate, rate date, and source are stored together"
      },
      {
        "type": "given",
        "text": "a receipt currency equals the tenant reporting currency",
        "when": "currency details open",
        "then": "the conversion uses rate 1 with source `identity` and makes no exchange-rate lookup"
      },
      {
        "type": "given",
        "text": "no applicable rate exists",
        "when": "preflight runs",
        "then": "the receipt is blocked with `exchange_rate_missing`, no fallback rate is invented, and a deep link opens Currency details"
      }
    ]
  },
  {
    "id": "US-017",
    "epic": "Accounting projection and payload approval",
    "role": "accountant",
    "action": "review tax arithmetic and tax-code mapping before export",
    "benefit": "tax errors do not reach the ledger",
    "story": "As a accountant, I want to review tax arithmetic and tax-code mapping before export, so that tax errors do not reach the ledger.",
    "gui_flow": [
      "Accountant opens Receipt Detail \u2192 Tax panel shows net, tax, gross, and line-item totals",
      "Accountant expands Validation \u2192 arithmetic checks display pass or fail with tolerance",
      "Accountant selects provider tax treatment \u2192 compatible QuickBooks tax codes load",
      "Accountant maps the receipt tax treatment \u2192 preview shows provider payload totals",
      "Accountant saves \u2192 readiness recalculates and audit history records the mapping",
      "Accountant opens Export Preparation \u2192 tax-ready receipts appear in Ready"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "net plus tax equals gross within 0.01 source-currency units",
        "when": "validation runs",
        "then": "tax arithmetic passes and records the exact evaluated values"
      },
      {
        "type": "given",
        "text": "line items contain mixed tax rates",
        "when": "validation runs",
        "then": "the receipt is warning or blocked according to mapping completeness and each unmapped line identifies its index"
      },
      {
        "type": "given",
        "text": "tax exceeds gross or is negative",
        "when": "validation runs",
        "then": "the receipt is blocked with a stable error code and no provider payload is generated"
      }
    ]
  },
  {
    "id": "US-018",
    "epic": "Accounting projection and payload approval",
    "role": "finance reviewer",
    "action": "see the exact provider payload preview without secrets before posting",
    "benefit": "I can approve the accounting interpretation",
    "story": "As a finance reviewer, I want to see the exact provider payload preview without secrets before posting, so that I can approve the accounting interpretation.",
    "gui_flow": [
      "Reviewer opens Export Preflight \u2192 selects a Ready receipt",
      "Reviewer selects Preview provider payload \u2192 a read-only structured panel opens",
      "Panel shows purchase date, source and provider currencies, lines, accounts, tax codes, memo, and attachment filename",
      "Sensitive OAuth data and binary attachment bytes are absent \u2192 redaction note is visible",
      "Reviewer compares totals \u2192 calculated provider total and source total show their tolerance",
      "Reviewer closes preview \u2192 selected receipts and warning acknowledgements remain unchanged"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "a mapped foreign-currency receipt is ready",
        "when": "payload preview is requested",
        "then": "the response is deterministic for the preparation and includes mapping_version and receipt_version"
      },
      {
        "type": "given",
        "text": "the receipt changes after preparation",
        "when": "payload preview is requested",
        "then": "the API returns 409 `preparation_stale` and the UI preserves selection while offering Run preflight again"
      },
      {
        "type": "given",
        "text": "a non-admin/non-reviewer role requests preview",
        "when": "the endpoint is called",
        "then": "the API returns 403 and records no payload content in logs"
      }
    ]
  }
]
```

## Product Requirements
### A. Complete QuickBooks connected workflow
**Evidence/stories:** accounting integration table stakes and opaque sync complaints; US-010..012.

- Replace the informational Connect button with a working call to `POST /product/connections/quickbooks/oauth/start`; navigate only to the returned fixed Intuit URL.
- Start returns 503 `credential_store_unavailable` when the 32-byte key or Intuit client configuration is absent. It never returns OAuth state separately from the authorization URL.
- Implement Authorization Code + PKCE. Persist encrypted verifier; callback validates state, tenant binding, expiry, single use, provider errors, and realm ID, then exchanges code at Intuit's fixed token endpoint.
- Callback tenant is recovered only from the stored state record. It must not depend on browser `X-Tenant-ID` headers, which are unavailable on provider redirect.
- Store AES-GCM ciphertext with key version and expiry; refresh once on 401/expired credential; atomically replace rotated refresh tokens; `invalid_grant` marks reauthorization required.
- Implement test, reconnect, disconnect/revoke, reference list, mapping validate, mapping save, connection detail, and redacted audit endpoints exactly as specified below.
- Mapping validation requires active expense account, optional payment account, tax strategy, vendor fallback, attachment policy, and a reference snapshot no older than 15 minutes.
- UI must implement disconnected, callback success/error, healthy, expiring, reauthorization, loading, empty references, validation errors, save success, and disconnect confirmation.
- Backward compatibility: legacy CSV/quickbooks/xero connection creation and current list/test APIs continue unchanged. New OAuth connection provider is `quickbooks_online`.
- Non-goals: Xero, invoices/bills, production login, provider certification.

### B. Durable export, retry, and reconciliation
**Evidence/stories:** matching/reconciliation and duplicate risk; US-013..015.

- Extend existing provider runs rather than creating a parallel unreferenced path. QuickBooks command creates a queued run and one item per valid receipt, returns HTTP 202, and commits before provider I/O.
- Implement a worker service with atomic claim, lease expiry, restart recovery, and no network call inside a SQLite write transaction.
- Dedupe key includes tenant, provider, connection, receipt ID/version, mapping version, and operation. Existing successful provider link yields `already_exported` without API create.
- Retry 429, 5xx, timeout, and transport errors at 1/4/16 seconds or provider Retry-After, maximum three attempts. Persist `next_attempt_at`. 4xx validation is terminal. Auth failure pauses unattempted items and connection.
- Upload source attachment only after purchase creation; attachment failure produces `needs_reconciliation`, not a second purchase.
- Add run list/detail, filtered/paginated items, item detail, retry eligible failures, and verify endpoints.
- Retry rejects changed receipt/mapping versions, never reposts successful items, and records exclusions.
- Verification compares date, currency, total tolerance 0.01, vendor/account/tax references, and attachment state. Persist immutable snapshots.
- UI polls every 2 seconds while active, stops terminally, announces changes accessibly, and supports partial failure and reconnect recovery.
- Non-goals: provider deletion, automatic remote recreation, webhooks, batches above 200.

### C. Accounting projection and payload approval
**Evidence/stories:** foreign-currency and tax errors; US-016..018.

- Mark projections stale whenever total, tax, currency, date, or line items change. Projection refresh must use current receipt version and newest tenant-admin rate on/before receipt date; identity rate is explicit.
- Store Decimal strings, not floats. Support ISO currencies configured by the project; quantize using declared minor units, default 2 only when configured.
- Tax validation returns stable field/line codes for negative tax, tax over gross, net+tax mismatch, line sum mismatch, mixed rates, and unmapped provider codes.
- Integrate projection/tax issues into accounting readiness. Missing rate or impossible tax blocks export. Tolerance-only mismatch is warning. Mapping omissions deep-link to mapping.
- Provider preview is generated from immutable preparation snapshot, pinned mapping, projection, receipt version, and attachment metadata. It is role-limited to admin/reviewer, redacted, deterministic, and never raw-byte/credential-bearing.
- Receipt Accounting tab must show source and reporting values, rate/date/source, stale state, refresh, tax arithmetic, line issues, loading/error/success/recovery.
- Export Preparation must show destination/mapping version, projections, deep links, structured provider preview drawer, warning acknowledgement, and stale-preparation recovery without losing selection.
- Non-goals: tax filing/advice, rate download, cryptocurrency.

## UI and UX Specification
### Personas and primary journey
Admin connects and maps QuickBooks; bookkeeper fixes accounting blockers and exports; accountant retries/reconciles; reviewer approves the provider interpretation. Primary journey: Integrations → QuickBooks detail/Mapping → Receipt Accounting → Export Preparation/Preview → Run Detail → Item Reconciliation.

### Information architecture and design system
Keep existing sidebar and routes. Add no top-level item. Reuse Tailwind and current `card`, buttons, Modal, Toast, WorkflowState, Skeleton, StatusBadge. Add shared components only when used on at least two screens. WCAG 2.2 AA contrast, 44 px targets, 2 px focus ring plus offset, reduced motion, semantic headings, and no color-only status.

### Responsive and accessibility contract
- Mobile <760 px: stacked content, cards instead of wide tables, sticky bottom primary action.
- Tablet 760–1049 px: two-column mapping/accounting layouts where space permits.
- Desktop ≥1050 px: sidebar plus 12-column content, split comparison and persistent summary rail.
- Error submission focuses summary; summary links focus invalid field. Route headings receive focus after callback redirect. Dialogs trap focus and return it. Live run updates use polite announcements throttled to five seconds.

### First-use guidance
Integrations checklist derives from server state: Connect company, Validate mapping, Export first receipt. Each complete step uses icon plus text. When configuration is missing, show `Administrator setup required` with exact missing variable names but never values.

## Screen Inventory and User Flows
### 1. Integrations `/integrations`
Header plus provider cards. QuickBooks card reflects server state, not hardcoded `Not connected`. Disconnected primary `Connect QuickBooks`; healthy primary `Open connection`; reauthorization primary `Reconnect QuickBooks`. Loading skeleton keeps dimensions. Fetch error retains last data with `Retry status`. Callback query renders focused success/error banner and removes sensitive query parameters via router replace.

### 2. QuickBooks detail `/integrations/quickbooks/[id]`
Header: company, sandbox badge, health, Test connection, Disconnect menu. Tabs Overview, Mapping, Audit. Overview shows scopes, token expiry category not exact token, last test, company suffix. Mapping has expense/payment accounts, vendor fallback, tax strategy/code, attachment policy, Validate then Save. Audit is redacted. Empty-reference state has Retry provider data. Disconnect modal exact action `Disconnect QuickBooks`.

### 3. Receipt Accounting `/receipts/[id]?tab=accounting`
Existing header and tabs. Two-column Source values/Reporting values, then Tax validation and line issues. Primary `Refresh conversion`; secondary links `Edit receipt` and `Add exchange rate`. Missing rate and stale projection explain impact. Success shows rate provenance and updated UTC time. Image/detail remain usable if projection API fails.

### 4. Export Preparation `/exports/prepare`
Destination selector, receipt selection, `Run preflight`. Results show Ready/Warning/Blocked counts, connection and mapping version, projection summary, expandable stable codes/deep links. Ready row `Preview provider payload`. Structured drawer groups header, lines, tax, accounts, attachment, snapshot. Sticky action contains warning acknowledgements and `Export ready items`. Stale 409 preserves selection and replaces CTA with `Run preflight again`.

### 5. Export Runs `/exports`
Existing connection/history screen gains provider run list with destination, company, counts, status, timestamp, `Open run`. Loading, no runs, failed load, pagination, and reconnect banner specified.

### 6. Provider Run Detail `/exports/runs/[id]`
Header, text progress, Created/Already exported/Failed/Needs reconciliation cards, URL-backed filters. Desktop table/mobile cards. Failed row drawer has safe code, request ID, attempts, next retry, version conflict. `Retry failed items` confirmation enumerates eligible/excluded counts. Poll active run every two seconds.

### 7. Reconciliation `/exports/runs/[id]/items/[itemId]`
ReceiptLens vs QuickBooks comparison with Match/Mismatch text and icons for date, currency, total, vendor, account, tax, attachment. Primary `Verify in QuickBooks`; links to receipt and allowlisted provider host. Missing remote gives `Run a new preflight`, never Recreate. Previous snapshot stays visible on retryable fetch failure.

### 8. Connection-loss recovery
Banner on preparation/run pages. Admin action `Reconnect QuickBooks`; non-admin text `Ask an administrator`. Run and selection state remain. After callback, return to prior route stored in the state allowlist.

### End-to-end success/failure
Success: connect → callback → validate/save mapping → add/refresh rate → preflight → preview → export → worker creates and attaches → run completes → verify remote. Failure: token invalid_grant pauses items → reconnect → retry eligible → successful links skipped → attachment mismatch reconciled.

### UI verification
Install Chromium before test. Capture and inspect 1440×900 and 390×844 screenshots for disconnected/connected Integrations, mapping validation error/success, missing-rate/resolved Accounting, blocked/ready Preflight, partial/completed Run, mismatch/verified Reconciliation. Run axe on all eight states with zero critical/serious violations. Generated images/traces are evidence only and excluded from final package unless repository policy explicitly tracks them.

## Architecture and Technical Design
### Boundaries
Strengthen existing modules rather than introduce duplicates:
- `credential_store.py`: key versions, encrypt/decrypt, rotation helper, fail-closed configuration.
- `connection_service.py`: PKCE/state/callback lifecycle, token refresh/revoke, references/cache/mappings/audit.
- `quickbooks_connector.py`: fixed-host OAuth and accounting HTTP adapter with typed provider errors and request IDs.
- `provider_export_service.py`: durable run/item queue, leases, attempts, retry, attachment, aggregate status.
- `reconciliation_service.py`: normalized remote comparison and snapshots.
- `accounting_projection.py`: Decimal/minor units, staleness, validation, snapshot preview.
- `product_api.py`: dependency initialization, exact endpoints, stable error mapping.
- Frontend API/types/hooks/components and route pages consume real endpoints. No production mock data.

### State/data flow
OAuth callback resolves tenant through state hash. SWR cache keys remain route/tenant scoped. Mutations revalidate connection/preparation/run. Worker entrypoint `process_due(limit, now)` is deterministic and can run in-process in tests; add CLI `receipts-lens provider-worker --once|--poll-seconds` for deployment without a queue dependency.

### Error/logging
Stable codes from prior plan plus `provider_attachment_failed`, `provider_lease_lost`, `mapping_snapshot_stale`. JSON errors: code, message, field/path, retryable, provider_request_id. Structured logs use tenant hash and IDs; never callback URL, auth header, receipt image/text, token, verifier, code, or raw provider body.

### Dependency decision
No new runtime dependency. `cryptography`, `httpx`, pytest, Playwright, and axe already exist. Add pytest coverage tooling to dev extras only if repository tooling requires reproducibility; update lockfile.

### Alternatives rejected
New provider service stack, synchronous request posting, raw JSON-only UI, manual retry by creating another preparation, source-value mutation, and simultaneous Xero remain rejected.

## Data, API, and Compatibility Changes
### Schema completion
Migrate existing foundation tables additively: OAuth encrypted verifier/key version/provider error; connection environment/scopes/expiry/disconnect; mapping reference snapshot JSON; run lease/heartbeat/counts/completed; item retryable/next attempt/provider request/attachment/reconciliation; provider link mapping version/dedupe; immutable reconciliation snapshots; accounting projection tax/line validation/stale reason/minor unit. Add indexes for due items, tenant runs, state expiry, and links. Migration from current archive schema must be tested twice for idempotency.

### Exact API contract
- `POST /product/connections/quickbooks/oauth/start` body `{return_path}` → 201 `{authorization_url,state_expires_at}`.
- `GET /product/connections/quickbooks/oauth/callback` validates provider query and returns 303 only to allowlisted local paths.
- `GET /product/connections/{id}`; `POST /test`; `POST /disconnect`.
- `GET /product/connections/{id}/references?kind=accounts|tax_codes|vendors`.
- `POST /product/connections/{id}/mappings/validate`; `POST /mappings`; `GET /mappings/current`.
- `POST /product/export-preparations` response extends with provider, mapping_version, projections, snapshot_hash.
- `GET /product/export-preparations/{prep}/receipts/{receipt}/payload-preview`.
- `POST /product/export-commands`: CSV remains 200 synchronous; QBO returns 202 durable run.
- `GET /product/provider-export-runs`; `GET /{run}`; `GET /{run}/items`; `GET /{run}/items/{item}`.
- `POST /product/provider-export-runs/{run}/retry` body item IDs.
- `POST /product/provider-export-runs/{run}/items/{item}/verify`.
- `GET /product/receipts/{id}/accounting-projection`; `POST /refresh`.
- Existing APIs, response fields, CSV path, and legacy connection behavior stay compatible.

## Security and Privacy Considerations
PKCE verifier and tokens encrypted AES-GCM with key version; state random/hashed/single-use/10-minute; callback tenant from state only; fixed Intuit hosts; return path allowlist; no open redirect; strict role matrix; tenant predicate in every query; external link allowlist; attachment magic/size validation; error redaction limited 2 KB; diagnostic bundle excludes provider secrets; disconnect revokes then deletes active ciphertext while retaining audit links; expired states purged. Seeded-secret tests inspect responses, logs, audit, diagnostics, and SQLite outside credential blob.

## Test Strategy (TDD)
### RED tests
Split the combined service test into `test_us_010_...` through `test_us_018_...`, with at least three criteria-named tests per story. First add failing API tests, then implementation; then failing Playwright story flows, then UI. Preserve concise RED/GREEN output in development report.

### Unit/integration
- OAuth PKCE, callback without headers, expiry/replay/cross-tenant/open redirect, encryption/key versions, refresh rotation/invalid_grant/revoke.
- Mapping cache, inactive refs, snapshot freshness, validation fields.
- Real SQLite restart, lease recovery, 50-item replay, Retry-After injectable clock, auth pause, attachment partial failure, retry inclusion/exclusion.
- Reconciliation all fields/missing remote/snapshot immutability.
- Decimal minor units, rate dates, identity/missing, projection stale triggers, tax mixed lines, readiness blockers, preview hash/redaction/RBAC.
- `httpx.MockTransport` covers every QuickBooks adapter method. Opt-in `qbo_sandbox` test is release-required but credentialless CI may skip transparently.

### E2E/accessibility
Playwright tagged US-010..018. Use a test-only provider transport injected server-side, not browser production mocks. Verify all screens, focus, keyboard, mobile, stale-data recovery, reconnect return, and axe.

### Commands
- Targeted story files, then affected regressions, then `pytest -q`.
- Coverage over all six provider modules with `--cov-fail-under=90`; credential/connection branch target 100%.
- `python -m ruff check app tests`; `npm ci`; typecheck; build; Playwright install/test.
- Backend/frontend startup/check `/health`, `/ready`, `/integrations`.
- All repository gates and git push verification.

### Pass criteria
All 27 acceptance criteria have API/service tests and applicable E2E. US-010..018 each PASS, not PARTIAL. New modules ≥90%, credential/state 100% branch. Zero regression failures. Real sandbox test passes before release. Playwright/axe and screenshot inspection complete. No secret markers escape.

## Documentation Deliverables
README: configuration, worker, full user journey, troubleshooting, sandbox warning. CHANGELOG. `docs/quickbooks-online.md`: real endpoint/scopes/setup/reconnect/runbook. API and accounting export guides with exact shapes/status codes. CLI docs for worker. FEATURES-DONE only for fully PASS stories. Development report with RED/GREEN, sandbox status, coverage, gates, screenshot evidence, migration, integrity, traceability, blocked items, commit.

## Expected File Changes
Modify the seven provider foundation modules, `product_api.py`, service startup, CLI, dependency metadata/lock, export/accounting integration, frontend API/types/routes/components, story tests, Playwright, gates, README/CHANGELOG/docs/FEATURES-DONE/development-report. Add QuickBooks detail, reconciliation route, shared provider UI components, and split acceptance tests. Do not change research findings or this plan during development unless a proven contradiction is logged.

## Traceability Matrix
| Research need | Evidence | Story | Requirement | Acceptance | Implementation | Test evidence | Priority |
|---|---|---|---|---|---|---|---|
| Connected provider | Integration table stakes | US-010 | Real start/callback/PKCE | Success, replay, timeout criteria | connection/QBO/API/UI | OAuth API + E2E | P0 |
| Credential continuity | Opaque sync complaints | US-011 | Refresh/health/reconnect/disconnect | Refresh rotation and invalid_grant | credential/connection/detail UI | transport/API/E2E | P0 |
| Safe mapping | Currency/tax mismatch evidence | US-012 | References and immutable mapping | valid, drift, validation criteria | connection/API/mapping UI | mapping API/E2E | P0 |
| Zero duplicate posting | Research exit metric | US-013 | Durable queue/dedupe/retry | replay, prior link, 429 criteria | provider export/worker | restart/fake provider | P0 |
| Partial recovery | Sync reliability pain | US-014 | Item detail/retry/redaction | aggregate, version, safe error | run APIs/UI | API/E2E | P0 |
| Prove remote result | Reconciliation pain | US-015 | Remote comparison/snapshot | match, mismatch, missing criteria | reconciliation/UI | transport/E2E | P0 |
| Preserve currency | Foreign-currency complaint | US-016 | Projection/staleness/rates | foreign, identity, missing criteria | projection/readiness/UI | Decimal/API/E2E | P0 |
| Prevent tax errors | Tax rework complaint | US-017 | Arithmetic/line mapping | tolerance, mixed, impossible criteria | projection/mapping/UI | unit/API/E2E | P0 |
| Approve interpretation | Transparent preflight | US-018 | Redacted snapshot preview | deterministic, stale, RBAC criteria | preview API/drawer | hash/log/E2E | P0 |

## Risks and Mitigations
Provider drift: centralized adapter and MockTransport contracts. Credentials: AES-GCM, key versions, redaction, fail closed. Duplicate entries: links, dedupe, leases, restart tests. SQLite contention: short claims and no network in transactions. Auth loss: pause/reconnect/resume. Attachment partial failures: never recreate purchase. Tax/FX: Decimal, provenance, blockers, no advice. Scope risk: this pass completes existing stories only, and FEATURES-DONE cannot list PARTIAL work. Tooling: install browser/ruff before implementation and treat unavailable tools as blocker, not substitute verification.

## Definition of Done
- [ ] US-010..018 are PASS end to end; no PARTIAL story is listed as done.
- [ ] All planned APIs and all seven screens work with real server state.
- [ ] 50-item replay, restart, Retry-After, auth pause/reconnect, attachment, retry, and reconciliation tests pass.
- [ ] Projection/tax/readiness/preview tests and UI flows pass.
- [ ] Real QBO sandbox create/get/verify passes before release or release is BLOCKED.
- [ ] Every acceptance criterion maps to RED/GREEN evidence.
- [ ] Coverage, security, regression, lint, typecheck, build, startup, Playwright, axe, screenshots pass.
- [ ] All lab gates and `git-push-verify.sh` pass; absent Git remote is BLOCKED.
- [ ] Documentation exactly matches behavior; FEATURES-DONE lists only complete stories.
- [ ] Migration from current archive is idempotent and restart-safe.
- [ ] No secrets, caches, dependencies, build output, traces, or scratch artifacts remain.
- [ ] Baseline reconciliation and complete-project ZIP verification pass.
