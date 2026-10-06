# SPEC: gate test harness — pin interpreter to `sys.executable` (loop4)

- Status: PLAN (no code changed by this spec)
- Date: 2026-10-06
- Item: accepted from ASK explore (loop4), verified by loop4 reviewer (APPROVE 4.7/5 with deferred doc gap)
- Previous work: `7272190 fix(hooks): resolve the repo venv interpreter, fail closed when none can run the gate` + `064f81a test(hooks): regression gate for pre-commit venv interpreter resolution` — the **hook** was fixed; the **test harness** was not. This spec covers only the harness.
- Traceability at HEAD `f84915b`: `python3 scripts/traceability_runner.py` was re-measured loop3 as `485 (24.4%)`; this item is test-only surface, not `app/` — traceability unchanged.
- Research grounding: primary snippets + links are quoted in §0 below, not carried by reference.

## §0 Research grounding (verbatim, re-measured 2026-10-06)

1. The harness defect (six call sites, measured `grep -rn '"python3"' tests/` at HEAD `f84915b`):
   ```
   tests/test_veritas_gate.py:135:        ["python3", str(repo / "scripts" / "veritas_gate.py"), *args],
   tests/test_veritas_gate.py:249:        ["python3", str(scripts / "veritas_gate.py"), "--verify-diff"],
   tests/test_veritas_gate.py:576:        ["python3", str(scripts / "veritas_gate.py"), "--verify-diff", "--role", "auto"],
   tests/test_permissions_constitutional_protection.py:107:        ["python3", str(repo / "scripts" / "veritas_gate.py"), *args],
   tests/test_precommit_gate_enforcement.py:277:            "python3",
   tests/test_precommit_gate_enforcement.py:310:        ["python3", str(GATE), "--history-scan"],
   ```
   `tests/test_precommit_hook_interpreter.py:238` (`assert "python3" in out`) is an assertion string about hook diagnostics, NOT a spawn — out of scope.

2. The gate needs `yaml` (`scripts/veritas_gate.py:28`):
   ```python
   import yaml
   ```
   Ambient `python3 -c 'import yaml'` → `ModuleNotFoundError: No module named 'yaml'` on the agent PATH (hermes 3.14 toolchain), while `.venv/bin/python -c 'import yaml'` → `OK`. Same diff, opposite verdict by interpreter resolution — the failure class closed for the hook at `7272190` and still live in the harness.

3. The hook precedent that this spec follows (`.githooks/pre-commit:31-56`, shipped at `7272190`):
   ```bash
   for _cand in "${REPO_ROOT}/.venv/bin/python" python3; do
     ...; if "$_cand" -c 'import yaml' >/dev/null 2>&1; then _veritas_py="$_cand"; break; fi; done
   if [[ -z "$_veritas_py" ]]; then echo "no interpreter with the 'yaml' module found." >&2; exit 2; fi
   ```
   The test-harness fix is narrower: no shell probe, just `sys.executable` — the venv Python is already the process running the tests. `tests/test_traceability_gate.py:48` (`[sys.executable, *args]`) and `tests/test_profile_honesty.py:58` already use this pattern in this suite (measured `grep -rn 'sys\.executable' tests/`).

4. The harness helpers that spawn the gate (re-measured `sed -n` at file:line):
   - `tests/test_veritas_gate.py:127-141` (`def _run_gate` → `["python3", str(repo / "scripts" / "veritas_gate.py"), *args]`)
   - `tests/test_veritas_gate.py:240-258` (inline `["python3", str(scripts / "veritas_gate.py"), "--verify-diff"]` in `test_git_context_failure_exits_2`)
   - `tests/test_veritas_gate.py:568-589` (inline `["python3", …, "--verify-diff", "--role", "auto"]` in `test_auto_role_without_git_context_fails_closed`)
   - `tests/test_permissions_constitutional_protection.py:100-113` (`def _run_gate` same shape at `:107`)
   - `tests/test_precommit_gate_enforcement.py:265-291` (`"python3"` at `:277`) and `:302-340` (`["python3", str(GATE), "--history-scan"]` at `:310`)

