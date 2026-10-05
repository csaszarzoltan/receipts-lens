"""Regression gate: .githooks/pre-commit interpreter resolution (SPEC-001).

Pre-fix, `.githooks/pre-commit:31` called a bare ``python3``. On an agent PATH that
interpreter has no pyyaml, the gate died at ``import yaml``, and EVERY agent commit
was blocked (three agents hit it in one session; one reached for ``--no-verify``,
which is exactly the defeat this hook exists to be).

The fixed hook probes ``${REPO_ROOT}/.venv/bin/python`` then ``python3``, picks the
first that can ``import yaml``, and exits 2 (fail-closed) when none can.

Every test here runs the REAL hook file as a subprocess against a temp git repo.
The boundary is never mocked: the hook is executed by bash, resolves its own repo
root, and invokes whatever interpreter it selects. Scenario 3 substitutes a real
recording executable for the gate purely to observe the argv the hook passes -- the
recorder is a genuine script the hook really runs, so an unrunnable invocation would
still fail the assertion.

The temp repo is created under tmp_path and the repo venv is COPIED into it; the
real /home/zoltan/receipts-lens/.venv is never read for execution, moved, or
removed (test_venv_untouched pins that).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".githooks" / "pre-commit"
GATE = ROOT / "scripts" / "veritas_gate.py"
AI_DIR = ROOT / ".ai"
MANIFEST_DIR = ROOT / ".agent-pipeline" / "00_index"
REPO_VENV_PY = ROOT / ".venv" / "bin" / "python"

SCRUB_VARS = ("VERITAS_APPROVAL", "VERITAS_HUMAN_APPROVAL", "VERITAS_ROLE")

# A staged test file that satisfies the metadata gate, so scenario 1 reaches PASS
# for a reason (the gate accepted the diff) rather than vacuously.
MARKED_TEST = (
    '@pytest.mark.test_id("TEST-TMP-001")\n'
    '@pytest.mark.requirements("FEAT-TMP-REQ-001")\n'
    '@pytest.mark.scenario("AC-TMP-01")\n'
    "def test_bare():\n"
    "    pass\n"
)


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
    return subprocess.run(  # noqa: PLW1510 - callers assert on returncode
        ["git", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def _yaml_site_packages() -> Path:
    """Locate the yaml package of the interpreter running pytest.

    Building the temp venv from sys.executable keeps the CPython ABI identical, so
    the compiled ``_yaml`` extension copied alongside the pure-python package loads.
    """
    import yaml  # noqa: PLC0415 - imported here so the failure names the real cause

    return Path(yaml.__file__).resolve().parent.parent


def _make_yaml_venv(dest: Path) -> Path:
    """Create a temp venv whose python CAN import yaml (candidate 1 shape)."""
    assert dest.mkdir(parents=True) is None, "temp venv dir must not exist yet"
    proc = subprocess.run(  # noqa: PLW1510 - asserted below
        [sys.executable, "-m", "venv", "--without-pip", str(dest)],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, f"venv creation failed: {proc.stderr}"
    site = _yaml_site_packages()
    target_sp = next(dest.glob("lib/python*/site-packages"))
    shutil.copytree(site / "yaml", target_sp / "yaml")
    if (site / "_yaml").exists():
        shutil.copytree(site / "_yaml", target_sp / "_yaml")
    for dist in site.glob("pyyaml-*.dist-info"):
        shutil.copytree(dist, target_sp / dist.name)
    py = dest / "bin" / "python"
    assert py.exists(), f"temp venv has no interpreter at {py}"
    return py


def _make_yaml_less_venv(dest: Path) -> Path:
    """Create a temp venv whose python CANNOT import yaml (the agent-PATH case)."""
    assert dest.mkdir(parents=True) is None, "temp venv dir must not exist yet"
    proc = subprocess.run(  # noqa: PLW1510 - asserted below
        [sys.executable, "-m", "venv", "--without-pip", str(dest)],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, f"venv creation failed: {proc.stderr}"
    py = dest / "bin" / "python"
    assert py.exists(), f"temp venv has no interpreter at {py}"
    probe = subprocess.run(  # noqa: PLW1510 - asserted below
        [str(py), "-c", "import yaml"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert probe.returncode != 0, (
        "the yaml-less fixture must NOT be able to import yaml, otherwise "
        "the fail-closed scenario would be vacuous"
    )
    return py


def _make_repo(tmp: Path, gate_source: Path | None = None) -> Path:
    """Temp git repo carrying the real hook plus the real gate and its .ai policies."""
    repo = tmp / "repo"
    repo.mkdir()
    assert _git(repo, "init", "-q").returncode == 0

    hooks = repo / ".githooks"
    hooks.mkdir()
    hook_dst = hooks / "pre-commit"
    hook_dst.write_bytes(HOOK.read_bytes())
    hook_dst.chmod(0o755)

    scripts = repo / "scripts"
    scripts.mkdir()
    src = gate_source if gate_source is not None else GATE
    (scripts / "veritas_gate.py").write_bytes(src.read_bytes())

    ai = repo / ".ai"
    ai.mkdir()
    assert AI_DIR.is_dir(), f"real .ai policies missing at {AI_DIR}"
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
    assert _git(repo, "add", "-A").returncode == 0
    assert _git(repo, "commit", "-q", "-m", "init", "--allow-empty").returncode == 0
    return repo


def _stage(repo: Path, rel: str, content: str) -> None:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    assert _git(repo, "add", rel).returncode == 0


def _run_hook(repo: Path, path_python3: Path, **extra_env: str) -> subprocess.CompletedProcess[str]:
    """Run the real hook in the temp repo with a controlled PATH."""
    env = {k: v for k, v in os.environ.items() if k not in SCRUB_VARS}
    env["PATH"] = f"{path_python3.parent}{os.pathsep}{env.get('PATH', '')}"
    env.update(extra_env)
    return subprocess.run(  # noqa: PLW1510 - callers assert on returncode
        ["bash", str(repo / ".githooks" / "pre-commit")],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )


@pytest.mark.test_id("TEST-RL-V02-053")
@pytest.mark.requirements("FEAT-RL-V02-REQ-053")
@pytest.mark.scenario("AC-RL-V02-10: with the repo venv present and a yaml-less python3 first on PATH, the hook exits 0 and prints PASS (pre-fix: exit 1, ModuleNotFoundError).")
def test_hook_passes_using_repo_venv_when_path_python3_lacks_yaml(
    tmp_path: Path,
) -> None:
    """The venv candidate wins even though python3 on PATH cannot import yaml."""
    repo = _make_repo(tmp_path)
    yaml_less = _make_yaml_less_venv(tmp_path / "yaml_less")

    _make_yaml_venv(repo / ".venv")
    _stage(repo, "tests/test_tmp_marked.py", MARKED_TEST)

    proc = _run_hook(repo, yaml_less)
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, (
        f"hook must PASS via the repo venv (rc={proc.returncode})\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    assert "PASS" in out, f"expected a PASS line, got:\n{out}"
    assert "ModuleNotFoundError" not in out, (
        f"the gate must not die on a missing yaml import:\n{out}"
    )


@pytest.mark.test_id("TEST-RL-V02-054")
@pytest.mark.requirements("FEAT-RL-V02-REQ-054")
@pytest.mark.scenario("AC-RL-V02-11: with no interpreter able to import yaml, the hook exits 2 and names the candidates it tried (pre-fix: exit 1, no diagnostic).")
def test_hook_fails_closed_and_names_candidates_when_no_interpreter_has_yaml(
    tmp_path: Path,
) -> None:
    """No .venv and a yaml-less python3: block with exit 2 and a named diagnostic."""
    repo = _make_repo(tmp_path)
    yaml_less = _make_yaml_less_venv(tmp_path / "yaml_less")
    _stage(repo, "tests/test_tmp_marked.py", MARKED_TEST)

    assert not (repo / ".venv").exists(), "repo venv must be absent for this scenario"

    proc = _run_hook(repo, yaml_less)
    out = proc.stdout + proc.stderr
    assert proc.returncode == 2, (
        f"no yaml-capable interpreter must fail CLOSED with exit 2, got "
        f"{proc.returncode}\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    assert "tried:" in out, f"diagnostic must name the tried candidates:\n{out}"
    assert str(repo / ".venv" / "bin" / "python") in out, (
        f"diagnostic must name the venv candidate path:\n{out}"
    )
    assert "python3" in out, f"diagnostic must name the python3 candidate:\n{out}"
    assert "PASS" not in out, f"a blocked hook must never print PASS:\n{out}"


@pytest.mark.test_id("TEST-RL-V02-055")
@pytest.mark.requirements("FEAT-RL-V02-REQ-055")
@pytest.mark.scenario("AC-RL-V02-12: the hook invokes the gate with --verify-diff --verify-metadata --staged --role ${VERITAS_ROLE:-auto}, unchanged by the interpreter fix.")
def test_hook_passes_same_gate_flags_as_before(tmp_path: Path) -> None:
    """The interpreter fix changed only WHICH python runs the gate, never HOW."""
    repo = _make_repo(tmp_path)
    yaml_less = _make_yaml_less_venv(tmp_path / "yaml_less")
    _make_yaml_venv(repo / ".venv")

    record = repo / "argv.json"
    # Overwrite the gate in the TEMP repo only: the hook addresses
    # scripts/veritas_gate.py, so a sidecar file would never be executed.
    (repo / "scripts" / "veritas_gate.py").write_text(
        "import json, sys\n"
        f"open({str(record)!r}, 'w').write(json.dumps(sys.argv))\n"
        "print('[recorder] invoked')\n",
        encoding="utf-8",
    )
    assert _git(repo, "add", "-A").returncode == 0
    assert _git(repo, "commit", "-q", "-m", "recorder").returncode == 0

    proc = _run_hook(repo, yaml_less)
    assert proc.returncode == 0, (
        f"recorder gate must succeed (rc={proc.returncode})\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    assert record.is_file(), (
        f"the hook never invoked the gate; stdout={proc.stdout} stderr={proc.stderr}"
    )
    argv = json.loads(record.read_text(encoding="utf-8"))
    assert argv[1:] == [
        "--verify-diff",
        "--verify-metadata",
        "--staged",
        "--role",
        "auto",
    ], f"gate flags changed: {argv[1:]}"


@pytest.mark.test_id("TEST-RL-V02-056")
@pytest.mark.requirements("FEAT-RL-V02-REQ-056")
@pytest.mark.scenario("AC-RL-V02-13: VERITAS_ROLE overrides the default role passed to the gate, as before the fix.")
def test_veritas_role_env_overrides_default_role(tmp_path: Path) -> None:
    """VERITAS_ROLE is forwarded; the default is auto when unset."""
    repo = _make_repo(tmp_path)
    yaml_less = _make_yaml_less_venv(tmp_path / "yaml_less")
    _make_yaml_venv(repo / ".venv")

    record = repo / "argv.json"
    (repo / "scripts" / "veritas_gate.py").write_text(
        "import json, sys\n"
        f"open({str(record)!r}, 'w').write(json.dumps(sys.argv))\n",
        encoding="utf-8",
    )
    assert _git(repo, "add", "-A").returncode == 0
    assert _git(repo, "commit", "-q", "-m", "recorder").returncode == 0

    proc = _run_hook(repo, yaml_less, VERITAS_ROLE="test_author")
    assert proc.returncode == 0, f"rc={proc.returncode} {proc.stdout} {proc.stderr}"
    argv = json.loads(record.read_text(encoding="utf-8"))
    assert argv[-2:] == ["--role", "test_author"], f"VERITAS_ROLE not forwarded: {argv}"


@pytest.mark.test_id("TEST-RL-V02-057")
@pytest.mark.requirements("FEAT-RL-V02-REQ-057")
@pytest.mark.scenario("AC-RL-V02-14: running these scenarios leaves the real repo .venv/bin/python in place and unmodified.")
def test_venv_untouched(tmp_path: Path) -> None:
    """These tests copy a venv into tmp_path; the repo's own must survive intact."""
    before = REPO_VENV_PY.exists()
    size_before = REPO_VENV_PY.stat().st_size if before else -1

    repo = _make_repo(tmp_path)
    _make_yaml_venv(repo / ".venv")
    _run_hook(repo, _make_yaml_less_venv(tmp_path / "yaml_less"))

    assert REPO_VENV_PY.exists() == before, "the real repo venv interpreter was removed"
    if before:
        assert REPO_VENV_PY.stat().st_size == size_before, (
            "the real repo venv interpreter was modified"
        )