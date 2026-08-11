# Features Done

## Features Done (this pass)
- QuickBooks Online sandbox foundation: tenant-bound single-use OAuth state, AES-GCM credential storage, connection health, and immutable mapping versions.
- Replay-safe provider export: durable run/item state, deterministic receipt-version dedupe, provider links, redacted errors, and reconciliation comparison.
- Source-currency and tax provenance: Decimal conversion, dated manual rates, identity conversion, tax arithmetic validation, and deterministic redacted payload preview.
- QuickBooks onboarding UX: accessible three-step connection, mapping, and verification guidance inside the existing Integrations screen.

## Sources
- research-findings.md items addressed: practical QuickBooks/Xero connector hardening; multi-currency and tax-aware normalization.
- implementation-plan.md requirements addressed: Features A, B, and C provider-domain foundation and primary UX entry point.
- user stories covered: US-010, US-011, US-012, US-013, US-014, US-015, US-016, US-017, US-018.
- CHANGELOG.md section this maps to: `[Unreleased - Provider integration] - 2026-08-11`.
