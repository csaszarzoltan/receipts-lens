# Implementation Plan

## Executive Summary
This pass will deliver three integrated features on the existing FastAPI, SQLite, Next.js 14, React 18, TypeScript, SWR, Tailwind, pytest, and Playwright stack:

1. **Accounting-safe review and export gate** covering US-001 through US-003.
2. **Transparent OCR confidence and exception queue** covering US-004 through US-006.
3. **Inbox-to-books automation with safe rules** covering US-007 through US-009.

The product slice is deliberately bounded around one outcome: a bookkeeper can receive receipts, identify and correct uncertain fields with source evidence, apply only previewed automation, and export only receipts that pass deterministic accounting checks. The pass does not add a live QuickBooks or Xero connector, billing, travel/expense cards, or new OCR providers. Existing endpoints and file formats remain compatible; additions are versioned, tenant-scoped, and persisted in the existing product SQLite database.

The Next.js workspace remains the primary UI. The legacy `/workspace` surface remains available but receives no new feature work. No new runtime dependency is required. New quality-gate shell scripts are repository-owned wrappers around existing commands and checks, not application dependencies.

## Current-State Validation
The research report matches the project:

- `pyproject.toml` defines ReceiptLens 1.4.0 on Python 3.11+ with FastAPI, Pydantic, Pillow, pytesseract, httpx, multipart, and reportlab.
- `frontend/package.json` defines Next.js 14.2.35, React 18.3.1, TypeScript, SWR, Recharts, Tailwind, Playwright, and axe.
- `app/product_api.py` already exposes receipt upload/list/detail, review, OCR boxes, history, validation, export preparation, export runs, automation rules, previews, and inbound-email endpoints.
- `app/advanced_workspace.py` persists assets, OCR boxes, automation rules, notifications, saved views, duplicate decisions, preferences, history, and export runs.
- `app/accounting_workspace.py` persists inbound-email records and export preparations and implements readiness validation.
- `app/product_service.py` persists tenant receipts/jobs, versions, metadata, approvals, connections, and activity history.
- The Next.js application already contains review, receipt detail, export preparation, automation, and inbox pages, so this is an enhancement and consolidation pass rather than a rewrite.
- The report's nine selected stories are actionable and align with existing primitives. The missing elements are calibrated queue filters, complete provenance presentation, immutable export preflight/run semantics, attachment-level ingestion, rule conflict/version/run tracking, and rollback.

Planning assumptions that are now decisions:

- SQLite remains the reference product store for this pass.
- `X-Tenant-ID` and `X-Role` remain for compatibility and tests; production authentication is deferred.
- The source receipt image is immutable. Corrections alter structured data only.
- “Ready” is computed, never manually set.
- Export preparation is a snapshot; export execution references that snapshot and an idempotency key.
- Automation affects future receipts by default. Existing receipts change only through an explicit previewed run.
- Rollback is optimistic and atomic: receipts modified after the automation run are conflicts and are not reverted.

## Research Priorities
| Rank | Research-backed priority | Selected | Reason |
|---|---|---|---|
| P0 | Accounting-safe review and export gate | Yes | Directly addresses matching, tax, completeness, and auditability pain while reusing implemented validation/export primitives. |
| P0 | Transparent OCR confidence and exception queue | Yes | Converts uncertain OCR into focused work and makes quality measurable instead of relying on accuracy claims. |
| P1 | Inbox-to-books automation with safe rules | Yes | Completes the existing inbound-email and rules foundations with preview, conflict handling, run history, and rollback. |
| P1 | Production QuickBooks/Xero connectors | Deferred | Requires OAuth, provider sandboxes, mapping certification, replay recovery, and operational ownership after internal export contracts are stable. |
| P1 | Multi-currency/tax expansion | Deferred | Current validation and exchange-rate primitives are retained; jurisdiction-specific behavior needs separate fixtures and accounting review. |
| P2 | Privacy-first deployment program | Deferred | Existing retention/diagnostic primitives remain; threat model and deployment hardening merit a dedicated security pass. |
| P2 | Usage-based packaging | Deferred | Billing must follow measured activation, cost, and willingness-to-pay data. |

## Selected Scope for This Pass
### Feature A: Accounting-safe review and export gate
Deliver a single review-to-export workflow with deterministic readiness, deep-linked blockers, warning acknowledgement, immutable preparation snapshots, idempotent export execution, and auditable receipt/export history. Satisfies US-001, US-002, and US-003.

### Feature B: Transparent OCR confidence and exception queue
Add server-side confidence filters and ordering, field-level provenance selection, accessible OCR-box highlighting, and a labelled benchmark/calibration report maintained through Diagnostics. Satisfies US-004, US-005, and US-006.

### Feature C: Inbox-to-books automation with safe rules
Persist email attachments individually, process supported attachments independently, quarantine unsupported content, add retry, and introduce draft/versioned rules with preview conflicts, explicit runs over selected receipts, run history, and atomic rollback. Satisfies US-007, US-008, and US-009.

Coherence boundary: these features share receipt versions, history, readiness, provenance, and tenant-scoped persistence. They form one complete operational path. Forecasting, budgets, subscriptions, reports, approvals, and duplicates must continue to work but are regression scope only.

## Deferred Scope and Rationale
1. **Live QuickBooks connector:** defer to the next integration phase after idempotent provider-neutral export has test evidence. Prerequisites: OAuth secret storage, sandbox tenant, mapping policy, attachment upload, rate-limit handling, and reconciliation tests.
2. **Live Xero connector:** defer until the QuickBooks adapter contract proves provider portability. Same prerequisites plus Xero certification review.
3. **Jurisdiction-specific VAT/GST engines:** defer to a tax domain phase. Prerequisites: target countries, accountant-reviewed rules, rounding policy, and legal disclaimer.
4. **New OCR providers or model training:** defer until the benchmark identifies actual failure segments. The adapter seam may be clarified but no provider is added.
5. **Production authentication/SSO:** defer to a dedicated identity and tenancy pass. Current headers remain explicitly non-production.
6. **Billing and usage enforcement:** defer until beta telemetry establishes unit economics and acceptable limits.
7. **Travel, cards, reimbursement payments, and generalized AP:** rejected for the current product wedge; they dilute the exception-to-export workflow.
8. **Legacy workspace migration/removal:** defer. The Next.js app becomes the documented primary surface, while `/workspace` stays compatible.
9. **README rewrite during this planning phase:** prohibited by the phase's hard scope. The development pass must update README as specified below.

