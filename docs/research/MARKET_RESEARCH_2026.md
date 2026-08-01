# ReceiptLens market research and product plan

Research date: 2026-08-01. Scope: receipt capture, OCR APIs, expense workflows, privacy, and accounting handoff. Quotes are short excerpts or faithful paraphrases of public pages. Search-result claims were treated as directional evidence, not statistically representative market estimates.

## Multi-source findings

### 1. Reddit and community forums

1. Users describe receipt-reward apps as "a lot of work for not much in return," making low-friction capture and immediate value important. Source: Reddit, r/Frugal, *Are any of the receipt scanning apps worth the effort?* https://www.reddit.com/r/Frugal/comments/14nf6a2/
2. Privacy is an explicit tradeoff: a commenter asks what a user's "privacy and personal information is worth." This supports transparent retention and export controls. Source: same r/Frugal thread.
3. Self-hosters request OAuth/security, PostgreSQL support, and working browser access; they also value item-level analytics such as price trends and merchant spend. Source: Reddit, r/selfhosted, *Receipt Manager Webapp with OCR*. https://www.reddit.com/r/selfhosted/comments/mxifni/

### 2. GitHub projects and feature discussions

1. Open Receipt OCR uses separate API, worker, Redis queue, and PostgreSQL-ready persistence, showing demand for durable background processing beyond an in-memory demo. Source: Open Receipt OCR development guide. https://iursevla.github.io/open-receipt-ocr/development.html
2. InvOCR advertises multiple OCR engines, auto-language detection, table extraction, validation, and batch processing. Missing language and provider flexibility are competitive gaps for basic Tesseract-only projects. Source: InvOCR documentation. https://fin-officer.github.io/invocr/
3. The receipt-ocr project exposes CLI, programmatic API, FastAPI service, and multiple LLM providers. Developers expect more than a single HTTP endpoint and want provider choice. Source: bhimrazy/receipt-ocr. https://github.com/bhimrazy/receipt-ocr

### 3. Review platforms and low-rating themes

1. Capterra summarizes SAP Concur complaints as a "slow and outdated interface" with "frequent errors and glitches." Fast search and a focused workflow are marketable differentiators. Source: Capterra Expense Report Software. https://www.capterra.com/expense-report-software/
2. A Ramp reviewer says account details and permissions were confusing during setup. Role-safe defaults and clear errors matter. Source: Capterra Ramp reviews. https://www.capterra.com/p/207081/Ramp/reviews/
3. A reviewer reports incomplete SAP integration requiring manual transfer of work-order and service-order fields. Cost center and project allocation must travel with receipts. Source: Capterra Ramp reviews, Charles E.

### 4. Product Hunt and launch communities

1. The ReceiptSnap maker says intelligent categorization was not supported yet, while a commenter asks how it will move beyond personal use. Business workflows and smarter organization are expected expansion paths. Source: Product Hunt, Receipt Snapper And Scanner. https://www.producthunt.com/products/receipt-snapper-and-scanner
2. Spenno's maker says competing trackers report only "you spent $85" rather than what was purchased, and emphasizes line items, price history, and immediate image deletion. Source: Hunted/Product Hunt summary, Spenno. https://hunted.space/dashboard/spenno
3. Receipt Scanner markets automatic gallery discovery, ten languages, 150+ currencies, cloud cleanup, and reports. Capture automation, localization, and portability are active differentiators. Source: Hunted/Product Hunt summary. https://hunted.space/dashboard/receipt-scanner-track-expense

### 5. Stack Overflow and practitioner questions

1. A highly viewed Tesseract question asks for PDF input while preserving the original layout in a searchable PDF, not plain text only. Source: Stack Overflow, *Tesseract OCR PDF as input*. https://stackoverflow.com/questions/29657237/
2. The same discussion highlights language-pack configuration as a recurring operational concern. Multi-language OCR must be configurable and documented. Source: same Stack Overflow thread.
3. Practitioners recommend OCRmyPDF or a "sandwich" text layer, signaling demand for traceable source documents and export formats rather than lossy extraction. Source: same Stack Overflow thread.

### 6. Competitor capabilities and market comparisons

1. Current comparisons differentiate providers by degraded-receipt accuracy, multi-currency and multi-language support, pricing transparency, and SDK availability. Source: Invoice Data Extraction, *Best Receipt OCR APIs Compared*. https://invoicedataextraction.com/blog/receipt-ocr-api
2. Leading cloud services expose field confidence and bounding regions for audit traceability. Source: Worldmetrics 2026 OCR comparison. https://worldmetrics.org/best/ocr-receipt-scanning-software/
3. Competitor comparisons emphasize review workflows, accounting handoff, flexible exports, and proof-of-concept evaluation on a customer's own receipts. Source: Receipt OCR Software comparison. https://www.receiptocrsoftware.com/compare

