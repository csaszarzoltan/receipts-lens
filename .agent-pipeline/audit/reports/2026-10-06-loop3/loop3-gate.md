dispatch:  inline prompt (loop3 gate brief)
agent:     reviewer
repo:      /home/zoltan/receipts-lens @ 6808e7c
brief:     sha256:253ddb2704d8
verdict:   none - first pass
status:    DONE - all 5 ACs measured with pasted output, RED proven in place and restored byte-exactly

# loop3 gate — TTL expiry-on-conflict for price_alert_sent claim

Commits under review: d992690 (product) + 53a1f32 (gate 058..060) + 6808e7c (traceability), on spec c0bfaf1.
Plan: .agent-pipeline/audit/reports/2026-10-06-loop3/loop3-plan.md

## 1. AC1 producer gate
Command: `env -u PYTHONPATH PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest tests/test_price_alert_ttl.py -v`
Output:
```
collected 3 items
tests/test_price_alert_ttl.py ...  [100%]
3 passed in 1.43s
```
PASS — 3 passed, including anti-regression TEST-RL-V02-059 (fresh claim still False, mutex holds).

## 2. AC2 consumer (sampler vs sink, CLAUDE.md 3g/3h)
Command: `... -m pytest tests/test_price_alert_ttl.py::test_stranded_claim_is_resent_by_daily_scheduler -v`
Output: `1 passed in 1.23s`. PASS — the test seeds an expired claim row, runs the real
`daily_scheduler` through `app/subscription_alerts.py:948` (`_claim_price_alert_sent` wrapper at
:701 -> `store.claim_price_alert_sent`), stubbed send only. The :948 suppress-vs-send branch is
driven, not just the store. Consumer proven, not only the sampler.

## 3. AC3 no regression
Command: `... -m pytest tests/test_price_alert_concurrency.py tests/test_price_alert_release_paths.py tests/test_price_alert_f2_5.py tests/test_subscription_alerts.py -p no:warnings`
Output: `90 passed, 1 skipped in 23.43s`. No FAILED. PASS.

## 4. AC4 premise grep (non-docstring code line reading notified_at with age)
Command A output (app/product_service.py, code lines):
```
279:    def _price_alert_claim_age_seconds(self, notified_at: str | None) -> float | None:
289:            ts = datetime.fromisoformat(notified_at)
298:        age = self._price_alert_claim_age_seconds(notified_at)
316:                "SELECT notified_at FROM price_alert_sent "
399:                    "SELECT notified_at FROM price_alert_sent "
```
Command B output (app-wide): same SELECT/age lines in product_service.py, plus
`app/subscription_alerts.py:744` (docstring-only mention of the old hazard text).
Pre-fix comparison: `git show c0bfaf1:app/product_service.py | grep notified_at` shows only
docstring prose ("written here and read nowhere", "no TTL, no expiry") — zero SELECT/age code
lines. PASS — the read+age path is new code, and AC4's falsification shape is satisfied.

## 5. RED proof — in-place mutation, gate fails, restored byte-exactly (CLAUDE.md 3b)
First attempt (reported, not hidden): `PRICE_ALERT_CLAIM_TTL_SECONDS = 24*60*60 -> 10**9`
left the gate GREEN (3 passed) — the tests backdate *relative to the constant*, so scaling the
constant is a vacuous mutant. Discarded as evidence; chose a mutant on the line the change
depends on instead.
Real mutant: `app/product_service.py:299`
before: `return age is not None and age > PRICE_ALERT_CLAIM_TTL_SECONDS`
after:  `return False  # MUTANT: expiry disabled`
Gate output under mutant:
```
FAILED tests/test_price_alert_ttl.py::test_expired_claim_can_be_reclaimed - A...
FAILED tests/test_price_alert_ttl.py::test_stranded_claim_is_resent_by_daily_scheduler
2 failed, 1 passed in 0.78s
```
RED proven: expiry branch off -> 058 and 060 fail, 059 (mutex half) still passes — exactly the
expected split. Restore: `cp /tmp/product_service.bak app/product_service.py`,
md5 `963beeb840de7a15715ab2bdb33beb85` before and after (identical), `git diff --quiet` clean
("TREE CLEAN - restored byte-exactly"), gate re-run green (3 passed).
File/line/failed-count/restore-md5 all recorded. PASS.

