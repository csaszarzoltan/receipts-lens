# SPEC — D1.1 savings-summary all-zero for tenants that have receipts

**Date:** 2026-09-28 | `GET /api/v1/analytics/savings-summary` returns `total_spent 0.0`, `avg_by_category {}`, `potential_saving 0` although receipts exist (13 receipts, tenant `t1`).

## Root cause (established — reproduce before coding)
`app/savings.py:57` calls `spending_analytics.by_category(...)`; `app/analytics.py:122` (inside it) reads the in-memory `receipt_store` (`app/analytics.py:12` → singleton `app/reports.py:78`, seeded `:106-107`). No `/api/v1` route writes there; the real write path is `app/api.py:1222` → `app/product_service.py:161` `INSERT INTO receipts` (schema `:69`), i.e. SQLite, exposed as `app.product_api.service` (`app/product_api.py:34`). The dashboard hit this same bug and was already fixed: `app/consumer_dashboard.py:61-74` reads the SQLite, its docstring (`:64-66`) warns it is *"NOT the global in-memory `receipt_store` which production never writes to (F1.2 B1)"*, and `:136-150` is the working accumulation. `app/savings.py` was never migrated.

## 1. Approach — (a) reuse the dashboard reader
**Choice (a):** `app/savings.py` calls `_tenant_receipt_payloads` (`app/consumer_dashboard.py:61`) and accumulates from the payloads. **(b) inlining would recreate the exact drift that caused this defect** — two surfaces must read the same store, and a third copy restores the divergence risk.

**Circular import: none — verified by AST scan of `app/*.py` module-level imports.** `savings -> {analytics, recurring}`; `consumer_dashboard -> {budgets, subscriptions_api}`; `product_api -> {…, product_service, subscriptions_api, …}`. Reachability: `consumer_dashboard -> savings` = **False**, `product_api -> savings` = **False**, `product_api -> consumer_dashboard` = **False**. So `savings -> consumer_dashboard` is a DAG edge. Do **not** import `_CATEGORY_LABELS` (`app/consumer_dashboard.py:37-42`) — savings returns raw keys.

**Exact import must be function-local**, mirroring `app/consumer_dashboard.py:68`. A module-level import would transitively pull `product_api` and execute `app/product_api.py:34` `service = ProductService(...)` at import time — and `tests/test_red_savings_p1.py:27` imports `_period_bounds` from `app/savings` for a pure date helper, so it would build a DB as a side effect. Function-local also resolves the object *after* the `:57-58` monkeypatch, which a module-level `from app.product_api import service` would miss.
**Accepted limitation:** the endpoint already receives `service` (`app/api.py:1534` → `app/savings.py:41`) but the reused helper reads `product_api.service`. Consistency with the shipped, verified dashboard fix outweighs DI purity here; do not refactor the helper's signature in this lane.

## 2. Target files
1. **`app/savings.py`** — the only production file changed.
   - **Delete `:13`** `from app.analytics import spending_analytics` (sole consumer is `:57`; else ruff `F401`).
   - **Add** module-level `_category_groups(tenant_id, date_from, date_to) -> dict` (place after `_period_bounds`, i.e. after `:32`): function-local import of `_tenant_receipt_payloads`, then accumulate — date filter `date_from <= str(p.get("date") or "") <= date_to` (as `app/consumer_dashboard.py:139`); `line_items[].category or "Uncategorized"` (`:148`); price `float(item.get("price", item.get("amount", 0)) or 0.0)` (`:149`); empty `line_items` → one `"Uncategorized"` group of `float(p.get("total") or 0.0)` (`:142-146`).
   - Return **exactly** the shape `by_category` returned, so downstream is untouched: `{"total_spent": float, "currency": "USD", "groups": [{"key","total","count","avg","max","min"}, …]}`, `total = round(total,2)`, `avg = round(total/count, 2)`, groups sorted by key (mirrors `app/analytics.py:97-108`).
   - **Replace `:57`** with `cat = _category_groups(tenant_id, date_from, date_to)`.
   - **Leave `:58-64` unchanged** — `{g["key"]: g["avg"] for g in groups}`, `total_spent`, and `potential_saving = round(sum(max(0.0, g["total"] - g["avg"]) …), 2)` work verbatim because the shape is preserved. `:14`, `:66-86` (`top_candidates`), `:88-95` (payload), `:98` untouched.
2. **`tests/test_red_savings_p1.py`** — §4 only. Test file; no assertion removed.
3. **Not touched:** `app/analytics.py`, `app/consumer_dashboard.py`, `app/reports.py`, `app/api.py` (route `:1532-1534` needs no change), `app/product_service.py`.

## 3. Acceptance criteria
Fixture (AC-D1-1/2/3): tenant `sav-fix`, receipts via `service.create_receipt` at `_date_ago(20/10/5)` with items `[("A1",10.0,"A")]`, `[("A2",30.0,"A")]`, `[("B1",5.0,"B")]`, plus `[("Old",999.0,"A")]` at `_date_ago(200)`; header `{"X-Tenant-ID":"sav-fix","X-Role":"admin"}`; `?period=90d`.

