dispatch:  .agent-pipeline/audit/reports/2026-10-05-loop2/loop2-plan.md (inline loop-2 planner brief)
agent:     developer
repo:      /home/zoltan/receipts-lens @ 7ab087a
brief:     sha256:64085b751959 (loop2-plan.md on disk)
verdict:   none - first pass
status:    DONE - hook fix + regression test, RED shown pre-fix and GREEN post-fix

NOTE ON ROLES: the brief said to leave the test to test_author if repo policy forbids
writing tests/**. Checked AGENTS.md + METHODOLOGY.md + workflows/principles.md for a
"test author only" rule: no hit (`grep -rn -i "test.author|test_author|who.*writ.*test|
developer.*test" METHODOLOGY.md workflows/principles.md` -> empty). tests/ already holds
developer-written pytest files, so the NEW test file stays inside this change's allowlist
(Target File 2: brief names tests/test_pre_commit_hook_interpreter.py; spec item list
names tests/test_precommit_hook_interpreter.py — used the SPEC's spelling since the spec
wins on disagreement).

ITEM 1 - resolve venv first, probe not assume: DONE.
  The hook now iterates `"${REPO_ROOT}/.venv/bin/python"` then `python3`, selecting the
  first candidate that passes `"$cand" -c 'import yaml'`; the venv candidate is skipped
  unless `[[ -x ... ]]` (probe, never unconditional). Fresh-clone (no .venv) falls to
  `python3` if it has yaml, else blocks per item 2.

ITEM 2 - block when no interpreter has yaml: DONE, exit 2, verbatim item-3 diagnostic.
  The guard runs INSIDE the `[[ -f scripts/veritas_gate.py ]]` branch and `exit 2`s — it
  does NOT fall through to the weaker embedded fallback gate (which never checks
  policy-lock / protected paths / secrets).

ITEM 3 - identical behaviour when the interpreter resolves: DONE.
  Same `"--verify-diff --verify-metadata --staged --role ${VERITAS_ROLE:-auto}"` args,
  same PASS/FAIL lines; only `$python` replaced `$python3`. Verified by (B) below.

ITEM 4 - class fix, one site: DONE, only .githooks/pre-commit:31 changed. Verified the
  spec's item-4 claim: `grep -ln 'import yaml' scripts/*.py` -> only scripts/veritas_gate.py;
  the scripts/*.sh heredoc callers do not import yaml (not re-measured here; spec measured).

COMMAND (A) - OLD failing command, agent-like PATH (yaml-less python3 first):
  $ env -i PATH="/home/zoltan/.hermes/tools/python-3.14.7+20260901-linux-x64/bin:/usr/bin:/bin" HOME="$HOME" sh -c 'cd /home/zoltan/receipts-lens && python3 scripts/veritas_gate.py --verify-diff --verify-metadata --staged --role auto'
  Traceback (most recent call last):
    File "/home/zoltan/receipts-lens/scripts/veritas_gate.py", line 28, in <module>
      import yaml
  ModuleNotFoundError: No module named 'yaml'
  exit=1
  (Also: bare `python3 -c 'import yaml'` with that interpreter -> same ModuleNotFoundError, exit=1.)

COMMAND (B) - after fix, venv present, agent-like PATH -> PASS, exit 0:
  $ env -i PATH="/home/zoltan/.hermes/tools/python-3.14.7+20260901-linux-x64/bin:/usr/bin:/bin" HOME="$HOME" bash .githooks/pre-commit
  >> [VERITAS GATE] Verifying git diff (role mode: implementer)...
  [INFO] No modified files detected in diff.
  >> [VERITAS GATE] Verifying structured test metadata...
  [INFO] No Python test files modified.
  [OK] VERITAS Gate Check PASSED. Execution permitted.
  veritas pre-commit: PASS (runner staged diff + metadata)
  exit=0

COMMAND (C) - fail-closed, venv hidden, yaml-less PATH -> diagnostic + exit 2, venv restored:
  $ env -i PATH=".../python-3.14.7.../bin:/usr/bin:/bin" HOME="$HOME" bash -c 'mv .venv/bin/python .venv/bin/python.hidden; .githooks/pre-commit 2>&1; rc=$?; mv .venv/bin/python.hidden .venv/bin/python; echo "exit=$rc"'
  veritas pre-commit FAIL: no interpreter with the 'yaml' module found.
  veritas pre-commit FAIL: tried: /home/zoltan/receipts-lens/.venv/bin/python, python3
  veritas pre-commit FAIL: fix with: python3 -m venv .venv && .venv/bin/pip install pyyaml
  veritas pre-commit FAIL: refusing to run the gate under an interpreter it cannot import; run with
  veritas pre-commit FAIL: 'git commit --no-verify' ONLY if CI is your gate (see hook header).
  exit=2
  (post-check: `ls -l .venv/bin/python` -> symlink -> python3.11 present; no .venv/bin/python.hidden left.)

COMMAND (D) - targeted test file RED pre-fix / GREEN post-fix:
  RED (hook stashed to pre-fix, `git stash push -- .githooks/pre-commit`):
    $ .venv/bin/python -m pytest tests/test_precommit_hook_interpreter.py -v
    FAILED test_hook_passes_with_venv_on_yaml_less_path
    FAILED test_hook_blocks_fail_closed_when_no_interpreter_has_yaml
      (pre-fix hook exits 1 with ModuleNotFoundError instead of 0 / 2)
    2 failed in 0.99s
  GREEN (fix restored via `git stash pop`):
    $ .venv/bin/python -m pytest tests/test_precommit_hook_interpreter.py -v
    tests/test_precommit_hook_interpreter.py ..   [100%]
    2 passed in 1.02s

COMMIT: <sha filled after commit>
WORKING TREE: `git status --short` shows only allowlisted paths + pre-existing dirty audit files (named, not staged).
DIFF STAT: .githooks/pre-commit (+22/-2) + tests/test_precommit_hook_interpreter.py (new). Nothing else touched.

TIME USED: ~14 minutes
