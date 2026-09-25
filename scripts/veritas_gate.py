#!/usr/bin/env python3
"""VERITAS 1.1 — Deterministic Quality & Governance Gate Runner.

Receipts-Lens project. Ported from the MealMind reference implementation
(scripts/veritas_gate.py), adapted to receipts-lens product paths:
app/**, frontend/**, tests/**, frontend/e2e/**.

Provides automated, fail-closed enforcement of:
- Constitutional policies and unbendable R4 rules
- Strict role-based diff isolation (Implementer vs Test Author vs Spec Author)
- Path Eligibility Oracle (R0-R4 risk escalation; R3 = auth/payment/migration)
- Structured test metadata validation (test_id + requirements + scenario)
- History scan for committed secrets
- Deterministic command execution and audit logging
"""

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

# Ensure UTF-8 output encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001, S110 - best-effort console encoding only
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_DIR = REPO_ROOT / ".ai"
CONSTITUTIONAL_POLICY = AI_DIR / "constitutional-policy.yaml"
PROJECT_PROFILE = AI_DIR / "project-profile.yaml"
PERMISSIONS_POLICY = AI_DIR / "permissions.yaml"
QUALITY_GATES = AI_DIR / "quality-gates.yaml"
RISK_POLICY = AI_DIR / "risk-policy.yaml"
AUDIT_LOG = REPO_ROOT / ".agent-pipeline" / "audit" / "veritas_audit.jsonl"

# R3 sensitive paths requiring Assurance Path and human sign-off.
# Receipts-lens product paths: auth (auth_api, google_oidc, security,
# credential_store, intuit_oauth), payment/subscription, DB migrations.
R3_SENSITIVE_PATTERNS = [
    r"^app/auth_api\.py",
    r"^app/google_oidc\.py",
    r"^app/security\.py",
    r"^app/credential_store\.py",
    r"^app/intuit_oauth\.py",
    r"^app/.*auth.*",
    r"^app/subscriptions_api\.py",
    r"^app/subscription_alerts\.py",
    r"^app/.*payment.*",
    r"^app/.*stripe.*",
    r"^app/.*secret.*",
    r"^alembic/.*",
    r"^.*/migrations/.*",
    r"^.*\.migration\.py",
    r"^\.ai/constitutional-policy\.yaml",
]

SECRET_PATTERNS = [
    re.compile(
        r"(?i)(password|secret|api_key|token|private_key)\s*[:=]\s*"
        r"['\"][A-Za-z0-9_\-]{16,}['\"]"
    ),
    re.compile(r"sk_live_[0-9a-zA-Z]{24}"),
    re.compile(r"ghp_[0-9a-zA-Z]{36}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)aws_(?:access_key_id|secret_access_key)\s*[:=]\s*['\"]?\S{8,}"),
    re.compile(r"xox[bap]-[0-9A-Za-z\-]{10,}"),
    re.compile(r"AIza[0-9A-Za-z\-_]{20,}"),
]

# VERITAS test metadata markers. A marker counts as present only when it is
# called with a non-empty string literal value — a bare ``@pytest.mark.test_id``
# or an empty ``@pytest.mark.scenario("")`` carries no traceability and must not
# satisfy the metadata gate. A trailing ``,`` or ``)`` after the first argument
# keeps legal multi-argument markers (e.g. ``test_id("A", "B")``) valid.
REQUIRED_TEST_MARKERS = ("test_id", "requirements", "scenario")
_MARKER_PATTERNS = {
    name: re.compile(
        rf"pytest\.mark\.{re.escape(name)}\(\s*[\"'][^\"']+[\"']\s*[,)]"
    )
    for name in REQUIRED_TEST_MARKERS
}


# Git-context failures are gate failures with exit 2 (never a
# silent empty-diff PASS). Set from any fail-closed git branch.
_GIT_CONTEXT_FAILED = False


