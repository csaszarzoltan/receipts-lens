"""VERITAS 1.1 — gate runner negative selftests (receipts-lens).

Contract:
1. Mixed app+tests diff = FAIL (blocked with reason).
2. Missing test metadata (test_id/requirements/scenario) = FAIL.
3. R3 sensitive path (auth / payment) without approval = FAIL
   (VERITAS_APPROVAL exempts).
4. Policy hash tamper = FAIL.
5. Git-context failure (non-repo) = FAIL with exit 2 (fail-closed).
6. History scan: clean = PASS, committed secret = FAIL.
7. Metadata markers must carry a non-empty value, and the pytest markers
   themselves must be registered in pyproject.toml.
8. (ZOO-30) Staged-mode checks read the index blob (``git show :path``), not
   the working tree; non-staged diff file collection honours VERITAS_DIFF_BASE
   so CI sees the merged diff instead of a vacuous clean-tree PASS.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "veritas_gate.py"
AI_DIR = ROOT / ".ai"
MANIFEST_DIR = ROOT / ".agent-pipeline" / "00_index"

SCRUB_VARS = ("VERITAS_APPROVAL", "VERITAS_HUMAN_APPROVAL")

# ZOO-30 fixtures: comment-prefixed like the QA suite so the gate's own
# line-based ``def test_*`` scan cannot read these as real unmarked tests.
_ZOO30_UNMARKED_FIXTURE = """
# import pytest
#
#
# def test_staged_probe():
#     assert True
"""

_ZOO30_MARKED_FIXTURE = """
# import pytest
#
#
# @pytest.mark.test_id("ZOO30-T1")
# @pytest.mark.requirements("ZOO-REQ-STAGED")
# @pytest.mark.scenario("AC-ZOO30")
# def test_staged_probe():
#     assert True
"""


def _zoo30_source(fixture: str) -> str:
    """Uncomment a fixture so it can be written to disk as real Python."""
    return "".join(
        line.removeprefix("# ") if line.startswith("# ") else line.lstrip("#")
        for line in fixture.splitlines(keepends=True)
        if line.strip("# \n")
    )


ZOO30_UNMARKED = _zoo30_source(_ZOO30_UNMARKED_FIXTURE)
ZOO30_MARKED = _zoo30_source(_ZOO30_MARKED_FIXTURE)


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
    """Create a minimal git repo with runner + policies + manifest."""
    repo = tmp / "repo"
    repo.mkdir()
    assert _git(repo, "init", "-q").returncode == 0

    scripts = repo / "scripts"
    scripts.mkdir()
    (scripts / "veritas_gate.py").write_bytes(GATE.read_bytes())

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

    (repo / ".gitkeep").write_text("")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "init", "--allow-empty")

    return repo


def _stage_files(repo: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        assert _git(repo, "add", rel).returncode == 0


def _run_gate(
    repo: Path, *args: str, extra_env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run veritas_gate.py inside the temp repo with approval vars scrubbed."""
    env = {k: v for k, v in os.environ.items() if k not in SCRUB_VARS}
    if extra_env:
        env.update(extra_env)
    return subprocess.run(  # noqa: PLW1510 - caller asserts on returncode
        [sys.executable, str(repo / "scripts" / "veritas_gate.py"), *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.mark.test_id("TEST-RL-V02-001")
@pytest.mark.requirements("FEAT-RL-V02-REQ-001")
@pytest.mark.scenario("AC-RL-V02-01")
def test_mixed_app_and_test_diff_blocked(tmp_path: Path) -> None:
    """Mixed app/** + tests/** diff in one change = FAIL with reason."""
    repo = _make_repo(tmp_path)
    _stage_files(
        repo,
        {
            "app/new_feature.py": "X = 1\n",
            "tests/test_new_feature.py": "def test_x(): pass\n",
        },
    )
    proc = _run_gate(repo, "--verify-diff", "--role", "implementer")
    assert proc.returncode != 0, "mixed app+tests diff must be BLOCKED"
    assert "FAIL" in (proc.stdout + proc.stderr).upper(), "expected FAIL output"


@pytest.mark.test_id("TEST-RL-V02-002")
@pytest.mark.requirements("FEAT-RL-V02-REQ-002")
@pytest.mark.scenario("AC-RL-V02-02")
def test_missing_test_metadata_blocked(tmp_path: Path) -> None:
    """Modified tests/*.py without test_id+requirements+scenario = FAIL."""
    repo = _make_repo(tmp_path)
    _stage_files(repo, {"tests/test_nometa_v02.py": "def test_bare(): pass\n"})
    proc = _run_gate(repo, "--verify-metadata")
    assert proc.returncode != 0, "missing metadata must be BLOCKED"
    out = proc.stdout + proc.stderr
    assert "FAIL" in out.upper(), "expected FAIL output"
    assert "test_nometa_v02" in out, "expected the offending file named"


@pytest.mark.test_id("TEST-RL-V02-003")
@pytest.mark.requirements("FEAT-RL-V02-REQ-003")
@pytest.mark.scenario("AC-RL-V02-03")
def test_r3_auth_path_without_approval_blocked(tmp_path: Path) -> None:
    """R3 auth path (app/auth_api.py) without VERITAS_APPROVAL = FAIL."""
    repo = _make_repo(tmp_path)
    _stage_files(repo, {"app/auth_api.py": "X = 1\n"})
    blocked = _run_gate(repo, "--verify-diff", "--role", "implementer")
    assert blocked.returncode != 0, "R3 auth path without approval must be BLOCKED"
    assert "FAIL" in (blocked.stdout + blocked.stderr).upper()

    allowed = _run_gate(
        repo,
        "--verify-diff",
        "--role",
        "implementer",
        extra_env={"VERITAS_APPROVAL": "human:test-123"},
    )
    assert allowed.returncode == 0, (
        f"VERITAS_APPROVAL must exempt the R3 gate (rc={allowed.returncode})\n"
        f"stdout: {allowed.stdout}\nstderr: {allowed.stderr}"
    )


@pytest.mark.test_id("TEST-RL-V02-004")
@pytest.mark.requirements("FEAT-RL-V02-REQ-004")
@pytest.mark.scenario("AC-RL-V02-04")
def test_r3_payment_path_without_approval_blocked(tmp_path: Path) -> None:
    """R3 payment path (app/subscriptions_api.py) without approval = FAIL."""
    repo = _make_repo(tmp_path)
    _stage_files(repo, {"app/subscriptions_api.py": "X = 1\n"})
    blocked = _run_gate(repo, "--verify-diff", "--role", "implementer")
    assert blocked.returncode != 0, "R3 payment path without approval must be BLOCKED"
    assert "FAIL" in (blocked.stdout + blocked.stderr).upper()

    allowed = _run_gate(
        repo,
        "--verify-diff",
        "--role",
        "implementer",
        extra_env={"VERITAS_HUMAN_APPROVAL": "human:test-456"},
    )
    assert allowed.returncode == 0, (
        f"VERITAS_HUMAN_APPROVAL must exempt the R3 gate (rc={allowed.returncode})\n"
        f"stdout: {allowed.stdout}\nstderr: {allowed.stderr}"
    )


@pytest.mark.test_id("TEST-RL-V02-005")
@pytest.mark.requirements("FEAT-RL-V02-REQ-005")
@pytest.mark.scenario("AC-RL-V02-05")
def test_policy_hash_tamper_blocked(tmp_path: Path) -> None:
    """Tampered .ai policy (hash drift vs policy-lock.json) = FAIL."""
    repo = _make_repo(tmp_path)
    lock = repo / ".ai" / "permissions.yaml"
    lock.write_text(lock.read_text(encoding="utf-8") + "# tamper\n")
    proc = _run_gate(repo, "--check-policies")
    assert proc.returncode != 0, "tampered policy must be BLOCKED"
    assert "HASH MISMATCH" in (proc.stdout + proc.stderr).upper()


@pytest.mark.test_id("TEST-RL-V02-006")
@pytest.mark.requirements("FEAT-RL-V02-REQ-006")
@pytest.mark.scenario("AC-RL-V02-06")
def test_git_context_failure_exits_2(tmp_path: Path) -> None:
    """Non-repo context = FAIL with exit 2 (fail-closed, never PASS)."""
    plain = tmp_path / "plain"
    plain.mkdir()
    scripts = plain / "scripts"
    scripts.mkdir()
    (scripts / "veritas_gate.py").write_bytes(GATE.read_bytes())
    env = {k: v for k, v in os.environ.items() if k not in SCRUB_VARS}
    proc = subprocess.run(  # noqa: PLW1510 - returncode asserted below
        [sys.executable, str(scripts / "veritas_gate.py"), "--verify-diff"],
        cwd=plain,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 2, (
        f"git-context failure must exit 2, got {proc.returncode}\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    assert "FAIL" in (proc.stdout + proc.stderr).upper()


@pytest.mark.test_id("TEST-RL-V02-007")
@pytest.mark.requirements("FEAT-RL-V02-REQ-007")
@pytest.mark.scenario("AC-RL-V02-07")
def test_history_scan_clean_passes(tmp_path: Path) -> None:
    """Clean history (no committed secrets in product paths) = PASS."""
    repo = _make_repo(tmp_path)
    proc = _run_gate(repo, "--history-scan")
    assert proc.returncode == 0, (
        f"clean history must PASS, got {proc.returncode}\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )


@pytest.mark.test_id("TEST-RL-V02-008")
@pytest.mark.requirements("FEAT-RL-V02-REQ-008")
@pytest.mark.scenario("AC-RL-V02-08")
def test_history_scan_finds_committed_secret(tmp_path: Path) -> None:
    """Committed AWS key in app/** history = FAIL."""
    repo = _make_repo(tmp_path)
    target = repo / "app" / "leaky.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    # A KEY-ID ertek a valós formatumot követi (AKIA + 16 nagy alfanumerikus),
    # hogy a gate AKIA-probe-ja megtalalja a commitban. A maszkolt alak
    # ("AKIAIO...MPLE") NEM illeszkedne, es a sajat fixture a diff-ben
    # (a gate a torolt sorokat is nez) sajat magat jelentené.
    _LEAK = "aws_secret" "_access_key"  # a gate ne lassa szovegkent
    target.write_text(f'KEY = "{_LEAK}=AKIAIOSFODNN7EXAMPLE"\n')
    assert _git(repo, "add", ".").returncode == 0
    assert _git(repo, "commit", "-m", "leak", "-q").returncode == 0
    proc = _run_gate(repo, "--history-scan")
    assert proc.returncode != 0, "committed secret must be BLOCKED"
    assert "FAIL" in (proc.stdout + proc.stderr).upper()


@pytest.mark.test_id("TEST-RL-V02-009")
@pytest.mark.requirements("FEAT-RL-V02-REQ-009")
@pytest.mark.scenario("AC-RL-V02-09")
def test_bare_markers_blocked(tmp_path: Path) -> None:
    """Decorators present but valueless (@pytest.mark.test_id) = FAIL.

    A bare marker carries no traceability, so it must not satisfy gate 10.
    """
    repo = _make_repo(tmp_path)
    _stage_files(
        repo,
        {
            "tests/test_bare_v02.py": (
                "import pytest\n"
                "\n"
                "\n"
                "@pytest.mark.test_id\n"
                "@pytest.mark.requirements\n"
                "@pytest.mark.scenario\n"
                "def test_bare_metadata():\n"
                "    pass\n"
            )
        },
    )
    proc = _run_gate(repo, "--verify-metadata")
    assert proc.returncode != 0, "bare markers without values must be BLOCKED"
    out = proc.stdout + proc.stderr
    assert "FAIL" in out.upper(), "expected FAIL output"
    assert "test_bare_v02" in out, "expected the offending file named"


@pytest.mark.test_id("TEST-RL-V02-010")
@pytest.mark.requirements("FEAT-RL-V02-REQ-009")
@pytest.mark.scenario("AC-RL-V02-09")
def test_empty_marker_value_blocked(tmp_path: Path) -> None:
    """Empty marker value (@pytest.mark.scenario("")) = FAIL."""
    repo = _make_repo(tmp_path)
    _stage_files(
        repo,
        {
            "tests/test_emptyval_v02.py": (
                "import pytest\n"
                "\n"
                "\n"
                '@pytest.mark.test_id("TEST-RL-V02-046")\n'
                '@pytest.mark.requirements("FEAT-RL-V02-REQ-009")\n'
                '@pytest.mark.scenario("")\n'
                "def test_empty_scenario():\n"
                "    pass\n"
            )
        },
    )
    proc = _run_gate(repo, "--verify-metadata")
    assert proc.returncode != 0, "empty marker value must be BLOCKED"
    out = proc.stdout + proc.stderr
    assert "FAIL" in out.upper(), "expected FAIL output"
    assert "test_emptyval_v02" in out, "expected the offending file named"


@pytest.mark.test_id("TEST-RL-V02-012")
@pytest.mark.requirements("FEAT-RL-V02-REQ-010")
@pytest.mark.scenario("AC-RL-V02-10")
def test_staged_metadata_reads_index_not_worktree(tmp_path: Path) -> None:
    """ZOO-30/F1a: staged marker-less test + compliant worktree = FAIL.

    Stages the marker-less blob, then rewrites the working tree with markers
    WITHOUT re-staging. The gate must judge the indexed content and block.
    Runs with an explicit non-implementer role so the tests/** deny matrix
    cannot mask the metadata verdict.
    """
    repo = _make_repo(tmp_path)
    target = repo / "tests" / "test_staged_blob_v02.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(ZOO30_UNMARKED, encoding="utf-8")
    assert _git(repo, "add", "tests/test_staged_blob_v02.py").returncode == 0
    # Working tree now looks compliant; the index still holds the bad blob.
    target.write_text(ZOO30_MARKED, encoding="utf-8")
    staged = _git(repo, "show", ":tests/test_staged_blob_v02.py").stdout
    assert "mark.test_id" not in staged, "precondition failed: index is not marker-less"

    proc = _run_gate(repo, "--verify-metadata", "--staged", "--role", "test_author")
    assert proc.returncode != 0, (
        "staged marker-less test must be BLOCKED even when the worktree "
        f"looks compliant:\n{proc.stdout}\n{proc.stderr}"
    )
    out = proc.stdout + proc.stderr
    assert "FAIL" in out.upper(), "expected FAIL output"
    assert "test_staged_blob_v02" in out, "expected the offending file named"


@pytest.mark.test_id("TEST-RL-V02-013")
@pytest.mark.requirements("FEAT-RL-V02-REQ-010")
@pytest.mark.scenario("AC-RL-V02-10")
def test_staged_secret_scan_reads_index_not_worktree(tmp_path: Path) -> None:
    """ZOO-30/F1b: staged secret + cleaned worktree = FAIL.

    Stages a file containing a live secret pattern, then scrubs the working
    tree WITHOUT re-staging. The secret scan must judge the indexed content
    and block. (Inverse of the metadata probe: proves the index, not the
    tree, is the source of truth.)
    """
    repo = _make_repo(tmp_path)
    target = repo / "docs" / "note.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    # a kulcs osszefuzese, hogy a forrasban ne legyen a gate sajat mintaja
    _TOK = "to" "ken"  # a gate ne lassa szovegkent a forrasban
    _SK = "sk_" "live_"  # a gate ne lassa szovegkent a forrasban
    target.write_text(f'{_TOK} = "{_SK}aaaaaaaaaaaaaaaaaaaaaaaa"\n', encoding="utf-8")
    assert _git(repo, "add", "docs/note.md").returncode == 0
    # Working tree now looks clean; the index still holds the secret.
    target.write_text("nothing to see here\n", encoding="utf-8")
    staged = _git(repo, "show", ":docs/note.md").stdout
    assert "sk_live_" in staged, "precondition failed: index does not hold the secret"

    proc = _run_gate(repo, "--verify-diff", "--staged", "--role", "implementer")
    assert proc.returncode != 0, (
        "staged secret must be BLOCKED even when the worktree "
        f"looks clean:\n{proc.stdout}\n{proc.stderr}"
    )
    assert "FAIL" in (proc.stdout + proc.stderr).upper(), "expected FAIL output"


@pytest.mark.test_id("TEST-RL-V02-014")
@pytest.mark.requirements("FEAT-RL-V02-REQ-010")
@pytest.mark.scenario("AC-RL-V02-10")
def test_diff_base_exposes_committed_violation_on_clean_tree(tmp_path: Path) -> None:
    """ZOO-30/F2: VERITAS_DIFF_BASE sees a violating commit on a clean tree.

    Reproduces the CI condition: worktree clean, violation already committed.
    With VERITAS_DIFF_BASE=HEAD~1 the file collection must surface the file
    and the metadata check must block instead of vacuously passing.
    """
    repo = _make_repo(tmp_path)
    target = repo / "tests" / "test_ci_blob_v02.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(ZOO30_UNMARKED, encoding="utf-8")
    assert _git(repo, "add", "tests/test_ci_blob_v02.py").returncode == 0
    assert _git(repo, "commit", "-m", "violating", "-q", "--no-verify").returncode == 0
    assert _git(repo, "reset", "-q", "--hard", "HEAD").returncode == 0
    status = _git(repo, "status", "--porcelain=v1", "--untracked-files=all").stdout
    assert status.strip() == "", f"precondition failed: worktree not clean\n{status}"

    proc = _run_gate(
        repo, "--verify-metadata", "--role", "auto", extra_env={"VERITAS_DIFF_BASE": "HEAD~1"}
    )
    assert proc.returncode != 0, (
        "committed marker-less test must be BLOCKED via VERITAS_DIFF_BASE "
        f"on a clean tree:\n{proc.stdout}\n{proc.stderr}"
    )
    out = proc.stdout + proc.stderr
    assert "FAIL" in out.upper(), "expected FAIL output"
    assert "test_ci_blob_v02" in out, "expected the offending file named"


@pytest.mark.test_id("TEST-RL-V02-015")
@pytest.mark.requirements("FEAT-RL-V02-REQ-010")
@pytest.mark.scenario("AC-RL-V02-10")
def test_staged_deletion_needs_no_markers(tmp_path: Path) -> None:
    """ZOO-30 edge: staging a tests/** deletion must not crash the gate.

    A deleted path has no staged blob; the metadata check skips it and the
    diff check passes (no new content to judge).
    """
    repo = _make_repo(tmp_path)
    target = repo / "tests" / "test_gone_v02.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(ZOO30_MARKED, encoding="utf-8")
    assert _git(repo, "add", "tests/test_gone_v02.py").returncode == 0
    assert _git(repo, "commit", "-m", "add", "-q", "--no-verify").returncode == 0
    assert _git(repo, "rm", "-q", "tests/test_gone_v02.py").returncode == 0

    meta = _run_gate(repo, "--verify-metadata", "--staged", "--role", "test_author")
    assert meta.returncode == 0, (
        f"staged deletion must not fail the metadata gate:\n{meta.stdout}\n{meta.stderr}"
    )


@pytest.mark.test_id("TEST-RL-V02-011")
@pytest.mark.requirements("FEAT-RL-V02-REQ-009")
@pytest.mark.scenario("AC-RL-V02-09")
def test_valued_markers_still_pass(tmp_path: Path) -> None:
    """A properly valued 3-marker test still PASSes (no false positive)."""
    repo = _make_repo(tmp_path)
    _stage_files(
        repo,
        {
            "tests/test_valued_v02.py": (
                "import pytest\n"
                "\n"
                "\n"
                '@pytest.mark.test_id("TEST-RL-V02-047")\n'
                '@pytest.mark.requirements("FEAT-RL-V02-REQ-009")\n'
                '@pytest.mark.scenario("AC-RL-V02-09")\n'
                "def test_valued_metadata():\n"
                "    pass\n"
            )
        },
    )
    proc = _run_gate(repo, "--verify-metadata")
    assert proc.returncode == 0, (
        f"valued markers must PASS, got {proc.returncode}\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    assert "PASS" in proc.stdout, "expected PASS output"


@pytest.mark.test_id("TEST-RL-V02-016")
@pytest.mark.requirements("FEAT-RL-V02-REQ-011")
@pytest.mark.scenario("AC-RL-V02-11")
def test_auto_role_infers_test_author_for_tests_only_diff(tmp_path: Path) -> None:
    """ZOO-28: tests-only staged diff with --role auto = PASS as test_author.

    Reproduces the pre-commit failure: --role auto used to mean implementer,
    whose deny matrix covers tests/**, so the Test Author could only commit
    with --no-verify.
    """
    repo = _make_repo(tmp_path)
    _stage_files(repo, {"tests/test_zz_probe_v02.py": "def test_x():\n    pass\n"})
    proc = _run_gate(repo, "--verify-diff", "--staged", "--role", "auto")
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, (
        f"tests-only diff with --role auto must PASS, got {proc.returncode}\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    assert "Inferred role 'test_author'" in out, "expected role inference logged"


@pytest.mark.test_id("TEST-RL-V02-017")
@pytest.mark.requirements("FEAT-RL-V02-REQ-012")
@pytest.mark.scenario("AC-RL-V02-12")
def test_auto_role_infers_spec_author_for_specs_only_diff(tmp_path: Path) -> None:
    """ZOO-28: specs-only staged diff with --role auto = PASS as spec_author."""
    repo = _make_repo(tmp_path)
    _stage_files(repo, {"specs/probe_v02.md": "# probe\n"})
    proc = _run_gate(repo, "--verify-diff", "--staged", "--role", "auto")
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, (
        f"specs-only diff with --role auto must PASS, got {proc.returncode}\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    assert "Inferred role 'spec_author'" in out, "expected role inference logged"


@pytest.mark.test_id("TEST-RL-V02-018")
@pytest.mark.requirements("FEAT-RL-V02-REQ-013")
@pytest.mark.scenario("AC-RL-V02-13")
def test_auto_role_stays_implementer_for_mixed_diff(tmp_path: Path) -> None:
    """ZOO-28: mixed app+tests diff with --role auto stays fail-closed.

    Ambiguous packets must keep the historical implementer default (and
    therefore FAIL on the tests/** deny), never guess a lenient role.
    """
    repo = _make_repo(tmp_path)
    _stage_files(
        repo,
        {
            "app/probe_v02.py": "X = 1\n",
            "tests/test_probe_v02.py": "def test_x():\n    pass\n",
        },
    )
    proc = _run_gate(repo, "--verify-diff", "--staged", "--role", "auto")
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0, "mixed app+tests diff with --role auto must be BLOCKED"
    assert "FAIL" in out.upper(), "expected FAIL output"
    assert "Inferred role" not in out, "ambiguous diff must not infer any role"


@pytest.mark.test_id("TEST-RL-V02-048")
@pytest.mark.requirements("FEAT-RL-V02-REQ-014")
@pytest.mark.scenario("AC-RL-V02-14")
def test_auto_role_without_git_context_fails_closed(tmp_path: Path) -> None:
    """ZOO-28: --role auto outside a repo = FAIL with exit 2, never a guess."""
    plain = tmp_path / "plain"
    plain.mkdir()
    scripts = plain / "scripts"
    scripts.mkdir()
    (scripts / "veritas_gate.py").write_bytes(GATE.read_bytes())
    env = {k: v for k, v in os.environ.items() if k not in SCRUB_VARS}
    proc = subprocess.run(  # noqa: PLW1510 - returncode asserted below
        [sys.executable, str(scripts / "veritas_gate.py"), "--verify-diff", "--role", "auto"],
        cwd=plain,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 2, (
        f"--role auto without git context must exit 2, got {proc.returncode}\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    assert "FAIL" in (proc.stdout + proc.stderr).upper()


@pytest.mark.test_id("TEST-RL-V02-049")
@pytest.mark.requirements("FEAT-RL-V02-REQ-015")
@pytest.mark.scenario("AC-RL-V02-15")
def test_auto_role_passes_hook_invocation_for_marked_test(tmp_path: Path) -> None:
    """ZOO-28: the exact hook invocation passes for a marked test-only commit.

    Runs the same flags .githooks/pre-commit passes
    (--verify-diff --verify-metadata --staged --role auto) against a fully
    marked test file: inference must pick test_author and both gates PASS.
    """
    repo = _make_repo(tmp_path)
    _stage_files(
        repo,
        {
            "tests/test_author_probe_v02.py": (
                "import pytest\n"
                "\n"
                "\n"
                '@pytest.mark.test_id("TEST-RL-V02-050")\n'
                '@pytest.mark.requirements("FEAT-RL-V02-REQ-015")\n'
                '@pytest.mark.scenario("AC-RL-V02-15")\n'
                "def test_author_probe():\n"
                "    pass\n"
            )
        },
    )
    proc = _run_gate(
        repo, "--verify-diff", "--verify-metadata", "--staged", "--role", "auto"
    )
    assert proc.returncode == 0, (
        f"hook invocation for marked test-only commit must PASS, "
        f"got {proc.returncode}\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    assert "PASS" in proc.stdout, "expected PASS output"
