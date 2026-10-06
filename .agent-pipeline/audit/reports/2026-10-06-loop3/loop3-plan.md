# SPEC: TTL + expiry-on-conflict for the `price_alert_sent` claim

- Status: PLAN (no code changed by this spec)
- Date: 2026-10-06
- Item: accepted from ASK explore, verified by REFUTE (loop3)
- Previous work: `77741a8` / `f74abf9` (claim-before-send + release-on-failure, APPROVED);
  this spec covers only what `product_service.py:378` deferred ("belong to a spec of their own").
- Research grounding: primary snippets + links are quoted in §0 below, not carried by reference.

## §0 Research grounding (verbatim, re-measured 2026-10-06)

1. The hazard, stated in shipped code (`app/product_service.py:314-335`):
   > "A claim that is never followed by a successful send is PERMANENT.
   > `notified_at` is written here and read nowhere in `app/` — there
   > is no TTL, no expiry and no reaper — so a process killed between the
   > claim and the send blocks that (tenant, merchant, amount, period)
   > alert forever."
2. The deferral (`app/product_service.py:378-382`):
   > "Deliberately NOT solved here: a TTL on the claim, a reaper that ages
   > out unfulfilled claims, or recording which run holds the claim and
   > checking that it is still alive. Those are behaviour changes to the
   > send path and belong to a spec of their own."
3. The consumer (`app/subscription_alerts.py:948`): `daily_scheduler` calls
   `_claim_price_alert_sent(...)` and on `False` increments
   `price_alerts_suppressed` and `continue`s — silently, by design.
4. Timestamp format (`app/product_service.py:152-153`):
   `def _now() -> str: return datetime.now(UTC).isoformat()` — ISO-8601,
   so an age comparison can parse it without a migration.
5. Traceability baseline: `python3 scripts/traceability_runner.py` reports
   `485 (24.4%)` markers with all three markers (re-measured 2026-10-06).
6. `analysis/next-moves.md` (§"Open item, planned but NOT built") records this
   item as planned-but-unbuilt and notes the planner dispatch was never run —
   this spec is that dispatch's output.

## 1. Target Files allowlist

| Path | Why in scope |
|---|---|
| `app/product_service.py` (`claim_price_alert_sent`, ~:341; read path ~:295) | The claim INSERT and the existence-check SELECT live here; expiry-on-conflict is an age check on `notified_at` at exactly these two points. |
| `app/subscription_alerts.py` (`_claim_price_alert_sent` :693, `daily_scheduler` claim site :948) | The live send path that must observe expiry; the consumer-line acceptance test drives :948. |
| `tests/test_price_alert_ttl.py` (NEW) | The gate for this behavior; no existing file covers expiry. |
| `scripts/traceability_runner.py` (RUN only, never edit) | Supplies the ID numbers for the new tests. |

Any file not in this table is OUT of scope for the BUILD. In particular:
`PROVENANCE.md` and `veritas_audit.jsonl` are append-only / labelled foreign
artifacts — DO NOT touch them.

## 2. The single behavior to change (observable)

**A claim older than the TTL no longer suppresses the alert: the next
`daily_scheduler` run re-detects the hike and re-sends it, instead of counting
`price_alerts_suppressed += 1` and continuing.**

What this is NOT: "notified_at is read somewhere" — a SELECT that parses the
timestamp but never changes the suppress-vs-send outcome satisfies nothing.

## 3. Acceptance criteria (all RUNNABLE — paste as-is)

Assume `<repo>` = `/home/zoltan/receipts-lens`.

- **AC1 — producer (expiry visible at the store boundary):**
  ```bash
  cd <repo> && pytest tests/test_price_alert_ttl.py -q
  ```
  Must include at least: (a) claim → backdate `notified_at` past the TTL
  (via SQL `UPDATE`, simulating a stranded claim) → `claim_price_alert_sent`
  for the same key returns `True` again; (b) a fresh claim still returns
  `False` on immediate re-claim (the mutex still works inside the TTL —
  this is the anti-regression half, per CLAUDE.md §3h: the criterion must
  forbid something, not just permit expiry).
