# Research Findings

## Executive Summary
ReceiptLens 1.4.0 is a substantial, test-backed receipt intelligence and bookkeeping workflow product rather than a narrow OCR demo. It combines Tesseract and optional vision-model extraction, a FastAPI service, a Next.js 14 workspace, tenant-scoped receipt/review/approval/export workflows, accounting-readiness checks, automation rules, duplicate handling, forecasts, and privacy/diagnostic controls. The strongest market wedge is not “better OCR” alone. It is a transparent, privacy-capable **exception-to-export workflow for small bookkeepers and owner-managed businesses**, with field provenance, deterministic preflight, safe automation, and predictable low-volume pricing.

The recommended next pass is intentionally narrow: (1) complete the accounting-safe review and export gate, (2) make confidence/provenance a first-class exception queue with measurable calibration, and (3) connect email/batch capture to previewable, reversible automation. QuickBooks/Xero production connectors should follow once the internal preflight and idempotency contracts are proven. This sequencing addresses recurring complaints about opaque matching, currency/tax errors, document handling, and pricing while building on code already present.

Evidence quality is mixed by design: official product and pricing pages establish current packaging and table stakes; community threads provide directional pain signals; project-file findings are verified locally. Market-size estimates differ dramatically across publishers, so this report treats direction as validated but does not use any single TAM figure for planning.

## Project Understanding
- **Purpose:** turn receipt images into structured, confidence-scored financial data, then review, enrich, approve, analyze, and export it. Verified in `app/api.py`, `app/ocr.py`, `app/product_api.py`, and `app/product_service.py`.
- **Target users:** small businesses, bookkeepers/accountants, finance reviewers, and developers embedding receipt OCR. This is inferred from the API, CLI, accounting profiles, roles (`admin`, `reviewer`, `integrator`), and the Next.js routes.
- **Stack:** Python 3.11+, FastAPI, Pydantic, Pillow, pytesseract, SQLite reference persistence, optional vision OCR, pytest/ruff; Next.js 14, React 18, TypeScript, SWR, Recharts, Tailwind, Playwright, and axe (`pyproject.toml`, `frontend/package.json`).
- **Principal flow:** capture by upload/URL/email/batch → OCR and confidence → tenant receipt/job → review and correction → metadata/rules/duplicates/approval → accounting validation → export preparation/export → history/diagnostics. Verified across `app/api.py`, `app/advanced_workspace.py`, `app/accounting_workspace.py`, and `frontend/app/**`.
- **UI:** a legacy server-served workspace and a broader Next.js application coexist. The Next frontend includes dashboard, receipts, upload, review, approvals, duplicates, automation, accounting, exports, inbox, subscriptions, forecast, reports, integrations, and settings.
- **Maturity:** broad feature surface, 56 test files, deployment assets, and version 1.4.0 indicate an advanced prototype or pre-production product. Production maturity is not proven because several paths remain in-memory, auth is header-based demo identity, and external connectors are not yet demonstrated end to end.

## Current-State Gap Analysis
| Area | Verified strength | Gap / consequence | Evidence |
|---|---|---|---|
| Functional | Sync/async and batch OCR, duplicate checks, review, approvals, forecasting, exports | Breadth outruns a single polished daily workflow; some CLI export paths emit empty results | `app/api.py`, `app/cli.py` |
| OCR quality | Preprocessing, multi-language Tesseract, optional vision fallback, confidence and boxes | No shipped calibration dashboard or labelled benchmark gate ties confidence to false-clear risk | `app/preprocessing.py`, `app/ocr.py`, `app/quality.py` |
| Accounting | QuickBooks/Xero/generic profiles, readiness validation, line items, mapping primitives | Provider-grade connector behavior, OAuth, replay-safe posting, and reconciliation are not proven | `app/export.py`, `app/accounting_workspace.py`, `app/integrations.py` |
| Workflow | Saved views, notifications, rules, history, work queue, optimistic concurrency | Rule conflict visualization and user-facing rollback are missing; idempotency header is accepted but discarded in workspace update | `app/advanced_workspace.py`, `app/product_api.py` |
| Security | SSRF guard, magic-byte validation, audit-chain and webhook primitives | CORS permits all origins while credentials are enabled; demo tenant/role headers are not production authentication | `app/api.py`, `app/security.py`, `app/governance.py` |
| Persistence | Tenant-scoped SQLite product service and data-plane reference | Other analytics/budget/job stores remain process-memory, limiting restart safety and horizontal scaling | `app/platform.py`, `app/budgets.py`, `app/reports.py` |
| UX | Extensive responsive Next.js route set, empty states, accessibility tooling | Dual frontend surfaces create maintenance and product-coherence risk; onboarding and failure recovery need evidence from E2E tests | `frontend/app`, `analysis/architecture-frontend.md` |
| Documentation | Large README and many focused guides | Documentation breadth may overwhelm first-time GitHub visitors; architecture/current-state distinctions need continued pruning, but this research phase is prohibited from changing README | `README.md`, `docs/` |
| Distribution | Docker/Railway assets, CLI, API, PWA-oriented frontend | No validated installation telemetry, hosted trial funnel, or packaging/pricing implementation | `infra/`, `railway.toml`, `pyproject.toml` |

