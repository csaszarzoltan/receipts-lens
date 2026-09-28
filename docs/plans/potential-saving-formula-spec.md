# SPEC — potential_saving: late-half mean minus early-half mean

**Date:** 2026-09-28 | **Scope:** `GET /api/v1/analytics/savings-summary` (`period` any) | **Formula: DECIDED, not negotiable.**

## 1. Formula (pseudo-code)

```
date_from, date_to   = _period_bounds(period)            # app/savings.py:16-31
span                 = (date_to - date_from).days
is_early(d)          = 2 * (d - date_from).days < span   # d < midpoint; exact, no float
midpoint             = date_from + span/2                 # days >= midpoint are LATE
for payload in _tenant_receipt_payloads(tenant_id):       # app/consumer_dashboard.py:61
    if not (date_from <= str(p["date"]) <= date_to): continue      # :53 verbatim
    items  = p["line_items"] or []                         # app/savings.py:55
    if not items:                                          # :56-65 verbatim shape
        amt, cats = f(p["total"]), ["Uncategorized"]
    else:
        amt, cats = f(p["total"]), [str(i["category"] or "Uncategorized") for i in items]
    # PER-LINE amount per category, exactly as _category_groups does at
    # app/savings.py:66-68 — NOT the whole receipt total for every
    # category it touches. A 40.00 two-line receipt (20 food + 20 fuel)
    # contributes 20.0 to "Food" and 20.0 to "Fuel", never 40 to both.
    side[c][is_early(d)].append(line_amount(c) if line_amount(c) is not None else amt)
potential_saving = round(sum(
    max(0.0, mean(late[c]) - mean(early[c]))
    for c in cats if len(early[c]) >= 2 and len(late[c]) >= 2), 2)
# GUARD: a category needs BOTH halves at count >= 2, else it contributes 0.0
# CLAMP : max(0.0, ...) is per-category, before the sum — brief FC1/Risks
# empty  -> no categories -> 0 ; single receipt -> one half empty -> 0.0
```

## 2. Target file + line anchors — `app/savings.py` (ONLY file)

| Anchor | Action |
|---|---|
| `app/savings.py:120-123` | **REPLACE** `potential_saving = round(sum(max(0.0, g["total"] - g["avg"])), 2)` — call the new helper |
| after `app/savings.py:91` | **ADD** module-level `_half_means(tenant_id, date_from, date_to) -> dict` (per §1; function-local `_tenant_receipt_payloads` import, same as `:45`) |
| `app/savings.py:34-91` `_category_groups` | **UNCHANGED** — still feeds `avg_by_category` / `total_spent` |
| `app/savings.py:118,151` `avg_by_category` | **UNCHANGED** |
| `app/savings.py:125-145` `top_candidates`, `:147-154` payload, `:157` | **UNCHANGED** |
| tests | **UNTOUCHED** — see §5, they are the acceptance suite |

## 3. SEMANTICS of `avg_by_category` — DECISION

`avg_by_category` **KEEPS its current meaning: mean receipt amount over the WHOLE window** (both halves pooled, as `g["avg"]` at `app/savings.py:81,118`). It does **NOT** become the late-half mean. No new response field is added — the body stays exactly 6 keys, because `tests/test_red_savings_store_fix.py:217-224` asserts full-dict equality on the empty payload; a 7th key turns TEST-SAVD1-004 RED for no consumer value. The early/late means are internal to the formula and are NOT exposed.

## 4. Acceptance criteria (literals = my verified 90d run)