5. The file that predates the hook fix (`git log --oneline -- tests/test_veritas_gate.py` newest `0992ccf` — predates `7272190`; `git log --oneline -50 --grep='interpreter'` returns only hook commits `7272190,064f81a,b14ea91,bac2da3`; `git log --oneline -50 --grep='sys.executable'` returns zero hits).

6. `analysis/next-moves.md` tail is stale as of loop4 explore: `## ITERATION 2` "SECOND FINDING ... NOT yet confirmed" is now CONFIRMED (the six sites above); `## THE ITEM ... .githooks:31` shipped at `7272190` series. Refresh of that file belongs to RECORD, not to this harness BUILD.

7. Reviewer gap deferred (loop4 reviewer `loop4-reviewer.md`): `app/subscription_alerts.py:720-753` stale `OPERATOR ACTION` ("nothing reads notified_at" / "delete manually" / "permanently") — doc/wiring slice, zero `app/` callers besides `def` (`grep -rn '_best_effort_release_price_alert_sent(' app/ --include='*.py' | grep -v 'def '` → empty), no behavior change, noted but OUT of scope for this harness item. Loop3 TTL shipped `d992690+53a1f32` (IDs 058..060, APPROVE 5.0).

## 1. Target Files allowlist — exact paths and why each is in scope

| Path | Call site(s) | Why in scope |
|---|---|---|
| `tests/test_veritas_gate.py` | `:135` (`_run_gate` helper), `:249` (inline in `test_git_context_failure_exits_2`), `:576` (inline in `test_auto_role_without_git_context_fails_closed`) | The gate's own selftests spawn `scripts/veritas_gate.py` via bare `python3`; verdict becomes ambient-PATH-dependent. |
| `tests/test_permissions_constitutional_protection.py` | `:107` (`_run_gate` helper, `["python3", str(repo / "scripts" / "veritas_gate.py"), *args]`) | Same `_run_gate` shape as above; constitutional-tamper tests drive the gate through it. |
| `tests/test_precommit_gate_enforcement.py` | `:277` (`"python3"` inside `["python3", str(repo / "scripts" / "veritas_gate.py"), "--verify-metadata", "--role", "auto"]`), `:310` (`["python3", str(GATE), "--history-scan"]`) | Two more harness spawns that resolve `python3` via `PATH`; `GATE` is `scripts/veritas_gate.py` (`:22`). |

Any file NOT in this table is OUT of scope for the BUILD. In particular:
- `tests/test_precommit_hook_interpreter.py` — only mentions `"python3"` in assertions about hook diagnostics (`:238`), not a spawn; its own spawns already use `[sys.executable, "-m", "venv", …]` — DO NOT touch it.
- `app/*`, `frontend/*`, `scripts/veritas_gate.py`, `.githooks/pre-commit` — not changed by this item (hook already shipped at `7272190`).
- `analysis/next-moves.md`, `app/subscription_alerts.py:720-753` — reviewer doc gap deferred; BUILD must not touch them (see §4).
- `scripts/traceability_runner.py` — runner only; this item adds no new tests, so runner IDs are unchanged.

The BUILD must name the 6 call sites above in its commit message body and must not leave any `["python3",` / `"python3"` spawn to `scripts/veritas_gate.py` in the three files.

## 2. The single behavior to change (observable)

**Gate test harness resolves the interpreter to the repo venv (`sys.executable`), not the ambient `PATH` `python3`, so the suite verdict is environment-independent.**

What this is NOT: "the files import sys" — an `import sys` that still spawns `python3` satisfies nothing. What it IS: every harness spawn that currently writes the literal `"python3"` must be driven by the interpreter that is already running the test process (`sys.executable` — which, under `.venv/bin/python -m pytest`, is the venv Python that can `import yaml`). Observable proof: the suite's pass/fail under a `PATH` whose `python3` is yaml-less is identical to its pass/fail under a `PATH` whose `python3` can import yaml, modulo only the integer assertions the tests make about gate return codes — never `ModuleNotFoundError: No module named 'yaml'`.

## 3. Acceptance criteria (all RUNNABLE — paste as-is)