## User Stories (BDD)
```json
[
  {
    "id": "US-001",
    "epic": "Accounting-safe review and export gate",
    "role": "bookkeeper",
    "action": "review all uncertain fields in one prioritized queue",
    "benefit": "I can export only accounting-ready receipts",
    "story": "As a bookkeeper, I want to review all uncertain fields in one prioritized queue, so that I can export only accounting-ready receipts.",
    "gui_flow": [
      "User opens Review Queue → sees items ordered by blocking severity and confidence",
      "User opens a receipt → sees image, extracted fields, and highlighted low-confidence sources",
      "User edits a field → validation and readiness recalculate immediately",
      "User opens line items → sees sum-to-total variance",
      "User clicks Complete → receipt moves to Ready when no blockers remain",
      "User opens Export Preparation → sees the completed receipt included"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "a receipt has one low-confidence total and valid source image",
        "when": "the user corrects the total and clicks Complete",
        "then": "the saved version increments once and readiness becomes exportable within 2 seconds"
      },
      {
        "type": "given",
        "text": "another reviewer saved a newer version",
        "when": "the user submits an edit based on the stale version",
        "then": "the UI shows a conflict, preserves the draft, and does not overwrite server data"
      },
      {
        "type": "given",
        "text": "the image endpoint fails",
        "when": "the user opens the receipt",
        "then": "the form remains usable and an error state offers Retry without marking the receipt complete"
      }
    ]
  },
  {
    "id": "US-002",
    "epic": "Accounting-safe review and export gate",
    "role": "accountant",
    "action": "see deterministic export blockers before posting",
    "benefit": "I do not create incomplete ledger entries",
    "story": "As a accountant, I want to see deterministic export blockers before posting, so that I do not create incomplete ledger entries.",
    "gui_flow": [
      "User opens Export Preparation → sees selected receipts",
      "User chooses an accounting connection → preflight starts",
      "User sees Ready, Warning, and Blocked groups with counts",
      "User expands a blocked receipt → sees field-level reasons and deep links",
      "User fixes the receipt → returns to preflight with selection preserved",
      "User clicks Export Ready Items → sees immutable run summary"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "ten receipts include two missing mandatory fields",
        "when": "the user runs preflight",
        "then": "exactly two are blocked with field names and eight are eligible"
      },
      {
        "type": "given",
        "text": "a warning-only receipt is selected",
        "when": "the user exports with warnings",
        "then": "the export requires explicit acknowledgement and records it in history"
      },
      {
        "type": "given",
        "text": "the connection test returns an authentication error",
        "when": "the user starts export",
        "then": "no receipt is posted and the run reports a retryable connection error"
      }
    ]
  },
  {
    "id": "US-003",
    "epic": "Accounting-safe review and export gate",
    "role": "reviewer",
    "action": "trace every correction and export decision",
    "benefit": "I can answer audit questions",
    "story": "As a reviewer, I want to trace every correction and export decision, so that I can answer audit questions.",
    "gui_flow": [
      "User opens Receipt Detail → sees current status and version",
      "User opens History → sees chronologically ordered events",
      "User selects an event → sees actor role, timestamp, and changed fields",
      "User compares before and after → sensitive image bytes are absent",
      "User filters to Export events → sees run and connection identifiers",
      "User downloads a redacted audit record → receives machine-readable JSON"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "a receipt has two corrections and one export",
        "when": "the user opens History",
        "then": "all three events appear with UTC timestamps and before/after field values"
      },
      {
        "type": "given",
        "text": "an event has no before value",
        "when": "the user opens its diff",
        "then": "the UI labels it Created rather than rendering a broken comparison"
      },
      {
        "type": "given",
        "text": "audit retrieval fails",
        "when": "the user opens History",
        "then": "the UI displays an error and retry control without inventing events"
      }
    ]
  },
  {
    "id": "US-004",
    "epic": "Transparent OCR confidence and exception queue",
    "role": "bookkeeper",
    "action": "filter work by confidence and business impact",
    "benefit": "I spend time only on likely errors",
    "story": "As a bookkeeper, I want to filter work by confidence and business impact, so that I spend time only on likely errors.",
    "gui_flow": [
      "User opens Review Queue → sees blocker and confidence filters",
      "User selects Total confidence below 0.80 → list updates",
      "User sorts by amount descending → high-value receipts move first",
      "User opens a result → low-confidence fields are visually distinguished",
      "User corrects the receipt → the queue count updates",
      "User saves the filter as a private view → it appears in Saved Views"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "five receipts match the confidence filter",
        "when": "the user applies it",
        "then": "the list shows exactly five and the URL stores the filter state"
      },
      {
        "type": "given",
        "text": "no receipts match",
        "when": "the user applies a stricter threshold",
        "then": "an empty state explains the filter and offers Clear filters"
      },
      {
        "type": "given",
        "text": "the list request times out",
        "when": "the user changes the filter",
        "then": "the previous list remains visible with a retryable loading error"
      }
    ]
  },
  {
    "id": "US-005",
    "epic": "Transparent OCR confidence and exception queue",
    "role": "quality owner",
    "action": "calibrate review thresholds from benchmark results",
    "benefit": "I can limit false clears",
    "story": "As a quality owner, I want to calibrate review thresholds from benchmark results, so that I can limit false clears.",
    "gui_flow": [
      "User opens Diagnostics → sees OCR Quality card",
      "User uploads or selects a labelled benchmark manifest → validation runs",
      "User starts evaluation → progress and sample count are shown",
      "User opens results → sees precision, recall, and false-clear rate per field",
      "User adjusts a proposed threshold → metrics recalculate on the benchmark",
      "User publishes thresholds → version and timestamp are recorded"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "a valid 200-field benchmark is loaded",
        "when": "the user evaluates threshold 0.80",
        "then": "the report shows confusion counts whose sum equals 200"
      },
      {
        "type": "given",
        "text": "the benchmark lacks labels for tax",
        "when": "the user evaluates it",
        "then": "tax is marked not evaluated and does not contribute to aggregate metrics"
      },
      {
        "type": "given",
        "text": "the benchmark schema is invalid",
        "when": "the user uploads it",
        "then": "publication is disabled and row-level validation errors are shown"
      }
    ]
  },
  {
    "id": "US-006",
    "epic": "Transparent OCR confidence and exception queue",
    "role": "reviewer",
    "action": "see OCR provenance on the receipt image",
    "benefit": "I can verify extracted values quickly",
    "story": "As a reviewer, I want to see OCR provenance on the receipt image, so that I can verify extracted values quickly.",
    "gui_flow": [
      "User opens a receipt → image and fields load side by side",
      "User focuses Vendor → matching OCR boxes highlight",
      "User focuses Total → the viewport pans to the source region",
      "User switches between AI and Tesseract provenance → values and confidence update",
      "User chooses a value → the field changes and validation reruns",
      "User saves → provenance choice is recorded in history"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "OCR boxes exist for the total",
        "when": "the user focuses Total",
        "then": "at least one normalized source box is highlighted on the image"
      },
      {
        "type": "given",
        "text": "no source box exists",
        "when": "the user focuses the field",
        "then": "the UI states Source region unavailable and still permits manual entry"
      },
      {
        "type": "given",
        "text": "the source image is corrupt",
        "when": "the viewer loads",
        "then": "an accessible error appears and no stale image from another receipt is displayed"
      }
    ]
  },
  {
    "id": "US-007",
    "epic": "Inbox-to-books automation with safe rules",
    "role": "business owner",
    "action": "forward receipts to a dedicated inbox",
    "benefit": "I do not manually upload every attachment",
    "story": "As a business owner, I want to forward receipts to a dedicated inbox, so that I do not manually upload every attachment.",
    "gui_flow": [
      "User opens Inbox → sees the tenant forwarding address",
      "User forwards an email with image and PDF attachments → message appears as Processing",
      "System validates attachment types → accepted files enter the receipt pipeline",
      "User opens the message → sees per-attachment status",
      "User opens a created receipt → sees sender and email subject provenance",
      "User archives the processed message → it leaves the active inbox"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "an email contains two supported attachments",
        "when": "processing completes",
        "then": "two receipts are created and linked to one email record"
      },
      {
        "type": "given",
        "text": "an email includes an unsupported executable",
        "when": "processing runs",
        "then": "the executable is quarantined while supported attachments continue"
      },
      {
        "type": "given",
        "text": "OCR fails for one attachment",
        "when": "processing completes",
        "then": "the message is Partial, one receipt exists, and the failed attachment has a Retry action"
      }
    ]
  },
  {
    "id": "US-008",
    "epic": "Inbox-to-books automation with safe rules",
    "role": "admin",
    "action": "preview an automation rule before activation",
    "benefit": "I avoid unintended bulk changes",
    "story": "As a admin, I want to preview an automation rule before activation, so that I avoid unintended bulk changes.",
    "gui_flow": [
      "User opens Automations → sees active and draft rules",
      "User clicks New rule → condition and action builder opens",
      "User enters vendor and amount conditions → validation runs",
      "User clicks Preview → matching receipt count and samples appear",
      "User reviews conflicts → higher-priority rule effects are shown",
      "User activates the rule → future uploads use the versioned rule"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "a rule matches 12 existing receipts",
        "when": "the user previews it",
        "then": "the preview reports 12 and shows up to 20 representative receipts without changing data"
      },
      {
        "type": "given",
        "text": "the new rule conflicts with an active rule",
        "when": "the user previews it",
        "then": "the conflict and winning priority are displayed before activation"
      },
      {
        "type": "given",
        "text": "the preview API fails",
        "when": "the user clicks Activate",
        "then": "activation remains disabled and the draft is preserved"
      }
    ]
  },
  {
    "id": "US-009",
    "epic": "Inbox-to-books automation with safe rules",
    "role": "admin",
    "action": "reverse an erroneous automation run",
    "benefit": "I can recover without manual cleanup",
    "story": "As a admin, I want to reverse an erroneous automation run, so that I can recover without manual cleanup.",
    "gui_flow": [
      "User opens Automations → selects a rule",
      "User opens Run History → sees affected counts and timestamps",
      "User opens a run → sees receipt-level before/after changes",
      "User clicks Roll back → impact preflight checks later edits",
      "User confirms eligible rollback → changes are reverted atomically",
      "User opens a receipt history → sees rollback provenance"
    ],
    "acceptance_criteria": [
      {
        "type": "given",
        "text": "a run changed ten receipts and none changed later",
        "when": "the user confirms rollback",
        "then": "all ten return to prior metadata and one rollback event is recorded per receipt"
      },
      {
        "type": "given",
        "text": "two receipts were edited after the run",
        "when": "the user preflights rollback",
        "then": "those two are excluded and identified as conflicts while eight remain eligible"
      },
      {
        "type": "given",
        "text": "rollback fails mid-transaction",
        "when": "the system handles the error",
        "then": "zero partial reversions persist and the run remains retryable"
      }
    ]
  }
]
```

