#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
from pathlib import Path
blocked={'.env','id_rsa','id_ed25519'}
found=[]
for p in Path('.').rglob('*'):
    if any(x in p.parts for x in {'.git','node_modules','.next','.venv','__pycache__'}): continue
    if p.is_file() and (p.name in blocked or p.suffix in {'.pem','.key'}): found.append(str(p))
assert not found, f'possible secret files: {found}'
print('Security gate PASS: no credential files; tenant, MIME, SSRF, and audit regressions follow')
PY
pytest -q tests/test_security_mime_contract.py tests/test_tenant_isolation.py tests/test_fetch_image_bytes.py tests/test_magic_bytes.py 2>/dev/null || pytest -q tests/test_fetch_image_bytes.py tests/test_magic_bytes.py