Assume `<repo>` = `/home/zoltan/receipts-lens` and the repo venv is `.venv/bin/python` (symlink to `python3.11`; `import yaml` succeeds there and fails under the ambient `python3` 3.14).

- **AC-GREP — harness uses `sys.executable` (no bare `python3` spawn to the gate remains):**
  ```bash
  cd /home/zoltan/receipts-lens && grep -rn '"python3"' tests/test_veritas_gate.py tests/test_permissions_constitutional_protection.py tests/test_precommit_gate_enforcement.py; echo "exit:$?"
  # Expected: no output and exit:1 (no matches). Any line matching ["python3", ... veritas_gate ...] or "python3" spawn to GATE fails.
  # Complementary positive — must return ≥6 hits for the new shape:
  cd /home/zoltan/receipts-lens && grep -rn 'sys\.executable' tests/test_veritas_gate.py tests/test_permissions_constitutional_protection.py tests/test_precommit_gate_enforcement.py
  # Expected: ≥6 matches covering the 6 sites above (helpers + inline spawns). `import sys` must be present in each file that now uses sys.executable.
  ```

- **AC-ISOLATION — verdict is environment-independent (yaml-less ambient `PATH` does not flip the suite):**
  ```bash
  cd /home/zoltan/receipts-lens
  # Build a yaml-less shim and put it first on PATH; prove the shim is the resolved python3 and that it cannot import yaml:
  mkdir -p /tmp/loop4-yaml-less-shim && printf '#!/bin/sh\nexec /usr/bin/python3 "$@"\n' > /tmp/loop4-yaml-less-shim/python3 && chmod +x /tmp/loop4-yaml-less-shim/python3
  PATH=/tmp/loop4-yaml-less-shim:$PATH python3 -c 'import yaml' 2>&1 | head -2; echo "shim-exit:$?"
  # Expected: ModuleNotFoundError and non-zero — the shim's python3 is yaml-less
  which python3; python3 --version
  # Expected: /tmp/loop4-yaml-less-shim/python3 first
  # Now run the harness under that PATH via the venv interpreter (harness must use sys.executable, i.e. the venv python, not the shim):
  PATH=/tmp/loop4-yaml-less-shim:$PATH .venv/bin/python -m pytest tests/test_veritas_gate.py tests/test_permissions_constitutional_protection.py tests/test_precommit_gate_enforcement.py -q
  # Expected: same pass count as the clean-tree run (AC-GREEN) and NO test fails with ModuleNotFoundError / "No module named 'yaml'". Any failure must be for the integer gate reason the test asserts (returncode / output), not for a missing yaml import. Paste the full pytest tail.
  ```

- **AC-GREEN — suite still green on a clean tree (no behavior regression):**
  ```bash
  cd /home/zoltan/receipts-lens && .venv/bin/python -m pytest tests/test_veritas_gate.py tests/test_permissions_constitutional_protection.py tests/test_precommit_gate_enforcement.py tests/test_precommit_hook_interpreter.py -q
  # Expected: all passed (or passed + expected skips), zero failures. Paste the pytest tail with counts. The 20-test veritas_gate suite is the anchor: loop2 measured it green under three clean PATHs; it must stay green.
  ```

All three ACs must be pasted as real command output in the BUILD report; `not measured` is not a pass for any of them.

## 4. OUT of scope (deliberately NOT decided here)

