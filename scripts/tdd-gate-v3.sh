#!/usr/bin/env bash
# TDD gate -- primary test set for the quality workflow.
#
# Every file listed below MUST exist. A missing file is a gate failure, not a
# reason to quietly run a smaller set: a `|| fallback` silently swallows a real
# test failure, so the gate could pass while a regression stood.
# The pre-flight loop turns "file not found" into a visible, explicit error.
set -euo pipefail

PRIMARY=(
  tests/test_us_010_018_provider_workflow.py
  tests/test_development_stories.py
  tests/test_export_readiness_workflow.py
  tests/test_accounting_readiness_ui.py
  tests/test_quality_service.py
)

missing=()
for test_file in "${PRIMARY[@]}"; do
  if [ ! -f "$test_file" ]; then
    missing+=("$test_file")
  fi
done

if [ ${#missing[@]} -gt 0 ]; then
  echo "TDD gate FAIL: primary test files are missing:" >&2
  printf '  - %s\n' "${missing[@]}" >&2
  echo "Add the test, or remove it from the primary set. Never fall back silently." >&2
  exit 1
fi

echo "TDD gate: running ${#PRIMARY[@]} primary test files (provider workflow, development stories, export/accounting readiness, quality service)."
pytest -q "${PRIMARY[@]}"
echo "TDD gate PASS: provider workflow, development stories, export/accounting readiness, and quality-service regressions are green."