## Product Requirements
### A. Accounting-safe review and export gate
**Evidence and stories:** recurring matching, tax, line-item, and missing-document complaints; accounting integration is table stakes. US-001, US-002, US-003.

**Functional requirements**
- `GET /product/review-items` returns paginated items with readiness, blocker count, lowest field confidence, total, currency, created time, and version. It accepts `confidence_field`, `confidence_lt`, `readiness`, `sort`, `limit`, and `offset`.
- Receipt detail and review expose structured fields, immutable source image, normalized OCR boxes, selected provenance source, validation, and history in one coordinated view.
- Saving uses existing optimistic concurrency. A 409 response contains current version and current server fields; the UI preserves the unsaved draft and offers **Reload server version** and **Copy my draft**.
- Completing a receipt reruns readiness. Completion is rejected with 422 if blockers remain. Warning-only receipts may complete.
- Export preparation persists requested receipt IDs, connection ID, per-receipt validation snapshot, valid IDs, blockers, warnings, receipt versions, and creation time.
- Export execution requires `preparation_id`, `Idempotency-Key`, and `acknowledged_warning_receipt_ids`. If a receipt version changed after preparation, execution returns 409 and no export is created.
- Repeating an execution with the same tenant and idempotency key returns the original run and creates no duplicate rows.
- Receipt history contains creation, correction, completion, preparation, warning acknowledgement, export, and rollback events, with UTC timestamps and no image bytes/secrets.
- Audit-record download is JSON and tenant-scoped.

**Validation and business rules**
- Mandatory export fields: vendor, date, total, currency. Total cannot be negative; tax cannot exceed total; date must be ISO date; line-item mismatch over 0.01 is a warning; missing cost center remains a warning unless the chosen mapping marks it required.
- `ready` means no validation errors, status completed/approved, and current receipt version equals the version in the preparation.
- Warnings cannot be silently ignored. Every exported warning receipt must be included in acknowledgement.
- An export run is immutable. Retry creates or returns a run tied to the same preparation and idempotency key.
- Limits: 1-200 receipt IDs per preparation; duplicates are normalized to first occurrence; unknown or cross-tenant IDs become blockers without leaking existence.

**Failure behavior**
- Image failure does not disable form correction.
- Validation failure is field-addressable and links back to the edit control.
- Connection failure creates a failed run with retryable status and sanitised error code; no receipt is marked exported.
- Partial provider behavior is not implemented in this pass. The reference CSV provider is atomic from the product's perspective.

**Compatibility**
- Existing response fields remain. New fields are additive.
- Existing `POST /product/export-runs` remains accepted and delegates to the new preparation-based service only when `preparation_id` is supplied; legacy request shape remains under tests.
- Existing CSV output columns and delimiter behavior remain unchanged.

**Acceptance summary**
- A 10-receipt fixture with two missing required fields yields exactly two blocked and eight eligible.
- A stale edit never overwrites a newer version and the draft remains visible.
- Replaying the same export command produces one run.
- History lists all relevant events in reverse chronological order and contains no binary/image payload.

**Non-goals:** live QBO/Xero posting, payment/reimbursement, tax advice, editing the source image, merging duplicate receipts.

### B. Transparent OCR confidence and exception queue
**Evidence and stories:** users distrust opaque extraction and need focused exception handling. US-004, US-005, US-006.

**Functional requirements**
- Queue filtering supports one confidence field at a time: `vendor`, `date`, `total`, `tax`, `currency`, or `line_items`; threshold range is 0.00-1.00 inclusive. Null confidence sorts before numeric confidence and matches any `confidence_lt` filter.
- Queue URL query parameters are the source of truth. Saved views persist supported filters and sort.
- Receipt review maps a focused field to one or more OCR boxes. Boxes are keyboard reachable through the field, not individually tabbed. The viewer pans/zooms the union rectangle with reduced motion respected.
- AI and Tesseract provenance choices are shown only when both results exist. Choosing a candidate updates the draft, reruns client validation, and records source name after save.
- A benchmark manifest is a UTF-8 JSON file with schema version, cases, receipt fixture reference, and expected fields. Images remain test fixtures and are not uploaded by Diagnostics in production mode.
- Diagnostics can run a configured server-side benchmark fixture set. It reports evaluated count, true-clear, false-clear, true-review, false-review, precision, recall, and false-clear rate per field and aggregate.
- Threshold publication persists a versioned threshold profile by tenant. Default thresholds remain current behavior until an admin publishes a profile.

**Validation and business rules**
- Only admin can run a benchmark or publish thresholds; reviewer can view the active profile and latest report.
- A field with no expected label is `not_evaluated` and excluded from aggregate denominator.
- Metric count invariants are enforced: confusion counts sum to evaluated labels.
- Publishing is disabled if the manifest is invalid, evaluation has zero labels, or any metric calculation failed.
- Threshold profile includes version, field thresholds, benchmark report ID, actor role, and UTC timestamp.

**Failure behavior**
- Empty queue displays **No receipts match these filters** and **Clear filters**.
- Queue refresh failure leaves previous data visible with **Retry**.
- Missing boxes display **Source region unavailable** while editing remains enabled.
- Corrupt/missing image clears the previous image from memory and shows an accessible error.
- Benchmark errors identify case ID and field without displaying receipt raw text in logs.

**Compatibility**
- Existing OCR engines and confidence values are unchanged.
- Existing review endpoint without filters returns its prior item collection plus additive metadata.
- Thresholds influence routing only after explicit publication.

**Acceptance summary**
- Filters and sorting are deterministic and represented in the URL.
- The 200-label benchmark fixture reports counts summing to 200.
- At least one normalized box highlights for a fixture with known total coordinates.
- No stale image appears when navigation changes to a broken asset.

**Non-goals:** retraining OCR, claiming universal accuracy, editing OCR boxes, arbitrary user image upload into the benchmark, multiple simultaneous threshold profiles.