# Role inference for --role auto.
#
# The pre-commit hook and the CI PR job both pass ``--role auto``, which
# historically always meant "assume implementer". The implementer deny matrix
# in .ai/permissions.yaml covers tests/** and specs/**, so a test-only or
# spec-only commit was blocked — leaving the Test Author with --no-verify as
# the only way to work, which is exactly the escape the gate must prevent.
#
# Inference is deliberately narrow: it fires only when EVERY file falls under
# the same role's own allow-prefix below. Anything else — infra edits, mixed
# packets, or a path two roles both own — keeps the historical implementer
# default, which is the fail-closed side of the choice. The table is a hint
# about WHO is committing; .ai/permissions.yaml remains the authority and
# its deny matrix still runs over every file, so a stale prefix can only make
# the gate stricter, never looser.
ROLE_DOMAINS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("test_author", ("tests/", "frontend/e2e/", ".agent-pipeline/03_e2e_suites/")),
    ("spec_author", ("specs/", ".agent-pipeline/02_specs/", "docs/specs/")),
    ("reviewer", (".ai-execution/reviews/", ".agent-pipeline/04_defects/")),
)

# The historical --role auto behaviour, and the fail-closed fallback when the
# diff does not unambiguously belong to exactly one non-implementer role.
DEFAULT_ROLE = "implementer"


def _mark_git_context_failed() -> None:
    """Record that the gate failed for lack of trustworthy git context."""
    global _GIT_CONTEXT_FAILED
    _GIT_CONTEXT_FAILED = True


def human_approval_present() -> bool:
    """R3/R4 sign-off: VERITAS_APPROVAL (spec) or VERITAS_HUMAN_APPROVAL."""
    for var in ("VERITAS_APPROVAL", "VERITAS_HUMAN_APPROVAL"):
        if os.environ.get(var, "").strip():
            return True
    return False


def log_audit_event(event_type: str, details: dict, verdict: str):
    """Append an immutable event to the append-only audit log."""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "verdict": verdict,
        "details": details,
    }
    try:
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as e:
        print(f"[FATAL] Failed to write audit log (R4 Rule #6): {e}", file=sys.stderr)
        raise RuntimeError(f"Audit log write failure (R4 Rule #6): {e}") from e


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run git fail-closed. A missing/non-repository context is a gate failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"git execution failed: {exc}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown git error").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return result


def ensure_git_repository() -> None:
    result = _run_git(["rev-parse", "--is-inside-work-tree"])
    if result.stdout.strip().lower() != "true":
        raise RuntimeError("repository context is not a Git work tree")


def configured_diff_args(staged_only: bool = False) -> list[str]:
    """Select a deterministic local or CI comparison range."""
    if staged_only:
        return ["diff", "--cached"]
    base = os.environ.get("VERITAS_DIFF_BASE", "").strip()
    if base:
        _run_git(["rev-parse", "--verify", base])
        return ["diff", f"{base}...HEAD"]
    return ["diff", "HEAD"]


