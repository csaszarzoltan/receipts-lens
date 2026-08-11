# Implementation Plan

## Executive Summary
This pass advances ReceiptLens from a provider-neutral exception-to-export product into a **single-provider, sandbox-verified accounting integration**. The selected scope is deliberately one coherent daily-close path: (1) QuickBooks Online sandbox OAuth and versioned mapping, (2) replay-safe posting with per-item reconciliation and recovery, and (3) source-currency/tax provenance from receipt through provider payload preview. It covers nine new BDD stories, US-010 through US-018.

The plan builds on the completed US-001 through US-009 workflow rather than reopening it. QuickBooks Online is the only live provider in scope. Xero, production identity, billing, jurisdiction-specific tax advice, and autonomous currency-rate fetching are deferred. Existing CSV export, demo header identity, OCR, review, automation, and all legacy endpoints remain compatible.

The implementation must use the existing FastAPI, SQLite, Next.js 14, SWR, Tailwind, pytest, and Playwright stack. Add only the official Intuit OAuth/API client boundary implemented with the existing `httpx`; do not add a provider SDK. Provider I/O must be behind an interface so deterministic fake-server integration tests can run without credentials, while one opt-in sandbox test proves the real contract when credentials are available.

## Current-State Validation
- ReceiptLens 1.4.0 already provides tenant-scoped receipts, optimistic versions, accounting readiness, provider-neutral connections, immutable preparations, idempotent export commands, artifacts, audit history, and a Next.js export UI (`app/product_service.py`, `app/accounting_workspace.py`, `app/export_workflow.py`, `app/product_api.py`, `frontend/app/(app)/exports/**`).
- The completed development report confirms US-001 through US-009 pass and identifies the next product limitations: CSV-only export, header-based demo identity, no live provider posting, 79% measured coverage in selected workflow modules, and unavailable browser screenshots in that environment (`development-report.md`).
- Research prioritizes one provider sandbox deeply before adding a second, and separately identifies multi-currency/tax preservation as P1 because accounting integrations, reconciliation, and currency mistakes drive user pain (`research-findings.md`, Differentiation Opportunities and Priority-Ranked Development Recommendations).
- Existing `connections` records and `Connection` frontend type model provider/name/mapping but not OAuth state, encrypted credentials, provider company metadata, mapping versions, provider links, item attempts, or reconciliation snapshots. Additive schema migration is required.
- The app already depends on `httpx`, so no new Python runtime package is necessary. Built-in `secrets`, `hashlib`, `hmac`, `base64`, and an environment-supplied 32-byte key are sufficient for state generation and authenticated token encryption using a new repository-local AES-free encrypt-then-MAC construction only if cryptography is unavailable. Preferred decision: add `cryptography>=43` because authenticated encryption for OAuth tokens must not be hand-rolled.
- A real product UI is appropriate and already exists. This is an enhancement to Integrations, Export Preparation, Export Runs, and Receipt Detail, not a frontend rewrite.

## Research Priorities
| Rank | Candidate | Decision | Evidence-to-risk rationale |
|---|---|---|---|
| P0 | QuickBooks Online sandbox connector | Select | Research says accounting integration is table stakes and recommends one provider sandbox deeply; provider-neutral preflight is already complete. |
| P0 | Replay-safe posting and reconciliation | Select | User pain centers on matching and opaque sync; idempotent commands and receipt versions provide a strong base. |
| P0 | Source-currency and tax provenance | Select | Currency/tax mistakes are directly reported and the project already has rate and validation primitives. |
| P1 | Xero connector | Defer | Simultaneous providers would duplicate OAuth, mapping, and reconciliation risk before the first contract is proven. |
| P1 | Production identity/SSO | Defer | Required before public production, but not necessary to prove the sandbox integration contract; current role checks remain explicit. |
| P2 | Billing and usage enforcement | Defer | Requires activation and cost telemetry after provider workflow validation. |
| P2 | New OCR provider/model | Defer | No benchmark evidence justifies changing extraction in this pass. |

## Selected Scope for This Pass
### Feature A: QuickBooks Online sandbox connector
Implement admin-only OAuth 2.0 Authorization Code with PKCE/state, encrypted token storage, company discovery, connection health, disconnect, and immutable mapping versions. Stories: US-010, US-011, US-012.

### Feature B: Reconciled and replay-safe provider export
Extend the existing preparation/command model with queued per-item provider posting, deterministic deduplication, rate-limit retry, immutable item attempts, run detail, failed-item retry, remote verification, and reconciliation status. Stories: US-013, US-014, US-015.

### Feature C: Source-currency and tax provenance
Preserve original and reporting values, dated-rate provenance, arithmetic validation, provider tax-code mapping, and a redacted deterministic provider-payload preview tied to preparation and mapping versions. Stories: US-016, US-017, US-018.

Scope boundary: complete the connected QuickBooks sandbox path for purchase/expense-style transactions only. Do not implement invoices, bills, payments, reimbursements, cards, payroll, bank-feed matching, or production certification.

## Deferred Scope and Rationale
1. **Xero OAuth and posting:** next provider-adapter phase after QuickBooks contract, retry, and reconciliation metrics are green.
2. **Production authentication, SSO, and invite acceptance:** dedicated identity phase; prerequisite for public multi-tenant hosting.
3. **Jurisdiction-specific VAT/GST advice:** tax-domain phase with accountant-reviewed country fixtures and legal wording.
4. **Automatic third-party FX-rate fetching:** integration phase after data-source licensing, cache, and outage policy are chosen. This pass accepts tenant-admin supplied rates only.
5. **Provider webhooks and bidirectional updates:** reconciliation phase after outbound links are proven; polling verification is sufficient here.
6. **Xero/QuickBooks simultaneous launch or provider certification:** operational release phase with real partner accounts.
7. **Billing, quotas, and usage-based pricing:** commercial experiment phase after sandbox-to-beta conversion data.
8. **Production migration from SQLite to PostgreSQL:** scale phase; new services must remain repository-interface compatible.
9. **Legacy `/workspace` removal:** frontend consolidation phase; no behavior changes in this pass.
10. **OCR model/provider changes:** quality phase only when labelled benchmark evidence identifies a segment-specific gap.

