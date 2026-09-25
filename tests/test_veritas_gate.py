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
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "veritas_gate.py"
AI_DIR = ROOT / ".ai"
MANIFEST_DIR = ROOT / ".agent-pipeline" / "00_index"

SCRUB_VARS = ("VERITAS_APPROVAL", "VERITAS_HUMAN_APPROVAL")


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
        ["python3", str(repo / "scripts" / "veritas_gate.py"), *args],
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
        ["python3", str(scripts / "veritas_gate.py"), "--verify-diff"],
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
    target.write_text('KEY = "aws_secret_access_key=AKIAIO...MPLE"\n')
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
                '@pytest.mark.test_id("TEST-RL-V02-010")\n'
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
                '@pytest.mark.test_id("TEST-RL-V02-011")\n'
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
