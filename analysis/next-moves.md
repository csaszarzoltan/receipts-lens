# receipts-lens — next moves

## 2026-10-05 — recovery complete, both human approvals exercised

Six commits, remote 0/0: `5645ea0, eb5d6ff, 3da3cd0, 0992ccf, 3fc14d8,
8e0039b, eac2902, 77741a8, f74abf9`. Full suite 1755 passed, 10 skipped.

### Closed
1. Abandoned-worktree recovery — `zoo21` contained the other two as ancestors,
   so it was merged as the trunk rather than raced. Two real security defects
   resolved on the way: a `cd ""` guard that could never fail closed, and a
   masked `pytest || pytest` fallback.
2. Gate 10 + the traceability runner — previously the gate read a file with no
   enforced threshold. Now measured at 24.0% with a 4.0% ratchet, and the gate
   bites in place (verified by mutation, byte-exact restore).
3. `.ai/quality-gates.yaml` — carried `percent: "4.8"` from a function that
   scans a smaller set than gate 10 consumes. Replaced with the runner's own
   output. It was causing a live test failure, not just reading wrong.
4. `.ai/policy-lock.json` re-pinned to the post-fix hashes (R4, human-approved).
5. **Price-alert duplicate email (R3)** — claim-before-send plus release on
   every failure path. Reviewed at 3.1/5 first; three findings closed:
   unguarded releases that could strand a claim and kill the whole run, a
   "delivered on an earlier run" success message that was false, and an
   undocumented permanent-claim limit.

### The honest limits, written down rather than smoothed over
- The claim and the send are **not atomic**. Separate transaction, then a
  network call. This closes the duplicate on graceful paths; it is not
  exactly-once delivery.
- A claim whose send never completes was **permanent** — now expiry-on-conflict
  (shipped 2026-10-06 at d992690, TTL 24h via `PRICE_ALERT_CLAIM_TTL_SECONDS`). Recovery
  previously a manual row delete; now self-heals. Documented in
  `product_service.claim_price_alert_sent`. (Update: the "permanent / delete manually"
  operator text in `subscription_alerts.py:720-753` is now stale — see loop4 reviewer
  loop4-reviewer.md, deferred doc-only cleanup.)
- Traceability is **24.0%**, not the 100% the config once implied. 738 spec
  references do not resolve; the e2e tree is 0%. See `.ai/traceability-gap.md`.
- Run one `subscription-alerts` process at a time only until the claim window
  is closed by a real atomic operation, not merely by the current code.

### Not done, on purpose
- `analysis/` is the only doc the loop reads first; the three abandoned
  worktrees were left in place with their branches intact and their dirty state
  snapshotted at `$TMPDIR/repo-rescue-20261004/worktree-dirty/`.


## 2026-10-05 — next-work-loop, iteration 1 (returned to BUILD twice)

Loop ran on top of the recovery above. Sentinel: the tree was RED at the start, so
the first item was not chosen from candidates — it was the failing test.

### Shipped this loop
- `86de73b` `fix(policy)` — `.ai/quality-gates.yaml` carried the 0992ccf numbers
  (474/1978, 24.0%) while the runner had reported 480/1984 (24.2%) since the
  price-alert tests landed, so gate 10's own test compared 1978 against 1984 and
  failed on a clean HEAD. Written by a dispatched agent that was killed by its own
  timeout before it could commit; the orchestrator found the work in the tree.
- `60e3c89` `chore(policy)` — R4 re-pin of the stale hash.
- `2741628` `fix(gate)` — closes the reviewer's three findings (see below).
- `61b8b11` `chore(policy)` — R4 re-pin after 2741628.

Suite after everything: **1755 passed, 10 skipped, 0 failed**.

### The reviewer scored the first pair REQUEST-CHANGES 3.8/5
`correctness 4 · evidence 3 · honesty 3 · scope 5 · verification 4`.

- **`.ai/quality-gates.yaml` claimed "the runner's own numbers" while
  `unresolved_spec_references: 58` sat three lines under it.** The runner says
  750. 58 is a REAL measurement of a different thing (synthetic self-referential
  ids, enforced only under `--strict-traceability`). Fixed by naming both:
  `unresolved_synthetic_self_refs_strict_only: 58` and
  `runner_spec_references_unresolved_count: 750`. **58 was not overwritten** —
  deleting a real measurement is not a fix for a bad name.
- **`60e3c89`'s message claimed an audit record that did not exist.** Verified:
  `grep -c VERITAS_HUMAN_APPROVAL .agent-pipeline/audit/veritas_audit.jsonl` → 0,
  and the log had no approval event type at all. Corrected by a NEW commit, never
  an amend. **This was the orchestrator's own error, in a message it wrote.**
- **`human_approval_present()` never logged.** So an R4/R3 sign-off left no
  who/what/when evidence. New `log_approval_event()` writes an `APPROVAL` event
  at both call sites, carrying the variable NAME, the scope, the files and the
  commit sha — **never the variable's VALUE**, which may hold the owner's words.
  Additive only: proven both ways in one run (without the var → FAIL and blocked;
  with it → PASS plus the event).

### Open item, planned but NOT built — SHIPPED 2026-10-06 as loop3 (now loop4)
**TTL + expiry-on-conflict for the `price_alert_sent` claim.** Proposed by
`explore` iteration 1, independently re-measured by the orchestrator; shipped at
`d992690 feat(alerts): TTL expiry-on-conflict` + `53a1f32 test(alerts): gate` +
`6808e7c tracer` + `d57f036 gate APPROVE 5.0/5` (loop3). Spec:
`.agent-pipeline/audit/reports/2026-10-06-loop3/loop3-plan.md`. Old note kept for record:
`app/product_service.py:378` deferred it as *"belong to a spec of their own"* —
that spec is `loop3-plan.md`. `notified_at` is now read + aged (grep `SELECT notified_at` where).