### C. Inbox-to-books automation with safe rules
**Evidence and stories:** multi-channel capture and automation are expected, but opaque rules create operational risk. US-007, US-008, US-009.

**Functional requirements**
- Inbound email has parent status and child attachment records. Supported MIME types for this pass: JPEG, PNG, TIFF, BMP, WEBP, GIF, and PDF. Image magic bytes must match. PDF acceptance is ingestion-only unless an existing supported parser can create image pages; otherwise the attachment becomes `failed` with code `pdf_processing_unavailable`, not a fake receipt.
- Each attachment has filename, declared MIME, detected MIME, byte size, SHA-256, status, attempt count, receipt ID, error code, and timestamps. Raw bytes use the existing asset/blob storage path, not JSON columns.
- Email parent status is `processing`, `completed`, `partial`, `failed`, `quarantined`, or `archived`, derived from children.
- Retry is attachment-specific, increments attempt, and is idempotent while processing. Unsupported executable content is quarantined and never sent to OCR.
- Rules have lifecycle `draft`, `active`, or `archived`, monotonically increasing version, priority, conditions, actions, created/updated actor and timestamps.
- Preview returns exact match count, up to 20 sample receipts, and conflicts with active rules including winning rule by priority then creation time.
- Activation requires a successful preview of the same draft version. It affects new receipts only.
- Explicit automation run accepts a rule version and receipt IDs or saved-view snapshot. It persists per-receipt before/after, receipt version before/after, outcome, and errors.
- Rollback preflight classifies each successful item as eligible or conflict. Confirmed rollback runs in one SQLite transaction over eligible items. Any database error rolls back all eligible changes.

**Validation and business rules**
- Rule priority is integer 0-1000, lower number wins. Tie-breaker is older active rule ID creation time, then lexical rule ID for determinism.
- Conditions remain the existing allowlist: vendor contains, currency, min total, max total. Actions remain tags, project, cost center, request approval.
- Conflicting actions are same target field with differing values on a receipt. Preview must display both values and winner.
- Activation is rejected if draft changed after preview or preview failed.
- Rollback never reverses fields changed after run version. Such receipts are conflicts and remain unchanged.
- Cross-tenant email, attachment, rule, run, and rollback IDs return 404.

**Failure behavior**
- One bad attachment does not block supported siblings.
- OCR failure leaves attachment retryable with sanitized code.
- Preview failure preserves draft and disables activation.
- Automation run records item-level failures and continues only when failure is validation-related; transaction/system failure aborts the whole run.
- Rollback system failure produces zero persisted reversions.

**Compatibility**
- Existing rule create/list/preview endpoints remain, with additive lifecycle/version fields.
- Existing email simulation payload remains accepted; new attachment detail is additive.
- Existing automatic application on upload uses only active rules and records a run.

**Acceptance summary**
- Two supported attachments create two linked receipts.
- Unsupported executable is quarantined while sibling image succeeds.
- Preview causes zero receipt mutations.
- Rollback of ten unchanged receipts reverts ten; two later-edited receipts are excluded as conflicts.

**Non-goals:** full SMTP server, mailbox provider integration, arbitrary scripts/actions, schedule engine, cross-tenant shared rules, PDF OCR implementation if absent.

## UI and UX Specification
### Personas and primary journey
- **Marta, bookkeeper:** starts in Review Queue, resolves high-value blockers, prepares an export, acknowledges warnings, and downloads the CSV run artifact.
- **Alex, admin:** inspects benchmark quality, publishes thresholds, creates and previews rules, and reverses an erroneous run.
- **Sam, business owner:** forwards documents, checks attachment processing, and retries one failed receipt.

Primary journey: Inbox or Upload → Review Queue → Receipt Review → Export Preparation → Export Run Success. Secondary admin journey: Diagnostics Quality → Automation Draft → Preview → Activate → Run History → Rollback.

### Information architecture and navigation
Keep the existing AppShell. Use these primary destinations and labels:
- **Dashboard**
- **Receipts**
- **Upload**
- **Review** with outstanding count badge
- **Approvals**
- **Accounting**
- **Export Center**
- **Inbox**
- **Automations**
- remaining existing destinations unchanged
- **Settings** with Diagnostics under it

Mobile bottom navigation remains Dashboard, Receipts, Upload, Review, More. Export, Inbox, Automation, and Settings appear in More. Breadcrumbs appear on receipt detail, export preparation/run, automation detail/run, and Diagnostics Quality.

### Design system decision
Reuse Tailwind and existing components. Do not add a new component library. Extend existing design tokens in `frontend/app/globals.css` and `tailwind.config.ts` only if a token is absent. Required tokens:
- spacing: 4, 8, 12, 16, 24, 32, 48 px;
- radii: 6 px controls, 10 px cards, 999 px pills;
- type: 14 px body-small, 16 px body, 20 px section heading, 28 px page title; line-height at least 1.4;
- semantic colors: canvas, surface, text, muted, border, primary, focus, success, warning, danger, info;
- minimum normal-text contrast 4.5:1 and large-text 3:1;
- focus ring: 2 px solid focus color plus 2 px offset;
- elevation: border by default, one subtle shadow only for dialogs/popovers;
- animations 150-200 ms; `prefers-reduced-motion` removes panning animation and nonessential transitions.

### Shared interaction rules
- Primary CTA is one filled button per screen. Secondary actions are outline or text.
- Destructive actions require confirmation with affected count.
- Toasts confirm non-destructive success; persistent inline banners report failures.
- Loading uses skeletons matching final geometry. Do not blank existing lists during refetch.
- Form validation appears below the field and in a summary linked to invalid controls.
- Dialog opening moves focus to its heading; close returns focus to trigger.
- Route changes focus the `h1`. Skip link targets `main`.
- Tables use semantic table elements on desktop. On screens below 760 px, receipt and run tables become labelled cards while preserving sort/filter controls.
- Status is never conveyed by color alone; include icon and text.

### Responsive behavior
- **Mobile:** 320-759 px. Single column, sticky bottom action bar, image above form, filter drawer, card lists.
- **Tablet:** 760-1049 px. Two-column where useful, collapsible sidebar overlay, image/form 45/55 split in landscape.
- **Desktop:** 1050 px and above. Fixed sidebar, review image/form 50/50, filter rail or horizontal bar, max content width 1440 px.

### Accessibility verification
Semantic landmarks, one `h1`, ordered headings, labelled controls, `aria-live=polite` for processing updates, `role=alert` for blocking errors, accessible table captions, keyboard-operable menus, and no keyboard trap. Playwright plus `@axe-core/playwright` must report zero serious or critical violations on all selected screens at 375x812 and 1440x900.

## Screen Inventory and User Flows
### 1. Review Queue, `/review`
**Purpose:** prioritize exceptions by readiness, confidence, and financial impact.

**Layout:** page header with `Review` title, outstanding count, and secondary **Refresh**; KPI strip for Blocked, Needs review, Warning, Ready; filter bar with readiness, field, threshold, sort, saved view, and **Clear filters**; result list/table; pagination. Primary action on each item: **Review receipt**.

**States:** skeleton rows on first load; prior rows plus inline retry banner on refetch failure; empty unfiltered state says **All clear** with **Upload receipts**; filtered empty state says **No receipts match these filters** with **Clear filters**; disabled saved-view action until a filter differs from defaults.

**Flow:** open Review → set Total and Below 0.80 → URL and list update → sort Amount high to low → open item → receipt screen focuses Total. Back returns with filter and scroll position preserved.

### 2. Receipt Review/Detail, `/receipts/[id]` and queue deep link
**Purpose:** verify source evidence, correct fields, resolve blockers, and complete.

