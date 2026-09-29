# SPEC — `GET /api/v1/analytics/recurring` contract conformance

Source of truth: `docs/plans/recurring-spend-2026-09-27.md:101-106` (+ F2.1 criterion `:47`). Date: 2026-09-29.

## 0. Current behaviour (verified)

`for_actor` hardcodes `limit=200`, takes no period (`app/recurring.py:153-156`); `avg_amount`/
`last_amount` span **all** returned items (`app/recurring.py:124-125`); the route takes
`period: str = "90d"`, discards it and echoes it, and the body has no `currency` key
(`app/api.py:1522-1529`); `grep -rn price_trend --include=*.py .` → 0 hits. The date field is the
payload's ISO `YYYY-MM-DD` `date` (`app/recurring.py:118`, `app/product_service.py:184`);
`list_reviews` already scopes by `actor.tenant_id` (`app/product_service.py:191`), so no tenant work.

## 1. Target files (allowlist — nothing else)

1. `app/recurring.py` — add period parsing/filtering, add `price_trend`.
2. `app/api.py` — pass `period` through, emit `currency`, translate `ValueError` → `422`.
3. `tests/test_red_recurring_contract.py` — NEW, RED first (P0 tests stay in
   `tests/test_red_recurring_p0_contract.py`, untouched).

## 2. `price_trend` rule (literal formula)

Zero new computation — derived from the `delta_pct` already on the group dict
(`app/recurring.py:133`, assigned `:141`):

```
d = float(item["delta_pct"])          # already rounded to 2dp at recurring.py:133
price_trend = "up" if d > 10.0 else "down" if d < -10.0 else "flat"
```

- **Threshold 10.0%** is the only normative figure in the plan: F2.1 (`:47`) requires that a last
  amount above `avg_amount * 1.1` yields `price_trend: up` with `delta_pct >= 10`. A 5% band would
  make `up` fire where `:47` says nothing and would pass `:47`'s trigger at `delta_pct == 5`, i.e.
  the plan's own example criterion falsified.
- **Not** the sibling `> 0.05 / < -0.05 → stable` at `app/subscriptions_api.py:256-261`: that is a
  *ratio* on a median-split between two halves of a month series — a different statistic from this
  `delta_pct`, and no part of the contract table at `:101-106` cites it.
- **Tie is `flat`** — the band is closed, matching `:47`'s strict `>` in the GIVEN clause. Note
  `:47` is internally inconsistent (GIVEN `> avg*1.1`, THEN `delta_pct >= 10`); this spec resolves
  it in favour of the GIVEN trigger, so `delta_pct == 10.0` is `flat`.
- `avg == 0` short-circuits `delta_pct = 0.0` (`app/recurring.py:130-131`) → `flat`; no division.
- `delta_pct` derives from the **unrounded** `avg` (`:133` uses `avg`, not `avg_rounded` from `:126`),
  so a >2-decimal mean yields a `delta_pct` not re-derivable from the printed `avg_amount`. ACs must
  use exact 2-decimal means so the field is hand-checkable.
- The `:106` example (`avg_amount 42.10`, `last_amount 48.30`, `delta_pct 14.7`) is arithmetically
  wrong — those two inputs give `14.73`. Do not assert `:106`'s numbers verbatim; ACs construct their
  own fixtures.
- `no-live-validation`: the vocabulary `{up,down,flat}` is a spec-level decision. `:47` names only
  `up`; nothing in `:101-106` enumerates the other two, and no live consumer parses this key.

## 3. `currency` rule

**Hardcode `"USD"`, exactly like the sibling endpoint.** `app/savings.py:198` (and `:89`) already
returns `"currency": "USD"` for `/analytics/savings-summary`, which the same contract table binds
at `:102`; two endpoints in one table must not disagree. Not derived: the payload does carry
`currency` (`app/product_service.py:184`), but no per-tenant currency setting exists anywhere and a
mixed-currency tenant has no well-defined single label — a majority vote is new aggregation logic,
larger than the contract gap. **Consequence:** a EUR/GBP tenant gets a wrong label rather than a
missing key; a correctness lie on a money field, acceptable only because `:102` requires the key and
no currency model exists (§6).

## 4. `period` rule

New module-level `parse_period_days(period) -> int` in `app/recurring.py`:

```
raw = period.strip().lower()
raw = raw[:-1] if raw.endswith("d") else raw      # "90d" -> "90"
days = int(raw)                                    # ValueError propagates
require 1 <= days <= 3650, else ValueError
```

Window: `date_to = datetime.now(UTC).date()`, `date_from = date_to - timedelta(days=days)` — same
anchoring as `app/savings.py:28-31`; compare the ISO string range `date_from <= date <= date_to` on
`payload["date"]` (`app/recurring.py:118`), mirroring the comparison at `app/savings.py:53`.

- **Filter BEFORE aggregation**, inside `from_reviews`: drop out-of-window entries at bucket-build
  time so `occurrences`, `avg_amount`, `delta_pct` and `price_trend` describe the window only.
  Filtering *after* grouping would leave `avg_amount` all-time and silently wrong — the exact bug
  these numbers exist to avoid.