**Constraints for later phases:** preserve tenant isolation; retain optimistic versions and auditability; do not make confidence claims without benchmark evidence; keep original currency and source document; support local/self-hosted operation; consolidate rather than expand feature surface; add real authentication before production; maintain Python 3.11 and Next.js 14 compatibility unless a dedicated upgrade pass is planned.

## Target Users and Jobs to Be Done
1. **Bookkeeper managing multiple SMBs:** “When documents arrive from mixed channels, help me identify only exceptions, correct them with source evidence, and publish clean transactions without duplicate work.”
2. **Owner-managed SMB:** “Let me capture receipts immediately, know what still needs attention, and hand off audit-ready data without learning accounting software internals.”
3. **Finance reviewer/approver:** “Show policy, evidence, and history so I can approve or reject quickly and defensibly.”
4. **Developer/integrator:** “Give me stable JSON, idempotent APIs, webhooks, clear limits, and self-host/privacy options so I can embed extraction safely.”

The most attractive initial segment is a small bookkeeping practice or finance operator processing roughly tens to low hundreds of documents monthly. This segment is too operationally demanding for a simple scanner, but may resist per-client bundles or a $500 API minimum [S7][S10].

## Target-Market Pain Points
| Problem | Segment | Recurrence observed | Evidence | Confidence | Implication |
|---|---|---:|---|---|---|
| Matching captured paperwork to existing ledger transactions is unreliable or delayed | QBO bookkeeper | Repeated within one detailed workflow report and central to competitor positioning | [S10], [S1], [S3] | MEDIUM | Make matching/preflight deterministic, explainable, and manually refreshable |
| Currency may be interpreted incorrectly, complicating reconciliation | Xero user with foreign-currency documents | One strong anecdote; category-wide international support claims suggest relevance | [S11], [S5] | LOW-MEDIUM | Preserve source currency and expose conversion provenance |
| Tax and line-item handling can require more work than manual entry | Bookkeeper | Multiple issues in one community thread; official competitors promote line-item extraction | [S11], [S1], [S2] | MEDIUM | Add sum checks, tax validation, and confidence-backed line-item review |
| Users fear lost documents and opaque processing states | Bookkeeper | Direct community report plus competitors emphasize centralized storage | [S11], [S8], [S9] | MEDIUM | Durable ingestion status, attachment-level retries, and immutable provenance |
| Pricing penalizes unused client accounts or low volume | Small practice | Direct complaint; confirmed contrast among bundle, per-member, flat, and minimum-commitment models | [S10], [S1], [S3], [S7], [S8] | HIGH | Offer transparent starter allocation and overage, not forced client bundles |
| Capture must work across mobile, desktop, and email | SMB/bookkeeper | Consistent table stake across Dext and Hubdoc | [S2], [S8], [S9] | HIGH | Unify upload, batch, and email into one traceable inbox |
| Raw OCR is insufficient; users buy approval, policy, and accounting outcomes | Finance teams | Consistent competitor packaging and independent category analysis | [S3], [S12], [S13] | HIGH | Position around exception-to-export, not scan accuracy alone |

