# Lessons Learned — Ruff P0 Audit (roadmap-010)

Date: 2026-08-14
Scope: `ruff check .` to 0 errors with the repo's own config, verified with the
repo `.venv` toolchain.

## Verification baseline

- Linter: `ruff 0.16.1` (repo `.venv`; `pyproject.toml` dev dep is `ruff>=0.4`,
  so the effective version comes from the lockfile/venv).
- Command: `PATH="$PWD/.venv/bin:$PATH" ruff check .`
  (default excludes cover `.venv`, `node_modules`, `__pycache__`; `*.db` is not
  linted by ruff at all).
- Tests: `PATH="$PWD/.venv/bin:$PATH" python -m pytest tests/ -q`

## What we found

The task brief mentioned "15 errors (E402 / F821 / E741)". The repo's pinned
ruff (0.16.1) reported **241 errors** instead — the brief's number matched an
older ruff era and the repo config had already removed E402/E741 from the
default rule set. Always re-measure with the repo `.venv` before trusting a
count from a task brief.

Error classes at start (241 total):

| Rule | Count | Nature |
|---|---|---|
| B008 | 97 | FastAPI `File(...)` / `Depends(...)` in argument defaults — idiomatic |
| I001 | 45 | Import sorting — auto-fixable |
| RUF059 | 17 | Unused unpacked variables in tests |
| BLE001 | 13 | Defensive catch-all `except Exception` |
| SIM117 | 10 | Nested `with` statements |
| UP017 / DTZ* | 9 | Timezone-naive datetime usage |
| FURB157 / UP024 / UP045 / UP035 / UP037 | 10 | Modernisation nits, auto-fixable |
| B026 | 6 | Star-arg unpacking after keyword argument |
| EXE001 | 4 | Shebang present, file not executable |
| TRY004 / F821 / RUF012 / B017 / PLW1510 / PIE810 / SIM102 / RUF100 / RUF019 | 30 | Mixed — 3×F821 were real test corruption |

## What we fixed (code)

1. **Repaired 2 dead/corrupted tests** (the highest-value find):
   - `tests/test_consolidated_workspace.py` — `test_asset_api_rejects_cross_tenant_access`
     body was stranded as unreachable code inside `get_all_paths()`; the test
     never ran. Restored it as a real test; it now exercises the tenant-isolation
     404 path (with the `X-Role` header the strict-auth dependency requires).
   - `tests/test_accounting_readiness_ui.py` — `test_08_dashboard_preferences_are_persisted_by_role`
     had the same stranding pattern (dead body after a `get_all_paths` copy).
     Restored; it now actually asserts role-scoped dashboard preferences.
   These were invisible for a long time: the suite was "green" while two tests
   did nothing.

2. **B026** — `real_client(transport=transport, *a, **kw)` → `real_client(*a, transport=transport, **kw)`
   in 6 test sites (lambda wrappers around httpx mock transports).

3. **DTZ003 / DTZ011 / DTZ007** — `datetime.utcnow()` → `datetime.now(UTC)`,
   `date.today()` → `datetime.now(UTC).date()`, `datetime.strptime` date-only
   validation → `date.fromisoformat` (timezone-aware hygiene in `app/api.py`,
   `app/accounting_workspace.py`).

4. **RUF059** — unused unpacked variables renamed to `_`-prefixed names
   (17 sites in tests + `app/report_generator.py`).

5. **RUF012** — `_FakeReceipt.items: list = []` / `confidence: dict = {}` →
   immutable tuple defaults (mutable class-attribute defaults).

6. **SIM102 / SIM117 / PIE810** — flattened nested `if`s and combined nested
   `with` statements; `startswith(("http://", "https://"))` tuple form.

7. **PLW1510** — `subprocess.run(...)` gained `check=True` (replacing a manual
   `assert proc.returncode`).

8. **EXE001** — `chmod +x` on the four `examples/*.py` shebang scripts.

9. **B017** — `pytest.raises(Exception)` → `pytest.raises(HTTPException)` in two
   URL-fetch tests (the guarded function always raises HTTPException).

10. **I001 / UP017 / UP024 / UP035 / UP037 / FURB157 / UP045 / FURB167 /
    RUF019 / RUF100** — resolved by `ruff check . --fix` (90 auto-fixes) plus a
    final `--unsafe-fixes` pass on the RUF059 sites.

## What we configured instead (deliberate)

Kept as per-file ignores, following the repo's existing convention
(`app/api_v2.py`, `app/auth_api.py`, `app/batch.py`, `app/ocr.py`,
`app/inbox_service.py` already had per-file ignores):

- **B008** on `app/api.py` + `app/product_api.py` — FastAPI `Depends`/`File`
  defaults are the framework idiom; refactoring to module-level singletons adds
  noise without value.
- **BLE001** on `app/api.py`, `app/advanced_workspace.py`, `app/categorizer.py`,
  `app/credential_store.py`, `app/preprocessing.py`,
  `app/provider_export_service.py`, `tests/test_fetcher_wiring.py`,
  `tests/test_security_egress_allowlist.py` — defensive catch-alls with safe
  fallbacks (OCR failure → `None` result, webhook delivery → log, JSON parse →
  `{}`), the same policy the repo already applied to its other modules.
- **TRY004** on `app/api.py` — `ValueError` in the Pydantic field validator is
  a deliberate API contract: Pydantic maps `ValueError` → 422, while
  `TypeError` would surface as 500. Tests pin the 422 behaviour.

## Pitfall we hit

The first fix pass converted the Pydantic validator's `ValueError`s to
`TypeError` (what TRY004 wants), which **broke the 422 contract**: two
`test_duplicate_detection` tests failed because `TypeError` escapes Pydantic as
a 500. Reverted the code change and moved TRY004 to the per-file ignore list.
Lesson: in Pydantic validators, `ValueError` is the *mechanism* for 422 — don't
"fix" it away.

## Final state

- `ruff check .` → **0 errors** (was 241).
- `pytest tests/ -q` → all tests pass except
  `tests/test_fetcher_wiring.py::test_batch_isolates_private_host_without_500`,
  which is a pre-existing known-failing test tracked in `.pytest-known-green.txt`
  (it waits for P0-3 fetcher wiring; verified failing on the pre-audit HEAD too).
- Two previously-dead tests now execute and pass.