def get_git_diff_files(staged_only: bool = False) -> list[str]:
    """Return changed files, including untracked files; fail on untrusted Git state."""
    ensure_git_repository()
    if staged_only:
        result = _run_git(["diff", "--name-only", "--cached"])
        return sorted(
            {
                line.strip().replace("\\", "/")
                for line in result.stdout.splitlines()
                if line.strip()
            }
        )

    result = _run_git(["status", "--porcelain=v1", "--untracked-files=all"])
    files: set[str] = set()
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        files.add(path.replace("\\", "/"))
    return sorted(files)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_policies() -> bool:
    """Verify required policy presence, structure, 12-rule core, and pinned hashes."""
    print(">> [VERITAS GATE] Checking policy integrity...")
    policies = [
        CONSTITUTIONAL_POLICY,
        PROJECT_PROFILE,
        PERMISSIONS_POLICY,
        QUALITY_GATES,
        RISK_POLICY,
    ]
    missing = [str(x.relative_to(REPO_ROOT)) for x in policies if not x.is_file()]
    lock_file = AI_DIR / "policy-lock.json"
    if not lock_file.is_file():
        missing.append(str(lock_file.relative_to(REPO_ROOT)))
    if missing:
        print(f"[FAIL] Missing required VERITAS policy files: {missing}")
        log_audit_event("CHECK_POLICIES", {"missing": missing}, "FAIL")
        return False

    constitutional = CONSTITUTIONAL_POLICY.read_text(encoding="utf-8-sig", errors="strict")
    numbered_rules = re.findall(r"^\s{2}(\d+):\s+", constitutional, flags=re.MULTILINE)
    required_tokens = [
        'schema_version: "1.1"',
        'policy_id: "VERITAS-CONSTITUTIONAL-R4"',
        'status: "authoritative_immutable"',
        "constitutional_rules:",
        "fail_closed_modes:",
    ]
    if numbered_rules != [str(i) for i in range(1, 13)] or any(
        token not in constitutional for token in required_tokens
    ):
        print("[FAIL] Constitutional policy structure or 12-rule sequence is invalid.")
        log_audit_event("CHECK_POLICIES", {"error": "invalid_constitutional_core"}, "FAIL")
        return False

    try:
        lock = json.loads(lock_file.read_text(encoding="utf-8-sig"))
        expected = lock["sha256"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"[FAIL] Policy lock is invalid: {exc}")
        log_audit_event("CHECK_POLICIES", {"error": "invalid_policy_lock"}, "FAIL")
        return False

    mismatches = []
    for policy in policies:
        rel = policy.relative_to(REPO_ROOT).as_posix()
        actual = _sha256(policy)
        if expected.get(rel) != actual:
            mismatches.append(rel)
    if mismatches:
        print(f"[FAIL] Policy hash mismatch: {mismatches}")
        log_audit_event("CHECK_POLICIES", {"hash_mismatch": mismatches}, "FAIL")
        return False

    print("[PASS] Policy core, rule count, and pinned hashes are valid.")
    log_audit_event("CHECK_POLICIES", {"status": "ok", "hashes_verified": 5}, "PASS")
    return True


def load_permissions_matrix() -> dict[str, list[str]] | None:
    """Load deny patterns per role from .ai/permissions.yaml.

    Returns {role: [deny_glob, ...]} or None if the policy is missing or
    invalid — callers must fail closed on None.
    """
    try:
        raw = PERMISSIONS_POLICY.read_text(encoding="utf-8-sig")
        data = yaml.safe_load(raw)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        print(f"[FAIL] Cannot load permissions policy: {exc}")
        log_audit_event("VERIFY_DIFF", {"error": "permissions_load_failed"}, "FAIL")
        return None
    if not isinstance(data, dict) or not isinstance(data.get("roles"), dict):
        print("[FAIL] Permissions policy has no 'roles' mapping.")
        log_audit_event("VERIFY_DIFF", {"error": "permissions_roles_missing"}, "FAIL")
        return None
    matrix: dict[str, list[str]] = {}
    for role, cfg in data["roles"].items():
        deny = (cfg or {}).get("deny", []) if isinstance(cfg, dict) else []
        matrix[str(role)] = [str(p) for p in deny]
    return matrix


def check_role_permissions(role: str, files: list[str]) -> bool:
    """Enforce the permissions.yaml deny matrix for a single role."""
    matrix = load_permissions_matrix()
    if matrix is None:
        print("[FAIL] Permissions matrix unavailable (fail closed).")
        return False
    if role not in matrix:
        print(f"[FAIL] Unknown role '{role}' (fail closed).")
        log_audit_event(
            "VERIFY_DIFF",
            {"violation": "unknown_role", "role": role, "files": files},
            "FAIL",
        )
        return False
    violations: list[tuple[str, str]] = []
    for path in files:
        for pattern in matrix[role]:
            if pattern and fnmatch.fnmatchcase(path, pattern):
                violations.append((path, pattern))
                break
    if violations:
        print(f"[FAIL] Role '{role}' deny-matrix violation:")
        for path, pattern in violations:
            print(f"   - {path} matches deny '{pattern}'")
        log_audit_event(
            "VERIFY_DIFF",
            {
                "violation": "permissions_deny",
                "role": role,
                "hits": [f"{p} :: {d}" for p, d in violations],
            },
            "FAIL",
        )
        return False
    return True


