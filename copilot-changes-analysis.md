# Out-of-Band Changes Analysis — receipts-lens

**Analyzed:** 2026-08-11 · **Range:** `6ce403c..HEAD` (last in-system commit → current)
**Source:** external (Copilot) development, 4 feature commits + 1 merge
**Scope:** 51 files, +2859 / −131 lines

## Summary

Between 2026-08-10 17:11 and 2026-08-11 16:01, an external agent (Copilot) shipped a large
"accounting connected workflow" phase on top of the lab-managed receipts-lens codebase:
receipt workflows (secure inbox, automation, export), QuickBooks Online sandbox provider
domain, and provider connection lifecycle APIs. All claims verified locally — tests, build,
and most gates reproduce. The work is **well-engineered but deliberately partial**: the
QuickBooks integration is a sandbox foundation with explicit "not production-certified"
disclaimers and several knowingly-incomplete flows (live OAuth callback, Intuit refresh/revoke,
detail UI screens). No release is claimed; no version bump was made (pyproject still 1.4.0).

## Commit-by-commit breakdown

| Commit | When | Scope |
|---|---|---|
| `3631cd5` | 08-10 17:11 | Workflow: confidence-filtered review, immutable/idempotent CSV exports, OCR benchmark profiles, redacted audit retrieval, versioned automation runs with optimistic rollback, API v2 async regression repair, docs. |
| `7d060e1` | 08-10 17:30 | Secure inbox: durable attachment processing (MIME + magic-byte validation), quarantine, retries, derived email status; deterministic automation conflict resolution, atomic rollback verification, workflow UI routes, env-driven CORS allowlist. |
| `a7370bb` | 08-11 14:48 | Exception-to-export automation verification + lab gates. |
| `6be8a75` | 08-11 15:14 | QuickBooks sandbox domain: encrypted tenant-scoped OAuth state + credentials, immutable mappings, replay-safe provider exports, remote reconciliation, Decimal currency/tax projections, QBO onboarding UX, BDD-derived regression coverage. |
| `f9058c0` | 08-11 16:01 | Connection lifecycle + mapping APIs: tenant-scoped list/detail, admin-only disconnect (credential purge), immutable mapping save/current, OAuth open-redirect protection, RED/GREEN acceptance coverage. |

## Layer analysis

### Services (new modules)

| Module | Lines | Purpose |
|---|---|---|
| `app/credential_store.py` | 18 | AES-GCM authenticated encryption for provider tokens; key from `RECEIPTLENS_CREDENTIAL_KEY` env (32-byte URL-safe Base64). Fail-closed via 503. |
| `app/connection_service.py` | 72 | Tenant-scoped QBO OAuth state (single-use, hashed, 10-min expiry), provider connections, credential rotation, mapping versions (immutable, snapshot-hash validated). |
| `app/accounting_projection.py` | 34 | `projection_rates` + `receipt_accounting_projections` tables; source-currency → reporting-currency projection with stale flag. |
| `app/provider_export_service.py` | 46 | Replay-safe export items with deterministic dedupe keys. |
| `app/export_workflow.py` | 71 | Export preparation → idempotent command execution → run history. |
| `app/automation_service.py` | 93 | Versioned automation runs with optimistic rollback; deterministic conflict resolution. |
| `app/inbox_service.py` | 92 | Secure attachment inbox: MIME + magic-byte type detection, quarantine, retries, derived email status. |
| `app/quality_service.py` | 52 | Confidence-filtered review + persisted OCR benchmark profiles. |
| `app/reconciliation_service.py` | 12 | Remote reconciliation comparison (`verified` / `needs_reconciliation` / `missing_remote`). |
| `app/quickbooks_connector.py` | 16 | Minimal fixed-host QBO API adapter (sandbox/prod hosts, company, references, purchase create/get). |

### API (product_api.py, +212 lines)

- `GET/POST /product/connections`, `POST /product/connections/{id}/test`
- `POST /product/exports` (+ preparations, commands with `Idempotency-Key` header, runs + run detail/artifact)
- `GET/POST /product/automation-rules`, `POST /product/automation-rules/preview`
- `GET/POST /product/export-runs`, `GET /product/export-runs/{run_id}/artifact`
- `GET /product/privacy/export` (portability), `validate_receipt_accounting`, projection refresh
- Credential-store unavailable → HTTP 503 fail-closed (verified in code)

### Frontend

- **Integrations page** (`integrations/page.tsx`): QuickBooks sandbox onboarding panel, real OAuth-start CTA
- **Inbox page** (`inbox/page.tsx`): −99 lines (simplified)
- New routes: `automations/[id]/runs/`, `automations/[id]/runs/[runId]`, `exports/runs/[id]`, `settings/diagnostics/quality`
- `WorkflowState.tsx` shared component
- `npm run build` → **PASS** (verified locally)

### Tests (+~290)

- `test_us_010_012_connection_completion.py`, `test_us_010_018_api_completion.py`, `test_us_010_018_provider_workflow.py`, `test_us_contract_api.py`, `test_completion_scope.py`, `test_development_stories.py`
- Full suite: **1290 passed + 10 skipped = 1300 collected, rc=0** (verified locally)
- Copilot's claimed "1,290 passing" is accurate.