## Competitor Weaknesses
- **Dext:** sophisticated and accountant-oriented, but per-client practice packaging and add-ons create cost/complexity concerns; a community user describes unreliable paperwork matching and delayed background sync [S1][S10].
- **Expensify:** strong end-to-end employee expense, card, travel, and approval platform, but it is broader and per-member priced; advanced controls move to custom/Control packaging [S3][S4]. ReceiptLens should not compete first on corporate travel.
- **Hubdoc:** simple flat pricing and strong Xero/QBO document collection, but community evidence flags multi-currency, tax-line, and document-reliability concerns [S8][S9][S11].
- **Veryfi:** excellent developer surface, multilingual/currency breadth, line items, and fraud options, but the production API starts at a $500 monthly minimum after the free tier [S5][S6][S7]. This leaves room for self-hosted and low-volume developer packaging.
- **Substitutes such as built-in QBO/Xero capture:** convenient because users already live in the ledger, but community reports describe buggy capture/matching and seat constraints [S10]. The strategic response is portability and transparent preflight, not another isolated archive.

## Competitor Comparison
| Product | Audience / positioning | Current pricing evidence | Core flow and strengths | Exploitable gap |
|---|---|---|---|---|
| Dext | Accountants, bookkeepers, SMB receipt/invoice capture | Partner Essentials from $17.70 per client/month annually, 10-client minimum shown [S1] | Mobile/email/drag-drop, categorisation, approvals, duplicate detection, line items, 36+ accounting integrations [S1][S2] | Transparent low-volume pricing; explainable matching and sync status |
| Expensify | Employee expenses, travel, cards, reimbursement | Collect $5/member/month; Control custom, as low as $9/active member with conditions [S3][S4] | SmartScan, approvals, reimbursement, cards, travel, QBO/Xero and ERP integrations [S3] | Focused bookkeeping exception workflow without travel/card complexity |
| Hubdoc | Document capture and centralized storage for Xero/QBO users | Official page shows $12/month after 30-day trial [S8] | Mobile, desktop, email, extracted key fields, unlimited usage/collaborators, Xero/QBO sync [S8][S9] | Better multi-currency/tax review, provenance, and operational reliability |
| Veryfi | Developers embedding global document extraction | Free up to 100 docs; Starter $500 minimum, receipt $0.08 and invoice $0.16 in help-center schedule [S6][S7] | Structured JSON, line items, taxes, 91 currencies, 38 languages, SDKs, fraud add-ons [S5] | Affordable self-host/low-volume product with human review and accounting UX |
| Built-in ledger capture | Existing QBO/Xero customers | Bundled with accounting subscription; exact price not separately validated | Lowest adoption friction and direct transaction context | Cross-ledger portability, open export, better confidence/provenance |

## Validated Demand Signals
1. **Accounting integration is table stakes (HIGH):** every direct packaged competitor emphasizes QBO/Xero or broader ledger connectivity [S1][S3][S8][S9].
2. **Multi-channel capture is table stakes (HIGH):** mobile, email, and desktop upload recur across Dext and Hubdoc [S2][S8][S9].
3. **Exception handling matters more than headline OCR (HIGH):** user complaints center on matching, currency, tax, and missing documents, while vendor pages sell categorisation, approval, duplicate, and line-item workflows [S1][S2][S10][S11].
4. **Low-volume pricing dissatisfaction is real (MEDIUM-HIGH):** one practitioner explicitly objects to paying for unused client bundles; current official pricing spans $12 flat, $5/member, per-client minimums, and a $500 API minimum [S1][S3][S7][S8][S10].
5. **International extraction is a differentiator (MEDIUM):** Veryfi explicitly supports 91 currencies and 38 languages; community evidence shows currency mistakes are costly [S5][S11].
6. **Privacy/self-hosting is a plausible niche (MEDIUM):** wider IDP growth is cloud-led, while regulatory/data-sovereignty pressure is rising. This is directional, not direct willingness-to-pay evidence [S14][S15][S20].
7. **Document chasing and portal retrieval remain unresolved (MEDIUM):** bookkeeping community discussion repeatedly identifies missing receipts, bank statements, payables documents, and portal downloads as operational bottlenecks [S16].