def infer_role_from_files(files: list[str], staged_only: bool = False) -> str:
    """Infer the committing role from the changed files, or return the default.

    Used for ``--role auto``. Fails closed: any file outside every known
    role domain, or a diff spanning two role domains, keeps the historical
    ``implementer`` default rather than guessing.
    """
    candidates = [
        (role, prefixes)
        for role, prefixes in ROLE_DOMAINS
        if all(any(f.startswith(p) for p in prefixes) for f in files)
    ]
    if len(candidates) != 1:
        # 0 = no role owns this diff; >1 = the diff straddles roles, or a
        # role whose allow-list overlaps another's. Either way, do not infer.
        return DEFAULT_ROLE
    role = candidates[0][0]
    scope = "staged" if staged_only else "diff"
    print(f"[INFO] Inferred role '{role}' from {len(files)} {scope} file(s).")
    return role


def resolve_role(role: str, staged_only: bool = False) -> str:
    """Resolve ``--role auto`` against the actual diff, or pass it through."""
    if role != "auto":
        return role
    try:
        files = get_git_diff_files(staged_only=staged_only)
    except RuntimeError as exc:
        # No trustworthy diff to infer from: keep the default, and let
        # verify_diff raise the fail-closed git-context failure itself.
        print(f"[INFO] Role auto-detection unavailable ({exc}); assuming '{DEFAULT_ROLE}'.")
        return DEFAULT_ROLE
    return infer_role_from_files(files, staged_only=staged_only)


def verify_diff(role: str = DEFAULT_ROLE, staged_only: bool = False) -> bool:
    """Check git diff for role separation, sensitive paths, and secrets."""
    print(f">> [VERITAS GATE] Verifying git diff (role mode: {role})...")
    try:
        files = get_git_diff_files(staged_only=staged_only)
    except RuntimeError as exc:
        print(f"[FAIL] Cannot establish trustworthy Git diff: {exc}")
        log_audit_event(
            "VERIFY_DIFF", {"error": "git_context_unavailable", "detail": str(exc)}, "FAIL"
        )
        _mark_git_context_failed()
        return False

    if not files:
        print("[INFO] No modified files detected in diff.")
        return True

    print(f"   Modified files ({len(files)}):")
    for f in files:
        print(f"     - {f}")

    # Role separation check: enforce the permissions.yaml deny matrix.
    if not check_role_permissions(role, files):
        return False

    # Rule 1: Constitutional policy immutability
    if ".ai/constitutional-policy.yaml" in files and not human_approval_present():
        print(
            "[FAIL] Constitutional Policy (.ai/constitutional-policy.yaml) "
            "cannot be modified autonomously (R4 Rule #1)."
        )
        log_audit_event(
            "VERIFY_DIFF",
            {"violation": "constitutional_tamper", "files": files},
            "FAIL",
        )
        return False

    # Detect touches
    touches_app = any(f.startswith(("app/", "frontend/app/")) for f in files)
    touches_tests = any(f.startswith(("tests/", "frontend/e2e/")) for f in files)
    touches_specs = any(
        f.startswith(("specs/", ".agent-pipeline/02_specs/")) for f in files
    )

    # Role separation (R4 Rule #8): implementer cannot touch tests/specs
    # together with code. The deny matrix already failed the change above;
    # this is a defense-in-depth mixed-diff guard.
    if role == "implementer" and (touches_tests or touches_specs):
        print("[FAIL] Role Isolation Violation (R4 Rule #8).")
        print("   Implementer cannot modify code and tests/specs in 1 change.")
        print(
            f"   Touches app: {touches_app}, tests: {touches_tests}, "
            f"specs: {touches_specs}"
        )
        print("   Split into separate Test Author and Implementer packets.")
        log_audit_event(
            "VERIFY_DIFF",
            {"violation": "role_isolation", "files": files},
            "FAIL",
        )
        return False

    # Check for R3 sensitive paths
    r3_touched = []
    for f in files:
        for pat in R3_SENSITIVE_PATTERNS:
            if re.match(pat, f):
                r3_touched.append(f)
                break

    if r3_touched and not human_approval_present():
        print(f"[FAIL] R3 sensitive paths touched without human approval: {r3_touched}")
        print("   Path Eligibility Oracle requires Assurance Path and sign-off.")
        log_audit_event(
            "VERIFY_DIFF",
            {"violation": "r3_approval_missing", "files": r3_touched},
            "FAIL",
        )
        return False

    # Secret scanning
    try:
        diff_args = configured_diff_args(staged_only)
        diff_text = _run_git(diff_args).stdout
        # Git diff omits untracked file contents, so scan every changed file directly too.
        for changed_file in files:
            candidate = REPO_ROOT / changed_file
            if candidate.is_file() and candidate.stat().st_size <= 5 * 1024 * 1024:
                diff_text += "\n" + candidate.read_text(encoding="utf-8", errors="replace")
    except RuntimeError as exc:
        print(f"[FAIL] Secret scan cannot obtain Git diff: {exc}")
        log_audit_event("VERIFY_DIFF", {"error": "secret_scan_diff_unavailable"}, "FAIL")
        return False

    for secret_pat in SECRET_PATTERNS:
        matches = secret_pat.findall(diff_text)
        if matches:
            print(f"[FAIL] Potential secret detected matching pattern: {matches[0]}")
            log_audit_event(
                "VERIFY_DIFF", {"violation": "secret_leak_detected"}, "FAIL"
            )
            return False

    print("[PASS] Diff verification successful. Safety checks passed.")
    log_audit_event("VERIFY_DIFF", {"files_count": len(files), "role": role}, "PASS")
    return True


