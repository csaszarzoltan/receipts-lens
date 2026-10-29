# Goal-cycle report (CELVEZERELT)

Date: 2026-10-29
Branch: `feat/goal-cycle-20261029` (from `main` at `1d3d926`)

## Goals

Goals were missing from the README, so they were written into a new `## Goals` section (six measurable goals). See `README.md`.

| # | Goal | Before | After | Evidence |
|---|---|---|---|---|
| 1 | Trustworthy totals: a total is shown only when source-field OCR confidence is high enough | met | met | `app/ocr.py:740-757` (total gated on source-field confidence, unread fields score 0.0); `app/quality.py:52-53` (`requires_review`); `tests/test_bug001_confidence.py`, `tests/test_us_022_ocr_confidence_contract.py` pass in the full run |
| 2 | Production never trusts client `X-Tenant-ID`/`X-Role` headers | met | met | `app/product_api.py:56-78` (`is_production()` → 401 for header-only); `app/auth_api.py:134-163`; `tests/test_production_auth_gate.py`, `tests/test_feature_core.py` pass |
| 3 | Household money insight: daily remaining budget and price-increase alerts | met | met | `app/consumer_dashboard.py:149-175` (`_daily_remaining`); `app/subscription_alerts.py:160` (`detect_price_increase`); `tests/test_us_023_consumer_dashboard_contract.py` passes |
| 4 | User data control: export all data, purge expired, erase the household | partially met | partially met | Before: no erase route; purge/export only (`app/product_api.py:522-531`); export capped at one page of 200 (`app/product_service.py` `portability_export`); owner role blocked by `role != "admin"` checks. After: erase added (`app/product_service.py` `erase_tenant`, `_tenant_tables`; `app/product_api.py:530`); export pages through all receipts; `PRIVACY_ROLES` lets the owner use retention/purge/erase. Export still covers receipts and approvals only (open item) |
| 5 | Accessible, responsive UI (axe WCAG 2.2 AA, no horizontal scroll at 390 px) | partially met | partially met | Specs exist: `frontend/e2e/ux-walk.spec.ts:42-43, 88-94`; `frontend/e2e/ux-plan.spec.ts:76`. Not run in CI. Live check of `/settings/privacy` at 390 and 1280 px: zero axe violations, no horizontal scroll. The wider e2e suite is stale (see open items) |
| 6 | Green gate: ruff, pytest, typecheck pass | partially met (ruff: 8 errors) | met locally; remote CI not yet observed | `ruff check app tests` 8 → 0; pytest 2019 passed, 10 skipped; `npm run typecheck` exit 0; `npm run test:ux` 38/38; `next build` exit 0 |

## Competitor findings (researched 2026-10-29)

Sources are mostly third-party. Official pages are flagged where they were found.