### Config / deps / env

- `pyproject.toml`: added `cryptography>=43` (installed 50.0.0 in venv); added ruff per-file ignore for `app/inbox_service.py`
- **No `.env.example`** exists in repo (env vars documented in README/docs instead)
- Env vars read by code: `RECEIPTLENS_CREDENTIAL_KEY`, `RECEIPTLENS_ALLOWED_ORIGINS`, `RECEIPTLENS_PRODUCT_DB`, `RECEIPTLENS_SMTP_ENABLED`, `LLM_API_KEY`, `LLM_MODEL`

### Docs

- `README.md` (+90): env table, subscription intelligence, provider foundation, integrations
- `CHANGELOG.md` (+67): `[Unreleased - Connected workflow completion] 2026-08-11`
- `docs/api.md` (+165): subscription alerts, accounting export guide refs
- `docs/quickbooks-online.md`, `docs/product-workflows.md`, `docs/subscription-alerts.md` (+~200)
- `FEATURES-DONE.md` (new), `development-report.md` (new — honest about partial state), `implementation-plan.md` (+572), `research-findings.md` (+512, overwritten wholesale)
- Lab gates added as scripts: `bdd-gate.sh`, `doc-sync-check.sh`, `git-push-verify.sh`, `security-gate.sh`, `tdd-gate-v3.sh`, `ui-gate.sh`

## Quality assessment

### Positives

- **Honest verification**: `development-report.md` explicitly says what is NOT done (live callback, refresh/revoke, detail UI, coverage, git push) — no inflated claims.
- **Security-conscious**: AES-GCM at-rest encryption, single-use hashed OAuth state, fixed Intuit hosts, open-redirect rejection, fail-closed 503 on missing key, replay-safe exports, CSV formula neutralization carried over.
- **All tests green locally** (1290 pass), frontend production build passes, TypeScript type-check passes.
- Deterministic idempotency (`Idempotency-Key` header) and immutable mapping versions are well-designed.

### Risks / defects

1. **P1 — `client_id: 'configured'` hardcoded** (`connection_service.py:19`): the OAuth authorization URL is built with a placeholder client_id and a *relative* redirect_uri. No Intuit app credentials are wired. The "Connect" CTA produces a URL that Intuit will reject. Sandbox-only, so not a production leak — but the button is effectively non-functional end-to-end.
2. **P1 — no `.env.example`**: all env vars documented only in README; a fresh clone has zero guidance on `RECEIPTLENS_CREDENTIAL_KEY` etc. (mitigated by docs, but drift-prone).
3. **P2 — live OAuth callback incomplete**: `complete_oauth()` exists and is tested, but no route performs the actual code↔token exchange with Intuit (no client secret, no refresh/revoke). US-010/011/012 explicitly PARTIAL.
4. **P2 — Ruff hygiene**: changed files carry ~57 non-B008 ruff violations (18× I001 import-sort, 16× RUF059 useless expression, 7× FURB157, plus DTZ/TRY/BLE). B008 (93×) is a pre-existing FastAPI pattern. Not blocking (tests green), but inconsistent with repo's ruff baseline claim.
5. **P3 — docs gap**: `docs/api.md` documents subscription/export endpoints but has **no section for the new `/product/connections`, `/product/automation-rules`, `/product/export-runs` endpoints** — the biggest API surface addition is undocumented in the API reference.
6. **P3 — `research-findings.md` / `implementation-plan.md` overwritten wholesale** (+512/+572, prior context replaced) — known Copilot pattern; the BDD gate reads `implementation-plan.md` so structure survived, but prior research history is gone.
7. **P3 — inbox page simplification** (`inbox/page.tsx` −99): verify no functionality was lost vs. the previous secure-inbox UI.

### File inventory (new)

```
FEATURES-DONE.md  development-report.md  implementation-plan.md  research-findings.md
app/{accounting_projection,automation_service,connection_service,credential_store,
     export_workflow,inbox_service,provider_connectors,provider_export_service,
     quality_service,quickbooks_connector,reconciliation_service}.py
docs/quickbooks-online.md
frontend/app/(app)/automations/[id]/runs/{page,[runId]/page}.tsx
frontend/app/(app)/exports/runs/[id]/page.tsx
frontend/app/(app)/settings/diagnostics/quality/page.tsx
frontend/components/WorkflowState.tsx
scripts/{bdd-gate,doc-sync-check,git-push-verify,security-gate,tdd-gate-v3,ui-gate}.sh
tests/{test_completion_scope,test_development_stories,test_us_010_012_connection_completion,
       test_us_010_018_api_completion,test_us_010_018_provider_workflow,test_us_contract_api}.py
```

## Verification record (2026-08-11, local)

| Check | Result |
|---|---|
| `git pull origin main` | up to date, clean tree |
| Full pytest | **1290 passed, 10 skipped (1300), rc=0** |
| Frontend `npm run build` | **PASS** |
| Ruff (changed files) | 57 non-B008 violations (P2) |
| `cryptography` import | 50.0.0 present in venv |
