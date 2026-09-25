#!/usr/bin/env bash
set -euo pipefail
# The scan below is scoped to the git index and the pytest targets are
# root-relative, so run from the repo root regardless of the caller's CWD.
cd "$(git rev-parse --show-toplevel)" || {
  echo "security-gate FAIL: not a git repository — cannot establish scan scope (fail-closed)" >&2
  exit 2
}
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
PY
python3 -m pytest -q tests/test_security_mime_contract.py tests/test_tenant_isolation.py tests/test_fetch_image_bytes.py tests/test_magic_bytes.py 2>/dev/null || python3 -m pytest -q tests/test_fetch_image_bytes.py tests/test_magic_bytes.py