- **Rocket Money** (subscriptions). Price-increase alerts and a "cancel for me" service for Premium members. Source: App Store listing https://apple.co/35oj1nj and the Rocket Money learn article https://www.rocketmoney.com/learn/personal-finance/does-rocket-money-work. Sources disagree on Premium price ($6–12 vs $7–14), so pricing was not used. Takeaway: our price-increase alerts (goal 3) are already in the same class. We did not copy the paid cancellation service, which is out of scope.
- **Monarch Money** (household budgeting). Official help article "Delete a Monarch Account" (https://help.monarch.com/hc/en-us/articles/4412388754708): deletion of the household is permanent and removes all data. The article advises exporting first. A third-party guide claims a 10,000-transaction export cap (unverified). Takeaway: supports an explicit erase flow with a warning to export first (feature 1). Our export cap was removed (feature 2).
- **Shoeboxed** (receipt scanning, accounting export). Vendor site https://www.shoeboxed.com/: OCR followed by human review. The "99.9%" accuracy figure is vendor-sourced and unverified. Independent reviews report extraction errors. Takeaway: flag uncertain values instead of claiming accuracy (goal 1, already in place).
- **Wallet by BudgetBakers** (budgets, shared budgets). Official index https://budgetbakers.com/llms.txt lists shared budgets and expense/receipt pages. Plan tiers for sharing are not confirmed. Takeaway: household sharing is table stakes. We already have members and roles.
- **Spendee** (shared wallets). Shared wallets for couples and families; AI receipt scanner per the Google Play listing. Sources disagree on which plan includes sharing (Capterra, Makerstack, Subscribed.fyi). Takeaway: same as Wallet, table stakes.

## Features implemented

Ranked by goal impact. Each is one logical commit.

1. **Admin/owner full tenant erasure** (goal 4). Schema-driven: every table with a `tenant_id` column (44 tables in the current schema, found at runtime with `PRAGMA table_info`), not a hard-coded list. Requires the body `{"confirmation": "ERASE"}`. Commits: `5c351f0` (backend), `cd04416` (confirmation changed from tenant id to the literal `ERASE`, because users cannot see their tenant id), `3e7a560` (erase-all control on the privacy page, 10 locales).
   - Decision: erasure is not audited, because the audit table is itself erased. Documented in `docs/product-workflows.md`.
2. **Full export** (goal 4). The export was capped at 200 receipts and silently truncated larger accounts. It now pages through all receipts. Commit `265343a`.
3. **Owner can use privacy actions** (goal 4). Magic-link sessions carry role `owner`, but every privacy check required `admin`. A shared `PRIVACY_ROLES = {"admin", "owner"}` now gates retention, purge and erase. Adult members stay denied. Commit `9482a39`. Found by the end-to-end check, not by code reading.
4. **CI frontend gate** (goal 6). The workflow ran only ruff and pytest. A new `frontend` job runs `npm ci`, `npm run typecheck` and `npm run test:ux`. Commit `4d8319f`.
5. **Ruff fixes** (prerequisite for goal 6). 8 errors → 0; behaviour unchanged (`math.isfinite` equals the old NaN/inf check). Commit `ba89bf4`.

Goals and documentation: `de3d5eb` (README Goals), `f1340f3` (product-workflows, CHANGELOG), plus the final commit containing this report.

No new dependencies or frameworks were added.

## Review findings

| # | Finding | Status | Reason |
|---|---|---|---|
| R1 | Household owner gets 403 on retention, purge and erase (`role != "admin"`) | fixed (`9482a39`) | Critical: blocks goal 4 for the only realistic user. Found by the live erase check |
| R2 | Erase confirmation required the tenant id, which the UI cannot show | fixed (`cd04416`) | Usability blocker |
| R3 | Export silently truncated at 200 receipts | fixed (`265343a`) | Data-completeness bug |
| R4 | Ruff: 8 errors, so CI lint was red on `main` | fixed (`ba89bf4`) | CI gate |
| R5 | CI never ran typecheck or UX tests | fixed (`4d8319f`) | Gate gap |
| R6 | Frontend e2e specs seed header auth, but `(app)` routes now require a session (`components/AppShell.tsx`). The privacy page redirects to `/login` with that seeding | partly fixed | Shared helper `frontend/e2e/session.ts` (dev magic-link login). `smoke.spec.ts` now passes 18/18 on session auth. `onboarding.spec.ts` and `consumer-dashboard.spec.ts` use session auth but still fail on copy and flow drift from the current UI (for example `Mi ez?` vs step-1 title `Kezdj egy nyugtával`, and missing dashboard block labels in the dark-mode test). Those need per-test updates |
| R7 | Export covered receipts and approvals only | partly fixed | `tables` section now holds every other tenant table, minus credential and digest columns, binary values and operational state. Receipt images are still not exported (binary; needs a separate download). Goal 4 stays partially met |
| R8 | Export re-runs the full receipt query per 200-item page, so cost is O(n²/200) | open | Acceptable at household scale. Fix with a single paged query if needed |
| R9 | OCR caches (`app/ocr.py`, LRU size 4) hold image bytes in process memory after erase | fixed | `ocr.clear_caches()` runs after a successful erase (`app/product_api.py`). Test: `tests/test_export_completeness.py::test_ocr_caches_are_cleared_on_erase` |
| R10 | `app/platform.py` opens its own SQLite file and is not instantiated by app code | open | Not on the tenant data path, so not erased. Confirm whether it is dead code |
| R11 | `next lint` has no ESLint config, and CI runs no lint for the frontend | open | Needs a decision on the lint setup |
| R12 | Playwright e2e is not run in CI, and it expects servers on 3010/8078 that CI does not start | open | Needs CI job design |

Decisions made during review: erasure is not audited (see feature 1). Adult members cannot erase. The owner can (R1).

## Iterations

- **Code review:** one targeted pass over the changed code and goal-critical modules (privacy, auth, OCR gating). It found R2 and R3 through reading. After the R1 fix, the affected tests and the full suite were re-run. There was no second formal review pass.
- **UI review:** one round. Live checks on `/settings/privacy` at 390 and 1280 px: axe WCAG 2.2 AA zero violations, no horizontal scroll, erase button disabled until `ERASE` is typed, correct position above the mobile tab bar after scrolling. An end-to-end erase click (against a scratch database only) found R1, which was then fixed and re-tested: 200 response, redirect to `/`, session returns 401, zero rows left for the erased tenant.
- **Limit:** 5 rounds per loop. Not reached. Both loops ended with no open critical issue.

## Git

- Branch: `feat/goal-cycle-20261029`
- Commits (oldest first): `de3d5eb`, `ba89bf4`, `5c351f0`, `265343a`, `4d8319f`, `cd04416`, `3e7a560`, `f1340f3`, `9482a39`, plus the commit for this report.
- Push and PR: performed after this report was committed (see the final chat message for the PR link).

## Tests

Commands run from the repository root unless noted. `-q` is set by `pyproject.toml` `addopts`; the full run overrode it with `-o addopts=""`.

| Command | Baseline (start) | Final |
|---|---|---|
| `.venv/bin/ruff check app tests` | exit 1, 8 errors | exit 0, "All checks passed!" |
| `.venv/bin/python -m pytest` | exit 0 (count suppressed by `-q`) | **2019 passed, 10 skipped**, exit 0, 167.62 s |
| `npm run typecheck` (in `frontend/`) | exit 0 | exit 0 |
| `npm run test:ux` (in `frontend/`) | 37 pass, 0 fail | **38 pass, 0 fail** |
| `next build` (isolated copy of `frontend/`, per README instruction) | not run | exit 0, no warnings in log |
| Targeted: `tests/test_tenant_erasure.py` + `tests/test_market_features.py` | n/a | 21 passed |
| Live UI check, `/settings/privacy` at 390 and 1280 px (scratch session) | n/a | axe 0 violations; no horizontal scroll; erase gating correct |
| Erase click end-to-end (scratch DB only) | n/a | 200, redirect to `/`, session 401; 44 tenant tables scanned, 0 rows left for the erased tenant |

The 10 skipped tests were already skipped at baseline. The live checks ran against a locally started API and dev server, with a scratch database (`scratchpad/ui-review.db`). The pre-existing servers on ports 3010 and 8123 were not modified. The real product database was not touched.

## Open items

- Blockers: none that stop completion.
- Remote CI has not run this branch yet. Its frontend job is unverified until the PR runs.
- Open review items: R6 (e2e copy and flow drift in two specs), R8, R10, R11, R12. R7 is partly fixed; receipt images are still missing from the export.
- Next steps, in order: (1) decide the export field list and exclude secrets, closing goal 4; (2) update the Playwright specs to session auth and wire them into CI, closing goal 5; (3) decide the ESLint setup; (4) clear OCR caches on erase.

## Changes to goals

- Added the `## Goals` section to the README (it was missing). Nothing else in the goal wording changed.
- Goal 2 check now names `tests/test_production_auth_gate.py` and `tests/test_feature_core.py`.
- Goal 4 check now names the erasure and export tests and carries an explicit "partially met" note with the reason.
- Goal 5 check says Playwright runs locally and is not yet in CI.

## Second round (after "continue")

Work on open items R6, R7 and R9.

- **R9 (fixed):** `ocr.clear_caches()` runs after a successful erase.
- **R7 (partly fixed):** the export gains a `tables` section with every other tenant table. Credential and digest columns, binary values and operational tables (`sessions`, `auth_tokens`, `oauth_states`, `upload_commands`, `feature_idempotency`) are excluded. Receipt images remain outside the export.
- **R6 (partly fixed):** `frontend/e2e/session.ts` logs in through the dev magic-link flow. `smoke.spec.ts` passes 18/18 on session auth. `onboarding.spec.ts` and `consumer-dashboard.spec.ts` use session auth, but still fail on copy and flow drift from the current UI, which needs per-test updates.
- **Review of the second-round change:** ruff clean. Export tests cover secret exclusion, blob exclusion, operational-table exclusion, and the OCR cache clear. The full suite was re-run. No new critical issue was found.

Tests, second round:

| Command | Result |
|---|---|
| `.venv/bin/ruff check app tests` | exit 0 |
| `.venv/bin/python -m pytest` (full, `-o addopts=""`) | **2023 passed, 10 skipped**, exit 0, 201.52 s |
| `npm run typecheck` | exit 0 |
| `npm run test:ux` | 38/38 |
| `npx playwright test smoke.spec.ts` (scratch config, own dev server on 3011 and API on 8078) | 18/18 passed |
| `npx playwright test onboarding.spec.ts consumer-dashboard.spec.ts` | 5 failed. Auth now works; failures are copy and flow drift (see R6) |

## Deploy and incident (live site)

**Incident (cause found and fixed):** `https://receipts.allthezoo.com` returned 200 for `/` and `/health`, but every `/_next/static` chunk returned 500. The production build in `frontend/.next` had been overwritten by a `next dev` run in the live frontend directory (`receipts-lens-frontend.service` serves that directory with `next start`). The `.next` folder had no `BUILD_ID`. The dev run was mine, from the review session, so the incident is mine too.

**Restore (done):** the production frontend was rebuilt from `origin/main` (`1d3d926`) in a separate worktree with `NEXT_PUBLIC_API_BASE_URL=https://receipts.allthezoo.com/api`, then swapped into the live directory. `receipts-lens-frontend.service` was restarted (BUILD_ID `3M9OZM6mbsjDgfPaoL_-3`). Checks after restore: `/health` 200, `/` 200, `/login` 200, sampled chunks 200, `/api/docs` 404 (production), and a headless load of `/login` showed the email form and no JavaScript errors. The broken `.next` was kept as evidence outside the repo.

**Not changed:** the API service (`receipts-lens-api.service`) is healthy but still runs the code it loaded at 09:31. The production DB was not written to. No migration was run, and this branch adds no schema changes.

**New work is not live.** PR #2 (`feat/goal-cycle-20261029`) is green on CI (`test` and `frontend`, after the packaging and CI fixes below). The merge into `main` was blocked by the permission check ("Merge Without Review"), so it was not merged or bypassed.

**CI fixes in this round:**
- `pyproject.toml`: package discovery is limited to `app*`. Flat-layout discovery found several top-level directories and failed `pip install -e ".[dev]"`. `main`'s CI was already failing for this reason.
- `ci.yml`: the test job installs `tesseract-ocr` and `tesseract-ocr-eng`, and fetches full history.
- `tests/test_price_alert_delivery_proof.py`: probes that need the live product DB skip with a reason when it's absent. Locally they still run against the real DB (4 passed).

**To put the new work live (needs your go-ahead):**
1. Merge PR #2 into `main`, or allow me to merge it.
2. Take a fresh DB backup with `scripts/backup-sqlite.sh`.
3. `git checkout main` in the working tree, so the API loads the new code. Then `sudo systemctl restart receipts-lens-api.service`.
4. Rebuild the frontend in place with the production env, then `sudo systemctl restart receipts-lens-frontend.service`.
5. Verify `/health`, the chunks, and a magic-link login to a test address.

**Open, cosmetic:** the live CSP (Caddy) blocks the Google Fonts stylesheet. The font falls back. Fixing it means editing the Caddy config and reloading, so it is out of scope for this round.

## GUI round: theme switch and full GUI test pass

**Reported:** the light-mode switch "does not work".

**Root cause (reproduced on the live build, then on a local production build):** for a new household, the first-run onboarding was a blocking modal on `/dashboard`. Its backdrop is a button that closes the dialog, and it covers the header, so the theme switch was unreachable. A real mouse click only dismissed the dialog. The second click switched the theme. The theme logic itself was correct on every pre-login page, in both directions, and across reloads.

**Fix (PR #3, branch `fix/gui-theme-onboarding`):**
- The first-run onboarding is an inline, dismissable card above the dashboard content (`components/Onboarding.tsx`, `app/(app)/layout.tsx`). The flow is unchanged.
- Thirteen hint lines used `text-slate-500` with no dark variant, measuring 3.75–4.23:1 on the dark background, below the 4.5:1 AA minimum. They now use `dark:text-slate-400`. Light mode is unchanged.

**New GUI suite:** `frontend/e2e/gui-full.spec.ts`.
- Public pages (landing, login, magic link, invite, Google callback): theme switch in both directions, persistence after reload, keyboard use, axe in both themes, under both OS colour schemes.
- All static app routes (44), in light and dark mode: heading visible, no error overlay, no console errors, no 5xx, no unexpected API 4xx, body theme follows the setting, axe serious/critical clean, no horizontal scroll at 390 px.
- The only allowed API error is `402 /api/v1/tax/deduction` on `/tax`. That is the Pro gate, and the page shows its upgrade prompt.
- First-run card: dismissable and not blocking; the header switch works on the first-run dashboard.
- Mobile navigation at 390 px, and an unknown-id state.

**Results:**
- Local production build (`next build` + `next start`, isolated copy, scratch DB, local API with a generated credential key): **100 passed**, exit 0.
- `npm run typecheck`: exit 0. `npm run test:ux`: 38/38.
- PR #3 CI: `frontend` and `test` both pass.

**Test bugs found and fixed along the way (not app defects):** the theme seed ran on every navigation and undid the stored choice on reload. Measuring `<body>` gave transparent backgrounds, which were read as dark. A stale server on the port served a half-rebuilt `.next`. The mobile nav selector matched the hidden desktop link.

**Deploy status:** PR #3 is **not merged**. The merge was blocked by the permission check ("Merge Without Review"). Live still runs the previous build, so the new-household header problem persists on live until PR #3 is merged. The fix is frontend-only: once merged, rebuild the frontend in an isolated worktree, swap `.next`, and restart `receipts-lens-frontend.service`. The API does not need a restart.