## Requirement clusters

Scoring uses 1 to 5 for frequency, intensity, willingness to pay, and feasibility. Opportunity score is their product. RICE uses estimated quarterly reach, impact (0.5/1/2/3), confidence, and person-weeks.

| Theme | Frequency | Intensity | WTP | Feasibility | Product | RICE | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Workflow controls and approvals | 5 | 5 | 5 | 4 | 500 | 45.0 | Build now |
| Search, tags, projects, cost centers | 5 | 4 | 4 | 5 | 400 | 60.0 | Build now |
| Privacy, retention, portability | 4 | 5 | 5 | 5 | 500 | 48.0 | Build now |
| Accounting integrations | 5 | 5 | 5 | 3 | 375 | 30.0 | Existing base, deepen next |
| OCR accuracy and language coverage | 5 | 5 | 4 | 2 | 200 | 18.0 | Roadmap after benchmark |
| Searchable PDF and source traceability | 3 | 4 | 3 | 3 | 108 | 15.0 | Later |

RICE assumptions: 100 active workspaces per quarter. Search/metadata reaches 80%, impact 1.5, confidence 80%, effort 1.6 person-weeks. Approval reaches 50%, impact 3, confidence 75%, effort 2.5. Privacy controls reach 40%, impact 3, confidence 80%, effort 2.0. These are planning assumptions to be replaced by beta data.

Kano interpretation: tenant isolation and retention safety are must-be qualities; search and allocation metadata are performance qualities; configurable approvals and one-click portability can delight small finance teams that currently combine several tools.

## Selected features and specifications

### F1. Receipt search and filters

**Description:** Tenant-scoped search with vendor/date/currency text matching, status, amount, tag filters, and stable pagination.

**User story:** As a finance operator, I want to find a receipt in seconds so that month-end evidence gathering does not require manual browsing.

**Acceptance criteria:**
- Given receipts from two tenants, when tenant A searches, then no tenant B record is returned.
- Given vendor and amount filters, when both are supplied, then only records satisfying both appear.
- Given invalid pagination, when requested, then the API returns 422.

**Technical solution:** `ProductService.search_receipts` reads SQLite rows scoped by tenant, joins metadata, applies deterministic filters, and returns `total/limit/offset`. API: `GET /product/receipts`. MVP uses in-process filtering; full scope moves predicates into indexed SQL and adds cursor pagination.

**Complexity:** M. **Monetization:** Free up to a record cap; advanced saved views in paid tier.

### F2. Tags and allocation metadata

**Description:** Add normalized tags, project, and cost-center fields to each receipt.

**User story:** As an accountant, I want project and cost-center context attached to evidence so that exports require no spreadsheet cleanup.

**Acceptance criteria:**
- Given duplicate tags with different case, when saved, then one normalized logical tag remains.
- Given another tenant's receipt ID, when metadata is updated, then 404 is returned.
- Given a tag filter, when searching, then only tagged receipts are returned.

**Technical solution:** Separate `receipt_metadata` table maintains compatibility with the receipt schema. `PUT /product/receipts/{id}/metadata` validates 20 tags maximum and 40 characters each. Audit events contain IDs, not receipt bodies.

**Complexity:** S. **Monetization:** Core tags free; cost-center/project fields paid team tier.

### F3. Threshold approval workflow

**Description:** Admin-defined currency thresholds automatically determine whether a receipt needs approval, with one immutable decision per request.

**User story:** As a finance lead, I want high-value receipts reviewed so that policy exceptions are visible before export.

**Acceptance criteria:**
- Given a USD 100 policy and USD 125 receipt, when approval is requested, then a pending approval is created.
- Given a USD 50 receipt, when approval is requested, then `not_required` is returned.
- Given a completed decision, when a second decision is attempted, then 409 is returned.
- Given an integrator role, when deciding, then 403 is returned.

**Technical solution:** `approval_policies` and `approvals` tables are tenant-scoped. The highest eligible active threshold is selected. Reviewer/admin roles can decide. Routes: policy creation, receipt approval request, and decision endpoint. Full scope adds multi-step chains and notifications.

**Complexity:** M. **Monetization:** Paid team tier.

### F4. Configurable retention and audited purge

**Description:** Per-tenant retention settings and an admin-only purge remove expired receipts and dependent workflow rows.

**User story:** As a privacy administrator, I want enforceable data retention so that stored receipt data matches company policy.

**Acceptance criteria:**
- Given 30-day retention, when purge runs, then only tenant records older than the cutoff are deleted.
- Given another tenant's old records, when tenant A purges, then tenant B data remains.
- Given retention outside 1 to 3,650 days, when saved, then 422 is returned.

