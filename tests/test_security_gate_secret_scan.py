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

Requirement: ZOO-24 / FEAT-RL-V02-REQ-010 (AC-RL-V02-10, AC-RL-V02-11) --
the credential-file scan that ``security-gate.sh`` performs. The ids below
(TEST-RL-V02-039 .. TEST-RL-V02-045, plus -019/-020) belong to this series
and to no other. They previously reused TEST-RL-V02-012 .. -018, which
``tests/test_veritas_gate.py`` owns for its staged-metadata checks; a test id
must identify exactly one test, so the two subjects were renumbered apart.
"""
from __future__ import annotations

import os
import re
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


def _gate_security_tests() -> tuple[str, ...]:
    """The gate's own dependency list, parsed out of the shipped script.

    The fixture used to hard-code two of the four names here, so it silently
    drifted: the gate gained two more required files and the fixture kept
    building a tree that could never satisfy it. Parsing the array means a
    future edit to the gate's dependency list is picked up by these tests
    instead of failing them with a message about a missing file.
    """
    text = GATE.read_text(encoding="utf-8")
    match = re.search(r"SECURITY_TESTS=\(\s*(.*?)\s*\)", text, re.DOTALL)
    assert match, "SECURITY_TESTS array not found in the gate script"
    names = [line.strip() for line in match.group(1).splitlines()]
    assert names, "SECURITY_TESTS array is empty"
    for name in names:
        assert name.startswith("tests/") and name.endswith(".py"), f"unexpected entry {name!r}"
    return tuple(names)


GATE_PYTEST_TARGETS = _gate_security_tests()


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


@pytest.mark.test_id("TEST-RL-V02-039")
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


@pytest.mark.test_id("TEST-RL-V02-040")
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


@pytest.mark.test_id("TEST-RL-V02-041")
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


@pytest.mark.test_id("TEST-RL-V02-042")
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


@pytest.mark.test_id("TEST-RL-V02-043")
@pytest.mark.requirements("FEAT-RL-V02-REQ-010")
@pytest.mark.scenario("AC-RL-V02-11")
def test_clean_repo_passes_without_warnings(tmp_path: Path) -> None:
    """No secrets anywhere -> clean PASS, and no false-positive warning noise."""
    repo = _make_repo(tmp_path)

    result = _run_gate(repo)

    assert result.returncode == 0, result.stderr
    assert "WARN" not in result.stdout
    assert "Security gate PASS" in result.stdout


@pytest.mark.test_id("TEST-RL-V02-044")
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


@pytest.mark.test_id("TEST-RL-V02-019")
@pytest.mark.requirements("FEAT-RL-V02-REQ-010")
@pytest.mark.scenario("AC-RL-V02-11")
def test_missing_security_test_is_not_reported_as_a_scan_result(tmp_path: Path) -> None:
    """Root cause of the fixture failures: the two outcomes must stay distinct.

    A missing security test is a DEPENDENCY failure, not a credential-scan
    result. The pre-flight used to run *after* the scan, so the gate printed
    "Security gate PASS: scanned N tracked files..." and only then failed for an
    unrelated reason -- one PASS, one FAIL, for one run. Whichever order they
    land in, a dependency-missing gate must never claim a scan PASS.
    """
    repo = _make_repo(tmp_path)
    (repo / "tests/test_tenant_isolation.py").unlink()
    _git(repo, "commit", "-qam", "drop a required security test")

    result = _run_gate(repo)

    assert result.returncode == 1, result.stdout
    assert "required test files are missing" in result.stderr, result.stderr
    assert "tests/test_tenant_isolation.py" in result.stderr
    # The credential scan never ran, so it must not have announced a result.
    assert "Security gate PASS" not in result.stdout, (
        f"a missing dependency was reported as a scan PASS:\n{result.stdout}"
    )
    assert "tracked files" not in result.stdout, (
        f"the scan reported a result despite the pre-flight failing:\n{result.stdout}"
    )


@pytest.mark.test_id("TEST-RL-V02-020")
@pytest.mark.requirements("FEAT-RL-V02-REQ-010")
@pytest.mark.scenario("AC-RL-V02-11")
def test_gate_never_silently_falls_back_to_a_smaller_test_set(tmp_path: Path) -> None:
    """The `|| fallback` must not come back.

    The shipped script once carried a second, narrower pytest invocation behind
    `|| python3 -m pytest ...`, contradicting its own header comment. If any
    fallback exists, a failing security test would be followed by a smaller run
    that could still exit 0.
    """
    text = GATE.read_text(encoding="utf-8")
    pytest_invocations = [
        line for line in text.splitlines() if line.strip().startswith("pytest")
        or line.strip().startswith("python3 -m pytest")
    ]
    assert len(pytest_invocations) == 1, (
        "expected exactly one test invocation in the gate, found "
        f"{len(pytest_invocations)}: {pytest_invocations}"
    )
    # Only executable shell lines, so a prose mention of `|| fallback` in a
    # comment does not read as a code path.
    code = [
        line
        for line in text.splitlines()
        if not line.lstrip().startswith("#")
    ]
    # The precise invariant: no pytest run may be guarded by `||`, which is what
    # let a failing security test fall through to a smaller set that exited 0.
    # `||` is legitimate elsewhere (`|| true`, `[ a ] || [ b ]` guards).
    guarded = [
        line.strip()
        for line in code
        if "||" in line and ("pytest" in line or line.strip().startswith("pytest"))
    ]
    assert not guarded, f"a pytest invocation is guarded by `||`: {guarded}"


@pytest.mark.test_id("TEST-RL-V02-045")
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
