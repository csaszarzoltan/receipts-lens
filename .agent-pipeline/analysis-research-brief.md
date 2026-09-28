# Analysis brief — savings-summary (P1)

## Q1 — potential_saving clamping
No clamp anywhere for underspend: `app/analytics.py` clamps only budget remaining (`max(0.0, total_budgeted - total_spent)` at app/analytics.py:398); no such clamp exists for the spec formula `actual - avg_by_category` (spec docs/plans/recurring-spend-2026-09-27.md:54, :120). Recommended formula:
`potential_saving = max(0.0, round(sum(actual_by_category) - sum(avg_by_category), 2))` — clamp negative totals at 0; but report per-category savings (`max(0.0, actual_c - avg_c)`) only for categories where spending is **above** average, and keep a negative per-category value out of `top_candidates` (only `potential_saving > 0` entries). Empty household → `0` (spec line 54, 103).

## Q2 — existing categorical aggregation
`SpendingAnalytics.by_category` (app/analytics.py:110–146), which builds `group_totals` via `_accumulate_item`/`_accumulate_receipt` (app/analytics.py:55, :71) and per-group averages in `_build_groups` (app/analytics.py:102). Reuse `by_category(...).groups` for `avg_by_category`.

## Q3 — top_candidates
Spec (docs/plans/recurring-spend-2026-09-27.md:64): "top_candidates max 2 elem, merchant szerint rendezve potential_saving csökkenő sorrendben" — i.e. cap 2, sorted by `potential_saving` **descending** (spec text's "merchant szerint rendezve" reads as the tiebreak). Note: RecurringAnalytics output is sorted by merchant asc (app/recurring.py:150) and `delta_pct > 0` merchants are the rising-price candidates; filter delta_pct > 0, rank by computed per-merchant potential_saving desc, take 2.

## Q4 — currency
Hardcoded `"USD"` today: app/analytics.py:141, :189, :232, :278, :407. No per-tenant currency setting in the codebase; spec also pins `currency: USD` (recurring-spend-2026-09-27.md:54).
