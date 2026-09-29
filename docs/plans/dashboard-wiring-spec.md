# SPEC — Wire Savings + Recurring onto the Consumer Dashboard

**Date:** 2026-09-29 | **Status:** ready for implementer | **Brief:** `.agent-pipeline/analysis/research-brief.md` (2026-09-27) + `.agent-pipeline/next-moves-brief.md` §4.1
**Baseline:** 24/24 green on `tests/test_red_recurring_p0_contract.py`, `tests/test_red_savings_p1.py`, `tests/test_us_023_consumer_dashboard_contract.py` (re-verified 2026-09-29).

## Target files (allowlist — nothing else)
| File | Change |
|---|---|
| `app/consumer_dashboard.py` | new `_savings_block()` helper; new `"savings"` key at `:317-326`; new `period` kwarg on `build_consumer_dashboard` (`:314`) |
| `app/api.py` | `period: str = "90d"` query param + validation + pass-through on `consumer_dashboard` (`:316-328`) |

No new files. No schema/migration. No writes.

## Verified surface
- `build_consumer_dashboard(tenant_id, today=None)` → 8 keys (`app/consumer_dashboard.py:314`, `:317-326`); sole caller `app/api.py:328`.
- `_price_alerts` (`app/consumer_dashboard.py:180-205`) is **not stale** — it reads `accounting.recurring(tenant)` via `_build_subscriptions` (`app/subscriptions_api.py:106-108`), i.e. *subscription* price-increase, a different source from the receipt-derived engines.
- `_TenantActor` (`app/consumer_dashboard.py:284-289`, `role="admin"`) already feeds `list_members` (`:250`) and `search_receipts` (`:296`).
- Savings reads via `_tenant_receipt_payloads(tenant_id)` (`app/savings.py:45-47`, `:107-114` → `app/consumer_dashboard.py:61-74`) and `service.list_reviews(actor)` (`WHERE tenant_id=?`, `app/product_service.py:191`).

## Decisions

**1. Key shape — option (b), one new top-level `savings` key.**
The premise "adding keys breaks a consumer keyed on the 8" holds only for a strict `set(keys) == {...}` assertion (e.g. `tests/test_us_023_consumer_dashboard_contract.py:44` "wire keys — the contract the UI renders from"); dict consumers ignore extras. (a) and (b) both break that equally, so shape decides. One key = one new wire block = the savings-summary payload plus recurring, so parity (AC-D2-2) is a field-for-field check rather than a reshuffle of two unrelated blocks.
**Exact resulting key set (9):** `generated_at, tenant, daily_remaining, monthly_by_category, price_alerts, cancellable_subscriptions, household, recent_receipts, savings`.
`savings` = the 6 keys of `app/savings.py:193-200` (`period, potential_saving, total_spent, avg_by_category, currency, top_candidates`) **plus** `savings_candidates: [...]` (the list from `RecurringAnalytics.for_actor`, `app/recurring.py:214-227`). Option (c) is rejected: `price_alerts` is subscription-sourced and already correct; overwriting it would destroy working F1.2 data.

**2. Actor — reuse `_TenantActor`.** Security, stated honestly: `role="admin"` grants **nothing extra today**, because every call this path makes is tenant-scoped with no role gate — `list_reviews` (`app/product_service.py:191`), `list_members` (`:249-252`), `search_receipts` (`:388-400`) inspect only `actor.tenant_id`; the `can_write`/role checks sit on mutate paths (`:207-208`, `:296`, `:461`). It is however a *false identity*: the route resolves a real role and throws it away (`_resolve_tenant_from_auth` returns only `identity["tenant_id"]`, `app/api.py:288-310`), so a `reviewer` is served as an `admin`. Harmless now, a latent trap if any admin-gated read is ever added to this path — logged as follow-up F1, not done here (it would touch the shared resolver used at `:766`).

**3. Period — add `period: str = "90d"` query param; invalid → `422`.** Validate explicitly with `RecurringAnalytics.parse_period_days` (`app/recurring.py:30-44`) *before* either engine and raise `HTTPException(422)`, matching `/analytics/recurring` (`app/api.py:1531-1532`). Do **not** rely on savings' own parser: `app/savings.py:16-31` silently falls back to 90 days, so `?period=7x` would return 90-day data under a `7x` label — precisely the hazard `app/recurring.py:32-37` documents. Today the dashboard ignores unknown query params, so this is additive, not a regression.

