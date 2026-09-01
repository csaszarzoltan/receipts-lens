# SPEC-002 / SPEC-024 / SPEC-036 Verification Report

Date: 2026-09-01

## Implemented
- Login role and household selectors removed; the local one-click path resolves the owner/admin identity automatically.
- `base_currency` added to tenant-scoped preferences, normalized to uppercase and preserved across partial updates.
- `POST /product/preferences` added as an alias to the existing update contract.
- Currency selector added to profile settings with immediate persistence status.
- Receipt cards show source amount and, when a stored current/date-valid exchange rate exists, the converted base-currency amount.
- SPEC-002, SPEC-024 and SPEC-036 requirements and the two requested GUI suites updated.

## Targeted pytest
Exit code: `0`
```text
[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[33m                                                                  [100%][0m
[33m=============================== warnings summary ===============================[0m
../../../opt/pyvenv/lib/python3.12/site-packages/fastapi/testclient.py:1
  /opt/pyvenv/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html

```

## Python syntax
`app/advanced_workspace.py` and `app/product_api.py`: PASS

## Playwright
The requested command was executed but could not start because the extracted project did not contain an installed `@playwright/test` dependency (`MODULE_NOT_FOUND`). This is an environment/dependency blocker, not a passing E2E result.

## TypeScript typecheck
The command was executed but project validation was blocked by the missing local frontend dependency installation. The compiler could not resolve React, SWR and their declarations across the existing project.

## Full regression
A full `pytest -q` run was started after the targeted GREEN run but did not finish within the available execution window. It is therefore recorded as incomplete, not as GREEN.