**Layout:** breadcrumb; header with vendor fallback, receipt ID, version, readiness badge; desktop split panel. Left: image toolbar (zoom, rotate view only, fit, source toggle when available), image, OCR highlight overlay, image error panel. Right: validation summary, vendor/date/total/tax/currency controls, confidence/source labels, line-item editor, metadata, sticky action bar with **Save draft** and primary **Complete review**. History is a lower tab alongside Details and Validation.

**States:** image and form load independently; missing image leaves form; stale save opens conflict dialog; save success shows version; blockers disable Complete with linked reason; warning-only completion remains enabled; unsaved navigation prompts.

**Flow:** select low-confidence Total → image pans to source → choose candidate or type correction → validation updates → Save draft → Complete review → success banner and **Prepare export** link.

### 3. Export Preparation, `/exports/prepare`
**Purpose:** create immutable preflight snapshot and resolve blockers.

**Layout:** breadcrumb and title; step indicator Select → Validate → Acknowledge → Export; connection selector; selected receipt count; three accordions Ready, Warnings, Blocked; each row shows vendor, total, version, reasons, and **Fix receipt**; sticky footer with secondary **Save preparation** and primary **Export ready items**.

**States:** validation skeleton; no selection prompts **Choose receipts**; missing connection disables export; stale preparation shows persistent banner and **Revalidate**; connection error creates failure panel with **Retry export**; warnings require checkboxes and an overall acknowledgement summary.

**Flow:** choose connection → validate → fix blocker in new route and return with selection → acknowledge warnings → export → navigate to run detail.

### 4. Export Run Detail, `/exports/runs/[id]` (new)
**Purpose:** provide immutable outcome and retry/download actions.

**Layout:** breadcrumb; status header with run ID and timestamp; summary cards requested/exported/failed; error panel when applicable; receipt list; audit metadata; primary **Download CSV** for completed reference provider, or **Retry export** for retryable failure; secondary **View preparation**.

**States:** processing polls every 2 seconds up to 60 seconds then uses manual Refresh; completed exposes artifact; failed exposes sanitized code; 404 has **Back to Export Center**.

### 5. Receipt Audit Record, `/receipts/[id]?tab=history`
**Purpose:** answer who changed what and when.

**Layout:** filter chips All, Corrections, Automation, Export; event timeline; selected event detail with actor role, UTC time, before/after diff, linked run/preparation; secondary **Download audit JSON**.

**States:** created events label missing before as Created; empty filter gives **No events in this category**; retrieval failure preserves receipt header and offers Retry.

### 6. Diagnostics Quality, `/settings/diagnostics/quality` (new)
**Purpose:** evaluate and publish confidence thresholds.

**Layout:** breadcrumb; active threshold profile card; benchmark selection card limited to repository-configured fixtures; **Run evaluation**; progress; result table per field; aggregate cards; threshold sliders/numeric inputs; primary **Publish thresholds**, secondary **Reset proposal**.

**States:** no prior report explains benchmark requirement; running disables publication; invalid manifest lists case/field errors; zero-label report blocks publication; success shows profile version and effective timestamp.

**Flow:** select fixture → run → inspect false-clear metrics → adjust threshold → metrics recalculate against stored results → publish → Review Queue uses profile on next request.

### 7. Inbox, `/inbox`
**Purpose:** observe email and attachment ingestion.

**Layout:** header with forwarding address and **Copy address**; status filters; message cards with sender, subject, time, parent status, and attachment counts; expandable attachment rows with status, filename, size, receipt link, error, and **Retry**; archive action in overflow menu.

**States:** empty state explains forwarding; processing uses live region; partial status lists success and failure; quarantine uses danger icon/text; retry disabled while processing; archive success removes card and offers Undo for 10 seconds.

### 8. Automations List, `/automations`
**Purpose:** manage draft/active/archived rules.

**Layout:** title and primary **New rule**; tabs Active, Drafts, Archived; rule cards with priority, summary, version, last run, and actions **Edit**, **Preview**, **Run history**.

**States:** empty active state offers New rule; API failure banner with Retry; archived is read-only except Restore as draft.

### 9. Automation Editor/Preview, `/automations/[id]` (new)
**Purpose:** edit a draft, preview matches/conflicts, and activate safely.

**Layout:** breadcrumb; status/version; condition builder; action builder; priority; sticky **Save draft** and primary **Preview rule**. After preview, lower panel shows exact count, up to 20 samples, conflicts, winner explanation, and primary **Activate rule**.

**States:** field validation; unsaved changes; preview spinner; preview error preserves draft and disables activation; changed draft invalidates prior preview; activation success routes to detail with confirmation.

### 10. Automation Run History, `/automations/[id]/runs`
**Purpose:** inspect applied runs and initiate rollback.

**Layout:** rule header; run table/cards with status, affected/failed counts, time, actor; row action **View run**.

### 11. Automation Run Detail/Rollback, `/automations/[id]/runs/[runId]`
**Purpose:** show receipt-level effects and safely reverse them.

**Layout:** summary; before/after item list; primary **Preview rollback** for completed runs; rollback panel categorizes Eligible and Conflicts; destructive **Roll back eligible changes** confirmation shows count.

**States:** no eligible changes disables rollback; conflicts link to receipt history; system failure shows zero-changes guarantee and Retry; success records rollback run and removes rollback CTA.

### End-to-end friendly failure recovery
Marta opens Review, filters low-confidence totals, corrects a receipt, and completes it. She opens Export Preparation and sees another receipt blocked for currency. **Fix receipt** deep-links to Currency; after saving, Back returns to the unchanged preparation selection. She acknowledges one line-total warning and exports. If the connection simulation fails, the run detail shows a retryable error and leaves all receipts unexported. **Retry export** reuses the same preparation with a new idempotency key; refresh/replay of that request returns the same run rather than duplicating output.

### UI verification procedure
- Build and type-check the frontend.
- Start FastAPI on 127.0.0.1:8000 and Next.js on 127.0.0.1:3000 with the documented API base URL.
- Run Playwright critical flows at desktop and mobile sizes.
- Run axe checks on all eleven screens.
- Capture screenshots for Review Queue, Receipt Review, Export Preparation, Diagnostics Quality, Inbox partial state, Automation Preview conflict, and Rollback preflight. Store intentional documentation screenshots under `docs/screenshots/`; temporary failure screenshots remain excluded from packaging.

## Architecture and Technical Design
### Boundaries
- **HTTP adapters:** `app/product_api.py` validates transport and delegates; no SQL is added directly to route handlers.
- **Review/readiness service:** extend `app/product_service.py` for queue queries and structured conflicts; reuse `AccountingWorkspace.validate` through a service facade.
- **Export workflow service:** new `app/export_workflow.py` owns preparation snapshots, idempotent execution, run state, audit record, and artifact metadata.
- **Quality service:** extend `app/quality.py` or add `app/quality_service.py` for manifest validation, metrics, reports, and threshold profiles.
- **Inbox service:** extend `app/accounting_workspace.py` only for schema migration compatibility; put attachment processing/state in new `app/inbox_service.py`.
- **Automation service:** move lifecycle/run/rollback behavior into new `app/automation_service.py`; `AdvancedWorkspace` remains persistence adapter for legacy methods.
- **Frontend API layer:** `frontend/lib/api.ts` and `types.ts` define all shapes. SWR owns server state; page-local React state owns drafts, viewer state, and selection.
- **No global store:** URL params own queue filters; server IDs own preparation/run state; localStorage is not used for financial drafts.

### Data flow
1. Ingestion creates email plus attachments or direct receipt.
2. OCR stores immutable asset, extraction, confidence, boxes, and provenance candidates.
3. Active automation rules execute and record a run.
4. Queue query joins computed readiness and threshold profile.
5. Reviewer saves with expected version; history records changed fields and provenance.
6. Preparation snapshots validation and receipt versions.
7. Execution checks snapshot versions, acknowledgements, connection, and idempotency, then writes immutable run and artifact metadata.

