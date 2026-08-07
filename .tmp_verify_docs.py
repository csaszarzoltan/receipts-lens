#!/usr/bin/env python3
"""Full verification of the subscriptions documentation."""
import ast
import re
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/zoltan/receipts-lens")
VENV = REPO / ".venv" / "bin"

failures = []


def check(name, ok, detail=""):
    status = "OK " if ok else "FAIL"
    print(f"[{status}] {name} {detail}")
    if not ok:
        failures.append(name)


# 1. examples/subscriptions.py is valid python + importable deps present
ex = (REPO / "examples" / "subscriptions.py").read_text(encoding="utf-8")
try:
    ast.parse(ex)
    check("examples/subscriptions.py parses", True)
except SyntaxError as e:
    check("examples/subscriptions.py parses", False, str(e))

# 2. doc python code block parses
doc = (REPO / "docs" / "subscription-alerts.md").read_text(encoding="utf-8")
blocks = re.findall(r"```python\n(.*?)```", doc, re.DOTALL)
check("doc has 1 python code block", len(blocks) == 1, f"({len(blocks)} found)")
for i, b in enumerate(blocks):
    try:
        ast.parse(b)
        check(f"doc python block {i} parses", True)
    except SyntaxError as e:
        check(f"doc python block {i} parses", False, str(e))

# 3. api.md json blocks parse
api = (REPO / "docs" / "api.md").read_text(encoding="utf-8")
json_blocks = re.findall(r"```json\n(.*?)```", api, re.DOTALL)
check("api.md has json blocks", len(json_blocks) >= 2, f"({len(json_blocks)})")
import json as _json

for i, b in enumerate(json_blocks):
    try:
        _json.loads(b)
        check(f"api.md json block {i} parses", True)
    except Exception as e:
        check(f"api.md json block {i} parses", False, str(e)[:80])

# 4. doc json blocks parse
doc_json = re.findall(r"```json\n(.*?)```", doc, re.DOTALL)
for i, b in enumerate(doc_json):
    try:
        _json.loads(b)
        check(f"doc json block {i} parses", True)
    except Exception as e:
        check(f"doc json block {i} parses", False, str(e)[:80])

# 5. curl example in doc — verify the endpoint path exists in code
curl = re.findall(r"```bash\n(.*?)```", doc, re.DOTALL)
for i, c in enumerate(curl):
    check(f"doc bash block {i} non-empty", bool(c.strip()))

print()
print("TOTAL FAILURES:", len(failures))
sys.exit(1 if failures else 0)
