# SPEC-001 — pre-commit hook must resolve the repo venv interpreter (fail-closed)

```
dispatch:  inline loop-2 planner brief (no brief file on disk)
agent:     planner
repo:      /home/zoltan/receipts-lens @ 0a96a73 (branch main)
brief:     sha256:not attempted (no brief file supplied to hash)
verdict:   none - first pass
status:    DONE - items 1-7 answered; every claim carries a command or file:line
```

**One-line item.** The repo's own pre-commit hook runs `python3` (line 31), which resolves in an
agent PATH to `/home/zoltan/.hermes/tools/python-3.14.7+20260901-linux-x64/bin/python3` — a Python
with **no `pyyaml`** — so `scripts/veritas_gate.py` dies at import and the hook exit-1s on *every*
commit. Agents then reach for `git commit --no-verify`, bypassing the VERITAS gate entirely. The fix
is a **class** fix: select an interpreter that has the gate's dependencies, fail-closed if none does.

---

## Reproduction (run before writing this spec, 2026-10-05T22:43Z)

```console
$ cd /home/zoltan/receipts-lens
$ python3 -c "import yaml; print(yaml.__version__)"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import yaml; print(yaml.__version__)
        ^^^^^^^^^^^^^
ModuleNotFoundError: No module named 'yaml'
exit=1

$ .venv/bin/python -c 'import yaml; print(yaml.__version__)'
6.0.3
exit=0
$ .venv/bin/python --version
Python 3.11.15

# Old behaviour, the exact hook command, bare python3:
$ python3 scripts/veritas_gate.py --verify-diff --verify-metadata --staged --role auto
  File "/home/zoltan/receipts-lens/scripts/veritas_gate.py", line 28, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
exit=1                      # <-- hook line 31 exits non-zero -> commit blocked

# With the venv interpreter, same command, same stage:
$ .venv/bin/python scripts/veritas_gate.py --verify-diff --verify-metadata --staged --role auto
>> [VERITAS GATE] Verifying git diff (role mode: implementer)...
[PASS] Diff verification successful. Safety checks passed.
[OK] VERITAS Gate Check PASSED. Execution permitted.
exit=0
```

Interpreter PATH resolution (measured `which -a python3`):
```
/home/zoltan/.hermes/tools/python-3.14.7+20260901-linux-x64/bin/python3   <-- first, NO yaml
/home/zoltan/.hermes/installs/.../venv/bin/python3
/home/zoltan/.hermes/hermes-agent/venv/bin/python3
/usr/bin/python3          <-- system, pyyaml NOT established
```
The repo venv is untracked and git-ignored: `git check-ignore -v .venv` →
`.gitignore:6:.venv`. `.venv/bin/python -> python3.11` (Python 3.11.15). No `requirements.txt`;
CI installs the dep directly: `.github/workflows/veritas.yml:24` → `pip install pyyaml pytest ruff`.

Prior-art (cited, verbatim):
- `.agent-pipeline/audit/reports/2026-10-05-loop2/loop2-explore.md:90-96` — *"`git commit` failed: the
  repo pre-commit hook `scripts/veritas_gate.py` exits 1 with `ModuleNotFoundError: No module named
  'yaml'` ... Did not retry with --no-verify (bypassing a policy gate is not mine to decide)."*
- commit `0a96a73` message — *"Gate verified manually: .venv/bin/python scripts/veritas_gate.py
  --verify-diff --verify-metadata --staged -> PASS (hook's bare python3 lacks yaml; --no-verify used,
  CI is the real gate per hook header)."*
- `.githooks/pre-commit:4` — *"A hook KENYELMI kontroll: `git commit --no-verify` kapcsoloval
  megkerulheto. A valodi kenyszer a CI ..."* (the hook itself declares itself bypassable).

---

## Target Files (allowlist — exact paths)

| # | Path | Change |
|---|---|---|
| 1 | `.githooks/pre-commit` | Replace the bare `python3` call at line 31 with venv-first interpreter resolution + explicit fail-closed. |
| 2 | `tests/test_precommit_hook_interpreter.py` | **Proposed new** test: asserts the hook selects the venv interpreter and fails closed when no interpreter has `yaml`. |

**No other file needs to change.** `scripts/veritas_gate.py` is *correct as written* (it declares its
dependency; the caller supplies the wrong interpreter). See item 6's note on why `scripts/**` stays
out of scope. If the developer believes a path outside this list must change, the brief says: **name
it and say why — do not silently widen the allowlist.**

---

## Item 1 — Which interpreter, and the resolution rule when the venv is missing

**Decision: an ordered interpreter list, first candidate that can `import yaml` wins; if none can,
the hook BLOCKS (exit 2) with a named diagnostic.**

