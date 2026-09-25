"""Quality-service contract tests: benchmark metrics, calibration and review policy.

Functions under test
--------------------
``app.quality.BenchmarkRunner`` and ``app.quality.ReviewPolicy`` -- the
deterministic OCR-quality contracts that ``scripts/tdd-gate-v3.sh`` names as
part of its primary test set.

These tests pin the properties the TDD gate relies on:

- ``BenchmarkRunner.run`` computes per-field exact-match, precision, recall,
  f1 and calibration ECE, and refuses empty input.
- ``ReviewPolicy.requires_review`` flags a low-confidence or missing field and
  clears a fully-confident one.
- ``ReviewPolicy.correct`` produces an auditable ``Correction`` and refuses
  an empty actor or empty change set.

Each test is written to fail if the quality contract regresses -- e.g. if
precision and recall are swapped, if ECE ignores confidence, or if a
low-confidence prediction stops being routed to review.
"""
from __future__ import annotations

import pytest

from app.quality import BenchmarkCase, BenchmarkRunner, ReviewPolicy


def _case(case_id: str, truth: dict, prediction: dict, confidence: dict) -> BenchmarkCase:
    return BenchmarkCase(case_id=case_id, truth=truth, prediction=prediction, confidence=confidence)


PERFECT = [
    _case("c1", {"vendor": "Alpha", "total": 10.0}, {"vendor": "Alpha", "total": 10.0},
          {"vendor": 1.0, "total": 1.0}),
    _case("c2", {"vendor": "Beta", "total": 20.0}, {"vendor": "Beta", "total": 20.0},
          {"vendor": 1.0, "total": 1.0}),
]

HALF_RIGHT = [
    _case("c1", {"vendor": "Alpha", "total": 10.0}, {"vendor": "Alpha"}, {"vendor": 1.0, "total": 1.0}),
    _case("c2", {"vendor": "Beta", "total": 20.0}, {"total": 20.0}, {"vendor": 1.0, "total": 1.0}),
]

ALL_WRONG = [
    _case("c1", {"vendor": "Alpha"}, {"vendor": "Zzz"}, {"vendor": 1.0}),
    _case("c2", {"vendor": "Beta"}, {"vendor": "Yyy"}, {"vendor": 1.0}),
]


# ---------------------------------------------------------------------------
# BenchmarkRunner
# ---------------------------------------------------------------------------


@pytest.mark.test_id("TEST-QS-001")
@pytest.mark.requirements("REQ-QS-01")
@pytest.mark.scenario("AC-QS-01")
def test_perfect_corpus_scores_perfectly():
    """A fully correct corpus scores 1.0 everywhere, including calibration."""
    report = BenchmarkRunner().run("v1", PERFECT)

    assert report.corpus_version == "v1"
    assert report.exact_match == {"total": 1.0, "vendor": 1.0}
    assert report.precision == 1.0
    assert report.recall == 1.0
    assert report.f1 == 1.0
    assert report.calibration_ece == 0.0


@pytest.mark.test_id("TEST-QS-002")
@pytest.mark.requirements("REQ-QS-01")
@pytest.mark.scenario("AC-QS-02")
def test_wrong_predictions_score_zero():
    """Predictions that never match truth cannot report recall or precision."""
    report = BenchmarkRunner().run("v1", ALL_WRONG)

    assert report.exact_match == {"vendor": 0.0}
    assert report.recall == 0.0
    assert report.f1 == 0.0


@pytest.mark.test_id("TEST-QS-003")
@pytest.mark.requirements("REQ-QS-01")
@pytest.mark.scenario("AC-QS-02")
def test_missing_prediction_lowers_recall_below_precision():
    """A field omitted from the prediction is a false negative, not a false positive."""
    report = BenchmarkRunner().run("v1", HALF_RIGHT)

    assert report.exact_match == {"total": 0.5, "vendor": 0.5}
    # Every emitted value is correct -> precision 1.0
    assert report.precision == 1.0
    # Half the truth values were never produced -> recall 0.5
    assert report.recall == 0.5
    assert report.f1 == pytest.approx(2 / 3)


@pytest.mark.test_id("TEST-QS-004")
@pytest.mark.requirements("REQ-QS-01")
@pytest.mark.scenario("AC-QS-02")
def test_precision_and_recall_are_not_swapped():
    """A corpus with false positives must show precision < recall.

    Swapping the two aggregates would leave the symmetric cases above green,
    so this is the case that distinguishes them.
    """
    # Two fields; one emitted with a wrong value, one emitted correctly, and a
    # third truth value never produced.
    cases = [
        _case("c1", {"vendor": "Alpha", "total": 10.0, "date": "2026-01-01"},
              {"vendor": "WRONG", "total": 10.0}, {"vendor": 1.0, "total": 1.0}),
    ]
    report = BenchmarkRunner().run("v1", cases)

    # emitted: 2, correct: 1 -> precision 0.5 ; truth: 3, correct: 1 -> recall 1/3
    assert report.precision == 0.5
    assert report.recall == pytest.approx(1 / 3)
    assert report.precision > report.recall