## Market and Pricing Evidence
The broader intelligent document processing market is growing, but published estimates conflict materially. Mordor estimates $3.17B in 2026 and 17.78% CAGR to 2031, while another 2026 report estimates $4B in 2026 and 32.6% CAGR to 2030 [S14][S15]. These figures should not be combined into a TAM. The defensible conclusion is directional: cloud automation, AI extraction, compliance, and finance workflows are expanding.

Observed pricing patterns:
- flat low-cost document capture: Hubdoc official price $12/month [S8];
- per-member expense workflow: Expensify Collect $5/member/month [S3];
- per-client accountant packaging: Dext partner pricing from $17.70/client/month with a displayed 10-client minimum [S1];
- usage/API hybrid: Veryfi free 100 documents, then $500 minimum with transaction rates [S7].

**Recommended validation price, not a claim of proven willingness to pay:** test a self-serve starter at CHF 9-19/month including a document allowance, plus transparent usage overage; test a practice plan only after multi-tenant client switching is productized. No reliable category-specific willingness-to-pay study was found. Do not set final prices until a concierge beta measures activation, documents processed, manual minutes saved, support burden, and conversion.

## Modern UX Expectations
- **Navigation/screens:** dashboard, capture inbox, receipt list/detail, exception review, approvals, export preparation/history, automations, integrations, members/roles, privacy, diagnostics. ReceiptLens largely has these routes.
- **First use:** guided first receipt, clear sample-data option, accounting destination choice, and a visible “first export” milestone. The architecture describes onboarding, but production behavior needs E2E proof.
- **States:** every async ingestion item needs queued/processing/needs-review/ready/failed; every screen needs empty/loading/error/retry/success; disabled actions must state the missing prerequisite.
- **Review interaction:** image and fields side by side on desktop, stacked on mobile; keyboard navigation; source-box focus; unsaved-change protection; optimistic concurrency conflict recovery.
- **Accessibility:** WCAG 2.2 AA target, 44x44 touch targets, visible focus, semantic error summaries, non-color status cues, reduced-motion support, and axe/Playwright gates.
- **Trust/privacy:** original-document hash, source channel, actor/timestamp history, retention controls, redacted diagnostics, encryption/deployment statement, and explicit AI-provider disclosure.
- **Discoverability:** progressive disclosure. Default to the daily queue and export outcome; hide advanced forecasting, diagnostics, and rule details until relevant.
- **Automation/integrations:** email capture, batch upload, saved views, rule preview, duplicate prevention, QBO/Xero, CSV, webhooks/API, idempotency, and replayable export runs.
- **Responsive baseline:** full capture and review on 320px; avoid wide tables as the only mobile representation; camera capture should be a primary mobile action.

## Open-Source and Automation Opportunities
- Keep Tesseract/Pillow as the offline baseline; expose optional model adapters behind a stable `DocumentExtractor` port rather than coupling UI to one provider.
- Adopt OpenTelemetry for request/job/export traces, with receipt content excluded by default.
- Generate and validate OpenAPI clients for the Next.js API layer to prevent endpoint/type drift.
- Use JSON Schema for rule definitions, export mappings, and benchmark manifests; support import/export of safe community profiles.
- Add a deterministic golden-dataset harness with field-level precision/recall, calibration curves, multilingual fixtures, and image-quality strata.
- Use outbox/idempotency primitives already present in `app/platform.py` for email ingestion and export delivery.
- Consider an n8n-compatible webhook/component after stable event schemas; automation should be externalizable without giving it direct database access.
- Track upstream issues for pytesseract/Tesseract language packs, Pillow decoding, Next.js security releases, and provider API version changes. Pin and scan dependencies in CI.