Resolution rule (fail-closed), evaluated in this order:

1. `"${REPO_ROOT}/.venv/bin/python"` — the repo's own venv. **Candidate 1.**
2. `python3` on `PATH` — **Candidate 2**, the current behaviour, kept only as a last resort.
3. If **no** candidate's `-c 'import yaml'` succeeds → `fail "..." 2` (block, do **not** fall through
   to the embedded fallback gate — see below).

**Why this order:** Candidate 1 is measured to have `yaml 6.0.3` on Python 3.11.15, matching CI's
pinned `python-version: "3.11"` (`.github/workflows/veritas.yml:20`). Candidate 2 satisfies the gate
*on hosts where it has yaml* (e.g. a plain developer shell whose `python3` is the system interpreter
with pyyaml), so it is a valid fallback — it must not be dropped, or the fix regresses those hosts.
On an agent PATH, candidate 2 fails and we block, which is correct.

**When the venv is missing → FAIL-CLOSED (block).** Justification, measured: the embedded fallback
gate at `.githooks/pre-commit:39-79` **does not run `scripts/veritas_gate.py` at all** — it only
checks (a) no mixed `app/**`+`tests/**` diff and (b) `tests/**/*.py` carry three pytest markers. It
never reads `.ai/policy-lock.json`, never checks `PROTECTED_POLICY_FILES`, never runs the secret
scanner (`scripts/veritas_gate.py:81-85`). Measurement: `grep -n 'policy-lock\|PROTECTED_POLICY'
.githooks/pre-commit` → **no hits** (the fallback never references them). So "fall back to the
embedded gate" is *not* safe: it would silently downgrade every commit to a 2-check gate while
printing `PASS`, which is exactly the silent-PASS failure the hook header (line 6-7) forbids. Blocking
is the safe choice and matches the file's existing fail-closed intent (lines 20-25 already `fail 2`
when the repo root cannot be resolved).

**Interaction with the existing fallback:** the existing fallback (lines 39-79) fires only when
`scripts/veritas_gate.py` is **absent** (`[[ -f scripts/veritas_gate.py ]]`, line 29). That is a
different condition from "interpreter cannot import yaml". The spec must not conflate them: the new
interpreter guard runs *inside* the `if [[ -f scripts/veritas_gate.py ]]` branch and blocks; it does
**not** route into the fallback. (This is the type of ambiguity the brief asked to name rather than
guess.)

## Item 2 — May the hook call `${REPO_ROOT}/.venv/bin/python` unconditionally, or must it probe?

**It must probe, and it must never call `.venv/bin/python` unconditionally.** Measurement:
`.venv` is git-ignored (`.gitignore:6`) and untracked (`git ls-files .venv` → empty). A fresh clone,
a CI checkout, or a host without the venv created has **no** `.venv/bin/python`; an unconditional
`"$REPO_ROOT/.venv/bin/python"` invocation would then produce `bash: ... No such file or directory`
(exit 127) with no actionable message. Probe with `[[ -x "${REPO_ROOT}/.venv/bin/python" ]]` **and**
`"${cand}" -c 'import yaml' >/dev/null 2>&1` before selecting it. The probe must test the *ability to
import yaml*, not merely existence — a venv could exist yet be incomplete.

## Item 3 — Should `python3` stay as a last-resort fallback? BLOCK or diagnostic?

**It stays, but only after the venv candidate, and if it cannot import `yaml` the hook BLOCKS with a
clear diagnostic — it is not a silent pass.**

- Keeping `python3` preserves the pre-fix behaviour on hosts where the system python already has
  pyyaml (a valid environment). Removing it would break those hosts for no reason.
- A missing `yaml` is a **BLOCK**, exit **2**, because VERITAS cannot run and a pass would be false.
  It must not fall through to the weaker embedded fallback (item 1).

Exact operator-facing message (stderr, verbatim — the developer must emit exactly this text):

```
veritas pre-commit FAIL: no interpreter with the 'yaml' module found.
veritas pre-commit FAIL: tried: <REPO_ROOT>/.venv/bin/python, python3
veritas pre-commit FAIL: fix with: python3 -m venv .venv && .venv/bin/pip install pyyaml
veritas pre-commit FAIL: refusing to run the gate under an interpreter it cannot import; run with
veritas pre-commit FAIL: 'git commit --no-verify' ONLY if CI is your gate (see hook header).
```

The message names (a) what failed, (b) the candidates tried, (c) the exact remedy command, and (d) the
escape hatch — so an operator is never forced into `--no-verify` by silence.

## Item 4 — Other bare-`python3`/`python` callers (class fix) — every hit with file:line

