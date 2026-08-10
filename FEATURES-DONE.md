# Features Done

## Features Done (this pass)
- Inbound attachment processing: safe byte persistence, filename normalization, MIME and magic-byte validation, quarantine, independent state, derived email state, tenant isolation, and attachment retry.
- Automation conflict handling: deterministic priority and tie-breaking, field-level conflict evidence, winner display contract, and atomic rollback failure coverage.
- Workflow UI routes: export run detail, OCR quality publication, automation preview, automation run history, rollback preview, and detailed Inbox attachment states.
- Security hardening: environment-driven CORS allowlist plus cross-tenant, upload-boundary, filename, audit, and CSV formula-injection regression coverage.

## Sources
- research-findings.md items addressed: multi-channel capture, transparent automation, accounting-safe operations, trust and security indicators.
- implementation-plan.md requirements addressed: US-007 attachment workflow, US-008 conflict preview, US-009 atomic rollback, planned workflow screens, CORS and tenant isolation.
- user stories covered: US-001, US-002, US-003, US-004, US-005, US-006, US-007, US-008, US-009.
- CHANGELOG.md section this maps to: 1.6.0.