### State and concurrency
- All write commands require tenant context.
- Receipt writes use expected version.
- Rule writes use expected rule version.
- Preparation is immutable. Revalidation creates a new preparation.
- Automation run and rollback are transaction boundaries.
- Idempotency table is keyed by tenant, scope, and key with 24-hour minimum retention; stored response includes status and resource ID.

### Alternatives considered
- **New UI library:** rejected; it adds bundle and migration cost without solving workflow gaps.
- **Redux/Zustand:** rejected; server state and local drafts fit SWR plus component state.
- **Background queue dependency:** rejected for this pass; current executor remains, with durable state and deterministic retries. A production worker is a later scalability phase.
- **Modify legacy workspace in parallel:** rejected; doubles implementation and testing cost.
- **Build live provider connector now:** rejected; internal correctness and idempotency come first.

## Data, API, and Compatibility Changes
### SQLite schema migration
Use additive, idempotent `CREATE TABLE IF NOT EXISTS` and column migration helpers. Increment the product schema version and test migration from a database created by 1.4.0.

New tables:
- `confidence_profiles(profile_id, tenant_id, version, thresholds_json, benchmark_report_id, active, created_by_role, created_at)` with one active profile per tenant.
- `benchmark_reports(report_id, tenant_id, manifest_name, metrics_json, evaluated_count, status, created_by_role, created_at)`.
- `inbound_email_attachments(attachment_id, email_id, tenant_id, filename, declared_type, detected_type, size_bytes, sha256, status, attempt, receipt_id, error_code, created_at, updated_at)`.
- `automation_rule_versions(rule_id, tenant_id, version, status, name, conditions_json, actions_json, priority, preview_token, previewed_at, created_by_role, created_at)`.
- `automation_runs(run_id, tenant_id, rule_id, rule_version, status, input_json, summary_json, rollback_of, created_by_role, created_at, completed_at)`.
- `automation_run_items(run_id, receipt_id, before_json, after_json, before_version, after_version, status, error_code)`.
- `export_commands(command_id, tenant_id, preparation_id, idempotency_key, warning_ack_json, run_id, response_json, created_at)` unique on tenant and idempotency key.

Extend export preparation persistence with receipt-version and validation-snapshot JSON. Do not drop legacy columns.

### Exact API additions and changes
All responses use existing error conventions plus `{code, message, field?, retryable?, current_version?}` for structured errors.

- `GET /product/review-items?confidence_field=total&confidence_lt=0.8&readiness=blocked&sort=amount_desc&limit=50&offset=0`
  - Response: `{items, total, limit, offset, active_threshold_profile}`.
- `PATCH /product/receipts/{id}/workspace` additive 409 body: `{code:"stale_version", message, current_version, current_fields}`.
- `GET /product/receipts/{id}/audit` returns redacted JSON audit record.
- `POST /product/export-preparations` request `{receipt_ids:[...], connection_id}`; response adds `receipt_versions` and `validation_snapshot`.
- `POST /product/export-commands` request `{preparation_id, acknowledged_warning_receipt_ids}` and required `Idempotency-Key`; response `{run_id,status,preparation_id,requested,exported,error_code,retryable}`.
- `GET /product/export-runs/{id}` returns immutable detail.
- `GET /product/export-runs/{id}/artifact` returns CSV only when completed.
- `POST /product/quality/benchmarks/run` request `{manifest_name}`; admin only.
- `GET /product/quality/benchmarks/{report_id}` retrieves metrics.
- `POST /product/quality/confidence-profiles` request `{benchmark_report_id, thresholds}`; admin only.
- `GET /product/quality/confidence-profiles/active` retrieves active profile.
- `GET /product/inbound-emails/{email_id}` returns parent plus attachment details.
- `POST /product/inbound-emails/{email_id}/attachments/{attachment_id}/retry` has empty body and returns attachment state.
- `POST /product/inbound-emails/{email_id}/archive` returns archived parent.
- `GET /product/automation-rules/{rule_id}` returns latest plus versions.
- `PATCH /product/automation-rules/{rule_id}` request `{expected_version,name,conditions,actions,priority}` creates next draft version.
- `POST /product/automation-rules/{rule_id}/preview` request `{version,receipt_ids?,saved_view_id?}` returns `{preview_token,match_count,samples,conflicts}`.
- `POST /product/automation-rules/{rule_id}/activate` request `{version,preview_token}`.
- `POST /product/automation-rules/{rule_id}/runs` request `{version,receipt_ids?,saved_view_id?}`.
- `GET /product/automation-rules/{rule_id}/runs` and `GET /product/automation-runs/{run_id}`.
- `POST /product/automation-runs/{run_id}/rollback-preview` returns eligible/conflicts.
- `POST /product/automation-runs/{run_id}/rollback` request `{eligible_receipt_ids}` and required `Idempotency-Key`.

### Migration and compatibility
- Migration runs at service startup inside a transaction and is idempotent.
- A copied 1.4.0 database must open with all old data readable.
- Existing endpoints, headers, and response fields remain accepted.
- Existing rule records are migrated as version 1 active rules.
- Existing inbound-email JSON attachments are converted lazily or by migration into child metadata rows without inventing bytes.
- No route is removed. Deprecations, if any, are documented but remain operational for this release.

## Security and Privacy Considerations
- Continue MIME allowlisting, magic-byte validation, size limits, sanitized filenames, SHA-256, SSRF protections, and tenant predicates on every query.
- Set attachment limit to 20 MB each and 20 attachments per email, matching existing image limit unless configuration specifies a lower value.
- Reject path traversal and never use user filename as filesystem path.
- Quarantine executable, script, archive, and unknown binary content. Quarantine means metadata retained, bytes inaccessible to OCR and UI download.
- Audit JSON excludes image bytes, raw OCR text by default, API keys, tokens, webhook secrets, and full attachment bytes.
- Logs include request ID, tenant ID, resource ID, operation, status, duration, and error code; never log receipt values, email bodies, or binary content.
- CORS wildcard-with-credentials is a known risk. The development pass must change configuration to explicit allowed origins from environment while retaining a test/dev default for localhost, and must add regression tests. This is an explicitly justified behavior change.
- Use constant-time comparison where secrets or idempotency signatures are compared. Do not expose whether a cross-tenant ID exists.
- Benchmark fixture selection is allowlisted server-side; no arbitrary filesystem path.
- CSV formula-injection protection remains mandatory.

## Test Strategy (TDD)
### Test mapping discipline
Every acceptance criterion in the embedded JSON receives a test ID in `FEATURES-DONE.md` and `development-report.md`. Test names include the story ID, for example `test_us_001_stale_version_preserves_server_data`. The traceability matrix below defines the minimum mapping; one test may cover multiple criteria only when all outcomes are asserted.

### RED tests before implementation
**Feature A**
- US-001: queue/review fixture corrects low-confidence total; stale version returns structured 409; image failure leaves workspace data available.
- US-002: exactly 2 of 10 blocked; warning acknowledgement required and audited; connection error creates failed retryable run with zero exports.
- US-003: history ordering and before/after; Created event rendering contract; audit failure UI retry.
- Idempotency replay test and migration-from-1.4.0 test.

**Feature B**
- US-004: server filter returns five; empty filter contract; failed SWR refetch preserves rendered rows in Playwright.
- US-005: 200 labels sum invariant; missing tax excluded; invalid manifest blocks publish with row errors.
- US-006: total box highlight; unavailable region message; corrupt asset clears prior image.

**Feature C**
- US-007: two attachments create two receipts; executable sibling quarantined; one OCR failure yields partial and retry.
- US-008: preview count 12 with no mutations; deterministic conflict winner; activation disabled after preview error/version change.
- US-009: ten-item rollback; two later edits excluded; injected transaction failure leaves zero reversions.

