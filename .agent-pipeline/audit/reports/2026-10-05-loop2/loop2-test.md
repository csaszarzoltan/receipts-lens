# loop2-test — regression gate for the pre-commit venv interpreter fix (SPEC-001)

```
dispatch:  test_author brief (loop2, item 6D / SPEC-001)
agent:     test-author
repo:      /home/zoltan/receipts-lens @ 064f81a
brief:     sha256:not attempted (no brief file was supplied; the task text arrived inline)
verdict:   none - first pass
status:    DONE — test file written, RED+GREEN proven with pasted output, committed as 064f81a
```

## What was delivered

`tests/test_precommit_hook_interpreter.py` (5 tests, ~320 lines). Each test:

1. `test_hook_passes_using_repo_venv_when_path_python3_lacks_yaml` — venv present,
   yaml-less `python3` first on PATH → exit 0, PASS printed, no ModuleNotFoundError.
2. `test_hook_fails_closed_and_names_candidates_when_no_interpreter_has_yaml` —
   no `.venv`, yaml-less `python3` → exit 2, diagnostic names both candidates, no PASS.
3. `test_hook_passes_same_gate_flags_as_before` — the exact argv
   `--verify-diff --verify-metadata --staged --role auto` is preserved.
4. `test_veritas_role_env_overrides_default_role` — `VERITAS_ROLE=test_author` is forwarded.
5. `test_venv_untouched` — the real repo `.venv/bin/python` still exists, same size.

Design decisions worth noting:

- Tests 3–4 overwrite `scripts/veritas_gate.py` **inside the temp repo** with a recorder
  script. This is not mocking the boundary: the real hook still runs under bash, resolves
  its own repo root, selects an interpreter by probing `import yaml`, and really executes
  that script — a broken invocation would still fail the test.
- The temp venv with yaml is built from `sys.executable` (same CPython ABI as the runner)
  by copying the `yaml` / `_yaml` / `pyyaml-*.dist-info` trees; the yaml-less venv is a
  plain `--without-pip` venv (verified: `import yaml` fails). No network, no pip.
- The marker style (`@pytest.mark.test_id/requirements/scenario`) matches
  `tests/test_veritas_gate.py`; scenarios carry the AC text, e.g.
  `AC-RL-V02-10 … (pre-fix: exit 1, ModuleNotFoundError)`.

## (A) RED on the pre-fix hook — pasted output

Pre-fix hook installed via `git show HEAD~1:.githooks/pre-commit > .githooks/pre-commit`
(confirmed: line 31 is the bare `if python3 "$runner" ...` call, no venv probe).
Command: `.venv/bin/python -m pytest tests/test_precommit_hook_interpreter.py -q`

```
tests/test_precommit_hook_interpreter.py:230: AssertionError
=========================== short test summary info ============================
FAILED tests/test_precommit_hook_interpreter.py::test_hook_passes_using_repo_venv_when_path_python3_lacks_yaml
FAILED tests/test_precommit_hook_interpreter.py::test_hook_fails_closed_and_names_candidates_when_no_interpreter_has_yaml
```

Excerpt of the fail-closed assertion failure (scenario 2), showing the pre-fix behaviour:

```
E       AssertionError: no yaml-capable interpreter must fail CLOSED with exit 2, got 1
E         stdout:
E         stderr: Traceback (most recent call last):
E           File ".../repo/scripts/veritas_gate.py", line 28, in <module>
E             import yaml
E         ModuleNotFoundError: No module named 'yaml'
E         veritas pre-commit FAIL: runner staged gate blokkolt (reszletek fent)
```

So on the pre-fix hook: scenario 1 exits 1 with ModuleNotFoundError (expected 0/PASS);
scenario 2 exits 1 with no diagnostic (expected exit 2 naming candidates).
Scenarios 3–5 pass on both hooks — 3/4 pass pre-fix only because the pre-fix hook's bare
`python3` *is* yaml-less fixture's `-less` no, they pass pre-fix because the bare-python3
call still invokes the recorder; they pin flag stability, not the fix. The gate's two
load-bearing tests (1, 2) both FAIL pre-fix. The fixed hook was restored afterwards
(`cp /tmp/fixed-pre-commit.bak .githooks/pre-commit`; `git diff --stat` clean, "hook restored").

## (B) GREEN on the fixed hook — pasted output

Command: `.venv/bin/python -m pytest tests/test_precommit_hook_interpreter.py` (fixed hook in place)

```
.....                                                                    [100%]
5 passed in 3.35s
```

## Commit

- SHA: `064f81a` — `test(hooks): regression gate for pre-commit venv interpreter resolution`
- `git show --name-status --format='' HEAD` → exactly one path:
  `A tests/test_precommit_hook_interpreter.py`
- Convention: `git log` shows feat/test/fix/docs prefixes; `test(scope):` matches
  (`test(alerts)` exists in history).
- The pre-commit hook itself ran on this commit and PASSED
  (`veritas pre-commit: PASS (runner staged diff + metadata)`), tests-only diff accepted.
- Pre-existing dirty paths (`.agent-pipeline/audit/traceability.json`,
  `.agent-pipeline/audit/veritas_audit.jsonl`) were left unstaged and uncommitted.
- The report copy at this path (`loop2-test.md`) is intentionally NOT committed with the
  test file: the hook's staged-mode checks apply to the index blob, and a reports/**
  addition is outside the `tests/**`-only gate the brief required. Durable copy stays
  here in the repo for the record; commit `064f81a` holds the test alone.
- Never pushed (orchestrator's decision).

## Items from the brief, each reported

1. Gate FAILS pre-fix / PASSES fixed — YES, proven above (2 RED, 5 GREEN).
2. Assertion 1 (venv + yaml-less PATH → exit 0 + PASS) — YES.
3. Assertion 2 (no yaml anywhere → exit 2 + named candidates) — YES.
4. Assertion 3 (same flags `--verify-diff --verify-metadata --staged --role ${VERITAS_ROLE:-auto}`) — YES, argv asserted verbatim (tests 3–4).
5. Restore anything moved — YES: pre-fix hook swapped back to the fixed revision, verified via `git diff --stat` (clean).
6. Markers matching `tests/test_veritas_gate.py` — YES, three markers per test.
7. Commit with explicit-path staging only, no `--no-verify` — YES; the hook ran and passed on the commit itself.
8. Report to both paths, non-empty — YES (this file + `/home/zoltan/.hermes/cache/scratch/dispatch-log/loop2-test.out`, same content).

TIME USED: ~9 minutes.
