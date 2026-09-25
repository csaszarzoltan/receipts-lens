# Traceability Gap — VERITAS gate 10 is declarative, not enforced

**Date:** 2026-09-25
**Scope:** ZOO-18 (QA fix) — the false `generated_traceability` achievement claim and the
unsatisfiable `require_100_percent_requirement_coverage` flag.
**Measured at:** `e4e9a82` (this is the commit the figures below describe)
**Status:** documentation fix landed. The underlying gap is **still open** (see §5).

---

## 1. What was false, and how we know

`.ai/project-profile.yaml` listed `generated_traceability` under
`adoption.achieved_controls`. "Achieved" in VERITAS means *a deterministic,
re-runnable runner artifact proves it*. Nothing does:

```
$ git grep -l traceability HEAD -- tests/ scripts/ .github/
(no output)
```

The only traceability-aware code in the repo is
`.agent-pipeline/03_e2e_suites/test_traceability_audit.py`. It is a **read-only
regex audit** over the `.agent-pipeline` SPEC/E2E manifest — it opens spec and
suite files and asserts that traced REQ/AC ids match the specs. It writes no
artifact, and it is not wired into `.github/workflows/veritas.yml`.

So gate 10's `require_runner_generated_traceability: true` describes a runner
that does not exist. The check is unsatisfiable, and therefore unsupported.

**The claim was false, and no gate could have caught it.** Nothing reads
`achieved_controls`; a false entry there is undetectable by construction.

## 2. Coverage: the number behind `require_100_percent_requirement_coverage`

Re-measured with `scripts/count_traceability_coverage.py` (committed-tree scope,
same marker regex as `verify_test_metadata()`):

| Metric | Value |
| --- | --- |
| Test files | 85 |
| Test functions | 1388 |
| With all three markers (`test_id`, `requirements`, `scenario`) | **31 (2.2%)** |
| Files with at least one non-compliant test | **82** |
| Files fully compliant | 3 |

Real coverage is ~2.2%, not 100%. The flag says 100%.

These counts describe the **committed tree at `e4e9a82`**, not the working
tree. Later commits in this repo add marker-complete tests and the number has
already risen: at `8162cc9` it is 34/1391 (2.4%). That is progress, and it is
also exactly why the figure must be tied to a commit. A number pinned in
`.ai/project-profile.yaml` that is measured against whatever `HEAD` happened to
be changes under the reader's feet — and, in a shared workspace, mid-test.
Re-measure after test changes land:

```bash
python scripts/count_traceability_coverage.py --ref <commit> --json
```

## 3. Why the gate cannot see it (the delta-scope blindness)

`verify_test_metadata()` (`scripts/veritas_gate.py` L432-449) only inspects test
files **present in the git diff**:

```python
test_files = [f for f in files if f.startswith(("tests/", ...)) and f.endswith(".py")]
if not test_files:
    print("[INFO] No Python test files modified.")
    return True          # <-- early exit: PASS with zero coverage
```

The 82 non-compliant files predate the policy and are never in a diff, so the
gate returns PASS while 97.6% of the suite is untraceable. This is not a bug in
the gate's intent — it is the *delta-scoped* design working as written. The
defect is that gate 10's config **reads as an absolute claim** while its only
implementation is **relative**. A boolean cannot express that difference; that
is why the flags are now labelled as targets and a `measured` block sits beside
them.

`verify_test_metadata()` is also not reached on every gate path — `--check-policies`
and `--run-suite` do not call it — so the "100% coverage" claim was never
exercised by any CI job.

## 4. Why nothing caught it (the 82 files are invisible)

Three compounding reasons, each sufficient on its own to hide the drift:

1. **Delta-scoped enforcement.** Only files in the current diff are checked
   (above). Pre-existing non-compliance is never revisited.
2. **No repo-wide mode.** There is no `verify_test_metadata` flag that sweeps
   the whole suite. `scripts/count_traceability_coverage.py` (added by this
   ticket) is the first tool that can.
3. **The metadata policy is opt-in by file age.** `traceability_policy.mode` is
   `migration` and `structured_metadata_required_for_new_tests: true` — meaning
   markers are required only on *new* tests. Nothing tracks the migration's
   completion, so 82 files can sit half-migrated indefinitely and the profile
   can still be (and was) written to look complete.

## 5. What is still open (not fixed here, by design)

- **No traceability runner exists.** Gate 10 remains unsatisfiable until one is
  built. ZOO-18 explicitly excludes implementing it (separate feature ticket).
- **The 82 non-compliant files are unchanged.** ZOO-18 forbids touching them.
  They remain the migration's outstanding work.
- **The migration has no completion criterion.** `traceability_policy` has no
  `target_percent` or `deadline`; the profile now records the measured 2.4% so
  the gap is visible, but nothing will fail while the number is low.
- **`control_evidence` for two controls is `unverified`.**
  `targeted_and_full_regression` and `context_fitness_enforcement` were not
  audited in this pass — this ticket audited traceability only. They remain
  `achieved_controls` on prior evidence; the profile now marks them
  `unverified` so a reader knows they were not re-proven here. A follow-up
  audit should confirm or move them.

## 6. Reproducing this

```bash
python scripts/count_traceability_coverage.py --ref e4e9a82   # the numbers above
python scripts/count_traceability_coverage.py --ref HEAD --json  # machine-readable
python scripts/count_traceability_coverage.py --list-files
python scripts/count_traceability_coverage.py --include-worktree   # in-flight work
```

By default the script reads the **committed tree** (`HEAD`) via `git ls-tree` /
`git show`, not the index and not the working tree. A shared workspace can
carry files that another agent has staged but not committed, and an index-based
count would fold another run's in-flight work into a figure pinned in
`.ai/project-profile.yaml`. Work-tree-only files are listed separately and never
folded into the headline number.

The classification mirrors `verify_test_metadata()` deliberately (non-empty
string-literal marker arguments; only the contiguous `@` decorator block above
`def test_*`), so the two agree on what "compliant" means. It is a static
textual measurement: it cannot verify a marker points at a real requirement,
and it does not resolve parameterized tests.

## 7. The rule this enforces

A control belongs in `achieved_controls` only when a deterministic, re-runnable
runner artifact proves it. A documented intent, a CI key, or a test that could
pass vacuously is not evidence. A configuration boolean states a **target**; it
is not a measurement of the current state.
