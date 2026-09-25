"""ZOO-27 — QA regression tests for the wired pre-commit gate.

The ZOO-23 finding claimed the pre-commit gate "enforces nothing". These
tests lock in what the gate *does* enforce, so the guarantee cannot silently
regress, and they pin the gaps found during QA.

Contract covered here:
1. A clean docs-only staged change commits (the gate does not block all work).
2. A mixed ``app/`` + ``tests/`` staged change is blocked.
3. **The metadata gate must inspect the STAGED blob, not the working tree.**
   Regression for the QA-found escape: staging a marker-less test and then
   editing the working tree to add markers bypassed the gate, and CI did not
   catch it either (the committed file had no markers).
4. **A clean checkout must not report an empty, unexamined diff as PASS.**
   Regression for the QA-found structural gap: in a clean CI checkout
   ``get_git_diff_files`` returns ``[]``, and ``verify_diff`` early-returns
   True — so role isolation, R3 paths, constitutional-tamper and the secret
   scan were all unreachable on the CI path.
5. The history scan must not flag the scanner's own test fixture as a leak.

Each negative test here is a genuine failure on current ``main`` unless the
production code is fixed; that is the intended red state.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "veritas_gate.py"
HOOK = ROOT / ".githooks" / "pre-commit"
AI_DIR = ROOT / ".ai"
MANIFEST_DIR = ROOT / ".agent-pipeline" / "00_index"

SCRUB_VARS = ("VERITAS_APPROVAL", "VERITAS_HUMAN_APPROVAL", "VERITAS_ROLE")

# NOTE: fixture sources are stored comment-prefixed and uncommented on use.
# Written flush-left, the gate's own line-based ``def test_*`` regex would read
# these fixtures as real unmarked test functions and block this very commit —
# a false positive that would make the QA suite uncommittable.
_MARKED_FIXTURE = """
# import pytest
#
#
# @pytest.mark.test_id("QA-1")
# @pytest.mark.requirements("REQ-1")
# @pytest.mark.scenario("SC-1")
# def test_sample_alert_route():
#     assert True
"""

_UNMARKED_FIXTURE = """
# import pytest
#
#
# def test_sample_alert_route():
#     assert True
"""


def _source(fixture: str) -> str:
    """Uncomment a fixture so it can be written to disk as real Python."""
    return "".join(
        line.removeprefix("# ") if line.startswith("# ") else line.lstrip("#")
        for line in fixture.splitlines(keepends=True)
        if line.strip("# \n")
    )


MARKED_TEST = _source(_MARKED_FIXTURE)
UNMARKED_TEST = _source(_UNMARKED_FIXTURE)


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "GIT_CONFIG_NOSYSTEM": "1",
        "HOME": str(cwd),
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }
    return subprocess.run(  # noqa: PLW1510 - caller asserts on returncode
        ["git", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _make_repo(tmp: Path) -> Path:
    """Minimal git repo carrying the real runner and the real .githooks hook."""
    repo = tmp / "repo"
    repo.mkdir()
    assert _git(repo, "init", "-q").returncode == 0

    (repo / "scripts").mkdir()
    (repo / "scripts" / "veritas_gate.py").write_bytes(GATE.read_bytes())

    (repo / ".githooks").mkdir()
    hook = repo / ".githooks" / "pre-commit"
    hook.write_bytes(HOOK.read_bytes())
    # The exec bit must survive: git silently SKIPS a non-executable
    # pre-commit hook, which would make every assertion below vacuous.
    hook.chmod(0o755)
    assert _git(repo, "config", "core.hooksPath", ".githooks").returncode == 0

    ai = repo / ".ai"
    ai.mkdir()
    if AI_DIR.is_dir():
        for name in AI_DIR.iterdir():
            if name.is_file():
                (ai / name.name).write_bytes(name.read_bytes())

    idx = repo / ".agent-pipeline" / "00_index"
    idx.mkdir(parents=True)
    manifest_src = MANIFEST_DIR / "manifest.json"
    if manifest_src.is_file():
        (idx / "manifest.json").write_bytes(manifest_src.read_bytes())
    (repo / ".agent-pipeline" / "audit").mkdir(parents=True)

    (repo / "docs").mkdir()
    (repo / "docs" / "seed.md").write_text("seed\n", encoding="utf-8")
    (repo / "app").mkdir()
    (repo / "app" / "seed.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "__init__.py").write_text("", encoding="utf-8")

    _git(repo, "add", ".")
    # Fixture setup, not a gate assertion: the seed necessarily stages .ai/**
    # and tests/, which the implementer role denies. Bypass the hook here so
    # every assertion below exercises the gate on a clean HEAD.
    _git(repo, "commit", "-m", "init", "--allow-empty", "--no-verify")
    return repo


def _env(**overrides: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in SCRUB_VARS}
    env.update(overrides)
    return env


def _commit(repo: Path, message: str, *extra: str) -> subprocess.CompletedProcess[str]:
    return _git(repo, "commit", "-m", message, *extra)


def _git_env(repo: Path, *args: str, **env_overrides: str) -> subprocess.CompletedProcess[str]:
    """Run a git command with VERITAS_* overrides (e.g. VERITAS_ROLE)."""
    base = {
        **os.environ,
        "GIT_CONFIG_NOSYSTEM": "1",
        "HOME": str(repo),
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }
    base.update(env_overrides)
    return subprocess.run(  # noqa: PLW1510 - caller asserts on returncode
        ["git", *args],
        cwd=repo,
        env=base,
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.mark.test_id("QA-ZOO27-001")
@pytest.mark.requirements("QA-REQ-GATE-WIRES")
@pytest.mark.scenario("AC-ZOO27-DOCS-COMMIT-ALLOWED")
def test_docs_only_staged_change_commits(tmp_path: Path) -> None:
    """Positive control: the gate must not block legitimate documentation work."""
    repo = _make_repo(tmp_path)
    (repo / "docs" / "adr.md").write_text("# ADR\n", encoding="utf-8")
    assert _git(repo, "add", "docs/adr.md").returncode == 0

    before = _git(repo, "rev-parse", "HEAD").stdout.strip()
    result = _commit(repo, "docs: adr")
    after = _git(repo, "rev-parse", "HEAD").stdout.strip()

    assert result.returncode == 0, f"docs-only commit was blocked:\n{result.stdout}\n{result.stderr}"
    assert before != after, "docs-only commit produced no commit"


@pytest.mark.test_id("QA-ZOO27-002")
@pytest.mark.requirements("QA-REQ-GATE-ENFORCES")
@pytest.mark.scenario("AC-ZOO27-MIXED-DIFF-BLOCKED")
def test_mixed_app_and_tests_staged_diff_is_blocked(tmp_path: Path) -> None:
    """Negative control: the mixed-diff guard must actually block a commit."""
    repo = _make_repo(tmp_path)
    (repo / "app" / "seed.py").write_text("VALUE = 2\n", encoding="utf-8")
    (repo / "tests" / "test_seed.py").write_text(MARKED_TEST, encoding="utf-8")
    assert _git(repo, "add", "app/seed.py", "tests/test_seed.py").returncode == 0

    before = _git(repo, "rev-parse", "HEAD").stdout.strip()
    result = _commit(repo, "mixed")
    after = _git(repo, "rev-parse", "HEAD").stdout.strip()

    assert result.returncode != 0, "mixed app/+tests/ commit was ALLOWED — gate is inert"
    assert before == after, "a commit was created despite the mixed diff"


@pytest.mark.test_id("QA-ZOO27-003")
@pytest.mark.requirements("QA-REQ-METADATA-ON-STAGED-BLOB")
@pytest.mark.scenario("AC-ZOO27-STAGED-BLOB-NOT-WORKTREE")
def test_metadata_gate_inspects_staged_blob_not_working_tree(tmp_path: Path) -> None:
    """Regression: the gate must judge the content that will be committed.

    Reproduces the QA-found escape. The working tree holds a properly marked
    test, the index holds the marker-less version that would actually be
    committed. The gate must block; if it reads the working tree it passes
    and a marker-less test lands in history.

    Runs as ``test_author`` deliberately: the default ``implementer`` role
    denies ``tests/**`` outright, which would block this for an unrelated
    reason and make the assertion vacuous.
    """
    repo = _make_repo(tmp_path)

    # 1) stage the marker-less version
    (repo / "tests" / "test_staged.py").write_text(UNMARKED_TEST, encoding="utf-8")
    assert _git(repo, "add", "tests/test_staged.py").returncode == 0

    # 2) make the working tree look compliant, WITHOUT re-staging
    (repo / "tests" / "test_staged.py").write_text(MARKED_TEST, encoding="utf-8")

    # Sanity: the index really does hold the marker-less content.
    staged = _git(repo, "show", ":tests/test_staged.py").stdout
    assert "mark.test_id" not in staged, "precondition failed: index is not marker-less"

    before = _git(repo, "rev-parse", "HEAD").stdout.strip()
    result = _git_env(repo, "commit", "-m", "staged-blob-probe", VERITAS_ROLE="test_author")
    after = _git(repo, "rev-parse", "HEAD").stdout.strip()

    assert before == after, (
        "marker-less test was committed: the metadata gate read the working "
        "tree instead of the staged blob"
    )
    assert result.returncode != 0, "gate allowed a commit whose staged content lacks markers"


@pytest.mark.test_id("QA-ZOO27-004")
@pytest.mark.requirements("QA-REQ-CLEAN-CHECKOUT-NOT-VACUOUS-PASS")
@pytest.mark.scenario("AC-ZOO27-CLEAN-TREE-DIFF-CHECK")
def test_diff_checks_are_not_vacuous_on_a_clean_checkout(tmp_path: Path) -> None:
    """Regression: a clean tree must not short-circuit the diff checks.

    On the CI path the runner starts from a clean checkout, so
    ``get_git_diff_files`` returns ``[]`` and ``verify_diff`` early-returns
    True. That silently skipped the role matrix, R3 paths, constitutional
    tamper and the secret scan. With ``VERITAS_DIFF_BASE`` set to the parent
    commit — exactly the PR condition the workflow uses — the check must
    still be able to see and reject a violating commit.
    """
    repo = _make_repo(tmp_path)

    # Build a violating commit, then restore a clean worktree at that commit,
    # which is what a CI checkout looks like.
    (repo / "tests" / "test_ci.py").write_text(UNMARKED_TEST, encoding="utf-8")
    assert _git(repo, "add", "tests/test_ci.py").returncode == 0
    assert _git(repo, "commit", "-m", "violating", "--no-verify").returncode == 0
    assert _git(repo, "reset", "-q", "--hard", "HEAD").returncode == 0

    # A clean checkout: nothing staged, nothing modified.
    status = _git(repo, "status", "--porcelain=v1", "--untracked-files=all").stdout
    assert status.strip() == "", f"precondition failed: worktree not clean\n{status}"

    result = subprocess.run(  # noqa: PLW1510 - caller asserts on returncode
        [
            "python3",
            str(repo / "scripts" / "veritas_gate.py"),
            "--verify-metadata",
            "--role",
            "auto",
        ],
        cwd=repo,
        env=_env(VERITAS_DIFF_BASE="HEAD~1"),
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode != 0, (
        "verify-metadata reported PASS on a clean checkout containing a "
        f"marker-less test:\n{result.stdout}"
    )


@pytest.mark.test_id("QA-ZOO27-005")
@pytest.mark.requirements("QA-REQ-HISTORY-SCAN-NO-FALSE-POSITIVE")
@pytest.mark.scenario("AC-ZOO27-HISTORY-SCAN-FIXTURE")
def test_history_scan_does_not_flag_the_scanner_own_fixture() -> None:
    """Regression: the history scan must not match its own test fixture.

    ``check_history_secrets`` probes for the literal ``aws_secret_access_key``
    across ``app frontend tests``. The gate's own selftest writes exactly
    that string into a temp file, so the probe matches the fixture and the
    CI push gate (``--check-all``) fails on a clean, secret-free history.
    """
    result = subprocess.run(  # noqa: PLW1510 - caller asserts on returncode
        ["python3", str(GATE), "--history-scan"],
        cwd=ROOT,
        env=_env(),
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, (
        "history scan flagged a committed secret in a secret-free history:\n"
        f"{result.stdout}\n{result.stderr}"
    )