## Other checks
- Production callers of `claim_price_alert_sent(`: `app/subscription_alerts.py:701`
  (wrapper def `_claim_price_alert_sent`) and `:948` (the `daily_scheduler` call site). Target
  exists in production — the right thing was built.
- `has_price_alert_sent` callers in app/: none besides its def (product_service.py:301); only
  tests call it. Consistent, not a defect: the read path was changed to agree with the claim
  path (an expired claim must read as not-sent, else :948's sibling checks would disagree).
  No dead-code concern — it is the public existence-check API covered by f2_5 + ttl tests.
- `git log --oneline -6`: 6808e7c / 53a1f32 / d992690 / f6055a2 / c0bfaf1 / a5539cb. Commit
  contents: 6808e7c = traceability.json only; 53a1f32 = tests/test_price_alert_ttl.py only;
  d992690 = app/product_service.py + loop3-dev.md (dev report co-located with the product
  commit — inside the iteration's allowlist, no foreign files). No blanket staging.
- `git ls-files --error-unmatch`: tests/test_price_alert_ttl.py tracked; app/product_service.py
  tracked; loop3-dev.md tracked; loop3-plan.md tracked.
- TEST-RL-V02 IDs: 058/059/060 occur only in tests/test_price_alert_ttl.py (counts 2/3/3 =
  marker + scenario prose, no cross-file reuse). The `uniq -d` hits (012/039/045/051) are
  pre-existing in test_veritas_gate.py / test_security_gate_secret_scan.py /
  test_traceability_gate.py / test_profile_honesty.py (e.g. 012 is prose "reused TEST-RL-V02-012
  .. -018" in the secret-scan docstring + the veritas marker) — untouched by this iteration,
  not this loop's debt.
- Gate read-only honored except the brief-mandated in-place RED mutation, which was restored
  byte-exactly (md5 match + `git diff --quiet` clean). No product/test/.ai file left modified.
- Traceability at HEAD records tests/test_price_alert_ttl.py: 3. Traceability commit message
  matches its content (`record the traceability measurement at 53a1f32`).
- Note (non-blocking): tests/test_price_alert_ttl.py module docstring cites
  "app/product_service.py:319-326" for the old hazard text that d992690 rewrote — stale line
  reference in a comment, harmless.

## Scores
| Dimension | Score | Weight | Why |
|---|---|---|---|
| brief quality | 5 | (info) | Narrow question, numbered ACs with exact commands, budget, explicit dual output paths |
| target choice | 5 | (info) | Production caller exists (:948 via :701); expiry-on-conflict matches plan |
| verification | 5 | (info) | Consumer :948 driven (060), anti-regression 059 present, RED proven on the depend-on line |
| scope discipline | 5 | (info) | Each commit inside its allowlist; no foreign files swept |
| process honesty | 5 | (info) | Commit order product->gate->traceability; IDs 058..060 unique to this loop; vacuous mutant reported, not hidden |
| evidence survival | 5 | (info) | All four artifacts tracked in git (ttl test, product, dev+plan reports); this report committed as loop3-gate.md |
| correctness | 5 | 30 | All 5 ACs measured green with pasted output |
| test coverage | 5 | 20 | New behavior has new gate (3 tests) + green; consumer line covered |
| spec compliance | 5 | 20 | Built per loop3-plan.md (TTL constant, expiry-on-conflict, conditional steal, :948 consumer test) |
| code quality | 5 | 15 | Typed helpers, rowcount-guarded steal, bad-stamp fail-closed; no facade/duplication |
| evidence | 5 | 15 | SHA 6808e7c seen, full test commands + counts pasted, mutation record complete |
Weighted total = (5*30 + 5*20 + 5*20 + 5*15 + 5*15)/5 = 500/5 = 5.0/5. No dimension <3.

APPROVE 5.0/5 — all five ACs measured green, consumer line driven, RED proven in place and restored.

git log --oneline -1: 6808e7c chore(policy): record the traceability measurement at 53a1f32
Test commands + counts: ttl file 3 passed; consumer single 1 passed; regression 90 passed, 1 skipped; mutant run 2 failed, 1 passed; post-restore 3 passed.

TIME USED: 5 minutes