## Differentiation Opportunities
| Priority | Capability | Problem / user | Evidence and competitor gap | Value | Complexity | Main risk | Success criterion |
|---|---|---|---|---|---|---|---|
| P0 | Accounting-safe review and export gate | Bookkeepers need confidence-aware correction, validation, and a deterministic handoff to the ledger. / Small-business bookkeeper / accountant | Reddit users report failed or delayed transaction matching; competitor offerings emphasize review, categorisation, duplicate detection, and ledger sync. Competitors combine capture with accounting sync, but users still report opaque matching and currency/tax problems. | Reduces rework and makes every export auditable. | MEDIUM | Mapping semantics and accounting-provider edge cases | At least 90% of a seeded mixed-quality batch reaches exportable state without leaving the review workspace; blocked exports always show a field-level reason. |
| P0 | Transparent OCR confidence and exception queue | Users do not need another black-box scan; they need to know what requires attention and why. / Bookkeeper processing 20-500 documents/month | Current competitors sell high extraction accuracy, while community feedback still describes incorrect currency, tax, document loss, and matching failures. Few SMB tools make field provenance, confidence, and correction impact central to the workflow. | Turns OCR uncertainty into a manageable work queue. | MEDIUM | Confidence calibration can mislead if not benchmarked | On a labelled benchmark, 95% of fields below the configured confidence threshold are routed to review, and false-clear rate is under 2%. |
| P1 | Inbox-to-books automation with safe rules | Receipts arrive by phone, email, upload, and batch; users want repetitive metadata and routing automated. / Owner-managed SMB and outsourced bookkeeper | Dext and Hubdoc promote multi-channel capture; Expensify promotes automatic submission/approval; ReceiptLens already has inbound email and rule primitives. Rule preview, explicit audit trail, and dry-run rollback can differentiate from opaque automation. | Shortens time from capture to ready-to-export. | MEDIUM | Rule conflicts and unintended bulk changes | For a 100-document test set, a preview reports exact matches before activation, conflicting rules are flagged, and every applied change is reversible. |
| P1 | Practical QuickBooks/Xero connector hardening | Users pay for outcomes in their accounting system, not extracted JSON. / Bookkeepers using QBO or Xero | Official competitor pages consistently position accounting integrations as core; Reddit complaints focus on matching and reconciliation. Open mapping profiles plus deterministic preflight and replayable exports can be more transparent. | Makes ReceiptLens usable in the daily close workflow. | HIGH | OAuth, API versioning, rate limits, and provider certification | A sandbox export of 50 valid receipts creates 50 linked transactions with zero duplicate replays and reconcilable source attachments. |
| P1 | Multi-currency and tax-aware normalization | International SMBs need the original currency, tax treatment, and conversion provenance preserved. / Cross-border freelancer, agency, or bookkeeper | A Hubdoc user reports dollar values being treated as pounds; Veryfi markets 91 currencies and 38 languages. ReceiptLens has exchange-rate and locale primitives but needs a coherent end-to-end UX. | Prevents reconciliation errors and supports European use cases. | MEDIUM | Jurisdiction-specific tax rules | All test receipts preserve source currency; conversions display rate, date, source, and rounding; no export silently substitutes a tenant currency. |
| P2 | Privacy-first deployment and retention controls | Financial documents are sensitive; some buyers prefer self-hosting or explicit deletion. / Privacy-conscious SMB, accountant, or developer | Market sources emphasize cloud automation while data-sovereignty requirements are rising; Veryfi sells secure API infrastructure. Local/self-hosted OCR plus explicit retention and redacted diagnostics is a credible niche. | Builds trust and avoids vendor lock-in. | MEDIUM | Operational burden and incomplete threat modelling | A privacy test proves retention purge removes DB rows and blobs, diagnostic bundles contain no receipt content or secrets, and self-host setup passes a documented smoke test. |
| P2 | Usage-based starter packaging | Low-volume users reject paying for unused client bundles or enterprise API minimums. / Solo operator and small bookkeeping practice | Reddit criticizes unused-client bundles; Veryfi starts with a free tier but jumps to a $500 minimum; Hubdoc is flat-price and Expensify is per member. A low fixed base plus included documents and transparent overage aligns price with value. | Creates an accessible wedge without unlimited-cost risk. | LOW | Unit economics depend on OCR provider and support load | At least 20 qualified beta users complete 50+ scans, 30% indicate willingness to pay within the tested CHF 9-19/month range, and gross processing cost remains below 20% of revenue. |