**Technical solution:** `retention_settings` stores policy; purge deletes metadata, approvals, jobs, then receipts in one SQLite transaction and records an audit event. Full scope uses scheduled jobs, legal holds, and dry-run counts.

**Complexity:** M. **Monetization:** Paid compliance add-on; 30-day default remains free.

### F5. Data portability export

**Description:** A versioned, tenant-scoped JSON export returns receipts, metadata, and approval history.

**User story:** As a workspace owner, I want a complete machine-readable export so that I can migrate or satisfy a data access request.

**Acceptance criteria:**
- Given multiple tenants, when exporting tenant A, then only tenant A data appears.
- Given an export, then `schema_version`, tenant ID, timestamp, receipts, and approvals are present.
- Given export creation, then an audit event is written without content payloads.

**Technical solution:** `GET /product/privacy/export` composes existing search results and approval records. Schema version 1 enables compatible evolution. Full scope streams ZIP/JSONL and includes cryptographic manifests.

**Complexity:** S. **Monetization:** Free trust feature; signed archives in compliance add-on.

## Three-month roadmap

### Month 1: discoverability and allocation
- Week 1: confirm schemas, migration safety, API design, and feature flags.
- Week 2: F1 implementation and unit/integration tests.
- Week 3: F2 implementation, isolation/security tests, API documentation.
- Week 4: beta release, usage instrumentation, saved-view fake door.
- Milestone: searchable, allocatable receipts. Dependencies: existing SQLite product service.

### Month 2: controls and approvals
- Week 5: F3 workflow design and policy model.
- Week 6: approval implementation and negative authorization tests.
- Week 7: reviewer UX prototype, email/webhook notification spike.
- Week 8: beta cohort release and willingness-to-pay interviews.
- Milestone: high-value receipts can be governed. Dependency: F1 for queue discovery; F2 for future policy conditions.

### Month 3: privacy and portability
- Week 9: F4 policy and purge implementation, backup/restore rehearsal.
- Week 10: F5 export schema and tenant-isolation test suite.
- Week 11: documentation, migration notes, load testing, security review.
- Week 12: release candidate, telemetry review, go/no-go.
- Milestone: compliance-ready MVP. F5 depends on F2/F3 schemas; F4 must understand all dependent tables.

MVP is the API and service implementation in this release. Full scope adds indexed SQL search, saved views, conditional/multi-step approvals, scheduled purge with legal holds, and streamed signed export archives.

## Validation plan

| Feature | Test | Confirm signal | Reject or revise signal |
|---|---|---|---|
| Search | Fake-door saved views plus beta task test | 50% of weekly users search; median find time under 20 s | Under 15% adoption or no time improvement |
| Metadata | Landing-page message for "export-ready cost centers" | 30% tag or allocate 5+ receipts; 20% fewer export edits | Fewer than 10% repeat use |
| Approvals | Feature flag for 10 finance teams; paid-tier survey | 5 teams configure a policy; 3 accept target price | No policy survives two cycles or zero WTP |
| Retention | Admin interview and dry-run counter | 70% of admins can choose policy unaided; no accidental deletions | Confusion over cutoff or any cross-tenant issue |
| Portability | Export button A/B test | 95% successful exports; trust score improves | High support rate or unusable downstream schema |

Instrumentation should record feature events and latency only, never receipt text or images. A/B tests should randomize by tenant, publish a primary metric before launch, and run long enough to cover month-end behavior.

## Iterative delivery record

1. **Cycle 1, understand:** extracted the archive, mapped 59 Python files and 31 baseline test modules, then ran the full baseline suite: 508 passed and 7 skipped.
2. **Cycle 2, discovery/design:** researched six source types, clustered evidence, scored opportunities, and specified five MVP features.
3. **Cycle 3, search/metadata:** implemented F1/F2 and targeted tests for tenancy, validation, filtering, and normalization.
4. **Cycle 4, approvals:** implemented F3 and tests for threshold selection, roles, idempotent pending requests, and conflict behavior.
5. **Cycle 5, privacy/portability:** implemented F4/F5 and tests for cutoff logic, cross-tenant safety, schema versioning, and routes.
6. **Cycle 6, release hardening:** updated API/product docs, README, changelog and version; ran targeted and full regression, lint, and compilation checks.

## Definition of Done

- [x] At least five source types with three concrete findings each
- [x] Requirements clustered and prioritized with RICE/Kano assumptions
- [x] At least five detailed feature specifications
- [x] Three-month roadmap with dependencies, MVP/full scope, and milestones
- [x] Validation plan with confirm/reject signals
- [x] Five marketable features implemented
- [x] Unit, integration, negative authorization, tenant-isolation, and route tests added
- [x] Existing tests retained and full regression executed
- [x] README, API/product docs, changelog, and version updated
- [x] Syntax compilation and Ruff checks executed