@pytest.mark.test_id("TEST-QS-005")
@pytest.mark.requirements("REQ-QS-02")
@pytest.mark.scenario("AC-QS-03")
def test_calibration_ece_penalises_overconfidence():
    """Confidently wrong answers have a worse ECE than the same answers hedged."""
    overconfident = [_case("c1", {"vendor": "Alpha"}, {"vendor": "Zzz"}, {"vendor": 1.0})]
    hedged = [_case("c1", {"vendor": "Alpha"}, {"vendor": "Zzz"}, {"vendor": 0.0})]

    assert BenchmarkRunner().run("v1", overconfident).calibration_ece == 1.0
    assert BenchmarkRunner().run("v1", hedged).calibration_ece == 0.0


@pytest.mark.test_id("TEST-QS-006")
@pytest.mark.requirements("REQ-QS-02")
@pytest.mark.scenario("AC-QS-03")
def test_run_requires_a_version_and_at_least_one_case():
    """An empty corpus is a programming error, not a zero-scoring report."""
    runner = BenchmarkRunner()

    with pytest.raises(ValueError):
        runner.run("", PERFECT)
    with pytest.raises(ValueError):
        runner.run("v1", [])


# ---------------------------------------------------------------------------
# ReviewPolicy
# ---------------------------------------------------------------------------


@pytest.mark.test_id("TEST-QS-007")
@pytest.mark.requirements("REQ-QS-03")
@pytest.mark.scenario("AC-QS-04")
def test_low_confidence_field_is_routed_to_review():
    """A field below its threshold must be flagged for human review."""
    policy = ReviewPolicy({"total": 0.9}, default=0.7)

    assert policy.requires_review({"total": 9.99}, {"total": 0.5}) is True


@pytest.mark.test_id("TEST-QS-008")
@pytest.mark.requirements("REQ-QS-03")
@pytest.mark.scenario("AC-QS-04")
def test_confident_field_is_not_routed_to_review():
    """A field at or above its threshold passes through unreviewed."""
    policy = ReviewPolicy({"total": 0.9}, default=0.7)

    assert policy.requires_review({"total": 9.99}, {"total": 0.95}) is False


@pytest.mark.test_id("TEST-QS-009")
@pytest.mark.requirements("REQ-QS-03")
@pytest.mark.scenario("AC-QS-05")
def test_missing_prediction_is_always_routed_to_review():
    """An unparsed field needs review regardless of reported confidence."""
    policy = ReviewPolicy({"total": 0.9}, default=0.7)

    assert policy.requires_review({"vendor": None}, {"vendor": 1.0}) is True


@pytest.mark.test_id("TEST-QS-010")
@pytest.mark.requirements("REQ-QS-03")
@pytest.mark.scenario("AC-QS-05")
def test_unlisted_field_falls_back_to_the_default_threshold():
    """With no explicit thresholds, every field is judged by the default alone.

    Both policies below are configured identically (no per-field thresholds) and
    differ only in ``default``; each field's verdict must track that default.
    """
    strict = ReviewPolicy({}, default=0.95)
    lenient = ReviewPolicy({}, default=0.10)

    assert strict.requires_review({"vendor": "A"}, {"vendor": 0.5}) is True
    assert lenient.requires_review({"vendor": "A"}, {"vendor": 0.5}) is False


@pytest.mark.test_id("TEST-QS-013")
@pytest.mark.requirements("REQ-QS-03")
@pytest.mark.scenario("AC-QS-05")
def test_configured_field_absent_from_prediction_is_reviewed():
    """A field the policy demands is still reviewed when the OCR omitted it.

    ``requires_review`` iterates the union of predicted and configured fields, so
    a configured-but-unparsed field is flagged even under a lenient default.
    """
    policy = ReviewPolicy({"total": 0.9}, default=0.10)

    assert policy.requires_review({"vendor": "A"}, {"vendor": 0.9}) is True


# ---------------------------------------------------------------------------
# ReviewPolicy.correct -- the audit trail
# ---------------------------------------------------------------------------


@pytest.mark.test_id("TEST-QS-011")
@pytest.mark.requirements("REQ-QS-04")
@pytest.mark.scenario("AC-QS-06")
def test_correction_preserves_the_original_prediction():
    """A correction is auditable: the pre-correction value is retained."""
    case = _case("c1", {"vendor": "Alpha"}, {"vendor": "Alfa"}, {"vendor": 0.4})
    correction = ReviewPolicy({}, default=0.7).correct(case, {"vendor": "Alpha"}, actor="u-1")

    assert correction.case_id == "c1"
    assert correction.original_prediction == {"vendor": "Alfa"}
    assert correction.corrected == {"vendor": "Alpha"}
    assert correction.actor == "u-1"
    assert correction.created_at


@pytest.mark.test_id("TEST-QS-012")
@pytest.mark.requirements("REQ-QS-04")
@pytest.mark.scenario("AC-QS-06")
def test_correction_requires_an_actor_and_a_change():
    """An unattributed or empty correction is rejected."""
    case = _case("c1", {"vendor": "Alpha"}, {"vendor": "Alfa"}, {"vendor": 0.4})
    policy = ReviewPolicy({}, default=0.7)

    with pytest.raises(ValueError):
        policy.correct(case, {"vendor": "Alpha"}, actor="")
    with pytest.raises(ValueError):
        policy.correct(case, {}, actor="u-1")