1. The reviewer doc gap `app/subscription_alerts.py:720-753` — stale `OPERATOR ACTION` / warning ("nothing reads `notified_at`", "delete manually", "permanently", "There is no reaper") and `tests/test_price_alert_ttl.py:3` line-ref stale. This is a **doc/wiring slice, zero `app/` callers** besides `def _best_effort_release_price_alert_sent`, no behavior change, deferred to a separate doc-only dispatch. This harness BUILD must NOT touch `app/subscription_alerts.py` or `tests/test_price_alert_ttl.py:3`.
2. Refresh of `analysis/next-moves.md` ITERATION-2 tail (stale "NOT yet confirmed" / shipped hook item) — belongs to RECORD, not to this harness fix.
3. `.githooks/pre-commit` — shipped at `7272190` (probes `${REPO_ROOT}/.venv/bin/python` then `python3`, fail-closed exit 2 when none can `import yaml`). No change.
4. Traceability IDs / `scripts/traceability_runner.py` / `.ai/quality-gates.yaml` / `PROVENANCE.md` / `veritas_audit.jsonl` — this item adds no new tests and touches no runner outputs.
5. TTL/state nuances of `price_alert_sent` — shipped `d992690+53a1f32`, IDs 058..060; not revisited here.
6. Product direction beyond the one behavior in §2 — no decision.
7. Implementation choice beyond "use `sys.executable` for these six spawns" — whether the BUILD also extracts a shared helper or leaves three helpers is not decided; the ACs decide.

## 5. Stop command (loop is done on this item iff this passes)

```bash
cd /home/zoltan/receipts-lens && grep -rn '"python3"' tests/test_veritas_gate.py tests/test_permissions_constitutional_protection.py tests/test_precommit_gate_enforcement.py; echo "grep-exit:$?" && PATH=/tmp/loop4-yaml-less-shim:$PATH .venv/bin/python -m pytest tests/test_veritas_gate.py tests/test_permissions_constitutional_protection.py tests/test_precommit_gate_enforcement.py -q && .venv/bin/python -m pytest tests/test_veritas_gate.py tests/test_permissions_constitutional_protection.py tests/test_precommit_gate_enforcement.py tests/test_precommit_hook_interpreter.py -q
```

Pass iff: first `grep` prints nothing and exits 1, second `pytest` (under yaml-less shim `PATH`) shows the same pass count as the third (clean `PATH`) with no `ModuleNotFoundError: No module named 'yaml'` in any failure, and third `pytest` is green. Paste all three outputs.

## 6. Test-ID range

**This item adds NO new tests and needs NO new IDs.**

It is a test-only harness repair (6 spawn sites → `sys.executable`), not a new gate. No `TEST-RL-V02-*` / `QA-ZOO27-*` IDs are allocated, no `scripts/traceability_runner.py` run is needed for IDs, and the traceability total is unchanged (`485 (24.4%)` at `f84915b`). If a BUILD nevertheless adds a new test file, it MUST run `python3 scripts/traceability_runner.py`, read its emitted maximum, and allocate above it — but the spec does not require it and the ACs do not assume it. The rule for why no IDs are needed: the change is bounded to existing harnesses and its `OUT of scope` closes new-suite creation; adding IDs would be scope creep.

## 7. Falsification (what would make this spec wrong)

The spec is wrong if the hazard is theoretical — i.e. no real execution environment that runs this suite ever resolves bare `python3` to a yaml-less interpreter, so the suite verdict is not actually environment-dependent.

Falsification command (the harness under a yaml-less ambient `PATH`):

```bash
cd /home/zoltan/receipts-lens
mkdir -p /tmp/loop4-yaml-less-shim && printf '#!/bin/sh\nexec /usr/bin/python3 "$@"\n' > /tmp/loop4-yaml-less-shim/python3 && chmod +x /tmp/loop4-yaml-less-shim/python3
PATH=/tmp/loop4-yaml-less-shim:$PATH python3 -c 'import yaml' 2>&1 | head -2; echo "shim-probe-exit:$?"
# Then, on the UNFIXED tree (before BUILD), run the harness under that PATH:
PATH=/tmp/loop4-yaml-less-shim:$PATH .venv/bin/python -m pytest tests/test_veritas_gate.py -q 2>&1 | tail -30
```

- If the unfixed tree still passes `20 passed` under the yaml-less shim `PATH`, the item is downgraded to hygiene (non-blocking) — the ambient resolver does not flip the verdict in practice.
- If the unfixed tree shows `2 FAILED` with `ModuleNotFoundError: No module named 'yaml'` (or `pydantic_core` wrong-ABI as loop2 measured under a foreign 3.14 `PYTHONPATH`), the spec's premise is confirmed.

