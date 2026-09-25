"""ZOO-24: the security-gate secret scan must be usable on a developer checkout.

Finding: ``scripts/security-gate.sh`` walked the working tree with
``Path('.').rglob('*')``, so a local, gitignored ``.env`` made the project's
own security gate fail on the ``main`` checkout — the gate could not be run at
all where it matters most. The two cases were also indistinguishable: a local
``.env`` and a *committed* ``.env`` produced the same assertion.

Contract pinned here, exercised against the real script in a throwaway repo:

  * **Tracked secret file -> gate FAILS (exit 1).** Repository content that
    carries a credential is a leak the moment it is committed or staged.
  * **Untracked/gitignored local secret file -> gate PASSES (exit 0)** and
    reports a warning naming the file. A local ``.env`` is expected developer
    state that the gate can never let through; blocking on it is what made the
    gate unusable. Surfacing it is still useful — it is a real local secret.
  * **Untracked secrets buried in an ignored directory are not enumerated** in
    that warning (``git ls-files --others --directory`` collapses the tree to
    ``dir/``). Pinned so the warning's non-exhaustiveness is a decision on
    record rather than a surprise.
  * The hard-coded junk-directory exclusion list is gone: a tracked secret
    inside a directory *named* like excluded build output is now a tracked
    secret and fails, because it is in the repository.
  * **No git context -> fail-closed (exit 2)**, never a silent PASS from an
    empty file list.

Every case runs the actual ``scripts/security-gate.sh`` in a subprocess with
its own git repo, so the assertions cover the shipped script, not a re-stated
copy of its logic.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "security-gate.sh"

# The gate shells out to ``python3`` and ``python3 -m pytest``. pytest only
# exists in the interpreter running this suite, so its bin dir is put first on
# PATH to keep the subprocess run honest about what a developer would have.
# Deliberately NOT resolved: in a venv that symlink points at the base
# interpreter, which has no pytest installed.
BIN_DIR = str(Path(sys.executable).parent)

STUB_TEST = "def test_noop():\n    assert True\n"
GATE_PYTEST_TARGETS = ("tests/test_fetch_image_bytes.py", "tests/test_magic_bytes.py")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }
    result = subprocess.run(  # noqa: PLW1510 - callers assert on returncode
        ["git", *args], cwd=repo, env=env, capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, f"git {args} failed: {result.stderr}"
    return result


def _make_repo(tmp_path: Path) -> Path:
    """Minimal repo carrying the real gate script and a passing test tree."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")

    (repo / ".gitignore").write_text(".env\n", encoding="utf-8")
    (repo / "scripts").mkdir()
    (repo / "scripts" / "security-gate.sh").write_bytes(GATE.read_bytes())
    (repo / "tests").mkdir()
    for name in GATE_PYTEST_TARGETS:
        (repo / name).write_text(STUB_TEST, encoding="utf-8")

    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "init")
    return repo