- **AC2 — consumer (the line that matters, `subscription_alerts.py:948`):**
  ```bash
  cd <repo> && pytest tests/test_price_alert_ttl.py::test_stranded_claim_is_resent_by_daily_scheduler -q
  ```
  Seeds a TTL-expired claim row, runs `daily_scheduler` with a stubbed
  send, and asserts the email goes out (`price_emails_sent` increments, no
  `price_alerts_suppressed` increment for that key). **If this test does not
  exist, the criterion is INCOMPLETE without it (CLAUDE.md §§3g/3h):** the
  loop-2 gate's blind spot was exactly this shape — a proven sampler
  (`get_delay`) with an unfed consumer (`asyncio.sleep`). Here the sampler
  is the claim INSERT and the sink is the `:948` suppress-vs-send branch;
  a gate that only tests the store proves the sampler, not the send.
- **AC3 — no silent-suppression regression (existing gates stay green):**
  ```bash
  cd <repo> && pytest tests/test_price_alert_concurrency.py tests/test_price_alert_release_paths.py tests/test_price_alert_f2_5.py tests/test_subscription_alerts.py -q
  ```
- **AC4 — the stranded-claim premise is observably gone:**
  ```bash
  cd <repo> && grep -rn "notified_at" app/product_service.py | grep -v '"""' | grep -Ei "select|where|strftime|julianday|datetime|age|ttl"
  ```
  Must return ≥1 code (non-docstring) line that reads `notified_at` with an
  age comparison. Docstring mentions alone fail this AC.

## 4. OUT of scope (deliberately NOT decided here)

1. The TTL duration value and whether it is a constant, parameter, or setting —
   the BUILD mandates whatever it implements **only as proven by AC1/AC2**,
   never as a preferred number.
2. Reaper shape (lazy expiry-on-conflict vs. background sweeper) — either
   satisfies this spec iff AC2 passes; the developer chooses, the gate proves.
3. Schema migrations (new columns, e.g. holder-run id) — not required; ISO
   `notified_at` is already parseable. If the BUILD adds any, they are
   additive-only.
4. Changing the claim-before-send ordering from `77741a8` — frozen.
5. Product direction (whether households WANT re-delivery) — decided: yes,
   a stranded claim must not suppress forever. No further product call exists.

## 5. Stop command (loop is done on this item iff this passes)

```bash
cd <repo> && pytest tests/test_price_alert_ttl.py tests/test_price_alert_concurrency.py tests/test_price_alert_release_paths.py -q && grep -rn "notified_at" app/product_service.py | grep -v '"""' | grep -Ei "select|where|strftime|julianday|datetime|age|ttl"
```

## 6. Test-ID range

New tests MUST take IDs above the current traceability maximum: run
`python3 scripts/traceability_runner.py`, read its emitted maximum, and use
numbers above it. Do NOT invent IDs and do NOT reuse existing ones
(measured precedent: `fix(tests): the new hook gate reused five test ids
that already existed` — that repair is the reason for this rule).

## 7. Falsification (what would make this spec wrong)

```bash
cd <repo> && grep -rn "notified_at" app/ --include='*.py' | grep -v '"""' | grep -Ei "select|where|<|>|age|ttl|expir"
```

- Ran 2026-10-06: returns NOTHING outside docstrings — no code reads
  `notified_at`, no reaper exists, no commit implements TTL
  (`git log --format='%h %s' --grep='TTL'` lists only docs/audit commits:
  `7d4d3c1`, `7ab087a`, `77741a8` — none ships expiry logic).
- If a re-run of that command returns a code line that ages out claims, this
  spec's premise is false and the spec is WITHDRAWN, not implemented.

## 8. Narrow BUILD slice (next dispatch, one sentence)

Implement TTL expiry-on-conflict for the `price_alert_sent` claim in
`app/product_service.py` (claim + read path) so that `daily_scheduler` at
`app/subscription_alerts.py:948` re-sends alerts whose claim is older than
the TTL, proven by `tests/test_price_alert_ttl.py` (new) with AC2 driving the
consumer line — implementation shape left to the developer, observable proven
by §5.
