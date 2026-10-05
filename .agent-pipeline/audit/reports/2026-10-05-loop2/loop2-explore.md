dispatch:  loop2 explore brief (inline, no brief file)
agent:     explore
repo:      /home/zoltan/receipts-lens @ 887317f26792e916de821ab30b6c5c84811296cf
brief:     sha256:nobrief-inline-task
verdict:   none - first pass
status:    DONE - all 6 items answered read-only; evidence pasted below

1. ONE next work item: give the `price_alert_sent` claim in
`app/product_service.py:claim_price_alert_sent` a TTL with expiry-on-conflict
(on IntegrityError, read the existing row's `notified_at` and steal the claim
if older than N hours), so a process killed between the claim INSERT and the
SMTP send stops suppressing that household's price-hike alert forever.

2. Evidence (commands run, output pasted):
   - `grep -rn 'notified_at' app/ --include='*.py'` returns only the schema
     (`app/product_service.py:94`), two INSERT sites (`:303`, `:388`), and
     docstrings (`:320`, `:356`, `app/subscription_alerts.py:744`). Zero reads
     of the value anywhere in `app/` — the column is write-only, so no TTL,
     expiry, or reaper can exist today.
   - `git log --oneline -50 --grep='TTL'` / `--grep='reaper' -i` hit only
     `77741a8 fix(alerts): claim the price alert before sending...`, whose own
     docstring at `app/product_service.py:378` says "Deliberately NOT solved
     here: a TTL on the claim, a reaper..." — the deferral is in shipped code.
   - `analysis/next-moves.md:83-86` ("Open item, planned but NOT built")
     independently records the same gap; a planner brief exists at
     `$TMPDIR/briefs/loop1-plan.txt` but the planner dispatch was never run.
   - Foreign-file claim CONFIRMED: `loop5-dev.out` header reads
     `repo: /home/zoltan/Veritas @ 8d39a33`; `bh-gate-3b.out` cites
     `/tmp/dispatch-log/bh-gate-3.md` and commit `50de71d`, and
     `git cat-file -t 50de71d` returns "fatal: Not a valid object name" in
     this repo (per `analysis/next-moves.md` ITERATION 2 section, re-verified
     file headers present in
     `.agent-pipeline/audit/reports/2026-10-05-loop1/`).

3. Why NOW vs the alternatives:
   - Rejected alternative A — provenance cleanup of `bec09c9` (remove the 2
     foreign files or add PROVENANCE.md): real defect, still OPEN (no
     PROVENANCE.md exists; `git log --grep='provenance' -i` hits only
     unrelated commits). Rejected because it is docs-only hygiene with zero
     user-visible effect; no alert, bill, or export changes either way.
   - Rejected alternative B — the traceability grind (1088 tests missing
     markers, 68 non-compliant files; measured just now via
     `python3 scripts/count_traceability_coverage.py`: 480/1568 = 30.6%
     marker-complete, up from 24.0% pinned at f74abf9). Rejected because it
     is a ~68-file mechanical grind with no user-visible defect and gate 10
     already ratchets on the measured value.
   - The TTL item wins because it is the only candidate that is a live,
     user-facing silent failure: a crashed run permanently suppresses a
     price-hike notification with no log line, no exit-code signal, and only
     a manual SQL DELETE as recovery (documented at
     `app/product_service.py:360-376`).

4. Production consumer? YES — this is a behavior slice, not a wiring slice.
   `grep -rn 'claim_price_alert_sent(' app/ --include='*.py' | grep -v 'def '`
   output:
   ```
   app/subscription_alerts.py:701:        store.claim_price_alert_sent(tenant, merchant, amount_cents, period_ym)
   app/subscription_alerts.py:948:            if not _claim_price_alert_sent(tenant, merchant, amount_cents, period_ym):
   ```
   `:701` is the `_claim_price_alert_sent` wrapper body; `:948` is the live
   call site in the daily scheduler send path. Non-zero callers confirmed.

5. Already done? NO.
   - `analyses/`: does not exist (`ls` returns "No such file or directory").
   - `analysis/`: contains only `architecture-frontend.md`,
     `next-moves.md`, `research-brief.md`; `grep -rn "TTL" analysis/` hits
     only `next-moves.md:30` and `:83-86`, both describing the item as OPEN.
   - `git log --oneline -50 --grep='<keyword>'`: `--grep='TTL'` and
     `--grep='reaper' -i` return only `77741a8` (the original claim, which
     defers TTL); `--grep='claim' -i` returns `bec09c9, 9be3d0a, 2741628,
     f74abf9, 77741a8, 3fc14d8, 3da3cd0` — none implements expiry. So the
     item is not done; a different item was not needed.

6. What could make this item wrong, and how to falsify it: the item assumes a
   crash can land between the claim INSERT and the send. If the scheduler
   runs claim and send in one synchronous block with no realistic kill window
   (e.g. single-threaded run-to-completion where the only gap is interpreter
   crash, measured at ~0 in production logs), the TTL adds complexity for a
   window that never fires. Falsify by checking: (a) whether any
   `price_alert_sent` row in a production/copied DB has a `notified_at` with
   no corresponding sent mail (a stranded row proves the window is real), or
   (b) whether `app/subscription_alerts.py:948` and the send call are adjacent
   with no await/yield/kill-point between them — read lines 940-1030 and
   confirm the gap is code-adjacent.

TIME USED: 8 minutes

COMMIT NOTE: path 2 was written and explicitly staged
(`git add .agent-pipeline/audit/reports/2026-10-05-loop2/loop2-explore.md`),
but `git commit` failed: the repo pre-commit hook `scripts/veritas_gate.py`
exits 1 with `ModuleNotFoundError: No module named 'yaml'` — an environment
defect unrelated to this docs-only file. The file remains staged but
UNCOMMITTED. Pre-existing dirty state untouched and still present:
`M .agent-pipeline/audit/traceability.json`,
`M .agent-pipeline/audit/veritas_audit.jsonl`. Did not retry with
--no-verify (bypassing a policy gate is not mine to decide).
STATUS REVISED: PARTIAL - report complete on both paths, commit blocked by hook env.