def _run_gate(repo: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PATH": f"{BIN_DIR}{os.pathsep}{os.environ.get('PATH', '')}"}
    return subprocess.run(  # noqa: PLW1510 - callers assert on returncode
        ["bash", "scripts/security-gate.sh"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.mark.test_id("TEST-RL-V02-012")
@pytest.mark.requirements("FEAT-RL-V02-REQ-010")
@pytest.mark.scenario("AC-RL-V02-10")
def test_local_gitignored_env_passes_with_warning(tmp_path: Path) -> None:
    """The regression: a local .env must not make the security gate unusable."""
    repo = _make_repo(tmp_path)
    (repo / ".env").write_text("LOCAL_ONLY=1\n", encoding="utf-8")
    assert _git(repo, "check-ignore", ".env").returncode == 0, "precondition: .env is ignored"

    result = _run_gate(repo)

    assert result.returncode == 0, f"gate failed on a local .env:\n{result.stderr}"
    assert ".env" in result.stdout, "the local secret should be reported, not silently dropped"
    assert "WARN" in result.stdout
    assert "Security gate PASS" in result.stdout


@pytest.mark.test_id("TEST-RL-V02-013")
@pytest.mark.requirements("FEAT-RL-V02-REQ-010")
@pytest.mark.scenario("AC-RL-V02-11")
def test_tracked_env_still_fails_the_gate(tmp_path: Path) -> None:
    """Narrowing the scan to the index must not let a committed secret through."""
    repo = _make_repo(tmp_path)
    (repo / ".gitignore").unlink()
    (repo / ".env").write_text("COMMITTED=1\n", encoding="utf-8")
    _git(repo, "add", "-f", ".env")
    _git(repo, "commit", "-qm", "commit a secret")

    result = _run_gate(repo)

    assert result.returncode == 1, f"committed .env must fail the gate:\n{result.stdout}"
    assert ".env" in result.stderr
    assert "Security gate PASS" not in result.stdout


@pytest.mark.test_id("TEST-RL-V02-014")
@pytest.mark.requirements("FEAT-RL-V02-REQ-010")
@pytest.mark.scenario("AC-RL-V02-10")
def test_tracked_pem_fails_the_gate(tmp_path: Path) -> None:
    """The extension rule still applies to tracked files."""
    repo = _make_repo(tmp_path)
    (repo / "certs").mkdir()
    (repo / "certs" / "server.pem").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "certs/server.pem")
    _git(repo, "commit", "-qm", "commit a pem")

    result = _run_gate(repo)

    assert result.returncode == 1, f"tracked .pem must fail the gate:\n{result.stdout}"
    assert "certs/server.pem" in result.stderr


@pytest.mark.test_id("TEST-RL-V02-015")
@pytest.mark.requirements("FEAT-RL-V02-REQ-010")
@pytest.mark.scenario("AC-RL-V02-10")
def test_tracked_secret_in_junk_named_dir_fails(tmp_path: Path) -> None:
    """Dropping the hard-coded exclusion list must not weaken the tracked check.

    A tracked secret is a repo-content leak even when its directory is named
    like excluded build output; only *untracked* state is out of scope.
    """
    repo = _make_repo(tmp_path)
    junk = repo / "node_modules" / "pkg"
    junk.mkdir(parents=True)
    (junk / "id_rsa").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "-f", "node_modules/pkg/id_rsa")
    _git(repo, "commit", "-qm", "commit a key under a junk-named dir")

    result = _run_gate(repo)

    assert result.returncode == 1, f"tracked id_rsa must fail the gate:\n{result.stdout}"
    assert "node_modules/pkg/id_rsa" in result.stderr


@pytest.mark.test_id("TEST-RL-V02-016")
@pytest.mark.requirements("FEAT-RL-V02-REQ-010")
@pytest.mark.scenario("AC-RL-V02-11")
def test_clean_repo_passes_without_warnings(tmp_path: Path) -> None:
    """No secrets anywhere -> clean PASS, and no false-positive warning noise."""
    repo = _make_repo(tmp_path)

    result = _run_gate(repo)

    assert result.returncode == 0, result.stderr
    assert "WARN" not in result.stdout
    assert "Security gate PASS" in result.stdout


@pytest.mark.test_id("TEST-RL-V02-017")
@pytest.mark.requirements("FEAT-RL-V02-REQ-010")
@pytest.mark.scenario("AC-RL-V02-10")
def test_untracked_secret_in_ignored_dir_is_not_enumerated(tmp_path: Path) -> None:
    """Pins the known limit of the warning: ignored trees are collapsed.

    ``git ls-files --others --directory`` reports ``vendor/`` as a directory
    entry, so a secret inside it is not named. The tracked check is unaffected.
    """
    repo = _make_repo(tmp_path)
    (repo / "vendor").mkdir()
    (repo / "vendor" / "id_ed25519").write_text("x\n", encoding="utf-8")

    result = _run_gate(repo)

    assert result.returncode == 0, result.stderr
    assert "id_ed25519" not in result.stdout, "collapsed dirs are not enumerated by design"


@pytest.mark.test_id("TEST-RL-V02-018")
@pytest.mark.requirements("FEAT-RL-V02-REQ-010")
@pytest.mark.scenario("AC-RL-V02-11")
def test_missing_git_context_fails_closed(tmp_path: Path) -> None:
    """Without git there is no trustworthy scope: exit 2, never a silent PASS."""
    repo = tmp_path / "not-a-repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "scripts" / "security-gate.sh").write_bytes(GATE.read_bytes())
    (repo / ".env").write_text("LOCAL_ONLY=1\n", encoding="utf-8")

    env = {**os.environ, "PATH": f"{BIN_DIR}{os.pathsep}{os.environ.get('PATH', '')}"}
    result = subprocess.run(  # noqa: PLW1510 - caller asserts on returncode
        ["bash", "scripts/security-gate.sh"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 2, f"no-git must fail closed:\n{result.stdout}"
    assert "Security gate PASS" not in result.stdout