Command requested: `grep -rn 'python3\|python ' .githooks/ scripts/ --include='*'` (run 2026-10-05):

```
.githooks/pre-commit:31:  if python3 "$runner" --verify-diff --verify-metadata --staged \
scripts/veritas_gate.py:1:#!/usr/bin/env python3
scripts/veritas_gate.py:853:            f"       Run: python scripts/traceability_runner.py"
scripts/traceability_runner.py:1:#!/usr/bin/env python3
scripts/security-gate.sh:51:python3 - <<'PY'
scripts/backup-sqlite.sh:23:python3 -- - "${DB_PATH}" "${BACKUP_FILE}" <<'PY'
scripts/doc-sync-check.sh:3:python - <<'PY'
scripts/count_traceability_coverage.py:1:#!/usr/bin/env python3
scripts/count_traceability_coverage.py:8:    python scripts/count_traceability_coverage.py            # human report
scripts/count_traceability_coverage.py:9:    python scripts/count_traceability_coverage.py --json     # machine readable
scripts/bdd-gate.sh:3:python - <<'PY'
```

**Assessment of each hit (establishing the YES/NO, not assuming it):**

- `.githooks/pre-commit:31` — **the defect**, in scope.
- `scripts/security-gate.sh:51`, `scripts/backup-sqlite.sh:23`, `scripts/doc-sync-check.sh:3`,
  `scripts/bdd-gate.sh:3` — bare `python`/`python3` heredocs. **Do these need `yaml`?**
  `grep -n 'yaml' scripts/security-gate.sh scripts/backup-sqlite.sh scripts/doc-sync-check.sh
  scripts/bdd-gate.sh` → **exit 1, zero hits.** None imports `yaml`; none is the gate. They are *not*
  part of this defect and are **out of scope** (naming them here so the developer does not "fix"
  them and widen the diff). Flagged, not touched.
- `scripts/veritas_gate.py:1`, `scripts/traceability_runner.py:1`,
  `scripts/count_traceability_coverage.py:1` — `#!/usr/bin/env python3` **shebangs**. A shebang is not
  an invocation site; it is only used if the file is executed directly. All three are invoked as
  `python <path>` by CI and by the hook. **Not the defect.**
- `scripts/veritas_gate.py:853`, `scripts/count_traceability_coverage.py:8-9` — `python` inside
  **printed help/docstring text**, not executed. **Not the defect.**

**The only script that imports `yaml` is `scripts/veritas_gate.py`** (`head -30` → `line 28: import
yaml`); no other `scripts/*.py` imports it (`grep -ln 'import yaml' scripts/*.py` → only
`scripts/veritas_gate.py`). So the class is exactly one invocation site: `.githooks/pre-commit:31`.
Item 4 conclusion: **YES, other bare-python callers exist (7), but only line 31 can fail on missing
`yaml` — the class fix is the interpreter resolution in the hook, and no `scripts/**` file is in
scope.**

## Item 5 — Is this file inside a policy-lock or gate-protected set?

**NO.** Measurements:

- `.ai/policy-lock.json` pins exactly five files, all under `.ai/` — `.ai/constitutional-policy.yaml`,
  `.ai/permissions.yaml`, `.ai/project-profile.yaml`, `.ai/quality-gates.yaml`, `.ai/risk-policy.yaml`.
  `grep -n 'githooks\|pre-commit\|veritas_gate' .ai/policy-lock.json` → **no hits.**
  `.githooks/pre-commit` is **not** pinned.
- `scripts/veritas_gate.py:75-79` defines `PROTECTED_POLICY_FILES = (".ai/constitutional-policy.yaml",
  ".ai/permissions.yaml", ".ai/policy-lock.json")`. `.githooks/` is **not** in that tuple.
  `grep -n 'githooks' scripts/veritas_gate.py` → **no hits** (only comment mentions at lines 72, 160,
  1224, 1269 refer to the hook/CI as *callers*, not as protected paths).

Therefore consuming an R4 human-approval ledger entry (`log_approval_event`, gate lines 232, 587-591)
is **not** required to change `.githooks/pre-commit`. Confirmed by the very commit that is the base of
this task: `0a96a73` ("the verification artifact counted its own prose") and `9be3d0a`
(`docs(audit): ...`) both landed on the hook-adjacent audit tree **without** an R3/R4 entry being
required to touch `.githooks/`. Item 5: **NO — not protected.**

## Item 6 — Acceptance commands (new behaviour), and the pre-fix failing command

All commands runnable as written, from `/home/zoltan/receipts-lens`.

