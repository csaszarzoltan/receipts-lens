#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
from pathlib import Path
for name in ['README.md','CHANGELOG.md','FEATURES-DONE.md','development-report.md','docs/product-workflows.md']:
    p=Path(name); assert p.is_file() and p.stat().st_size>100, name
readme=Path('README.md').read_text(encoding='utf-8').lower()
for phrase in ['confidence','export','automation','email']:
    assert phrase in readme, phrase
print('Documentation sync gate PASS: required documents and capability references are present')
PY