### Unit tests
- Readiness rule functions, confidence filter parser/sorter, metric calculations, threshold validation, MIME detection, parent-status derivation, rule conflict resolution, idempotency lookup, rollback eligibility, redaction, and structured error mapping.
- Changed/new Python modules require at least 90% statement coverage measured with pytest-cov, which must be added to dev dependencies only if not available in the lockfile.
- Frontend utility functions and reducers use existing testing approach; if no component unit runner exists, do not add one solely for this pass. Cover behavior through Playwright and TypeScript checks.

### Integration tests
- Temporary on-disk SQLite, real file bytes for valid/invalid images, real CSV artifact I/O, service restart, and migration from a copied legacy schema.
- No live external accounting API is required. Do not mock internal persistence in the integration suite.
- Validate transaction rollback by injecting a database failure after multiple eligible items.
- Validate no cross-tenant access for every new resource type.

### Browser/E2E tests
- Upload/inbox → review filter → source highlight → correction → completion → preparation → warning acknowledgement → export → CSV download.
- Automation draft → preview conflict → activate → explicit run → history → rollback conflict and success.
- Diagnostics benchmark → metric view → threshold publish → queue reflects profile.
- Mobile 375x812 and desktop 1440x900; keyboard-only pass for all primary actions.
- Axe on selected screens, zero serious/critical violations.

