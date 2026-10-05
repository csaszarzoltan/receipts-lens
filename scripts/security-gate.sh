#!/usr/bin/env bash
# Security gate -- credential scan, then the tenant / MIME / SSRF test set.
#
# Every test file listed below MUST exist. A missing file is a gate failure, not
# a reason to quietly run a smaller set: the previous `|| fallback` swallowed ANY
# non-zero pytest exit, so a failing tenant-isolation test still printed
# "Security gate PASS" and exited 0. The pre-flight loop below turns "file not
# found" into a visible, explicit error, and the pytest exit code is no longer
# discarded.
set -euo pipefail

# The scan below is scoped to the git index and the pytest targets are
# root-relative, so run from the repo root regardless of the caller's CWD.
#
# NOTE: `cd "$(git rev-parse --show-toplevel)" || exit 2` does NOT work as a
# fail-closed guard. When git fails the substitution expands to the empty
# string, and bash treats `cd ""` as a no-op that returns 0 -- so the `||` branch
# never fires and the gate continued in a directory with no git context. The
# top level is therefore captured and checked explicitly, before anything else.
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$REPO_ROOT" ] || [ ! -d "$REPO_ROOT" ]; then
  echo "security-gate FAIL: not a git repository — cannot establish scan scope (fail-closed)" >&2
  exit 2
fi
cd "$REPO_ROOT"
# Fail-closed pre-flight: the security test set must be COMPLETE before anything
# else runs. This runs BEFORE the credential scan on purpose. A missing test file
# is a different outcome from a credential leak, and the two must never be
# reported as one result. (ZOO-24: the pre-flight used to run *after* the scan,
# so the scan had already printed "Security gate PASS" before the gate went on
# to fail for an entirely unrelated reason.)
SECURITY_TESTS=(
  tests/test_security_mime_contract.py
  tests/test_tenant_isolation.py
  tests/test_fetch_image_bytes.py
  tests/test_magic_bytes.py
)
missing=()
for test_file in "${SECURITY_TESTS[@]}"; do
  if [ ! -f "$test_file" ]; then
    missing+=("$test_file")
  fi
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "Security gate FAIL: required test files are missing:" >&2
  printf '  - %s\n' "${missing[@]}" >&2
  echo "Add the test, or remove it from the security set. Never fall back silently." >&2
  exit 1
fi

python3 - <<'PY'
"""Secret-file scan.

Two different questions, two different answers (ZOO-24):

  * **Tracked** (in the git index) is repo content. A credential file here is
    a leak the moment it is committed or even merely staged — FAIL the gate.
  * **Untracked** (gitignored or not) is local-only state that this gate can
    never let through. Failing on it is what made the gate unusable on the
    developer's main checkout, where a local ``.env`` is expected. Report it,
    but do not block — the local file is a real secret the developer should
    know about, not a gate violation.

Scanning the index also removes the hand-maintained exclusion list
(``.git``/``.venv``/``node_modules``/``__pycache__``/``.next``): git already
knows what is and is not part of the repository.
"""
import subprocess
import sys
from pathlib import PurePosixPath

BLOCKED_NAMES = {'.env', 'id_rsa', 'id_ed25519'}
BLOCKED_SUFFIXES = {'.pem', '.key'}


def _ls_files(*args):
    """Repo-relative paths from ``git ls-files -z <args>``.

    Fail-closed: an unusable git context exits 2 rather than yielding an empty
    list that would read as a silent PASS.
    """
    result = subprocess.run(['git', 'ls-files', '-z', *args], capture_output=True)  # noqa: PLW1510
    if result.returncode != 0:
        detail = result.stderr.decode('utf-8', 'replace').strip()
        print(f'security-gate FAIL: git ls-files failed: {detail}', file=sys.stderr)
        sys.exit(2)
    return [p for p in result.stdout.decode('utf-8', 'surrogateescape').split('\0') if p]


def is_secret(path):
    """Secret-looking by name or extension — the rule the old rglob scan used."""
    p = PurePosixPath(path)
    return p.name in BLOCKED_NAMES or p.suffix in BLOCKED_SUFFIXES


all_tracked = _ls_files()
tracked_hits = [p for p in all_tracked if is_secret(p)]
if tracked_hits:
    print(f'security-gate FAIL: tracked secret files: {tracked_hits}', file=sys.stderr)
    sys.exit(1)

# ``--directory`` collapses untracked trees so .venv/ and node_modules/ are not
# walked, and untracked files are listed *including* gitignored ones — a local
# .env is exactly what this warning exists to surface. Collapsed entries end in
# '/' and are skipped, so this warning is not exhaustive about secrets buried
# inside ignored directories; the tracked check above is.
untracked = _ls_files('--others', '--directory')
untracked_hits = [p for p in untracked if not p.endswith('/') and is_secret(p)]
if untracked_hits:
    print(
        f'security-gate WARN: untracked local secret files (not in the repo, '
        f'gate still PASSES): {untracked_hits}'
    )

print(
    f'Security gate PASS: scanned {len(all_tracked)} tracked files, no credential files; '
    'tenant, MIME, SSRF, and audit regressions follow'
)
sys.exit(0)
PY
echo "Security gate: running ${#SECURITY_TESTS[@]} test files (MIME contract, tenant isolation, SSRF fetcher, magic bytes)."
pytest -q "${SECURITY_TESTS[@]}"
echo "Security gate PASS: credential scan, MIME-spoof, tenant-isolation, SSRF-fetcher and magic-byte regressions are green."

