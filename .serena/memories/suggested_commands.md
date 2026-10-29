# Commands
- Backend tests: `pytest -q` (testpaths=tests, addopts -q). Lint: `ruff check app tests`.
- Frontend (in `frontend/`): `npm run dev|build|typecheck|test:ux|test:ux:e2e`.
- CLI: `receipts-lens` (app.cli:main).
- Host is shared: never `pkill -f`; kill by pid after checking `/proc/<pid>/cwd`. Never run dev server where a prod build matters.
