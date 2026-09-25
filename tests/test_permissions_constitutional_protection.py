"""ZOO-32 — QA regression: the deny matrix itself must be constitutionally protected.

ADR-008 proved empirically that ``.ai/permissions.yaml`` can be rewritten by any
role's self-declared identity and the gate still PASSes — the deny matrix is
unenforced against its own tamper, and ``.ai/policy-lock.json`` (which pins the
hashes) is equally unprotected in ``verify_diff``. The constitutional policy is
the existing positive pattern: touching ``.ai/constitutional-policy.yaml``
without human approval FAILs ``verify_diff``.

Contract pinned here:
1. Staged ``.ai/permissions.yaml`` tamper without approval = FAIL (RED now).
2. Staged ``.ai/policy-lock.json`` tamper without approval = FAIL (RED now).
3. Staged ``.ai/constitutional-policy.yaml`` tamper without approval = FAIL
   (GREEN control — the pattern ``permissions.yaml`` must mirror).
4. ``permissions.yaml`` + consistently re-hashed lock WITH human approval =
   PASS (GREEN guard — the fix must not brick legitimate human updates).

Tests 1-2 are genuine failures on current ``main``; that red state is the
finding handed to Developer (ZOO-32).
"""
from __future__ import annotations

import hashlib
import json
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
    """Create a minimal git repo with runner + real policies + manifest."""
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


def _tamper_permissions(repo: Path) -> None:
    """Append a comment to permissions.yaml and stage it (hash now drifts)."""
    target = repo / ".ai" / "permissions.yaml"
    target.write_text(target.read_text(encoding="utf-8") + "\n# tampered\n")
    assert _git(repo, "add", ".ai/permissions.yaml").returncode == 0


def _rehash_lock(repo: Path) -> None:
    """Re-pin every .ai hash in policy-lock.json (valid JSON, hashes match)."""
    ai = repo / ".ai"
    lock_path = ai / "policy-lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    for name, pinned in lock["sha256"].items():
        blob = (repo / name).read_bytes() if "/" in name else (ai / name).read_bytes()
        _ = pinned
        lock["sha256"][name] = hashlib.sha256(blob).hexdigest()
    lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    assert _git(repo, "add", ".ai/policy-lock.json").returncode == 0


@pytest.mark.test_id("QA-ZOO32-001")
@pytest.mark.requirements("QA-REQ-PERMISSIONS-PROTECTED")
@pytest.mark.scenario("AC-ZOO32-PERMISSIONS-TAMPER-BLOCKED")
def test_permissions_yaml_tamper_without_approval_blocked(tmp_path: Path) -> None:
    """Staged .ai/permissions.yaml tamper without approval = FAIL.

    ADR-008 repro: any self-declared role rewrites the deny matrix and the
    gate PASSes. The matrix must carry the constitutional tamper protection.
    """
    repo = _make_repo(tmp_path)
    _tamper_permissions(repo)
    proc = _run_gate(repo, "--verify-diff", "--staged", "--role", "reviewer")
    assert proc.returncode != 0, "permissions.yaml tamper must be BLOCKED"
    out = proc.stdout + proc.stderr
    assert "FAIL" in out.upper(), "expected FAIL output"
    assert "permissions.yaml" in out, "expected the tampered file named"


@pytest.mark.test_id("QA-ZOO32-002")
@pytest.mark.requirements("QA-REQ-PERMISSIONS-PROTECTED")
@pytest.mark.scenario("AC-ZOO32-LOCK-TAMPER-BLOCKED")
def test_policy_lock_tamper_without_approval_blocked(tmp_path: Path) -> None:
    """Staged .ai/policy-lock.json rewrite without approval = FAIL.

    The lock pins the policy hashes; if it can be rewritten at will, any
    permissions.yaml protection is bypassable by re-hashing. Valid JSON with
    altered pins must still be blocked at the verify_diff layer.
    """
    repo = _make_repo(tmp_path)
    lock_path = repo / ".ai" / "policy-lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["sha256"][".ai/permissions.yaml"] = "0" * 64
    lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    assert _git(repo, "add", ".ai/policy-lock.json").returncode == 0
    proc = _run_gate(repo, "--verify-diff", "--staged", "--role", "reviewer")
    assert proc.returncode != 0, "policy-lock.json tamper must be BLOCKED"
    out = proc.stdout + proc.stderr
    assert "FAIL" in out.upper(), "expected FAIL output"
    assert "policy-lock.json" in out, "expected the tampered file named"


@pytest.mark.test_id("QA-ZOO32-003")
@pytest.mark.requirements("QA-REQ-PERMISSIONS-PROTECTED")
@pytest.mark.scenario("AC-ZOO32-CONSTITUTIONAL-PATTERN-HOLDS")
def test_constitutional_policy_tamper_without_approval_blocked(
    tmp_path: Path,
) -> None:
    """Positive control: constitutional-policy.yaml tamper is blocked today.

    This is the pattern permissions.yaml must mirror; it must keep holding
    after the fix lands.
    """
    repo = _make_repo(tmp_path)
    target = repo / ".ai" / "constitutional-policy.yaml"
    target.write_text(target.read_text(encoding="utf-8") + "\n# tampered\n")
    assert _git(repo, "add", ".ai/constitutional-policy.yaml").returncode == 0
    proc = _run_gate(repo, "--verify-diff", "--staged", "--role", "reviewer")
    assert proc.returncode != 0, "constitutional tamper must stay BLOCKED"
    assert "FAIL" in (proc.stdout + proc.stderr).upper()


@pytest.mark.test_id("QA-ZOO32-004")
@pytest.mark.requirements("QA-REQ-PERMISSIONS-PROTECTED")
@pytest.mark.scenario("AC-ZOO32-HUMAN-APPROVAL-EXEMPTS")
def test_permissions_tamper_with_human_approval_passes(tmp_path: Path) -> None:
    """Escape-hatch guard: permissions.yaml + re-hashed lock WITH approval = PASS.

    Legitimate human policy updates touch both files; the fix must exempt
    them via the same VERITAS_HUMAN_APPROVAL path the constitutional rule
    uses — not brick all policy maintenance.
    """
    repo = _make_repo(tmp_path)
    _tamper_permissions(repo)
    _rehash_lock(repo)
    check = _run_gate(repo, "--check-policies")
    assert check.returncode == 0, (
        "precondition failed: re-hashed lock must keep --check-policies green\n"
        f"stdout: {check.stdout}\nstderr: {check.stderr}"
    )
    proc = _run_gate(
        repo,
        "--verify-diff",
        "--staged",
        "--role",
        "reviewer",
        extra_env={"VERITAS_HUMAN_APPROVAL": "human:zoo-32-test"},
    )
    assert proc.returncode == 0, (
        f"human-approved policy update must PASS, got {proc.returncode}\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