## User Stories (BDD)
```json
[
  {
    "id": "US-010",
    "epic": "QuickBooks Online sandbox connector",
    "role": "tenant administrator",
    "action": "connect a QuickBooks Online sandbox company through OAuth",
    "benefit": "approved receipts can be posted without copying CSV files",
    "story": "As a tenant administrator, I want to connect a QuickBooks Online sandbox company through OAuth, so that approved receipts can be posted without copying CSV files.",
    "gui_flow": [
      "Administrator opens Integrations → sees QuickBooks Online marked Not connected",
      "Administrator selects Connect QuickBooks → sees a disclosure of requested scopes and data use",
      "Administrator selects Continue to Intuit → browser is redirected to the provider authorization URL with state and PKCE parameters",
      "Provider callback returns → ReceiptLens validates state, stores encrypted tokens, and shows the selected company name",
      "Administrator selects Test connection → sees Connected, company identifier suffix, and last-tested timestamp",
      "Administrator opens Export Preparation → QuickBooks Online is available as a destination"
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
    "epic": "QuickBooks Online sandbox connector",
    "role": "tenant administrator",
    "action": "inspect and refresh the accounting connection",
    "benefit": "expired credentials do not interrupt an export unexpectedly",
    "story": "As a tenant administrator, I want to inspect and refresh the accounting connection, so that expired credentials do not interrupt an export unexpectedly.",
    "gui_flow": [
      "Administrator opens Integrations → sees connection health, scope summary, and token expiry status",
      "Administrator selects Test connection → ReceiptLens requests provider company information",
      "Successful response appears → status changes to Healthy with a UTC timestamp",
      "Administrator selects Refresh authorization when consent is stale → a new OAuth flow begins",
      "Administrator returns from provider → the existing connection is updated rather than duplicated",
      "Administrator selects Disconnect → a confirmation dialog explains queued exports will stop"
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
    "epic": "QuickBooks Online sandbox connector",
    "role": "integrator",
    "action": "map ReceiptLens fields to QuickBooks purchase fields and validate the mapping",
    "benefit": "posting failures are caught before an export run",
    "story": "As a integrator, I want to map ReceiptLens fields to QuickBooks purchase fields and validate the mapping, so that posting failures are caught before an export run.",
    "gui_flow": [
      "Integrator opens QuickBooks connection detail → sees the Mapping tab",
      "Integrator chooses expense account, payment account, tax treatment, vendor fallback, and attachment behavior",
      "Integrator selects Validate mapping → server checks required fields and provider references",
      "Valid mapping appears → each row shows Ready and the Save mapping button enables",
      "Integrator saves → mapping version and editor role appear in the audit panel",
      "Integrator opens Export Preparation → preflight uses the saved mapping version"
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
    "epic": "Reconciled and replay-safe provider export",
    "role": "bookkeeper",
    "action": "post a prepared batch to QuickBooks exactly once",
    "benefit": "retries cannot create duplicate purchases",
    "story": "As a bookkeeper, I want to post a prepared batch to QuickBooks exactly once, so that retries cannot create duplicate purchases.",
    "gui_flow": [
      "Bookkeeper opens Export Preparation → selects exportable receipts and QuickBooks Online",
      "Bookkeeper runs Preflight → sees Ready, Warning, and Blocked groups plus mapping version",
      "Bookkeeper acknowledges warning receipts → Export ready items enables",
      "Bookkeeper selects Export ready items → a queued run appears with progress",
      "Worker posts each receipt with deterministic idempotency metadata → item rows update independently",
      "Run completes → summary shows Created, Already exported, Failed, and Needs reconciliation counts"
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
    "epic": "Reconciled and replay-safe provider export",
    "role": "bookkeeper",
    "action": "inspect every provider result and retry only failed items",
    "benefit": "partial failures can be recovered without reposting successful receipts",
    "story": "As a bookkeeper, I want to inspect every provider result and retry only failed items, so that partial failures can be recovered without reposting successful receipts.",
    "gui_flow": [
      "Bookkeeper opens Export Runs → sees destination, state, counts, and created timestamp",
      "Bookkeeper opens a partial run → sees one row per receipt and provider result",
      "Bookkeeper filters Failed → successful rows remain unchanged and hidden",
      "Bookkeeper opens a failed row → sees redacted provider error, attempt count, and next action",
      "Bookkeeper selects Retry failed items → a confirmation lists only retryable item identifiers",
      "Retry completes → rows update and the aggregate run state recalculates"
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
    "epic": "Reconciled and replay-safe provider export",
    "role": "accountant",
    "action": "reconcile a ReceiptLens receipt with its QuickBooks purchase and attachment",
    "benefit": "I can prove what the accounting system accepted",
    "story": "As a accountant, I want to reconcile a ReceiptLens receipt with its QuickBooks purchase and attachment, so that I can prove what the accounting system accepted.",
    "gui_flow": [
      "Accountant opens a successful run item → sees ReceiptLens and provider identifiers",
      "Accountant selects Verify in QuickBooks → ReceiptLens retrieves the purchase by provider identifier",
      "Comparison panel opens → amount, currency, date, vendor, account, tax, and attachment state are shown side by side",
      "Matching values show Verified → mismatches show Needs attention with field names",
      "Accountant selects Mark resolved after correcting the provider record → verification runs again",
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
    "epic": "Source-currency and tax provenance",
    "role": "cross-border bookkeeper",
    "action": "preserve original currency and conversion evidence from receipt through provider export",
    "benefit": "foreign receipts are not silently posted in the wrong currency",
    "story": "As a cross-border bookkeeper, I want to preserve original currency and conversion evidence from receipt through provider export, so that foreign receipts are not silently posted in the wrong currency.",
    "gui_flow": [
      "Bookkeeper opens Receipt Detail → sees Original amount, Original currency, and tenant reporting currency",
      "Bookkeeper selects Currency details → sees exchange-rate value, date, source, and conversion status",
      "Bookkeeper edits original currency → existing conversion becomes Stale and readiness recalculates",
      "Bookkeeper selects Refresh conversion → server resolves the configured dated rate",
      "Updated conversion appears → original values remain unchanged and converted values are visually secondary",
      "Bookkeeper opens Export Preflight → provider currency capability and conversion decision are explicit"
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
    "epic": "Source-currency and tax provenance",
    "role": "accountant",
    "action": "review tax arithmetic and tax-code mapping before export",
    "benefit": "tax errors do not reach the ledger",
    "story": "As a accountant, I want to review tax arithmetic and tax-code mapping before export, so that tax errors do not reach the ledger.",
    "gui_flow": [
      "Accountant opens Receipt Detail → Tax panel shows net, tax, gross, and line-item totals",
      "Accountant expands Validation → arithmetic checks display pass or fail with tolerance",
      "Accountant selects provider tax treatment → compatible QuickBooks tax codes load",
      "Accountant maps the receipt tax treatment → preview shows provider payload totals",
      "Accountant saves → readiness recalculates and audit history records the mapping",
      "Accountant opens Export Preparation → tax-ready receipts appear in Ready"
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
    "epic": "Source-currency and tax provenance",
    "role": "finance reviewer",
    "action": "see the exact provider payload preview without secrets before posting",
    "benefit": "I can approve the accounting interpretation",
    "story": "As a finance reviewer, I want to see the exact provider payload preview without secrets before posting, so that I can approve the accounting interpretation.",
    "gui_flow": [
      "Reviewer opens Export Preflight → selects a Ready receipt",
      "Reviewer selects Preview provider payload → a read-only structured panel opens",
      "Panel shows purchase date, source and provider currencies, lines, accounts, tax codes, memo, and attachment filename",
      "Sensitive OAuth data and binary attachment bytes are absent → redaction note is visible",
      "Reviewer compares totals → calculated provider total and source total show their tolerance",
      "Reviewer closes preview → selected receipts and warning acknowledgements remain unchanged"
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
### A. QuickBooks Online sandbox connector
**Problem/evidence:** research identifies accounting integration as table stakes and recommends one sandbox implementation. Existing CSV export does not complete the ledger outcome.

**Functional contract**
- Add provider value `quickbooks_online`; retain `csv`, `quickbooks`, and `xero` legacy values as accepted inputs but do not reinterpret them.
- OAuth is admin-only. Start endpoint generates 32-byte state, PKCE verifier/challenge, tenant binding, 10-minute expiry, single-use status, and normalized return path allowlisted to `/integrations`.
- Callback validates state, tenant binding, expiry, single use, and provider error before token exchange. Never accept tenant identity from callback query parameters.
- Store access and refresh tokens only as authenticated ciphertext. Master key comes from `RECEIPTLENS_CREDENTIAL_KEY`; startup remains available without it, but OAuth start returns 503 `credential_store_unavailable`.
- Do not return tokens, verifier, ciphertext, client secret, or authorization code in API responses, errors, logs, diagnostics, or audit records.
- Test connection calls provider company-info. One token refresh and one request retry are allowed for an expired token. `invalid_grant` marks `reauthorization_required`.
- Mapping versions contain expense account, payment account when applicable, vendor fallback, tax strategy, attachment behavior, and provider reference snapshots. Saving creates a new immutable version; preparations pin a version.

**Validation/business rules**
- Provider realm/company identifier is unique per tenant/provider active connection.
- Disconnect revokes remotely when possible, deletes ciphertext locally in the same transaction, sets disconnected, and does not delete historical links/audit.
- The provider base URL is fixed by `RECEIPTLENS_QBO_ENV` (`sandbox` default, `production` allowed only with `RECEIPTLENS_ALLOW_PRODUCTION_QBO=true`). User-supplied URLs are forbidden.
- Mapping validation checks provider references using a cached provider account/tax-code list no older than 15 minutes; stale cache triggers refresh.

**Acceptance:** every criterion in US-010..012; 100% branch coverage for state validation and token redaction; no plaintext token in SQLite inspection test.

**Non-goals:** production IdP login, Xero, provider certification, invoices/bills, bank-feed matching.

### B. Reconciled and replay-safe provider export
**Functional contract**
- Existing `POST /product/export-commands` remains synchronous for CSV. For a `quickbooks_online` preparation it creates a durable queued run and item rows, returning HTTP 202.
- Deterministic dedupe key is SHA-256 of tenant, provider, connection, receipt ID, receipt version, mapping version, and operation type. A successful provider link prevents a second create under any command key.
- Worker claims queued items atomically, posts one purchase plus optional receipt attachment, records request ID, provider ID, sync token, attempt count, timestamps, redacted error, and resulting status.
- Retry policy: 429/5xx/network errors respect Retry-After, exponential schedule 1/4/16 seconds in tests through injectable clock, maximum three attempts. 4xx validation errors are terminal non-retryable. Authentication errors pause connection and remaining unattempted items.
- Retry-failed endpoint creates new attempts only for retryable failed items whose receipt/mapping versions still match.
- Reconciliation fetches remote purchase and compares date, total tolerance 0.01 source currency, currency, vendor reference, account, tax, and attachment state. Status is `verified`, `needs_reconciliation`, or `missing_remote`; users cannot manually override comparison.

**Compatibility:** CSV artifacts and existing run responses remain unchanged. Add fields rather than rename. Existing old runs deserialize with destination `csv` and empty item list.

**Acceptance:** all US-013..015 criteria; restart test proves queued items resume without duplicate create; fake provider integration proves 50-item replay and partial retry.

**Non-goals:** inbound provider webhooks, deleting provider purchases, automatic recreation of deleted remote records, bulk sizes above 200.

### C. Source-currency and tax provenance
**Functional contract**
- Add receipt accounting projection separate from OCR payload: original currency/total/tax/net, reporting currency/amount, rate, rate date, source, conversion timestamp, and stale flag.
- Never mutate OCR original amount/currency due to conversion. Editing original currency/total marks existing conversion stale.
- Rate lookup uses newest tenant rate on or before receipt date, never after it. Identity conversion is explicit with rate 1.
- Tax validation computes net + tax versus gross and line totals using Decimal quantized to currency minor units. Floating-point arithmetic is prohibited in new money calculations.
- Provider tax-code mapping is stored in the pinned mapping version. Unmapped mixed-rate lines block; a single mapped receipt-level rate may apply only when every line shares the same rate.
- Payload preview is generated server-side from preparation snapshot, mapping version, receipt version, and accounting projection. It is never persisted with credentials and contains no binary bytes.

**Acceptance:** all US-016..018 criteria; deterministic property tests cover rounding boundaries and missing rates; preview snapshot hash is stable.

**Non-goals:** tax advice, tax filing, automatic rate-provider calls, cryptocurrency, unsupported currencies outside ISO 4217 configured list.

## UI and UX Specification
### Personas and journey
- **Tenant administrator:** connects and monitors QuickBooks, manages consent, disconnects safely.
- **Integrator/accountant:** maps accounts/tax codes and resolves mapping drift.
- **Bookkeeper:** preflights, exports, watches progress, retries failures, and reconciles.
- **Finance reviewer:** inspects currency/tax evidence and provider payload before posting.

Primary journey: Integrations → Connect QuickBooks → Mapping → Receipt currency/tax review → Export Preparation → Payload preview → Export run → Retry failures → Reconcile verified result.

### Information architecture
Keep the existing sidebar. `Integrations` owns connection and mapping. `Receipts/[id]` owns source-currency/tax evidence. `Exports/prepare` owns selection and preflight. `Exports/runs/[id]` owns provider progress and reconciliation. Do not add a new top-level navigation item.

### Design system
Reuse Tailwind tokens and existing `card`, `btn-primary`, `btn-secondary`, `WorkflowState`, `StatusBadge`, `Skeleton`, `Modal`, and `Toast`. Add no component library. New provider/status colors must derive from semantic tokens: success emerald, warning amber, failure rose, information brand blue, neutral slate. Text contrast must meet WCAG 2.2 AA; controls have 44×44 px touch targets; focus ring is 2 px with 2 px offset.

### Shared states and behavior
- Every provider-mutating button disables while pending and prevents duplicate submission.
- Skeletons match final block geometry; stale data remains visible with a non-modal retry banner.
- Success uses `role=status`; blocking error uses `role=alert`; focus moves to the first error summary after failed submission and to the page heading after route transition.
- Dialog focus is trapped, Escape closes non-destructive dialogs, and focus returns to invoker. Disconnect and retry batch confirmations require explicit action labels.
- Respect `prefers-reduced-motion`; no essential state depends on animation or color.
- Mobile <760 px stacks panels and uses a sticky bottom action bar; tablet 760–1049 px uses two columns where noted; desktop ≥1050 px uses sidebar plus content and a 12-column grid.

### Onboarding/first use
When no QuickBooks connection exists, Integrations shows a three-step checklist: Connect company, Validate mapping, Export first receipt. Progress derives from server state. Existing onboarding remains unchanged; it links to this checklist after first receipt completion.

## Screen Inventory and User Flows
### 1. Integrations list, `/integrations`
**Header:** title `Integrations`; subtitle `Connect an accounting destination and verify its health.` Primary top-right action is not global; actions stay in cards.

**QuickBooks card:** logo/icon, `QuickBooks Online`, environment badge, company or `Not connected`, health, last tested. Primary action `Connect QuickBooks` or `Open connection`; secondary `Learn what is shared`. Loading uses one card skeleton. Empty provider catalog is not possible. Error preserves card metadata and shows `Retry status`.

**Flow:** Connect → consent disclosure modal → `Continue to Intuit` → redirect. Callback success returns with focused success banner `QuickBooks connected`. Callback failure returns with focused error banner and `Try again`.

### 2. QuickBooks connection detail, `/integrations/quickbooks/[id]`
**Header:** company name, environment, status badge; actions `Test connection`, overflow `Disconnect`.

**Tabs:** Overview, Mapping, Audit. Overview shows company suffix, scopes, expiry status, created/tested timestamps, and reauthorization callout. Mapping contains grouped selects: Purchase accounts, Vendor behavior, Tax, Attachments. Each field includes accessible help text and validation status. Bottom sticky actions: `Validate mapping`, then `Save mapping` enabled only after latest validation succeeds. Audit is chronological and redacted.

**States:** account/tax reference loading skeleton; no accounts error with `Retry provider data`; validation summary links to fields; save success toast and version badge; disconnected state makes mapping read-only.

### 3. Receipt accounting panel, `/receipts/[id]?tab=accounting`
**Layout:** existing receipt header; tabs preserve History and Details. Accounting tab uses two desktop columns. Left `Source values` displays original gross/tax/net/currency and editable correction entry points. Right `Reporting values` displays converted amount, rate, date, source, stale badge, and `Refresh conversion`. Tax validation card lists arithmetic and line-level checks.

**States:** identity conversion, missing rate blocker with `Add exchange rate`, stale conversion warning, invalid arithmetic error, successful recalculation. On mobile, source precedes reporting and action bar is sticky.

### 4. Export Preparation, `/exports/prepare`
**Header:** title and destination selector. Keep receipt selection. After selection, primary `Run preflight`; secondary `Clear selection`.

**Preflight result:** summary cards Ready/Warning/Blocked; pinned connection and mapping versions; expandable receipt rows; blockers deep-link to Accounting or Mapping. Ready rows expose `Preview provider payload`. Payload drawer is read-only, syntax-independent definition list/tree, with Source, Provider interpretation, Lines, Tax, Attachment, Snapshot metadata. No raw JSON-only UI.

**Action bar:** warning checkbox count, `Export ready items`, exact count, disabled reasons. Stale preparation replaces action with `Run preflight again` while preserving selection.

### 5. Export run detail, `/exports/runs/[id]`
**Header:** destination/company, aggregate status, UTC created time. Summary cards Created, Already exported, Failed, Needs reconciliation. Progress bar has text percentage.

**Table/cards:** receipt, vendor, amount/currency, attempt, provider ID suffix, status, action. Filters All/Failed/Needs reconciliation/Verified are URL-backed. Failed row drawer shows safe error, request ID, retryability, and version state. Primary `Retry failed items` appears only for eligible rows; confirmation lists count and exclusions.

**Live updates:** SWR polls every 2 seconds while queued/processing, stops on terminal aggregate state, and announces count changes no more than once per 5 seconds.

### 6. Reconciliation view, `/exports/runs/[id]/items/[itemId]`
**Header:** receipt/vendor and status. Split comparison: ReceiptLens on left, QuickBooks on right, field rows with Match or Mismatch. Links: `Open receipt`; external provider link only from provider-returned fixed host and opens with `noopener noreferrer`.

Primary `Verify in QuickBooks`; disabled during request. Missing remote shows destructive-looking but non-destructive warning and `Run a new preflight`; no Recreate button. Success focuses `Verified` heading. Error preserves previous snapshot with `Retry verification`.

### 7. Connection-loss recovery banner
Across Export Preparation and active runs, `Reauthorization required` banner includes `Reconnect QuickBooks` for admins and `Ask an administrator` for other roles. It never discards preparation/run state.

### Complete success and failure paths
**Success:** admin connects → validates/saves mapping → bookkeeper fixes missing rate → preflights 50 receipts → previews one payload → acknowledges warnings → exports → watches 50 items → verifies a provider purchase → sees Verified audit event.

**Failure recovery:** token refresh returns invalid_grant → run pauses before unattempted items → banner explains reauthorization → admin reconnects → mapping remains pinned → bookkeeper selects Retry failed items → successful links are skipped → reconciliation completes without duplicates.

### UI verification
Developer must run type-check/build, backend and frontend startup, Playwright with installed Chromium, axe on all six screens, and capture desktop 1440×900 plus mobile 390×844 screenshots for Integrations disconnected/connected, Mapping error/success, Accounting missing-rate/success, Preflight blocked/ready, Run partial/completed, and Reconciliation mismatch/verified. Screenshots go only in development evidence if repository policy accepts them; otherwise record paths and exclude generated outputs from final package.

## Architecture and Technical Design
### Component boundaries
- `app/provider_connectors.py`: `AccountingProvider` protocol, provider errors, request/response domain types.
- `app/quickbooks_connector.py`: OAuth URL, token exchange/refresh, company info, reference lists, purchase create/get, attachment upload. All network calls use injected `httpx.Client`/transport and fixed base URLs.
- `app/credential_store.py`: authenticated encryption/decryption and redacted metadata. No provider semantics.
- `app/connection_service.py`: OAuth state, connections, health, disconnect, mapping versions, authorization.
- `app/provider_export_service.py`: queued runs/items, claim/attempt/retry, dedupe links, aggregate status.
- `app/reconciliation_service.py`: remote comparison and immutable snapshots.
- `app/accounting_projection.py`: Decimal currency conversion, tax arithmetic, payload preview inputs.
- `app/product_api.py`: thin HTTP validation/error mapping only.
- Frontend: typed API functions in `frontend/lib/api.ts`; new types in `frontend/lib/types.ts`; screen-specific client components under existing routes; shared `ConnectionStatus`, `MappingEditor`, `ProviderPayloadPreview`, `RunItemTable`, `ReconciliationComparison`, `AccountingProjectionCard`.

### Data flow/state
OAuth transient state and durable connections live in SQLite. SWR cache keys include tenant plus resource route; mutations call API then revalidate connection/preparation/run. No new global state store. Export worker is callable in-process for the reference adapter and exposes `process_next()` for deterministic tests; production deployment may schedule it separately without changing domain logic.

### Error model/logging
Stable codes: `oauth_state_invalid`, `oauth_state_expired`, `credential_store_unavailable`, `provider_reauthorization_required`, `provider_rate_limited`, `provider_validation_failed`, `mapping_reference_inactive`, `receipt_version_changed`, `preparation_stale`, `exchange_rate_missing`, `tax_arithmetic_invalid`, `remote_missing`. API errors include `code`, `message`, `field`, `retryable`, optional `provider_request_id`; never raw provider body. Structured logs contain tenant hash, run/item IDs, status, latency, attempt, and request ID, not receipt contents or credentials.

### Dependencies
Add `cryptography>=43` to Python dependencies and lockfile solely for AES-GCM token encryption. Do not add an Intuit SDK, queue framework, state store, or UI library. Tests use existing `httpx` MockTransport and pytest.

### Alternatives rejected
- Hand-rolled encryption: rejected due to credential risk.
- Simultaneous QBO/Xero: rejected due to duplicated provider risk.
- Posting synchronously in request: rejected because rate limits/retries require durable item states.
- Reusing CSV artifact as provider payload: rejected because account/tax references and reconciliation metadata require typed mapping.
- Storing converted values in OCR payload: rejected because source evidence must remain immutable.

## Data, API, and Compatibility Changes
### SQLite additive schema
Create migration-safe `CREATE TABLE IF NOT EXISTS` plus column checks for:
- `oauth_states(state_hash PK, tenant_id, provider, pkce_ciphertext, return_path, expires_at, used_at, created_at)`.
- `provider_credentials(connection_id PK, tenant_id, provider, token_ciphertext, key_version, expires_at, refresh_expires_at, updated_at)`.
- Extend `connections` add `provider_company_id`, `provider_company_name`, `environment`, `health`, `reauthorization_required`, `last_tested_at`, `disconnected_at`.
- `connection_mapping_versions(mapping_id PK, connection_id, tenant_id, version, payload_json, reference_snapshot_json, valid, created_by_role, created_at, UNIQUE(connection_id,version))`.
- Extend preparations add `mapping_version`, `destination_provider`, `projection_snapshot_json`, `snapshot_hash`.
- `provider_export_runs(run_id PK, tenant_id, preparation_id, connection_id, command_key, status, counts_json, created_at, completed_at)`.
- `provider_export_items(item_id PK, run_id, tenant_id, receipt_id, receipt_version, mapping_version, dedupe_key UNIQUE, status, attempt_count, provider_id, provider_sync_token, provider_request_id, retryable, safe_error_json, next_attempt_at, created_at, updated_at)`.
- `provider_links(link_id PK, tenant_id, provider, connection_id, receipt_id, receipt_version, provider_id, provider_sync_token, created_at, UNIQUE(tenant_id,provider,connection_id,receipt_id,receipt_version))`.
- `reconciliation_snapshots(snapshot_id PK, item_id, status, comparison_json, provider_sync_token, verified_at, created_at)`.
- `receipt_accounting_projections(receipt_id, tenant_id, receipt_version, payload_json, stale, updated_at, PRIMARY KEY(tenant_id,receipt_id))`.

All JSON is canonical sorted output. Historical records are never cascade-deleted when disconnecting.

### Exact API
- `POST /product/connections/quickbooks/oauth/start` body `{return_path}` → `{authorization_url,state_expires_at}`.
- `GET /product/connections/quickbooks/oauth/callback?code&state&realmId` → 303 redirect, no JSON tokens.
- `GET /product/connections/{id}` → metadata/health/current mapping version, no secrets.
- `POST /product/connections/{id}/test` → health, company, tested_at, reauthorization_required.
- `POST /product/connections/{id}/disconnect` → status disconnected.
- `GET /product/connections/{id}/references?kind=accounts|tax_codes|vendors` → normalized references plus fetched_at.
- `POST /product/connections/{id}/mappings/validate` body mapping → `{valid,errors,reference_snapshot}`.
- `POST /product/connections/{id}/mappings` body validated mapping + snapshot hash → immutable mapping version.
- Extend `POST /product/export-preparations` to accept `connection_id`; response includes provider, mapping_version, snapshot_hash, projections.
- `GET /product/export-preparations/{id}/receipts/{receipt_id}/payload-preview` → redacted typed preview or 409 stale.
- Extend `POST /product/export-commands`; provider target returns 202 and durable run.
- `GET /product/provider-export-runs/{id}` and `/items` with status/offset/limit.
- `POST /product/provider-export-runs/{id}/retry` body `{item_ids}`.
- `GET /product/provider-export-runs/{id}/items/{item_id}`.
- `POST /product/provider-export-runs/{id}/items/{item_id}/verify`.
- `GET /product/receipts/{id}/accounting-projection`.
- `POST /product/receipts/{id}/accounting-projection/refresh` body reporting_currency, optional rate_date.

### Compatibility/migration
No existing endpoint is removed. Existing connections without new columns default to legacy/unhealthy metadata. Existing CSV export commands remain synchronous. Existing frontend routes continue; new detail routes are additive. Database migration is restart-safe and tested from a fixture representing current schema.

## Security and Privacy Considerations
- OAuth state is random, hashed at rest, tenant-bound, single-use, and expires in 10 minutes. PKCE verifier is encrypted.
- AES-GCM master key is environment-only, minimum 32 bytes, supports key-version metadata, and is excluded from diagnostics.
- Client secret and tokens are never sent to browser. Callback query values are not logged.
- Provider base URLs and external links are fixed allowlists; no SSRF from connection configuration.
- Admin role required for connect/disconnect/mapping; admin or reviewer for payload preview; bookkeeper/admin for export/retry; all queries include tenant ID.
- Attachment upload validates stored image/PDF magic bytes and size before provider transmission.
- Redaction tests search API JSON, logs, audit, diagnostic bundle, SQLite non-credential tables, and error payloads for seeded token markers.
- Disconnect preserves financial audit links but removes active credential material. Retention/purge later must include expired OAuth states and disconnected ciphertext.

## Test Strategy (TDD)
### RED sequence and acceptance mapping
Create `tests/test_us_010_quickbooks_oauth.py` through `test_us_018_payload_preview.py`. Each acceptance criterion gets one named test `test_us_NNN_<criterion>`. Run each before implementation and record the expected failure, then GREEN. Production tests may not contain `pytest.raises(NotImplementedError)` as their only behavior.

**Feature A tests:** state entropy/expiry/replay/cross-tenant, callback redaction, encrypted-at-rest marker scan, refresh rotation, invalid_grant, disconnect, account cache, mapping required fields and inactive reference drift.

**Feature B tests:** 50-item real SQLite + `httpx.MockTransport` posting, duplicate replay across command keys, restart claim recovery, 429 injected clock, partial failure, retry version conflict, error redaction/size, remote verify/mismatch/missing.

**Feature C tests:** Decimal conversion/date selection/identity/missing rate, stale projection on correction, minor-unit rounding, mixed tax lines, negative/impossible tax, deterministic preview hash, stale 409, role 403, preview secret scan.

### Integration/E2E
- Real I/O: temporary SQLite file closed/reopened between queue and worker; local ASGI fake-provider server handles OAuth token, company, account, create, upload, and get endpoints.
- Opt-in real sandbox: `pytest -m qbo_sandbox` runs only when documented credentials exist, creates one uniquely memoed purchase in a dedicated sandbox, verifies it, and records provider ID for cleanup. It is required before release but skipped in credentialless CI.
- Playwright covers connect callback simulation, mapping validation, missing-rate recovery, preflight payload preview, partial run retry, mismatch reconciliation, keyboard focus, mobile layout, and axe.

### Commands
Existing supported commands:
- Target feature: `pytest -q tests/test_us_010_quickbooks_oauth.py ... tests/test_us_018_payload_preview.py`.
- Affected regressions: `pytest -q tests/test_development_stories.py tests/test_export_readiness_workflow.py tests/test_accounting_readiness_ui.py tests/test_us_contract_api.py`.
- Full: `pytest -q`.
- Coverage: `pytest -q <new test files> --cov=app.quickbooks_connector --cov=app.credential_store --cov=app.connection_service --cov=app.provider_export_service --cov=app.reconciliation_service --cov=app.accounting_projection --cov-report=term-missing --cov-fail-under=90`.
- Lint: `python -m ruff check app tests` after ensuring the dev extra installed from project metadata.
- Frontend: `cd frontend && npm ci && npm run typecheck && npm run build && npx playwright install chromium && npx playwright test`.
- Startup: backend `uvicorn app.main:app --host 127.0.0.1 --port 8000`; frontend `cd frontend && npm run start -- --hostname 127.0.0.1 --port 3000`; probe `/health`, `/ready`, `/integrations`.
- Gates: `bash scripts/tdd-gate-v3.sh`, `bash scripts/bdd-gate.sh`, `bash scripts/security-gate.sh`, `bash scripts/doc-sync-check.sh`, `bash scripts/ui-gate.sh`, `bash scripts/git-push-verify.sh .`.

### Objective pass/fail
- Every US-010..018 criterion has a passing test and traceability row.
- New/changed domain modules each ≥90% statement coverage and aggregate ≥90%; credential/state modules require 100% branch coverage.
- Zero full-regression failures; documented provider sandbox test passes before release.
- Type-check/build/startup pass; Playwright/axe has zero critical/serious violations; required screenshots visibly inspected.
- Security gate proves no plaintext seeded token outside encrypted credential blob and no cross-tenant access.

## Documentation Deliverables
- `README.md`: QuickBooks sandbox prerequisites, environment variables without values, connection flow, mapping, export/retry/reconcile, FX-rate setup, troubleshooting, production warning.
- `CHANGELOG.md`: new connector, encryption, schema, export/reconciliation, currency/tax, tests, and compatibility.
- `docs/quickbooks-online.md`: OAuth/scopes, sandbox app setup, mapping semantics, status/error codes, disconnect/reconnect, operational runbook.
- `docs/accounting-export-guide.md`: provider preflight, payload preview, warning acknowledgement, run/retry/reconciliation.
- `docs/api.md`: exact endpoints and shapes, 202 behavior, stable error codes.
- `FEATURES-DONE.md`: only completed US-010..018 items and sources mapping.
- `development-report.md`: RED/GREEN evidence per story, exact sandbox/fake-provider evidence, coverage, gates, screenshots, migrations, file list, blockers, integrity, traceability, commit message.

## Expected File Changes
**Add:** `app/provider_connectors.py`, `app/quickbooks_connector.py`, `app/credential_store.py`, `app/connection_service.py`, `app/provider_export_service.py`, `app/reconciliation_service.py`, `app/accounting_projection.py`; nine story-focused test modules plus fixtures; `docs/quickbooks-online.md`; frontend shared components and reconciliation route.

**Modify:** `app/product_api.py`, service initialization, `pyproject.toml`, `uv.lock`, existing schema/service modules, frontend types/API/routes, gate scripts, README, CHANGELOG, API/export docs, FEATURES-DONE, development-report. Do not modify research findings or this plan during development except to correct a proven contradiction, which must be separately documented.

## Traceability Matrix
| Research need | Research evidence | User story id | Planned requirement | Acceptance criterion | Planned implementation location | Planned test evidence | Priority |
|---|---|---|---|---|---|---|---|
| Deep single-provider integration | Competitors position accounting sync as core; research recommends one sandbox | US-010 | Tenant-bound OAuth/PKCE and encrypted token exchange | Matching callback stores one redacted connection | connection/credential/QBO services; Integrations | oauth callback integration | P0 |
| Prevent OAuth cross-tenant/replay | Production connector risk | US-010 | Single-use hashed state | Cross-tenant/replay returns 400, no token | connection service | state security tests | P0 |
| Recover provider timeout | Operational reliability need | US-010 | Retryable new state | timeout leaves disconnected and Retry available | API/UI | callback timeout + UI | P0 |
| Connection health | Opaque sync complaints | US-011 | Test/refresh/reauthorize | expired token refreshes once | QBO connector/detail | refresh transport test | P0 |
| Protect rotated credentials | OAuth risk | US-011 | Replace encrypted token set | old marker absent after rotation | credential store | SQLite marker test | P0 |
| Avoid refresh loops | Operational safety | US-011 | invalid_grant terminal health | reauthorization required | connection service/UI | invalid_grant test | P0 |
| Deterministic accounting mapping | Currency/tax/matching complaints | US-012 | Immutable validated mapping | active refs save new version | mapping service/editor | mapping integration | P0 |
| Detect provider drift | Provider references change | US-012 | preflight reference revalidation | inactive ref blocks with deep link | prep/mapping UI | drift test/E2E | P0 |
| Field validation | Modern error baseline | US-012 | 422 field errors | missing expense account disables save | API/editor | schema + E2E | P0 |
| No duplicate posting | Research success metric | US-013 | item dedupe and durable links | replay creates exactly 50 | provider export service | 50-item fake server | P0 |
| Skip prior success | Retry safety | US-013 | provider link lookup | no second request | export service | request-count test | P0 |
| Respect rate limits | Provider API reality | US-013 | bounded Retry-After policy | max three attempts, siblings continue | worker | injected-clock 429 test | P0 |
| Recover partial run | Matching/reliability pain | US-014 | immutable item detail/retry | aggregate 42/5/3 matches items | run service/UI | run detail test | P0 |
| Protect later edits | Existing optimistic contract | US-014 | version gate retry | changed item rejected | worker | conflict test | P0 |
| Redact provider errors | Financial credential privacy | US-014 | safe 2 KB error envelope | token removed; request ID kept | provider errors/UI | seeded-secret test | P0 |
| Prove remote result | Reconciliation pain | US-015 | fetch-and-compare | matching fields verify | reconciliation service/view | provider get test | P0 |
| Surface mismatch | Currency/tax errors | US-015 | tolerance comparison | total mismatch names field | reconciliation | mismatch test/E2E | P0 |
| Preserve deleted history | Audit need | US-015 | missing_remote status | link retained; recreate disabled | reconciliation/UI | delete simulation | P0 |
| Preserve source currency | Reported foreign-currency errors | US-016 | separate accounting projection | original unchanged with dated CHF result | projection/receipt UI | Decimal projection test | P0 |
| Identity conversion | Correct boundary behavior | US-016 | explicit rate 1 | no lookup | projection | identity mock assertion | P0 |
| Never invent FX | Trust requirement | US-016 | missing-rate blocker | deep-linked stable error | readiness/UI | missing rate API/E2E | P0 |
| Validate tax arithmetic | Reported tax rework | US-017 | Decimal arithmetic | 0.01 tolerance passes | projection/tax panel | rounding tests | P0 |
| Handle mixed tax | Accounting mapping gap | US-017 | line-level code completeness | unmapped indices listed | mapping/projection | mixed lines test | P0 |
| Block impossible tax | Accounting safety | US-017 | stable validation code | no payload generated | projection/preflight | negative/excess tests | P0 |
| Preview interpretation | Transparent preflight differentiation | US-018 | snapshot-bound redacted preview | deterministic versioned response | preview endpoint/drawer | snapshot hash test | P0 |
| Stale preview recovery | Concurrency | US-018 | 409 and preserved selection | Run preflight again | API/UI | stale E2E | P0 |
| Role/privacy | Financial data access | US-018 | admin/reviewer only | 403 and no payload logs | API | RBAC/log capture | P0 |

## Risks and Mitigations
- **Provider API/certification drift:** centralize provider adapter, pin minor API version in config, contract-test normalized shapes, record tested version/date.
- **Credential compromise:** authenticated encryption, strict redaction, key rotation metadata, no browser tokens, disconnect purge, 100% security branch coverage.
- **Duplicate financial entries:** deterministic dedupe, provider links, command idempotency, version-pinned preparation, restart tests.
- **Rate limits/outages:** durable per-item state, bounded Retry-After, connection pause on auth failure, retry UI.
- **Tax misinterpretation:** validation and mapping only; no legal advice; explicit preview and blockers.
- **FX rounding:** Decimal/minor units, dated rate provenance, source values immutable.
- **SQLite contention:** short claim transactions, no network I/O inside transaction, bounded batch 200. PostgreSQL remains future adapter.
- **Credentialless CI:** full fake-provider integration mandatory; real sandbox marker may skip in CI but must pass before release and be documented.
- **Header identity limitation:** retain explicit non-production banner and admin role checks; production identity remains release blocker.

## Definition of Done
- [ ] US-010 through US-018 complete with no façade, production mock, placeholder, or unconditional success.
- [ ] OAuth state, credential encryption, refresh, disconnect, and mapping are tenant-safe and redaction-tested.
- [ ] A 50-receipt fake-provider export is replayed with zero duplicate creates; restart and partial retry pass.
- [ ] Opt-in QuickBooks sandbox create/get/verify passes before release and provider IDs are recorded safely.
- [ ] Currency and tax projection preserves source values and blocks missing/invalid evidence.
- [ ] All acceptance criteria map to RED/GREEN test evidence and implementation in the development report.
- [ ] New/changed modules meet ≥90% coverage; credential/state modules meet 100% branch coverage.
- [ ] Targeted and full pytest regressions pass with zero failures.
- [ ] `tdd-gate-v3.sh`, `bdd-gate.sh`, `security-gate.sh`, `doc-sync-check.sh`, and `ui-gate.sh` pass.
- [ ] Ruff, type-check, production build, backend/frontend startup, Playwright, axe, and required screenshot inspection pass.
- [ ] README, CHANGELOG, API/export/QBO docs, FEATURES-DONE, and development-report match actual behavior.
- [ ] Migration from current SQLite fixture and restart recovery pass.
- [ ] No tokens, client secrets, `.env`, caches, dependencies, build output, traces, or scratch artifacts are packaged.
- [ ] Git add/commit/pull-rebase/push succeeds and `git-push-verify.sh` confirms clean tree and upstream HEAD; without repository metadata the phase must report BLOCKED, not PASS.
- [ ] Baseline reconciliation accounts for every intentional file change and no pre-existing file disappears.
- [ ] Complete project ZIP passes integrity, listing, separate extraction, required-file, and top-level-layout verification.