### Method notes this loop earned
- **A stalled agent is not a dead agent.** One dispatch returned an 81-byte
  artifact reading "GREEN on item 1. Checking policy-lock staleness..." — it had
  done two of three items and died before committing. Another returned 74 bytes
  naming exactly where it stopped. Diffing the target files is what told the
  difference between "did nothing" and "did most of it".
- **A read-only role whose tools write is not read-only.** The first reviewer ran
  `traceability_runner.py`, which wrote the very artifact it was auditing, and
  reported that itself, unprompted. It is recorded here because the next
  reviewer will do it too.
- **The queue's slots are global.** Our tickets waited 167–1097 s for a slot
  behind other sessions' dispatches. Wall times from this loop are not a verdict
  on this repo's health.

## ITERATION 2 (2026-10-05, later) — ORIENT finding, measured

### PROVENANCE DEFECT in bec09c9 (found by ORIENT, not by any gate)
`bec09c9` says: *"These 4 files are the dispatch artifacts ... the reasoning record for
the commits in this loop."* It committed **8** files, and **2 of them belong to other
repositories**:

  - `.agent-pipeline/audit/reports/2026-10-05-loop1/bh-gate-3b.out` (972 B)
      its own text cites `/tmp/dispatch-log/bh-gate-3.md` and commit `50de71d`;
      `git cat-file -t 50de71d` -> **fatal: Not a valid object name** in this repo.
      It is the **browser-helper** gate verdict (APPROVE 5.0/5, "2805 passed").
  - `.agent-pipeline/audit/reports/2026-10-05-loop1/loop5-dev.out` (6714 B)
      its own header reads: **`repo: /home/zoltan/Veritas @ 8d39a33`**.
      It is a **Veritas** developer report.

Measured: the commit message names `bh-gate` and `loop5` as filenames but **never says
they come from other projects** — greps for `Veritas` and `browser-helper` in the message
both return 0. A future reader of `reports/2026-10-05-loop1/` would reasonably conclude
these are receipts-lens evidence. **Class: the artifact-preservation fix imported foreign
evidence to strengthen a claim it did not support.**

Also measured: 3 of the 9 files in that directory (`loop1-gate2.out` 99 B,
`loop1-gate3.out` 4175 B, and the ORCHESTRATOR file) are receipts-lens, but the two
foreign ones **inflate the evidence directory from 7 to 9 files** without saying so.

Status: OPEN. The directory needs either the 2 foreign files removed, or a
`PROVENANCE.md` naming each file's true origin, and the commit message claim corrected.

## ITERATION 2 — results so far (2026-10-05 late)

### SHIPPED: bac2da3 (loop-2 explore + plan artifacts)
Both reports were written by agents whose OWN COMMIT THE HOOK BLOCKED. Neither explore nor
planner used --no-verify (both named the block instead - clause 3 behaviour working). The
reviewer DID use --no-verify and said so in its message, which is correct disclosure but
is exactly the defeat of the gate the hook exists to be.
Committed with PATH="<repo>/.venv/bin:$PATH" - the workaround, not the fix.

### THE ITEM (accepted, PLAN done, BUILD shipped): .githooks/pre-commit:31 — SHIPPED at 7272190 (hook fix) + 064f81a (gate) + 5fb6b36/0560c23/8af5d08, gate APPROVE 4.7/5
`python3 "$runner"` resolves to an interpreter WITHOUT pyyaml in an agent PATH (now fixed in hook, harness later):
    python3 scripts/veritas_gate.py --verify-diff --verify-metadata --staged --role auto
      -> ModuleNotFoundError: No module named 'yaml'
    PATH=<repo>/.venv/bin:$PATH  (identical command)
      -> [OK] VERITAS Gate Check PASSED, exit 0
Same diff, opposite verdict: the failure is interpreter RESOLUTION, not gate logic.
THREE agents hit it this session (explore, planner, reviewer) and one bypassed the gate.
Spec: .agent-pipeline/audit/reports/2026-10-05-loop2/loop2-plan.md (committed).
The spec's decision: probe candidates in order, venv first; if no candidate can import
yaml -> exit 2 fail-closed (the embedded fallback gate does NOT check policy-lock or
protected paths, so a silent fallback would be weaker than blocking).

### SECOND FINDING (was: NOT yet confirmed) — SHIPPED 2026-10-06 as loop4 harness (1a5f47f)
`tests/test_veritas_gate.py:135` and `:249` also call a bare `python3` to run the gate. So
that test file's verdict depends on the AMBIENT python3, not on the repo's venv. **Shipped at
1a5f47f test(gate): pin gate test harness spawns to sys.executable** (6 sites:
test_veritas_gate.py:135,249,576 + test_permissions...:107 +
test_precommit_gate_enforcement.py:277,310). Spec:
.agent-pipeline/audit/reports/2026-10-06-loop4/loop4-plan.md, gate APPROVE 4.7/5
(8ea5e0d). Was NOT yet confirmed; now CONFIRMED and FIXED — see loop4 ASK explore
c2d4e92. Original measurement kept: PATH=.venv/bin ->20 passed; PYTHONPATH injection 2 FAILED.

### STILL OPEN from iteration 1: the foreign artifacts in reports/2026-10-05-loop1/
bh-gate-3b.out (browser-helper, SHA 50de71d absent here) and loop5-dev.out (Veritas @ 8d39a33).
Independently confirmed by the loop-2 reviewer with `git cat-file -e`. Not yet cleaned.