def verify_test_metadata(staged_only: bool = False) -> bool:
    """Require test_id, requirements, and scenario metadata on modified Python tests."""
    print(">> [VERITAS GATE] Verifying structured test metadata...")
    try:
        files = get_git_diff_files(staged_only=staged_only)
    except RuntimeError as exc:
        print(f"[FAIL] Cannot establish test delta: {exc}")
        log_audit_event("VERIFY_METADATA", {"error": "git_context_unavailable"}, "FAIL")
        _mark_git_context_failed()
        return False
    test_files = [
        f
        for f in files
        if f.startswith(("tests/", ".agent-pipeline/03_e2e_suites/")) and f.endswith(".py")
    ]
    if not test_files:
        print("[INFO] No Python test files modified.")
        return True

    missing: list[str] = []
    for test_file in test_files:
        path = REPO_ROOT / test_file
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8-sig", errors="strict").splitlines()
        for index, line in enumerate(lines):
            match = re.match(r"\s*(?:async\s+)?def\s+(test_[A-Za-z0-9_]+)", line)
            if not match:
                continue
            decorators = []
            cursor = index - 1
            while cursor >= 0 and lines[cursor].lstrip().startswith("@"):
                decorators.append(lines[cursor].strip())
                cursor -= 1
            block = "\n".join(decorators)
            absent = [
                name
                for name in REQUIRED_TEST_MARKERS
                if not _MARKER_PATTERNS[name].search(block)
            ]
            if absent:
                missing.append(f"{test_file}::{match.group(1)} missing {','.join(absent)}")

    if missing:
        print(f"[FAIL] {len(missing)} tests lack mandatory VERITAS metadata:")
        for item in missing[:20]:
            print(f"     - {item}")
        log_audit_event("VERIFY_METADATA", {"missing": missing}, "FAIL")
        return False
    print("[PASS] All modified Python tests have test_id, requirements, and scenario metadata.")
    log_audit_event("VERIFY_METADATA", {"files_count": len(test_files)}, "PASS")
    return True


