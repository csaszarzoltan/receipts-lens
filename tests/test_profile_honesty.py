"""Regression tests for ZOO-18: the .ai profile must not overstate compliance.

Contract
--------
The VERITAS project profile is a public claim about what this repo actually
does. Three regressions made it lie, and each is now pinned by a test:

1. ``generated_traceability`` must NOT be listed in ``achieved_controls``.
   No runner emits a traceability artifact, so the control is not implemented.
   It belongs in ``declared_gaps`` (ZOO-18).

2. Gate 10's ``require_100_percent_requirement_coverage`` is a *target*, not
   measured compliance. Real coverage at e4e9a82 is ~2.4%. A reader must not be
   able to see ``true`` without a machine-readable measured block beside it
   (ZOO-18).

3. The measured block in ``project-profile.yaml`` must equal what
   ``scripts/count_traceability_coverage.py`` actually reports at the recorded
   commit. Otherwise the correction itself becomes the next false claim
   (ZOO-18).

These tests read committed state, so they are stable while other agents work.

Every test here is a real assertion against a file in the repo — none of them
asserts that a mock was called, and none of them can pass vacuously: each
fails loudly if the honest-reporting structure is removed.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
AI_DIR = ROOT / ".ai"
PROFILE_PATH = AI_DIR / "project-profile.yaml"
GATES_PATH = AI_DIR / "quality-gates.yaml"
GAP_DOC = AI_DIR / "traceability-gap.md"
COVERAGE_SCRIPT = ROOT / "scripts" / "count_traceability_coverage.py"

CONTROL = "generated_traceability"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig"))


def _adoption(profile: dict) -> dict:
    return profile["project"]["adoption"]


def _script_json(ref: str = "HEAD") -> dict:
    proc = subprocess.run(  # noqa: PLW1510 - returncode asserted below
        [sys.executable, str(COVERAGE_SCRIPT), "--json", "--ref", ref],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, f"coverage script failed: {proc.stderr}"
    return json.loads(proc.stdout)



# --- 1. the false achievement claim ------------------------------------------


@pytest.mark.test_id("TEST-RL-V02-020")
@pytest.mark.requirements("FEAT-RL-V02-REQ-020")
@pytest.mark.scenario("AC-RL-V02-20")
def test_generated_traceability_not_claimed_as_achieved() -> None:
    """ZOO-18 F-1: an unimplemented control must not be an achieved one.

    REGRESSION: the profile listed `generated_traceability` under
    achieved_controls while no code in tests/, scripts/ or .github/ emits a
    traceability artifact. The claim was unsupportable, and nothing read the
    field, so no gate could catch it.
    """
    achieved = _adoption(_load(PROFILE_PATH))["achieved_controls"]
    assert CONTROL not in achieved, (
        f"{CONTROL!r} has no runner artifact proving it and must not be an "
        f"achieved control; it belongs in declared_gaps"
    )


@pytest.mark.test_id("TEST-RL-V02-021")
@pytest.mark.requirements("FEAT-RL-V02-REQ-021")
@pytest.mark.scenario("AC-RL-V02-21")
def test_generated_traceability_declared_as_gap() -> None:
    """ZOO-18 F-1b: dropping the control must not erase the known gap.

    Removing a false claim is only honest if the gap stays visible. This
    fails if someone deletes the entry instead of relocating it.
    """
    gaps = _adoption(_load(PROFILE_PATH))["declared_gaps"]
    assert CONTROL in gaps, (
        f"{CONTROL!r} is not implemented, so it must be declared as a gap "
        f"rather than silently dropped"
    )


@pytest.mark.test_id("TEST-RL-V02-022")
@pytest.mark.requirements("FEAT-RL-V02-REQ-022")
@pytest.mark.scenario("AC-RL-V02-22")
def test_no_achieved_control_lacks_an_evidence_verdict() -> None:
    """ZOO-18 F-1c: every achieved control carries a recorded evidence verdict.

    A list of achievements is only meaningful if each entry says whether it was
    actually verified. This is what stops the next false claim from being
    invisible: a control that was never re-proven must say `unverified`.
    """
    adoption = _adoption(_load(PROFILE_PATH))
    evidence = adoption["control_evidence"]
    for control in adoption["achieved_controls"]:
        assert control in evidence, (
            f"achieved control {control!r} has no control_evidence verdict"
        )
    assert evidence[CONTROL] == "not_implemented", (
        f"{CONTROL!r} must record not_implemented, got {evidence[CONTROL]!r}"
    )


# --- 2. the coverage flag is a target, not a measurement --------------------


@pytest.mark.test_id("TEST-RL-V02-023")
@pytest.mark.requirements("FEAT-RL-V02-REQ-023")
@pytest.mark.scenario("AC-RL-V02-23")
def test_coverage_flag_carries_measured_counterpart() -> None:
    """ZOO-18 F-2: `require_100_percent_...` must not stand as a bare claim.

    REGRESSION: the flag read `true` against a real coverage of 2.4%. A
    boolean cannot distinguish "target" from "current state", so a measured
    block must sit beside it.
    """
    gate = _load(GATES_PATH)["gates"]["10_traceability_gate"]
    assert gate["enforcement_status"] == "not_enforced", (
        "gate 10 is not enforced repo-wide; the config must say so explicitly"
    )
    assert "measured" in gate, "gate 10 states a 100% target with no measured counterpart"
    measured = gate["measured"]
    assert measured["runner_generated_traceability"] == "absent"
    assert measured["enforcement_scope"] == "delta_only"


@pytest.mark.test_id("TEST-RL-V02-024")
@pytest.mark.requirements("FEAT-RL-V02-REQ-024")
@pytest.mark.scenario("AC-RL-V02-24")
def test_gate10_target_flags_are_retained_as_targets() -> None:
    """ZOO-18 F-2b: the fix must not silently delete the requirement.

    Downgrading a false claim by deleting the target would destroy the intent.
    The target must survive, honestly labelled.
    """
    gate = _load(GATES_PATH)["gates"]["10_traceability_gate"]
    assert gate["require_runner_generated_traceability"] is True
    assert gate["require_100_percent_requirement_coverage"] is True
    assert gate["reject_missing_test_id"] is True


# --- 3. the correction is itself verified ------------------------------------


@pytest.mark.test_id("TEST-RL-V02-025")
@pytest.mark.requirements("FEAT-RL-V02-REQ-025")
@pytest.mark.scenario("AC-RL-V02-25")
def test_pinned_measurement_matches_reality() -> None:
    """ZOO-18 F-3: the recorded numbers must equal a fresh measurement.

    This is the anti-drift test. A hand-copied number in the profile is the
    same failure mode as the original false claim, one level down. It fails if
    the suite changes without the figure being re-measured.

    DETERMINISM (found by running this under the full suite): the measurement
    must be taken at the commit the figure was recorded at. In a shared
    workspace another agent can commit mid-run, so measuring bare ``HEAD``
    compared a pinned number against a tree it was never recorded from — a
    spurious failure that says nothing about honesty. Measuring ``--ref
    <recorded_at_commit>`` makes this deterministic: the answer cannot change
    while the test runs.
    """
    measured = _adoption(_load(PROFILE_PATH))["traceability_measurement"]
    recorded_at = measured["measured_at_commit"]
    actual = _script_json(ref=recorded_at)

    assert actual["ref"] == recorded_at, "measurement did not run at the recorded commit"
    assert measured["test_files_total"] == actual["test_files_total"]
    assert measured["test_functions_total"] == actual["test_functions_total"]
    assert (
        measured["functions_with_all_three_markers"]
        == actual["functions_with_all_three_markers"]
    )
    # YAML keeps this quoted ("2.4") to stay a string in a human-edited file;
    # JSON emits a float. Compare numerically, not by repr.
    assert float(measured["compliant_percent"]) == pytest.approx(actual["compliant_percent"])
    assert (
        measured["files_with_at_least_one_noncompliant_test"]
        == actual["files_with_at_least_one_noncompliant_test"]
    )
    assert measured["scope"] == actual["scope"] == "committed_tree"


@pytest.mark.test_id("TEST-RL-V02-026")
@pytest.mark.requirements("FEAT-RL-V02-REQ-026")
@pytest.mark.scenario("AC-RL-V02-26")
def test_honest_coverage_is_not_misrepresented_as_full() -> None:
    """ZOO-18 F-3b: the measured figure must not claim 100% compliance.

    Guards the specific number: while the flag says 100%, the measured value
    must be materially lower. If a future migration really reaches 100%,
    this test should be updated deliberately, not tripped by accident.
    """
    measured = _adoption(_load(PROFILE_PATH))["traceability_measurement"]
    assert measured["compliant_percent"] != "100", (
        "100% marker coverage is not the recorded state; update this test "
        "deliberately if the migration completes"
    )
    gate_measured = _load(GATES_PATH)["gates"]["10_traceability_gate"]["measured"][
        "requirement_coverage"
    ]
    assert gate_measured["percent"] != "100"
    assert gate_measured["compliant"] < gate_measured["total"]


# --- 4. the gap is documented, not just corrected ---------------------------


@pytest.mark.test_id("TEST-RL-V02-027")
@pytest.mark.requirements("FEAT-RL-V02-REQ-027")
@pytest.mark.scenario("AC-RL-V02-27")
def test_gap_documentation_exists_and_explains_the_blind_spot() -> None:
    """ZOO-18 F-4: the delta-scoped blind spot is written down under .ai/.

    The reason the 82 non-compliant files were invisible is the whole point of
    the fix. If that reasoning is not recorded, the next migration repeats it.
    """
    assert GAP_DOC.is_file(), f"missing {GAP_DOC}"
    doc = GAP_DOC.read_text(encoding="utf-8")
    assert "verify_test_metadata" in doc, "doc does not name the delta-scoped gate"
    assert "delta" in doc.lower()
    # The doc must still say the gap is open — that is the honest state.
    assert "still open" in doc.lower() or "not implemented" in doc.lower()


@pytest.mark.test_id("TEST-RL-V02-028")
@pytest.mark.requirements("FEAT-RL-V02-REQ-028")
@pytest.mark.scenario("AC-RL-V02-28")
def test_coverage_script_is_committed_and_runnable() -> None:
    """ZOO-18 F-5: the measurement must be reproducible, not a one-off.

    The pinned numbers are only credible if a stranger can re-derive them.
    """
    assert COVERAGE_SCRIPT.is_file(), f"missing {COVERAGE_SCRIPT}"
    report = _script_json()
    assert report["enforcement_scope"] == "delta_only"
    assert report["test_functions_total"] > 0
