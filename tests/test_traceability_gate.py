"""ZOO-21: gate 10 must CONSUME a runner-generated traceability artifact.

ZOO-18 closed a documentation gap — it proved that gate 10's
``require_runner_generated_traceability: true`` was an unsatisfiable claim,
because no code in the repo emitted a traceability artifact. ZOO-21 closes the
gap itself. These tests pin the four properties that make that real rather than
a new documentation claim:

1. **The runner exists and writes an artifact.** Without it, gate 10 has
   nothing to read and is unsatisfiable again — the exact ZOO-18 bug.
2. **The gate reads and verifies that artifact.** Not "declares" — reads. A gate
   that ignores the artifact would pass identically whether or not it existed.
3. **The gate FAILS on a regression.** The check that matters most. Gate 10 is
   only honest if removing a marker breaks the build, because
   ``verify_test_metadata()`` is delta-scoped and will not see it.
4. **The artifact cannot drift from reality.** ``--check`` re-derives the report
   at the commit the artifact records, so a hand-edited figure is rejected.

Every test asserts a real file on disk or a real subprocess exit code. None
asserts that a mock was called, and none can pass vacuously: each fails loudly
if the traceability mechanism is removed or neutered.

A note on what is deliberately NOT tested here: that 100% marker coverage is
achieved. It is not — it is 4.3% — and the migration of the 134 remaining files
is separate, out-of-scope work. These tests pin the enforcement that makes that
gap visible, not the gap's closure.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "traceability_runner.py"
GATE = ROOT / "scripts" / "veritas_gate.py"
ARTIFACT = ROOT / ".agent-pipeline" / "audit" / "traceability.json"
PROFILE = ROOT / ".ai" / "project-profile.yaml"
GATES = ROOT / ".ai" / "quality-gates.yaml"


def _run(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: PLW1510 - callers assert on returncode
        [sys.executable, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=180,
    )


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig"))


# --- 1. the runner exists and produces an artifact --------------------------


@pytest.mark.test_id("TEST-RL-V02-030")
@pytest.mark.requirements("FEAT-RL-V02-REQ-030")
@pytest.mark.scenario("AC-RL-V02-30")
def test_runner_is_committed_and_writes_an_artifact() -> None:
    """ZOO-21 A-1: something must actually emit the artifact.

    REGRESSION: this is the ZOO-18 finding verbatim. If the runner is deleted,
    gate 10's `require_runner_generated_traceability: true` becomes
    unsatisfiable again and the claim becomes false a second time.
    """
    assert RUNNER.is_file(), f"traceability runner missing: {RUNNER}"
    proc = _run(str(RUNNER), "--json")
    assert proc.returncode == 0, f"runner failed: {proc.stderr}"
    assert ARTIFACT.is_file(), f"runner did not write {ARTIFACT}"
    report = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert report["test_functions_total"] > 0, "artifact measured no tests at all"
    assert report["generated_by"] == "scripts/traceability_runner.py"
    assert report["commit"], "artifact does not record the commit it was generated from"


@pytest.mark.test_id("TEST-RL-V02-031")
@pytest.mark.requirements("FEAT-RL-V02-REQ-031")
@pytest.mark.scenario("AC-RL-V02-31")
def test_runner_scans_both_trees_the_gate_enforces() -> None:
    """ZOO-21 A-2: the measurement must cover what the gate actually scans.

    `verify_test_metadata()` has always scanned `tests/` AND
    `.agent-pipeline/03_e2e_suites/`. The only repo-wide measurement before
    this ticket looked at `tests/` alone, so 416 e2e test functions were
    invisible to it — the same delta-scope blindness one level up.
    """
    report = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert set(report["test_trees_scanned"]) == {
        "tests",
        ".agent-pipeline/03_e2e_suites",
    }
    trees = report["by_test_tree"]
    assert trees["tests"]["test_functions"] > 0, "tests/ was not measured"
    assert trees[".agent-pipeline"]["test_functions"] > 0, "e2e suite was not measured"
    assert report["test_functions_total"] == sum(
        t["test_functions"] for t in trees.values()
    )


# --- 2. the gate actually reads the artifact --------------------------------


@pytest.mark.test_id("TEST-RL-V02-032")
@pytest.mark.requirements("FEAT-RL-V02-REQ-032")
@pytest.mark.scenario("AC-RL-V02-32")
def test_gate_10_verifies_the_artifact() -> None:
    """ZOO-21 A-3: the gate must READ the artifact, not merely declare it.

    A gate that only declared the requirement would return the same result
    whether the runner existed or not. This asserts the read actually happens:
    deleting the artifact must break the gate.
    """
    assert GATE.is_file()
    source = GATE.read_text(encoding="utf-8")
    assert "verify_traceability" in source, "gate has no traceability check function"
    assert "traceability.json" in source, "gate never names the artifact it reads"

    # Behavioural proof: with the artifact gone, the gate must fail.
    artifact_backup = ARTIFACT.read_text(encoding="utf-8")
    try:
        ARTIFACT.unlink()
        proc = _run(str(GATE), "--verify-traceability")
        assert proc.returncode != 0, (
            "gate passed with the traceability artifact deleted — it is not "
            "reading it"
        )
        assert "artifact" in (proc.stdout + proc.stderr).lower()
    finally:
        ARTIFACT.write_text(artifact_backup, encoding="utf-8")


@pytest.mark.test_id("TEST-RL-V02-033")
@pytest.mark.requirements("FEAT-RL-V02-REQ-033")
@pytest.mark.scenario("AC-RL-V02-33")
def test_gate_rejects_a_hand_edited_artifact() -> None:
    """ZOO-21 A-4: the artifact must not be forgeable by editing it.

    A figure anyone can type into a JSON file is not evidence. `--check`
    re-derives the report at the commit the artifact itself records, so an
    inflated number is caught even when the real suite is unchanged.
    """
    backup = ARTIFACT.read_text(encoding="utf-8")
    try:
        report = json.loads(backup)
        report["functions_with_all_three_markers"] = 1853
        report["compliant_percent"] = 100.0
        ARTIFACT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

        proc = _run(str(RUNNER), "--check")
        assert proc.returncode != 0, (
            "a hand-edited artifact claiming 100% passed --check; the check "
            "must re-derive the measurement, not trust the file"
        )
        gate = _run(str(GATE), "--verify-traceability")
        assert gate.returncode != 0, "the gate accepted a hand-edited artifact"
    finally:
        ARTIFACT.write_text(backup, encoding="utf-8")


# --- 3. the gate FAILS on a real regression ---------------------------------


@pytest.mark.test_id("TEST-RL-V02-034")
@pytest.mark.requirements("FEAT-RL-V02-REQ-034")
@pytest.mark.scenario("AC-RL-V02-34")
def test_gate_fails_when_a_marker_is_removed() -> None:
    """ZOO-21 A-5 — the load-bearing test: the gate must BITE.

    REGRESSION FOUND WHILE BUILDING THIS: the first implementation compared a
    rounded percentage against a floor. Removing one of 80 compliant tests
    moves coverage from 4.3% to 4.3% — the ratchet sailed straight past a real
    regression, and the gate passed a marker deletion in the very file being
    edited. `verify_test_metadata()` cannot see it either: it is delta-scoped,
    and it returned PASS because the file's other markers were present.

    So enforcement is counted in TESTS, not percent: live compliant count is
    compared against the recorded count, and a loss fails the gate. This test
    is the proof that it does.
    """
    target = ROOT / "tests" / "test_profile_honesty.py"
    original = target.read_text(encoding="utf-8")
    # -051 is the id carried by test_profile_honesty.py::test_generated_
    # traceability_not_claimed_as_achieved. It must be an id that exists in the
    # CURRENT tree: the point of this test is that the gate bites on a marker
    # that IS there, so a phantom id here would make it pass vacuously.
    marker = '@pytest.mark.test_id("TEST-RL-V02-051")\n'
    assert marker in original, (
        "the fixture marker this test removes is gone; update the test rather "
        "than letting it pass vacuously"
    )
    try:
        target.write_text(original.replace(marker, "", 1), encoding="utf-8")
        proc = _run(str(GATE), "--verify-traceability")
        assert proc.returncode != 0, (
            "gate PASSED after a marker was removed from a compliant test — the "
            "regression check does not bite"
        )
        output = proc.stdout + proc.stderr
        assert "REGRESS" in output.upper() or "lost" in output.lower(), (
            f"gate failed without naming the lost marker:\n{output[-800:]}"
        )
    finally:
        target.write_text(original, encoding="utf-8")

    # And it must return to green once the marker is restored, or the gate is
    # simply broken rather than strict.
    green = _run(str(GATE), "--verify-traceability")
    assert green.returncode == 0, (
        f"gate still failing after the marker was restored:\n{green.stdout[-800:]}"
    )


# --- 4. the policy is measurable, not decorative ----------------------------


@pytest.mark.test_id("TEST-RL-V02-035")
@pytest.mark.requirements("FEAT-RL-V02-REQ-035")
@pytest.mark.scenario("AC-RL-V02-35")
def test_policy_declares_a_real_threshold() -> None:
    """ZOO-21 A-6: the 100% expectation must have a criterion attached.

    Before this, `traceability_policy` had no target_percent and no deadline,
    so nothing could ever fail and the number was free to stay low forever.
    """
    policy = _yaml(PROFILE)["traceability_policy"]
    assert "target_percent" in policy, (
        "traceability_policy has no target_percent, so the 100% expectation "
        "still has no pass/fail criterion"
    )
    assert float(policy["target_percent"]) == 100.0
    assert policy.get("coverage_enforcement") in {"ratchet", "fail_below_target"}, (
        "coverage_enforcement must name the enforcement regime in force"
    )
    if policy["coverage_enforcement"] == "ratchet":
        assert "enforcement_floor_percent" in policy, (
            "ratchet mode with no floor enforces nothing"
        )
        assert float(policy["enforcement_floor_percent"]) <= 100.0


@pytest.mark.test_id("TEST-RL-V02-036")
@pytest.mark.requirements("FEAT-RL-V02-REQ-036")
@pytest.mark.scenario("AC-RL-V02-36")
def test_gate_records_what_it_actually_enforces() -> None:
    """ZOO-21 A-7: `not_enforced` must not hide what IS enforced.

    Gate 10 now runs, but the 100% target is still not enforced. Those are two
    different facts, and collapsing them into one word is how the ZOO-18
    overclaim came about. The config must record both.
    """
    gate = _yaml(GATES)["gates"]["10_traceability_gate"]
    assert gate["enforcement_status"] == "not_enforced"
    assert gate["measured"]["runner_generated_traceability"] == "present"
    enforced = gate.get("enforced_now")
    assert enforced, (
        "the gate enforces real checks; `enforced_now` must list them so a "
        "reader is not told, flatly, that nothing is enforced"
    )
    assert "traceability_artifact_present" in enforced
    assert "no_marker_lost_versus_recorded" in enforced

    # The measured block must describe a real, re-derivable state.
    measured = gate["measured"]["requirement_coverage"]
    report = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert measured["total"] == report["test_functions_total"], (
        "gate 10's measured total disagrees with the committed artifact"
    )
    assert measured["compliant"] == report["functions_with_all_three_markers"]


@pytest.mark.test_id("TEST-RL-V02-037")
@pytest.mark.requirements("FEAT-RL-V02-REQ-037")
@pytest.mark.scenario("AC-RL-V02-37")
def test_measured_coverage_is_not_claimed_as_full() -> None:
    """ZOO-21 A-8: adding an artifact must not become a new overclaim.

    The artifact exists and the gate runs — the tempting next step is to write
    `require_100_percent_requirement_coverage: true` as if it were satisfied.
    It is 4.3%. The 100% remains a target, and this fails if the config ever
    quietly presents it as met.
    """
    report = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert report["compliant_percent"] != 100.0, (
        "100% marker coverage is not the recorded state; the 134 outstanding "
        "files are the migration's work, not a completed claim"
    )
    gate_measured = _yaml(GATES)["gates"]["10_traceability_gate"]["measured"][
        "requirement_coverage"
    ]
    assert gate_measured["percent"] != "100"
    assert gate_measured["compliant"] < gate_measured["total"]


@pytest.mark.test_id("TEST-RL-V02-038")
@pytest.mark.requirements("FEAT-RL-V02-REQ-038")
@pytest.mark.scenario("AC-RL-V02-38")
def test_gate_runs_on_check_all() -> None:
    """ZOO-21 A-9: the coverage target must be exercised, not just declared.

    `verify_test_metadata()` is not reached on every gate path — the ZOO-18
    audit noted --check-policies and --run-suite never call it, so the "100%"
    claim was never exercised by any CI job. Gate 10 must be on the path CI
    actually runs.
    """
    proc = _run(str(GATE), "--help")
    assert proc.returncode == 0
    assert "--verify-traceability" in proc.stdout
    source = GATE.read_text(encoding="utf-8")
    assert "if args.verify_traceability or args.check_all:" in source, (
        "gate 10 is not wired into --check-all, so CI would never run it"
    )
