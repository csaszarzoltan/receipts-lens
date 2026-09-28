# SPEC — GET /api/v1/analytics/savings-summary (P1)

Consumer-pivot cost-saving endpoint: per-category overspend vs category average,
plus top over-spending recurring merchants. Mirrors the existing recurring route
(`@_v1_route("get", "/analytics/recurring")`, app/api.py:1521) and
`RecurringAnalytics` style (app/recurring.py).

## Target Files
1. `app/savings.py` (NEW) — `class SavingsAnalytics` mirroring `RecurringAnalytics`
   (ctor + `for_actor(actor, service, period="90d") -> dict`); module-level
   `savings_analytics = SavingsAnalytics()`.
2. `app/api.py` — one route next to app/api.py:1521:
   `@_v1_route("get", "/analytics/savings-summary", response_model=dict)`,
   `Depends(api_v1_actor)`, calls `savings_analytics.for_actor(actor, service, period)`.
3. `tests/test_red_savings_p1.py` (NEW) — AC-P1-1..5.

## Endpoint contract
`GET /api/v1/analytics/savings-summary?period=90d` → 200:
```json
{"period": "90d", "potential_saving": 0.0, "total_spent": 0.0,
 "avg_by_category": {"Groceries": 12.5}, "currency": "USD",
 "top_candidates": [{"merchant": "...", "potential_saving": 3.0, "delta_pct": 10.0}]}
```
- `avg_by_category`: reuse `SpendingAnalytics.by_category(...).groups`
  (app/analytics.py:110–146) group `avg` values — do NOT re-derive per-item aggregates.
- `total_spent`: sum of per-category actuals in the same window
  (i.e. `SpendingAnalytics.by_category` `total_spent`).
- Per-category potential: `max(0.0, actual_c - avg_c)` — only categories above
  average contribute; `potential_saving = round(sum of clamped per-category
  deltas, 2)` (research brief Q1).
- `currency`: hardcoded `"USD"` (no per-tenant currency in codebase; brief Q4,
  app/analytics.py:141).
- Empty household → 200 with empty lists / 0 values — NOT 404.
- Tenant-scoped via `actor.tenant_id` passed into stores, like the recurring route.

## top_candidates
From `RecurringAnalytics.for_actor(actor, service)` results, filter
`delta_pct > 0`, compute per-merchant
`potential_saving = round(max(0.0, last_amount - avg_amount), 2)`, keep only
`potential_saving > 0`, sort by `potential_saving` DESC, cap 2. Empty list if
none qualify (brief Q3).

## Acceptance criteria (GIVEN/WHEN/THEN, in tests/test_red_savings_p1.py)
- **AC-P1-1** GIVEN no credentials, WHEN GET /api/v1/analytics/savings-summary,
  THEN status 401.
- **AC-P1-2** GIVEN tenant A authed and receipts uploaded under tenant B
  (distinct `tenant_id`), WHEN A requests the summary,
  THEN response reflects only A's data — B's receipts appear in neither
  `avg_by_category` nor `total_spent`.
- **AC-P1-3** GIVEN empty household (no receipts), WHEN authed GET, THEN 200 and
  body == `{"period":"90d","potential_saving":0,"total_spent":0,
  "avg_by_category":{},"top_candidates":[]}` plus `"currency":"USD"`
  (assert the 5 named keys; ignore any incidental keys).
- **AC-P1-4** GIVEN receipts in 2 categories where actual > avg in one and
  actual < avg in the other, THEN `potential_saving == round(max(0, actual_hi -
  avg_hi), 2)` (loser category contributes 0) and `total_spent == round(sum of
  actuals, 2)`; assert values are sourced from `SpendingAnalytics.by_category`
  logic (groups `avg` / `total_spent`), not an independent re-derivation.
- **AC-P1-5** GIVEN 3+ recurring merchants with `delta_pct > 0` over the window
  AND the household empty case, THEN `top_candidates` has ≤ 2 merchants ordered
  by per-merchant `potential_saving` DESC, all entries have
  `potential_saving > 0` and `delta_pct > 0`, and in the empty case the list is
  `[]`; response key `currency == "USD"`.
- Tests assert response dict fields (status code + JSON), never `find(source_string)`
  over distance; no marker-comment hacks needed since ACs probe HTTP output.

Test client: follow existing patterns in tests/test_api.py / tests/test_analytics.py
(app TestClient; no web research needed — everything repo-local)..

## Out of scope
- Per-tenant currency, budget-level tenant tagging (ledger API2-3 follow-up),
  negative-category reporting, any product/store code changes.

## Sources
- `.agent-pipeline/analysis-research-brief.md:4-5` — clamp formula.
- `.agent-pipeline/analysis-research-brief.md:7-8` — reuse `SpendingAnalytics.by_category`.
- `.agent-pipeline/analysis-research-brief.md:10-11` — top_candidates cap/rank.
- `.agent-pipeline/analysis-research-brief.md:13-14` — hardcoded USD.
- `docs/plans/recurring-spend-2026-09-27.md:54,64,103,120` — original spec.
- app/analytics.py:110–146, app/recurring.py:139–159, app/api.py:1521–1528.