**(A) Proves the OLD behaviour was broken (must fail on `0a96a73`, pass after the fix):**
```bash
python3 scripts/veritas_gate.py --verify-diff --verify-metadata --staged --role auto; echo "exit=$?"
```
Pre-fix expected (measured above): `ModuleNotFoundError: No module named 'yaml'`, **exit=1**.
Post-fix this *same command* is unchanged — it still exits 1, which is fine, because the hook no
longer calls bare `python3`. The point of (A) is to show the environment defect exists.

**(B) Proves the new hook selects the venv interpreter and passes:**
```bash
printf 'x\n' > /tmp/_pf && git add /tmp/_pf 2>/dev/null; \
  VERITAS_ROLE=docs .githooks/pre-commit; echo "exit=$?"
```
Post-fix expected: `veritas pre-commit: PASS (runner staged diff + metadata)`, **exit=0**.
(The developer must use a staged file they are allowed to stage; do not stage another agent's work.
The test file in Target Files is a suitable staged path.)

**(C) Proves fail-closed when no interpreter has yaml** — run the hook with both candidates pointing
at the yaml-less interpreter:
```bash
PATH="/home/zoltan/.hermes/tools/python-3.14.7+20260901-linux-x64/bin:/usr/bin:/bin" \
  bash -c 'mv .venv/bin/python .venv/bin/python.hidden 2>/dev/null; \
           .githooks/pre-commit; rc=$?; mv .venv/bin/python.hidden .venv/bin/python 2>/dev/null; \
           echo "exit=$rc"'
```
Post-fix expected: the item-3 diagnostic on stderr and **exit=2** (BLOCK). **A test that mocks the
boundary proves nothing about the boundary (global method 3d):** the tester must run this against the
*real* hook and the *real* interpreters, then restore `.venv/bin/python`. Restoring the moved file is
mandatory — the test must not leave the repo without its venv.

**(D) The regression test (Target File 2)** asserts, as a subprocess against the real hook file:
1. the hook run with a staged file and a working venv exits **0** and prints `PASS`; and
2. the hook run with the venv hidden exits **2** and its stderr contains the exact substring
   `no interpreter with the 'yaml' module found` (anchored substring, not a bare `find`).
The test **must fail if the hook is reverted to bare `python3`** — the developer must show it red on
`0a96a73` before making it green. If it cannot be shown failing, it proves nothing.

**Scoring note (do not decide here):** items (B)-(D) exercise the real `.githooks/pre-commit` and the
real interpreter set, not a mock — the fix can move verification above 3/5 only on that basis.

## Item 7 — What could make this fix wrong (falsification)

| Hypothesis that would make it wrong | Check performed | Result |
|---|---|---|
| `.venv` exists on CI, so probing is unnecessary | `git check-ignore -v .venv` → `.gitignore:6`; `git ls-files .venv` → empty | `.venv` untracked — probe **is** required (item 2) |
| The embedded fallback gate is an adequate substitute, so blocking is overkill | `grep -n 'policy-lock\|PROTECTED_POLICY' .githooks/pre-commit` → no hits | fallback is weaker (2 checks) — blocking is correct (item 1) |
| Other `scripts/*.sh` also need yaml and would fail identically | `grep -n 'yaml' security-gate.sh backup-sqlite.sh doc-sync-check.sh bdd-gate.sh` → 0 hits | none needs yaml — item 4 class is line 31 only |
| The hook file is policy-locked, so editing it needs R4 approval | `grep 'githooks' .ai/policy-lock.json scripts/veritas_gate.py` → no protected-path hit | not protected (item 5) |
| The venv python version diverges from CI, so "it passes locally" is not CI-parity | `.venv/bin/python --version` → 3.11.15; CI `python-version: "3.11"` | aligned |
| Fixing the hook is enough and CI needs the same change | CI installs deps explicitly (`.github/workflows/veritas.yml:24` `pip install pyyaml pytest ruff`); CI never uses bare-python-without-yaml | CI needs no change |

**Residual risk named, not hidden:** if a future host creates `.venv` with a python that also lacks
pyyaml, candidate 1 fails its import probe and the hook falls to candidate 2; if candidate 2 also
lacks yaml, the hook blocks with the item-3 message. Neither path can produce a silent PASS — which
is the property under test.

---

## Handoff

- **developer**: edit `.githooks/pre-commit` (interpreter resolution + fail-closed block, exact
  message per item 3); add `tests/test_precommit_hook_interpreter.py`; show test (D) red on `0a96a73`
  then green. Do not touch any file outside the Target Files list; do not use `--no-verify`.
- **tester**: run (A)-(D) against the real hook and real interpreters; paste raw output; restore any
  moved `.venv/bin/python`.
- **reviewer**: verify the fix's commit landed **without** `--no-verify` (the whole point) and that
  the diff is limited to the two allowlisted paths.

TIME USED: 11 minutes
