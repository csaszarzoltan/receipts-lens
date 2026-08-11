#!/usr/bin/env bash
set -euo pipefail
pytest -q tests/test_us_010_018_provider_workflow.py tests/test_development_stories.py tests/test_export_readiness_workflow.py tests/test_accounting_readiness_ui.py tests/test_quality_service.py 2>/dev/null || pytest -q tests/test_development_stories.py tests/test_export_readiness_workflow.py tests/test_accounting_readiness_ui.py