## User Stories (BDD)
```json
[
  {
    "id": "US-001",
    "epic": "Bookkeepers need confidence-aware correction, validation, and a deterministic handoff to the ledger.",
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
    "epic": "Bookkeepers need confidence-aware correction, validation, and a deterministic handoff to the ledger.",
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
    "epic": "Bookkeepers need confidence-aware correction, validation, and a deterministic handoff to the ledger.",
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
    "epic": "Users do not need another black-box scan; they need to know what requires attention and why.",
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
    "epic": "Users do not need another black-box scan; they need to know what requires attention and why.",
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
    "epic": "Users do not need another black-box scan; they need to know what requires attention and why.",
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
    "epic": "Receipts arrive by phone, email, upload, and batch; users want repetitive metadata and routing automated.",
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
    "epic": "Receipts arrive by phone, email, upload, and batch; users want repetitive metadata and routing automated.",
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
    "epic": "Receipts arrive by phone, email, upload, and batch; users want repetitive metadata and routing automated.",
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

## Priority-Ranked Development Recommendations
1. **P0: Accounting-safe review and export gate.** Complete one coherent happy path: capture → exception review → readiness → export preflight → immutable result. Add provider-neutral contracts before live connectors.
2. **P0: Transparent confidence/provenance queue.** Calibrate thresholds against a labelled benchmark and make field source, low-confidence filters, and conflict recovery first-class.
3. **P1: Safe inbox and automation.** Connect email/batch ingestion to previewable, versioned rules and atomic rollback.
4. **P1: Connector hardening.** Implement one provider sandbox deeply, with OAuth, idempotent posting, attachment linkage, and reconciliation, before adding the second.
5. **P1: Multi-currency/tax normalization.** Preserve original values and show conversion/tax provenance; do not silently coerce tenant currency.
6. **P2: Privacy-first operating mode.** Document local OCR, retention, blob purge, redacted diagnostics, and threat model.
7. **P2: Pricing experiment.** Instrument document volume, time-to-ready, corrections, and exports; run a concierge beta before billing implementation.

## Recommended Scope for the Next Development Pass
**In scope:**
- one consolidated Next.js flow for Review Queue, Receipt Detail, and Export Preparation;
- field-level source boxes, confidence filters, accessible status/error states, and version-conflict draft preservation;
- benchmark fixture format and quality report with false-clear metric;
- deterministic readiness rules and provider-neutral export command with idempotency key;
- email attachment status and retry model;
- rule preview, conflict detection, version history, and atomic rollback;
- targeted tests plus full regression: unit, API contract, integration, Playwright critical flow, axe checks, and restart/persistence tests.

**Out of scope:** travel booking/cards, reimbursement payments, generalized AP, more forecasting features, many new OCR providers, simultaneous QBO and Xero production launches, and final billing. The goal is a dependable exception-to-export product slice, not more surface area.

**Exit metrics:** 90% benchmark documents reach an explicit Ready or explainable Blocked state; false-clear rate below 2% on the labelled set; zero duplicate exports under replay; 100% export failures retain a retryable run record; critical flow works at 320px and passes automated axe checks; all existing and new tests pass.

## Risks, Unknowns, and Assumptions
- Community evidence is directional and self-selected; beta interviews and observed workflows are still required.
- Competitor pricing varies by country, billing term, card usage, and negotiated plan. Recheck before commercial decisions.
- Market reports disagree substantially; no report here justifies a bottom-up revenue forecast.
- OCR quality cannot be inferred from architecture or vendor claims. Build a representative benchmark before marketing accuracy.
- Accounting-provider certification, tax treatment, and regional data-hosting requirements may dominate timeline.
- The codebase contains broad capabilities, but this review did not run live third-party integrations or production-load tests.
- The coexistence of legacy and Next.js frontends is assumed temporary; consolidation needs an explicit migration plan.
- README improvement was requested in the surrounding user message, but the phase's hard scope permits only `research-findings.md`; therefore README is intentionally byte-identical.

## Sources
- **[S1] Dext Pricing Plans.** Dext. https://dext.com/en/partner/pricing (accessed 2026-08-11).
- **[S2] Capture Receipts & Invoices.** Dext. https://dext.com/us/business/product/capture-receipts-and-invoices (accessed 2026-08-11).
- **[S3] Expensify Pricing.** Expensify. https://www.expensify.com/pricing (accessed 2026-08-11).
- **[S4] Understand Expensify Pricing.** Expensify Help. https://help.expensify.com/articles/new-expensify/billing-and-subscriptions/explore-plans-subscriptions-and-pricing/Understand-Expensify-Pricing (accessed 2026-08-11).
- **[S5] Receipts OCR API.** Veryfi. https://www.veryfi.com/receipt-ocr-api/ (accessed 2026-08-11).
- **[S6] Veryfi Pricing.** Veryfi. https://www.veryfi.com/pricing/ (accessed 2026-08-11).
- **[S7] OCR API Plans & Prices.** Veryfi Help Center. https://faq.veryfi.com/en/articles/3743986-what-are-the-plans-prices-for-ocr-api (accessed 2026-08-11).
- **[S8] Hubdoc Pricing.** Hubdoc. https://www.hubdoc.com/pricing (accessed 2026-08-11).
- **[S9] Document & Data Capture Software.** Hubdoc. https://www.hubdoc.com/ (accessed 2026-08-11).
- **[S10] Receipt Capturing Apps?.** Reddit r/Bookkeeping. https://www.reddit.com/r/Bookkeeping/comments/pjzikk/receipt_capturing_apps/ (accessed 2026-08-11).
- **[S11] Hubdoc, Dext, AutoEntry or something else?.** Reddit r/xero. https://www.reddit.com/r/xero/comments/133mukt/hubdoc_dext_autoentry_or_something_else/ (accessed 2026-08-11).
- **[S12] Best Receipt Scanner Apps 2026.** FlowParse. https://flowparse.io/blog/best-receipt-scanner-apps-2026 (accessed 2026-08-11).
- **[S13] Receipt Management Software Comparison 2026.** Receiptor AI. https://receiptor.ai/blog/receipt-management-software-comparison-2026 (accessed 2026-08-11).
- **[S14] Intelligent Document Processing Market.** Mordor Intelligence. https://www.mordorintelligence.com/industry-reports/intelligent-document-processing-market (accessed 2026-08-11).
- **[S15] Intelligent Document Processing Market Report 2026.** Research and Markets / The Business Research Company. https://www.researchandmarkets.com/reports/5806873/intelligent-document-processing-market-report (accessed 2026-08-11).


- **[S16] Opportunity - Understanding bookkeeping pains.** Reddit r/Bookkeeping. https://www.reddit.com/r/Bookkeeping/comments/11hd9zc/opportunity_understanding_bookkeeping_pains/ (accessed 2026-08-11). Directional community evidence that document collection, bank statements, emailed attachments, and portal retrieval are recurring bookkeeping pain points.
- **[S17] Hubdoc 2026 Reviews and Alternatives.** GetApp. https://www.getapp.com/collaboration-software/a/hubdoc/ (accessed 2026-08-11). Aggregated review evidence from 92 reviews reports strong bookkeeping/document-management usage alongside document-recognition, processing, and sync complaints.
- **[S18] receipt-ocr.** GitHub, bhimrazy. https://github.com/bhimrazy/receipt-ocr (accessed 2026-08-11). Active MIT-licensed receipt OCR project combining Tesseract, LLM-assisted extraction, CLI, FastAPI, Docker, tests, and current Python support.
- **[S19] invoice2data 1.0.1.** PyPI. https://pypi.org/project/invoice2data/ (accessed 2026-08-11). Template-based invoice extraction library with pluggable PDF/OCR backends and CSV, JSON, and XML outputs.
- **[S20] Intelligent Document Processing Market 2026-2033.** Grand View Research. https://www.grandviewresearch.com/industry-analysis/intelligent-document-processing-market-report (accessed 2026-08-11). A third market estimate, useful mainly to confirm direction while reinforcing the wide disagreement among published TAM and CAGR figures.

### Project evidence
- `pyproject.toml`; `frontend/package.json`; `README.md`; `CHANGELOG.md`.
- `app/api.py`; `app/product_api.py`; `app/product_service.py`; `app/ocr.py`; `app/vision_ocr.py`; `app/preprocessing.py`.
- `app/advanced_workspace.py`; `app/accounting_workspace.py`; `app/platform.py`; `app/governance.py`; `app/integrations.py`; `app/export.py`; `app/quality.py`.
- `frontend/app/**`; `frontend/components/**`; `frontend/lib/**`; `analysis/architecture-frontend.md`; `tests/**`.