- **AC-D1-1** — GIVEN that tenant, WHEN the endpoint returns 200, THEN `total_spent == 45.0` (10+30+5, **not** `1044.0` — the 200-day-old receipt is outside the 90d window) and `avg_by_category == {"A": 20.0, "B": 5.0}` (both keys, non-empty, no `"Uncategorized"`).
- **AC-D1-2** — GIVEN the same fixture, WHEN the body returns, THEN `potential_saving == round(max(0.0, 40.0-20.0) + max(0.0, 5.0-5.0), 2) == 20.0` — the literal arithmetic, **not** merely `> 0`; a single-category group where `total == avg` contributes `0` (clamp preserved).
- **AC-D1-3** — GIVEN `sav-fix` (45.0) and tenant `sav-other` holding `[("Dinner",200.0,"Meals")]` at `_date_ago(3)`, WHEN called with `X-Tenant-ID: sav-fix`, THEN `total_spent == 45.0`, `"Meals" not in avg_by_category`, and no body value equals `200.0`; called with `X-Tenant-ID: sav-other` THEN `total_spent == 200.0` and `"Meals" in avg_by_category`.
- **AC-D1-4** — GIVEN a zero-receipt tenant, WHEN called, THEN the body is `{"period":"90d","potential_saving":0,"total_spent":0,"avg_by_category":{},"currency":"USD","top_candidates":[]}` (200, all six keys); **and** all 5 tests in `tests/test_red_savings_p1.py` pass after the §4 re-seed.

## 4. RISK — the 2 `receipt_store`-seeded tests must be re-seeded (do not weaken the ACs)
`_store_receipt` (`tests/test_red_savings_p1.py:69-85`, `receipt_store.store` at `:85`) seeds the in-memory store, which the endpoint no longer reads → both tests go RED. They pass today only because the endpoint reads the same wrong store they seed.
- **`test_savings_isolates_tenant` (`:100-119`)** — replace `:104-105` with `_seed(service, tenant_a, "OfficeMart", _date_ago(10), "Office")` / `_seed(service, tenant_b, "LunchBox", _date_ago(10), "Meals")`. Keep `:111-119` **unchanged** (`"Office" in avg_by_cat`, `total_spent == 100.0`, `!= 300.0`, `!= 200.0`) — they then prove AC-D1-3. Delete the now-unused `_store_receipt` (`:69-85`) and the `ConfidenceReceipt`/`ReceiptItem` imports (`:22`).
- **`test_savings_clamped_per_category_delta` (`:142-175`)** — `:147-149` seed in-memory and `:152-157` cross-check the endpoint against `spending_analytics.by_category` (`:153`), the same buggy store — a self-fulfilling assertion that must go. Replace `:152-166` with **hard-coded literals**, keep the endpoint assertions `:170-175` unchanged: `avg_by_category == {"Groceries": 20.0, "Utilities": 5.0}` (10+30 → total 40, count 2, avg 20; 5 → total 5, count 1, avg 5), `total_spent == 45.0`, `potential_saving == 20.0`. Drop the now-unused `from app.analytics import spending_analytics` (`:21`). Clamp intent survives via the `Utilities` group where `total == avg → 0`.
- **`_seed` must carry a category.** `_parsed` (`:30-45`) builds `items=[SimpleNamespace(name=merchant, price=total)]` with **no `category`**, and `app/product_service.py:146-152` emits `getattr(i,"category",None)` → `None` → every `_seed`ed receipt lands in `"Uncategorized"`. Add a `category` param to `_parsed` and `_seed` (`:48-52`) and pass it through. Test 005 (`:181-247`, already uses `_seed`) stays untouched — it asserts only `top_candidates`, which come from `RecurringAnalytics` over the service, not the category half.

## 5. Sources
| Claim | file:line |
|---|---|
| Endpoint → `savings_analytics.for_actor(actor, service, period)` | `app/api.py:1532-1534`, `:40` |
| Savings reads the global in-memory store | `app/savings.py:57`, `app/analytics.py:122`, `:12` |
| That singleton + its seed | `app/reports.py:78`, `:106-107` |
| Real write path (SQLite) | `app/api.py:1222`, `app/product_service.py:161`, schema `:69` |
| Payload `line_items[].{name,price,category}` / `date` / `total` | `app/product_service.py:142-152` |
| `product_api.service` singleton (object the fix reads) | `app/product_api.py:34`, bound at `app/api.py:34` |
| Reused reader + F1.2 B1 warning | `app/consumer_dashboard.py:61-74` (docstring `:64-66`) |
| Reference accumulation (date / category / Uncategorized) | `app/consumer_dashboard.py:136-150` |
| Group shape + `round(total/count,2)` preserved | `app/analytics.py:97-108`, `:60-64` |
| Lazy-import precedent | `app/consumer_dashboard.py:68` |
| `max(0.0,…)` clamp, hardcoded `USD` | `app/savings.py:61-64`, `:93`; brief `analysis/research-brief.md:12,15,20` |
| Tests to re-seed / monkeypatch / no-category `_parsed` | `tests/test_red_savings_p1.py:69-85,100-119,142-175,57-58,30-45` |
| Contract to preserve | `docs/plans/savings-summary-spec.md` |

**Validation:** repo-local AST + source reading only — **no live validation**; every claim is anchored to a file:line above. **Out of scope:** `analytics.py`/`reports.py` still back other analytics endpoints; the split store is a separate cleanup lane. This spec fixes only the savings category half.

*Handoff: implementer edits `app/savings.py` (§2) then re-seeds the 2 tests (§4); tester asserts AC-D1-1..4 over HTTP plus the full `tests/test_red_savings_p1.py`.*
