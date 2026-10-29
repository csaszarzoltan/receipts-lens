# Task completion gate
Run on the committed tree:
1. `pytest -q`
2. `ruff check app tests`
3. `cd frontend && npm run typecheck && npm run build` (when frontend touched)
Then exercise the change via the real user path (browser/API) before calling it done; update docs + tests.