**4. Pass the SAME period to both.** Dashboard's own `RecurringAnalytics().for_actor(actor, service, period)` gets it, matching `app/api.py:1528`. **Known inconsistency, not fixed here:** `app/savings.py:171` calls `for_actor(actor, service)` with no period, so savings' *internal* `top_candidates` is period-independent even when `potential_saving` is not. Surfacing that as follow-up F2.

**Implementation notes.** Import `savings_analytics` **function-locally** inside `_savings_block` and take `service` from `from app.product_api import service as product_service` — same pattern as `:238`/`:294`, and the reason `app/savings.py:39-44` gives (avoiding ProductService singleton side effects + the `savings ↔ consumer_dashboard` import cycle). Signature becomes `build_consumer_dashboard(tenant_id, today=None, period: str = "90d")` — defaulted, so `app/api.py:328` and any direct call stay valid. Pass `service` in from the route (`app/api.py:34` already imports it).

## AC-D2 (GIVEN/WHEN/THEN)
- **AC-D2-1 (key set)** GIVEN a tenant with receipts, budgets and subscriptions seeded via `product_service.create_receipt` WHEN `GET /api/v1/consumer/dashboard` (valid `Authorization: Bearer`) THEN `200` and `set(body.keys()) == {generated_at, tenant, daily_remaining, monthly_by_category, price_alerts, cancellable_subscriptions, household, recent_receipts, savings}`, and `set(body["savings"].keys()) == {period, potential_saving, total_spent, avg_by_category, currency, top_candidates, savings_candidates}`.
- **AC-D2-2 (parity / anti-drift)** GIVEN the same tenant and the same `period` in one test run WHEN both `GET /api/v1/consumer/dashboard?period=P` and `GET /api/v1/analytics/savings-summary?period=P` are called THEN for each of the 6 savings keys `body["savings"][k] == summary[k]` **and** `body["savings"]["period"] == P == summary["period"]`. (A dedicated drift test; `body["savings"] != summary` is expected only by the extra `savings_candidates` key — assert per-key, never whole-dict equality.)
- **AC-D2-3 — the period actually changes the result. With the straddling fixture
  (4 receipts at 60/50/40/30 days ago: 10.0, 30.0, 40.0, 40.0) the dashboard
  returns `potential_saving == 20.0` with `period == "90d"`, and
  `potential_saving == 0.0` with `period == "30d"`, because the 60/50-day-ago
  records fall outside a 30d window.
  **CORRECTED BY REVIEW CYCLE 1.** The original AC-D2-3 read "the
  `savings.recurring` merchant sets differ between 90d and 30d". That is
  VACUOUS: the fixture seeds four distinct one-off merchants that no recurring
  detector flags, so `savings_candidates` is `[]` at both periods and an
  empty-vs-empty comparison is always true. The windowed `potential_saving`
  pair above is the non-vacuous reading and is what TEST-DASHWIRE-003 asserts.

- **AC-D2-4 (invalid period)** GIVEN a valid session WHEN `GET /api/v1/consumer/dashboard?period=7x` (or `0d`, or `99999d`) THEN `422` with no partial payload body; and the same input on `/api/v1/analytics/recurring` yields `422` — i.e. no surface can return a 90-day answer under a non-90d label.
- **AC-D2-5 (isolation + empty state)** GIVEN tenants A (seeded) and B (empty), plus the absence of any `Authorization` header WHEN both are queried THEN A's `savings` contains no merchant string present only in B, B's `savings` equals `{period: P, potential_saving: 0.0, total_spent: 0.0, avg_by_category: {}, currency: "USD", top_candidates: [], savings_candidates: []}`, and the unauthenticated request is `401` — the new block must not weaken the existing auth gate (`app/api.py:288-310`).

## NOT IN SCOPE
1. Frontend/UI rendering, HTML templates, i18n labels.
2. `app/savings.py:171` — threading `period` into savings' internal `RecurringAnalytics` call (follow-up F2; changes an existing tested engine).
3. Replacing `_resolve_tenant_from_auth` with a role-returning variant / threading a real `Actor` (follow-up F1; shared with `app/api.py:766`).
4. Any write path, notification delivery (F2.5), Stripe, `price_trend`/`currency` conformance work, or the `potential_saving` self-cancelling formula defect (`next-moves-brief.md` §5c).
5. Caching, pagination or cap changes to the `savings_candidates` items; `limit=200` stays (`app/recurring.py:222`).

**Handoff:** implementer edits only `app/consumer_dashboard.py` + `app/api.py` per Decisions 1–4; tester writes AC-D2-1..5, with AC-D2-2 as the required anti-drift gate.