def check_history_secrets(max_commits: int = 50) -> bool:
    """History scan — committed secrets in product paths fail the gate.

    Runs ``git log -S`` per literal probe plus ``git log -G`` per
    regex probe over the last ``max_commits`` commits. Any hit = FAIL.
    Fail-closed on git errors (exit 2 path via _mark_git_context_failed).
    """
    print(">> [VERITAS GATE] Scanning git history for committed secrets...")
    try:
        ensure_git_repository()
    except RuntimeError as exc:
        print(f"[FAIL] Cannot scan history without git context: {exc}")
        log_audit_event("HISTORY_SCAN", {"error": "git_context_unavailable"}, "FAIL")
        _mark_git_context_failed()
        return False
    probes = [
        "BEGIN PRIVATE KEY",
        "aws_secret_access_key",
        "xoxb-",
    ]
    # Regex-shaped probes (sk_live_/ghp_/AIza) match documentation of the
    # scanner itself — verify those with content grep (-G), not -S pickaxe.
    regex_probes = [
        (r"sk_live_[0-9a-zA-Z]{24}", "sk_live_"),
        (r"ghp_[0-9a-zA-Z]{36}", "ghp_"),
        (r"AIza[0-9A-Za-z\-_]{20,}", "AIza"),
    ]
    history_paths = ["app", "frontend", "tests"]
    hits: list[str] = []
    for probe in probes:
        try:
            result = _run_git(
                [
                    "log",
                    f"--max-count={max_commits}",
                    "-S",
                    probe,
                    "--oneline",
                    "--",
                    *history_paths,
                ]
            )
        except RuntimeError as exc:
            print(f"[FAIL] History scan git error: {exc}")
            log_audit_event("HISTORY_SCAN", {"error": "git_log_failed"}, "FAIL")
            _mark_git_context_failed()
            return False
        for line in result.stdout.splitlines():
            if line.strip():
                hits.append(f"{probe} :: {line.strip()[:100]}")
    for pattern, label in regex_probes:
        try:
            result = _run_git(
                [
                    "log",
                    f"--max-count={max_commits}",
                    "-G",
                    pattern,
                    "--oneline",
                    "--",
                    *history_paths,
                ]
            )
        except RuntimeError as exc:
            print(f"[FAIL] History scan git error: {exc}")
            log_audit_event("HISTORY_SCAN", {"error": "git_log_failed"}, "FAIL")
            _mark_git_context_failed()
            return False
        for line in result.stdout.splitlines():
            if line.strip():
                hits.append(f"{label}<regex> :: {line.strip()[:100]}")
    if hits:
        print(f"[FAIL] {len(hits)} committed-secret hit(s) in history:")
        for item in hits[:10]:
            print(f"   - {item}")
        log_audit_event("HISTORY_SCAN", {"hits": hits[:20]}, "FAIL")
        return False
    print(f"[PASS] No committed secrets in last {max_commits} commits.")
    log_audit_event("HISTORY_SCAN", {"max_commits": max_commits, "hits": 0}, "PASS")
    return True


def load_quality_commands() -> list[str]:
    """Read regression commands from .ai/project-profile.yaml.

    The runner executes the profile's ``quality_commands.regression``
    lines verbatim — never a hardcoded pytest-only suite. Returns []
    on any load/parse problem; callers must fail closed on [].
    """
    try:
        raw = PROJECT_PROFILE.read_text(encoding="utf-8-sig")
        data = yaml.safe_load(raw)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        print(f"[FAIL] Cannot load project profile: {exc}")
        log_audit_event("FULL_SUITE", {"error": "profile_load_failed"}, "FAIL")
        return []
    cmds = ((data or {}).get("quality_commands") or {}).get("regression", [])
    if not isinstance(cmds, list) or not all(isinstance(c, str) for c in cmds):
        print("[FAIL] Project profile quality_commands.regression is invalid.")
        log_audit_event("FULL_SUITE", {"error": "profile_regression_invalid"}, "FAIL")
        return []
    return [c for c in cmds if c.strip()]