### Commands
Supported existing commands:
- Python targeted: `pytest -q tests/test_product_features.py tests/test_export_readiness_workflow.py tests/test_accounting_readiness_ui.py`
- Python full regression: `pytest -q`
- Ruff: `ruff check app tests`
- Frontend install: `cd frontend && npm ci`
- Type-check: `cd frontend && npm run typecheck`
- Build: `cd frontend && npm run build`
- E2E: `cd frontend && npx playwright test`
- Backend startup smoke: `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Frontend startup smoke after build: `cd frontend && npm run start -- --hostname 127.0.0.1 --port 3000`

New repository gate wrappers to add and execute:
- `bash scripts/tdd-gate-v3.sh`
- `bash scripts/bdd-gate.sh`
- `bash scripts/security-gate.sh`
- `bash scripts/doc-sync-check.sh`
- `bash scripts/ui-gate.sh`
- `bash scripts/git-push-verify.sh`

The wrappers must fail closed, use only repository-supported commands, print command/status evidence, and be documented. `git-push-verify.sh` verifies clean working tree, current branch upstream, local HEAD equals upstream HEAD, and the pushed commit includes required artifacts. If the execution environment has no authenticated remote, the development phase is incomplete and must state that gate as blocked rather than fabricating success.

### Objective gates
- All targeted tests pass after each feature.
- Full pytest, Ruff, type-check, Next build, Playwright, and startup smoke pass.
- Changed/new Python modules have at least 90% statement coverage.
- Every BDD criterion maps to a passing test ID.
- No serious/critical axe violation.
- No duplicate export or rollback under repeated idempotency key.
- All six lab gate scripts exit 0, including UI gate because a UI exists.

## Documentation Deliverables
The development phase must update:

- **`README.md`:** rewrite the opening GitHub-facing section to explain the product in one paragraph; show current screenshots; list the exception-to-export workflow; distinguish Next.js primary UI from legacy workspace; provide backend/frontend quickstart; explain Tesseract and optional vision setup; identify demo auth limitations; list supported import/export behavior; link focused docs; include tested commands. Keep advanced API reference out of the opening overview.
- **`CHANGELOG.md`:** add a release entry with Added, Changed, Security, Fixed, Compatibility, and Migration sections, including explicit CORS change and new schema.
- **`docs/api.md`:** document every new/changed endpoint, request/response, headers, status codes, idempotency, pagination/filter semantics, and compatibility.
- **`docs/product-workflows.md`:** document inbox-to-review-to-export and automation rollback with failure recovery.
- **`docs/accounting-export-guide.md`:** document readiness rules, warnings, preparation snapshot, replay behavior, and CSV artifact.
- **`docs/gui-workspace.md`:** document new Next.js screens, keyboard behavior, and legacy-workspace status.
- **`FEATURES-DONE.md`:** requirement/story/test traceability list; each story and criterion marked implemented only with test evidence and file locations.
- **`development-report.md`:** summary; architecture decisions; migrations; exact files changed; test/gate commands and results; coverage; screenshots; known limitations; git commit hash, branch, remote, and push verification.

Documentation must describe observed behavior after tests, not planned behavior. `doc-sync-check.sh` validates route names, documented commands, version references, required files/sections, and absence of placeholders.

## Expected File Changes
**Backend additions:**
- `app/export_workflow.py`
- `app/quality_service.py` if `app/quality.py` cannot retain a single responsibility
- `app/inbox_service.py`
- `app/automation_service.py`

**Backend modifications:**
- `app/product_api.py`
- `app/product_service.py`
- `app/advanced_workspace.py`
- `app/accounting_workspace.py`
- `app/quality.py`
- `app/api.py` for explicit CORS configuration only
- `pyproject.toml` and `uv.lock` only if pytest-cov is newly required

**Frontend additions:**
- `frontend/app/(app)/exports/runs/[id]/page.tsx`
- `frontend/app/(app)/settings/diagnostics/quality/page.tsx`
- `frontend/app/(app)/automations/[id]/page.tsx`
- `frontend/app/(app)/automations/[id]/runs/page.tsx`
- `frontend/app/(app)/automations/[id]/runs/[runId]/page.tsx`
- focused components under `frontend/components/` for validation summary, provenance viewer, confidence filter, export status groups, attachment status, rule builder, conflict table, and rollback preview

**Frontend modifications:**
- existing review, receipt detail, export preparation, inbox, automation, diagnostics pages
- `frontend/lib/api.ts`, `frontend/lib/types.ts`, relevant hooks, AppShell/navigation, globals/tokens only where necessary

**Tests:**
- extend current targeted files and add focused tests such as `tests/test_export_workflow.py`, `tests/test_quality_calibration.py`, `tests/test_inbox_attachments.py`, `tests/test_automation_runs.py`, `tests/test_schema_migration_v140.py`
- add Playwright specs for review/export, quality, inbox, and automation rollback

**Gates and docs:**
- add six scripts under `scripts/`
- update documentation listed above
- add `FEATURES-DONE.md`, `development-report.md`, and intentional screenshots

Do not modify unrelated forecasting, budget, subscription, approval, duplicate, or report behavior except to fix a regression introduced by this pass.

## Traceability Matrix
| Research need | Research evidence | User story id | Planned requirement | Acceptance criterion | Planned implementation location | Planned test evidence | Priority |
|---|---|---|---|---|---|---|---|
| Focus corrections on uncertain receipts | Competitor accuracy claims conflict with user reports of currency/tax errors | US-001 | Unified review with source evidence and readiness recomputation | Correcting total increments version and reaches exportable within 2 seconds | `product_service.py`, review/detail pages | `test_us_001_happy`, Playwright review/export | P0 |
| Prevent data loss under concurrent review | Current optimistic version exists; drafts need recovery | US-001 | Structured 409 and preserved client draft | Stale submission does not overwrite and draft remains | `product_api.py`, receipt page | `test_us_001_stale`, E2E conflict | P0 |
| Continue review when image fails | Users report missing/opaque documents | US-001 | Independent image/form loading | Retryable image error; completion remains false | receipt page, asset endpoint | `test_us_001_image_error` | P0 |
| Deterministic preflight | Matching and completeness are core pains | US-002 | Immutable validation snapshot and groups | Exactly 2 blockers and 8 eligible in fixture | `export_workflow.py`, prepare page | `test_us_002_preflight_counts` | P0 |
| Explicit warning consent | Tax/line mismatch can require manual review | US-002 | Warning acknowledgement in command and audit | Warning export blocked until acknowledged | export API/UI | `test_us_002_warning_ack` | P0 |
| Recover from connector failure | Background sync failures reported | US-002 | Failed immutable run, zero posts, retryable error | Auth error creates failed run without exports | export service/run page | `test_us_002_connection_failure` | P0 |
| Audit who changed what | Accounting workflow requires defensibility | US-003 | Redacted chronological history and JSON download | 3 expected events with UTC before/after | history/audit API and tab | `test_us_003_history` | P0 |
| Render creation safely | Missing before values are valid | US-003 | Created event semantic state | UI displays Created, no broken diff | history component | `test_us_003_created_event` | P0 |
| Recover audit retrieval | Operational UI needs friendly errors | US-003 | Persistent receipt header and Retry | No invented events after failure | history component | `test_us_003_error` | P0 |
| Prioritize confidence exceptions | Users need exception handling over raw OCR | US-004 | URL-backed confidence filter and sort | Five exact matches and URL state | queue query/review page | `test_us_004_filter`, E2E | P0 |
| Explain empty results | Modern baseline requires explicit empty states | US-004 | Filtered empty CTA | Empty message plus Clear filters | review page | `test_us_004_empty` | P0 |
| Preserve work during refresh failure | Opaque processing erodes trust | US-004 | SWR stale-data error banner | Prior list remains with Retry | review hook/page | `test_us_004_timeout` | P0 |
| Measure false-clear risk | No quality claim without benchmark | US-005 | Versioned benchmark metrics | Counts sum to 200 | quality service/diagnostics | `test_us_005_metrics` | P0 |
| Handle missing labels correctly | Benchmark data can be partial | US-005 | Exclude not-evaluated fields | Tax excluded from aggregate | quality service | `test_us_005_missing_label` | P0 |
| Block invalid publication | Thresholds can misroute receipts | US-005 | Strict manifest validation | Row errors and disabled publish | quality API/page | `test_us_005_invalid_manifest` | P0 |
| Verify extraction source quickly | Provenance reduces review time | US-006 | Field-to-box focus and pan | Known total box highlighted | viewer component | `test_us_006_box`, E2E | P0 |
| Allow manual fallback | Boxes may not exist | US-006 | Source unavailable state | Manual input remains enabled | viewer/detail page | `test_us_006_no_box` | P0 |
| Prevent stale source display | Cross-document confusion is harmful | US-006 | Clear image before new load | Broken asset never shows previous image | viewer component | `test_us_006_corrupt` | P0 |
| Multi-channel ingestion | Dext/Hubdoc make email capture table stakes | US-007 | Attachment-level processing | Two supported files create two links | inbox service/UI | `test_us_007_two_attachments` | P1 |
| Quarantine unsafe content | Financial inbox is an attack surface | US-007 | MIME/magic allowlist and quarantine | Executable quarantined; image succeeds | inbox/security service | `test_us_007_quarantine` | P1 |
| Retry one failed attachment | One failure must not block siblings | US-007 | Attachment Retry and partial parent | One receipt plus retry action | inbox API/page | `test_us_007_partial_retry` | P1 |
| Preview before automation | Opaque automation risks bulk errors | US-008 | Zero-mutation preview with sample count | Count 12, max 20 samples, no writes | automation service/editor | `test_us_008_preview` | P1 |
| Resolve rule conflicts | Multiple rules can target same field | US-008 | Deterministic priority and winner display | Conflict and winner shown | automation service/UI | `test_us_008_conflict` | P1 |
| Prevent stale activation | Draft can change after preview | US-008 | Preview token bound to version | Activation disabled/rejected | automation API/editor | `test_us_008_stale_preview` | P1 |
| Reverse erroneous runs | Safe automation requires recovery | US-009 | Atomic rollback with history | Ten receipts reverted with events | automation service/run page | `test_us_009_rollback` | P1 |
| Preserve later manual edits | Rollback must not destroy newer work | US-009 | Version-based conflict exclusion | Two conflicts excluded, eight eligible | automation service | `test_us_009_conflicts` | P1 |
| Guarantee transaction atomicity | Partial reversal is unacceptable | US-009 | Single transaction and retryable failure | Injected failure persists zero reversions | automation service | `test_us_009_atomic_failure` | P1 |

## Risks and Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Scope is still broad | Partial features | Implement in vertical slices A then B then C; feature flags are not completion substitutes; stop only at selected-scope boundary. |
| Schema drift or data loss | Existing installs fail | Additive migration, copied 1.4.0 DB integration test, backup guidance, no column drops. |
| Confidence metrics mislead | False trust | Labelled fixture, explicit denominator, false-clear primary metric, versioned publication, no marketing claim. |
| Rollback overwrites newer data | Financial corruption | Receipt versions, preflight, conflict exclusion, atomic transaction, immutable run items. |
| Duplicate exports | Ledger duplication | Tenant-scoped idempotency key, preparation version check, immutable run, replay test. |
| Malicious attachments | Code execution/data exposure | MIME plus magic validation, strict limits, quarantine, no filename path use, tenant isolation. |
| Dual UI confusion | Maintenance overhead | New work only in Next.js; document primary surface; preserve legacy compatibility without parallel feature implementation. |
| Gate scripts absent today | False completion claim | Add explicit scripts; fail closed; record output in development report; no substitution with manual summary. |
| Git push unavailable | Lab policy failure | Treat as blocker, retain completed artifact, report exact remote/auth limitation; never claim success without upstream hash match. |

## Definition of Done
- [ ] All three selected features are complete end to end with no facade, placeholder, synthetic success, or unpersisted critical state.
- [ ] All nine embedded stories and every acceptance criterion have implementation and test evidence.
- [ ] Inbox/upload → review/provenance → completion → preparation → acknowledgement → export artifact works.
- [ ] Automation draft → preview/conflict → activate → run → rollback works.
- [ ] Diagnostics benchmark → metrics → threshold publish → queue behavior works.
- [ ] Existing behavior remains compatible, including legacy endpoints and `/workspace`.
- [ ] Additive migration from a 1.4.0 database passes and existing records remain readable.
- [ ] Targeted tests pass during each slice, then full `pytest -q` passes.
- [ ] Meaningful integration tests use on-disk SQLite and real file/CSV I/O.
- [ ] Changed/new Python modules achieve at least 90% statement coverage.
- [ ] `ruff check app tests` passes.
- [ ] Frontend `npm ci`, type-check, build, Playwright, and startup smoke pass.
- [ ] Desktop and mobile screenshots and keyboard checks are complete.
- [ ] Axe reports zero serious or critical issues on selected screens.
- [ ] `scripts/tdd-gate-v3.sh` passes.
- [ ] `scripts/bdd-gate.sh` passes.
- [ ] `scripts/security-gate.sh` passes.
- [ ] `scripts/doc-sync-check.sh` passes.
- [ ] `scripts/ui-gate.sh` passes.
- [ ] README, CHANGELOG, API/workflow/export/GUI docs, `FEATURES-DONE.md`, and `development-report.md` match tested behavior.
- [ ] README gives a concise, accurate GitHub overview and clearly identifies the Next.js primary UI and demo-auth limitation.
- [ ] No secrets, credentials, caches, virtual environments, coverage artifacts, build outputs, screenshots outside intentional docs, or scratch data are committed or packaged.
- [ ] Requirement → story → implementation → test → evidence traceability is complete.
- [ ] Git commit and push are completed; `scripts/git-push-verify.sh` proves local HEAD equals upstream HEAD and working tree is clean.
- [ ] The complete project is packaged, ZIP integrity-tested, listed, extracted into a separate directory, checked for required files, and confirmed to have no extra enclosing directory.