- **Shorter than data span:** no clamping. Merchants with an in-window receipt appear; those
  without disappear from `items` entirely (never `occurrences: 0`). Clamping a 1-day window up to
  the data span would mislabel the response and hide the emptiness.
- **Unparseable → `422`, not ignore** (`:104`). *Stricter than* `app/savings.py:24-25`, which
  silently falls back to 90 days; that leniency returns a 90-day answer under a `period=7x` label —
  a data-correctness lie. `app/api.py` catches `ValueError` → `HTTPException(422)`, following
  `app/api.py:1504-1505`.
- **Compatibility:** `from_reviews(..., date_from=None, date_to=None)` and `for_actor(..., period=None)`
  default to *no filtering*, so all three existing 2-arg callers are untouched
  (`app/savings.py:171`, `tests/test_red_savings_p1.py:294`, and the route before its change).

## 5. Acceptance criteria (GIVEN / WHEN / THEN)

- **AC-RC-1 — shape.** GIVEN an authenticated tenant with ≥1 receipt, WHEN
  `GET /api/v1/analytics/recurring?period=90d`, THEN `200` and the body has exactly the keys
  `{period, currency, items}`; every element has all of `{merchant, occurrences, frequency,
  avg_amount, last_amount, delta_pct, price_trend}` with `price_trend ∈ {"up","down","flat"}` and
  `currency == "USD"`.
- **AC-RC-2 — `price_trend` boundary, exactly on the tie (pins §2).** Every fixture uses an exact
  2-decimal mean, so nothing the rounding at `app/recurring.py:126` does can perturb the assertion.
  All cases read the JSON body fields directly — no `find()` or substring-distance check.
  - **Clearly above:** GIVEN `100.00, 100.00, 120.00` THEN `avg_amount == 106.67`,
    `delta_pct == 12.5`, `price_trend == "up"`.
  - **Exactly on the tie:** GIVEN `9.50, 9.50, 11.00` THEN `avg_amount == 10.0` and
    `delta_pct == 10.0` exactly, `price_trend == "flat"` (the band is closed, §2).
  - **One cent over the tie:** GIVEN `9.50, 9.50, 11.01` THEN `delta_pct == 10.06` and
    `price_trend == "up"`.
  - **One cent under the tie:** GIVEN `9.50, 9.50, 10.99` THEN `delta_pct == 9.94` and
    `price_trend == "flat"`.
  - **Mirror below the tie:** GIVEN `21.00, 21.00, 18.00` THEN `avg_amount == 20.0` and
    `delta_pct == -10.0` exactly, `price_trend == "flat"`; one cent lower, GIVEN
    `21.00, 21.00, 17.99` THEN `delta_pct == -10.04` and `price_trend == "down"`.
  - **Zero-mean short-circuit:** GIVEN all-zero amounts THEN `delta_pct == 0.0` and
    `price_trend == "flat"` (no division, `app/recurring.py:130-131`).

  **The numbers above were computed against the real formula at
  `app/recurring.py:133`, `(round(last,2) - avg_unrounded) / avg_unrounded * 100`.
  They are NOT the intuitive `(last - avg)/avg` of the last element alone — an earlier
  draft of this AC used wrong values and the fixtures were recomputed.**
- **AC-RC-3 — period CHANGES the result, not just the echo.** GIVEN one Tesco receipt dated
  `datetime.now(UTC).date()` (computed at test time, never hardcoded) and one dated 45 days before
  it, WHEN called `?period=30d`, THEN `occurrences == 1`; WHEN called `?period=90d`, THEN
  `occurrences == 2`. Asserting only `body["period"] == "90d"` is explicitly insufficient.
- **AC-RC-4 — invalid period → 422.** GIVEN valid auth, WHEN `?period=7x`, `0d`, `-5d` or `abc`,
  THEN `422` and no `items` key.
- **AC-RC-5 — auth + empty state keep the new keys.** GIVEN no credentials, WHEN called, THEN
  `401`. GIVEN an authenticated tenant with zero receipts, WHEN called, THEN `200` with
  `items == []` **and** `currency == "USD"` present (not `404`, per `:103`).
- **AC-RC-6 — no regression.** For in-window receipts, `occurrences`/`avg_amount`/`delta_pct` at the
  default `period=90d` match pre-change values; `delta_pct == 0.0` (all-zero amounts) stays `flat`;
  and `GET /api/v1/analytics/savings-summary` still returns `200` — it consumes `RecurringAnalytics`
  at `app/savings.py:171` and now receives items with an extra `price_trend` key it ignores, since
  it reads `delta_pct`/`last_amount`/`avg_amount` via `.get()` at `app/savings.py:174-187`.

## 6. NOT IN SCOPE

`app/savings.py` (no edit, not even to share the parser — its lenient `_period_bounds`,
`app/savings.py:16-31`, and the `90d` hardcode at `:142` stay); per-tenant currency model and
inference from `payload["currency"]` (§3); `?frequency=weekly|monthly|all` (`:101`, separate gap);
`delta_pct` rounding semantics (§2) and the `limit=200` ceiling at `app/recurring.py:155`;
`app/recurring_cache` or any new table/index (`:87` defers to P1/P2); frontend, onboarding CTA,
push/email, Stripe gate (`:115`, `:121`).