Whether run now: **not attempted on the unfixed tree in this PLAN dispatch** — the explore + this plan re-measured the six sites, the `yaml` import line, and the shim construction, but the full unfixed-tree pytest under the shim is the BUILD's first verification step and would have consumed the 15-minute PLAN budget. The loop2 next-moves tail already records the adjacent injection (`PYTHONPATH=<hermes 3.14 site>` → 2 FAILED) as prior evidence; the exact `PATH=/tmp/loop4-yaml-less-shim` falsification is the BUILD's opening measurement. The `PATH=… .venv/bin/python -m pytest …` success criterion after the fix (AC-ISOLATION) is the complementary proof that the fix closes the hazard.

## 8. Narrow BUILD slice (next dispatch, one sentence)

Replace the bare `"python3"` spawns at the six call sites in `tests/test_veritas_gate.py:135,249,576`, `tests/test_permissions_constitutional_protection.py:107`, and `tests/test_precommit_gate_enforcement.py:277,310` with `sys.executable` so the gate test harness runs `scripts/veritas_gate.py` under the repo venv instead of the ambient `PATH` `python3` — implementation shape left to the developer, observable proven by §5.

## 9. Measurements re-ran for this spec (command → output/file:line)

| Claim | Command / file:line re-ran | Output (HEAD `f84915b`) |
|---|---|---|
| Six bare `python3` harness sites | `grep -rn '"python3"' tests/` | 6 lines: `test_veritas_gate.py:135,249,576`, `test_permissions_constitutional_protection.py:107`, `test_precommit_gate_enforcement.py:277,310` (+ hook-interpreter assertion at `:238` out of scope) |
| Harness already uses `sys.executable` nowhere in these files | `grep -rn 'sys\.executable' tests/test_veritas_gate.py tests/test_permissions_constitutional_protection.py tests/test_precommit_gate_enforcement.py` | empty (no hits) — vs. `tests/test_traceability_gate.py:48` has `[sys.executable, *args]` as precedent |
| Gate needs yaml | `sed -n '1,35p' scripts/veritas_gate.py` | line 28: `import yaml` |
| `_run_gate` helpers spawn `python3` | `sed -n '125,150p' tests/test_veritas_gate.py` / `sed -n '95,120p' tests/test_permissions_constitutional_protection.py` | both show `["python3", str(repo / "scripts" / "veritas_gate.py"), *args]` |
| Inline spawns at :249 and :576 | `sed -n '240,260p'` / `sed -n '565,590p' tests/test_veritas_gate.py` | both show `["python3", str(scripts / "veritas_gate.py"), …]` |
| Precommit gate spawns at :277 and :310 | `sed -n '265,315p'` / `sed -n '240,295p' tests/test_precommit_gate_enforcement.py` | `:277 "python3"` and `:310 ["python3", str(GATE), "--history-scan"]` |
| Hook fix shipped | `git log --oneline -3 --grep='venv interpreter'` | `064f81a` + `7272190` (hook probe + gate) |
| Harness file predates hook fix | `git log --oneline -- tests/test_veritas_gate.py \| head -1` | `0992ccf` (predates `7272190`) |
| Hook probes venv first then `python3`, fail-closed exit 2 | `sed -n '35,70p' .githooks/pre-commit` | `for _cand in "${REPO_ROOT}/.venv/bin/python" python3; … if "$_cand" -c 'import yaml'` / `exit 2` block |
| Venv Python can import yaml, ambient cannot | `.venv/bin/python -c 'import yaml'` / `python3 -c 'import yaml'` | `venv yaml OK` vs `ModuleNotFoundError: No module named 'yaml'` |
| Imports in target files | `grep -n '^import sys\|^import os\|^import subprocess' tests/test_veritas_gate.py …` | `os`+`subprocess` present, `sys` absent — BUILD will add `import sys` |
| Reviewer gap deferred (no `app/` callers) | `grep -rn '_best_effort_release_price_alert_sent(' app/ --include='*.py' \| grep -v 'def '` | empty (as reviewer reported) |

If a claim the ASK asserted was not re-run, it would be marked "not re-measured here; loop4 explore measured" — none: all six sites, the yaml line, the hook, and the log were re-measured above.