- **AC-PS-1** GIVEN 12 receipts @ 20.0, WHEN `?period=90d`, THEN `potential_saving == 0.0` (6 early / 6 late, equal means).
- **AC-PS-2** GIVEN early half @ 20.0 (>=2) and late half @ 40.0 (>=2), WHEN called, THEN `potential_saving == 20.0` — literal, not `> 0`.
- **AC-PS-3** GIVEN ONE receipt @ 250.0, WHEN called, THEN `potential_saving == 0.0` — the count>=2 guard, not `125.0`.
- **AC-PS-4** GIVEN an empty tenant, WHEN called, THEN `potential_saving == 0` and the 6-key body at `tests/test_red_savings_store_fix.py:217-224` is unchanged.
- **AC-PS-5** GIVEN early @ 40.0 (>=2) and late @ 20.0 (>=2), WHEN called, THEN `potential_saving == 0.0` — the `max(0.0, …)` clamp, never negative.

## 5. COMPATIBILITY — tests that go RED under the new formula

`midpoint = today-45` for any `period=90d`; all `_date_ago(5|10|20)` fixtures land in the LATE half, so every half has `early count == 0` and trips the guard.

| Test (file:line) | Fixture | Old | **NEW** |
|---|---|---|---|
| `tests/test_red_savings_store_fix.py:181` `TEST-SAVD1-002` | A:{10@20d,30@10d} B:{5@5d}; early=0,late≥1 both cats | `20.0` | **`0.0`** (A early 0, B early 0 → both guard-trip) |
| `tests/test_red_savings_p1.py:146` `TEST-SAVINGS-P1-004` | Groceries:{10@20d,30@10d} Utilities:{5@5d}; early=0 | `20.0` | **`0.0`** (both cats guard-trip) |

**STAY GREEN (verified line by line):** `test_red_savings_store_fix.py:151` (`:160-163` assert only `total_spent 45.0` + `avg_by_category {"A":20.0,"B":5.0}` — both window-scoped, §3), `:188` (`:196-204` only `total_spent`/`avg_by_category`/leak scan), `:210` (empty, AC-PS-4); `test_red_savings_p1.py:72` (401), `:81` (`:92-100` only `currency`/`avg_by_category`/`total_spent`), `:106` (empty), `:152` (`:176-218` assert only `top_candidates`, derived from `RecurringAnalytics` at `app/savings.py:125-145` — untouched). **`assert body["potential_saving"] > 0`** at `test_red_savings_store_fix.py:182` also fails and is removed with the edit at `:181`.

**ACCEPTED PRODUCT RISK — short-window sparsity (raised by reviewer, not validated).**
The 45-day midpoint rule requires **≥2 line records per half**. On
`period=30d` that means ≥2 records in the first 15 days AND ≥2 in the last
15. For low-frequency categories (Utilities, Insurance) a household will
return 0.0 almost always, so the metric reads "no savings" on sparse data
rather than "insufficient data". This is accepted for the P1 lane, but a
future lane must either (a) return a `sample_size` / `insufficient_data`
flag, or (b) require a longer minimum window. **No live validation** — the
consequence is reasoned from the guard, not measured on real households.

## 6. Sources

| Claim | file:line |
|---|---|
| `max(0.0,…)` clamp before sum | brief `analysis/research-brief.md:12,20,25`; `app/budgets.py:234`; `app/analytics.py:398` |
| Payload read path / date+category fallback | `app/savings.py:45,53,67-68`; `app/consumer_dashboard.py:61,136-150` |
| 6-key payload is asserted verbatim | `tests/test_red_savings_store_fix.py:217-224` |
| `avg_by_category` = window `total/count` | `app/savings.py:81,118` |
| Old formula replaced | `app/savings.py:120-123` |
| `top_candidates` source (untouched) | `app/savings.py:125-145`; `app/recurring.py:70-151` |

**Validation:** literals are my own 90d run + arithmetic from each fixture; repo-local sources only. **The count>=2 guard and the half-split are decided by the request, NOT validated by the brief** — the brief's FC1 describes the superseded merchant-level formula (`research-brief.md:12`). Per pipeline rules that part is **`no-live-validation`**; carry the clamp precedent only.

*Handoff: implementer edits `app/savings.py:120-123` + adds `_half_means` after `:91` per §1; tester runs AC-PS-1..5 (new unit tests) + the two RED expectations in §5 flipped to `0.0`.*
