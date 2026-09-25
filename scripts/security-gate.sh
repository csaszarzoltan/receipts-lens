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

python - <<'PY'
from pathlib import Path
blocked={'.env','id_rsa','id_ed25519'}
found=[]
for p in Path('.').rglob('*'):
    if any(x in p.parts for x in {'.git','node_modules','.next','.venv','__pycache__'}): continue
    if p.is_file() and (p.name in blocked or p.suffix in {'.pem','.key'}): found.append(str(p))
assert not found, f'possible secret files: {found}'
print('Security scan PASS: no credential files in the tree.')
PY

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

echo "Security gate: running ${#SECURITY_TESTS[@]} test files (MIME contract, tenant isolation, SSRF fetcher, magic bytes)."
pytest -q "${SECURITY_TESTS[@]}"
echo "Security gate PASS: credential scan, MIME-spoof, tenant-isolation, SSRF-fetcher and magic-byte regressions are green."