def _run_profile_command(cmd: str) -> bool:
    """Execute one profile regression line via the shell, fail-closed."""
    print(f"   $ {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=REPO_ROOT,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"[FAIL] Regression command failed to start: {cmd} ({exc})")
        return False
    if result.returncode != 0:
        print(f"[FAIL] Regression command exited {result.returncode}: {cmd}")
        return False
    return True


def run_full_suite() -> bool:
    """Execute syntax check, lint, and profile-driven regression suite."""
    print(">> [VERITAS GATE] Executing regression verification...")

    # 1. Syntax compileall
    print("   [1/3] Running syntax compilation...")
    res1 = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "app", "tests"],
        cwd=REPO_ROOT,
        check=False,
    )
    if res1.returncode != 0:
        print("[FAIL] Syntax compilation failed.")
        return False

    # 2. Ruff check
    print("   [2/3] Running ruff lint check...")
    res2 = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "app", "tests"],
        cwd=REPO_ROOT,
        check=False,
    )
    if res2.returncode != 0:
        print("[FAIL] Ruff lint check failed.")
        return False

    # 3. Profile-driven regression: every
    # quality_commands.regression line from .ai/project-profile.yaml.
    cmds = load_quality_commands()
    if not cmds:
        print("[FAIL] No regression commands in project profile (fail closed).")
        return False
    print(f"   [3/3] Running {len(cmds)} profile regression command(s)...")
    for cmd in cmds:
        if not _run_profile_command(cmd):
            print("[FAIL] Profile regression suite failed.")
            log_audit_event("FULL_SUITE", {"failed_command": cmd}, "FAIL")
            return False

    print("[PASS] All regression checks passed.")
    log_audit_event("FULL_SUITE", {"status": "success"}, "PASS")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="VERITAS 1.1 Deterministic Gate Runner (receipts-lens)"
    )
    parser.add_argument(
        "--check-policies", action="store_true", help="Verify policy files"
    )
    parser.add_argument(
        "--verify-diff", action="store_true", help="Verify git diff"
    )
    parser.add_argument(
        "--verify-metadata", action="store_true", help="Verify test metadata"
    )
    parser.add_argument(
        "--staged", action="store_true", help="Inspect only staged git changes"
    )
    parser.add_argument(
        "--role",
        default=DEFAULT_ROLE,
        help=(
            "Assumed role (permissions.yaml deny matrix enforced). 'auto' "
            "infers test_author / spec_author / reviewer when every changed "
            f"file falls in that role's domain, else '{DEFAULT_ROLE}'."
        ),
    )
    parser.add_argument(
        "--run-suite", action="store_true", help="Run full regression suite"
    )
    parser.add_argument(
        "--history-scan",
        action="store_true",
        help="History scan: git log over last 50 commits for committed secrets.",
    )
    parser.add_argument("--check-all", action="store_true", help="Run all standard gate checks")

    args = parser.parse_args()

    # 'auto' is kept for CI / pre-commit hook compat: it resolves against the
    # real diff so a test-only or spec-only packet is judged as that role
    # instead of being denied outright by the implementer matrix. Anything
    # ambiguous stays on DEFAULT_ROLE.
    args.role = resolve_role(args.role, staged_only=args.staged)

    if not any(
        [
            args.check_policies,
            args.verify_diff,
            args.verify_metadata,
            args.run_suite,
            args.history_scan,
            args.check_all,
        ]
    ):
        args.check_all = True

    success = True
    if args.check_policies or args.check_all:
        success = check_policies() and success

    if args.verify_diff or args.check_all:
        success = verify_diff(role=args.role, staged_only=args.staged) and success

    if args.verify_metadata or args.check_all:
        success = verify_test_metadata(staged_only=args.staged) and success

    if args.history_scan or args.check_all:
        success = check_history_secrets() and success

    if args.run_suite or args.check_all:
        success = run_full_suite() and success

    if not success:
        print("\n[BLOCKED] VERITAS Gate Check FAILED. Execution blocked.")
        # Git-context failures (not-a-repo / git command errors) are
        # infra-distrust failures, not ordinary gate violations: exit 2 so
        # callers (CI, pre-commit) never mistake them for a clean PASS or
        # a plain FAIL(1). Never PASS on an empty/unreadable diff.
        if _GIT_CONTEXT_FAILED:
            sys.exit(2)
        sys.exit(1)

    print("\n[OK] VERITAS Gate Check PASSED. Execution permitted.")
    sys.exit(0)


if __name__ == "__main__":
    main()
