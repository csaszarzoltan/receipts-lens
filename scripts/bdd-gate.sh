#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
import json
from pathlib import Path
p=Path('implementation-plan.md').read_text(encoding='utf-8')
a=p.index('```json',p.index('## User Stories (BDD)'))+7
b=p.index('```',a)
stories=json.loads(p[a:b])
assert len(stories)>=9
assert len({s['id'] for s in stories})==len(stories)
assert all(5<=len(s['gui_flow'])<=8 for s in stories)
assert all(len(s['acceptance_criteria'])>=3 for s in stories)
tests=Path('tests/test_development_stories.py').read_text(encoding='utf-8')
missing=[s['id'] for s in stories if f"test_{s['id'].lower().replace('-', '_')}_" not in tests]
assert not missing, missing
print(f'BDD gate PASS: {len(stories)} stories are structurally valid and mapped to behavioral tests')
PY
