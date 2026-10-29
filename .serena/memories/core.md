# ReceiptLens core
Receipt intelligence workspace (v1.4): OCR (Tesseract / vision), confidence-scored review, accounting export, automation rules.
- `app/` FastAPI backend; flat module layout, `<feature>_api.py` / `_service.py` / `_models.py` triples (e.g. refund_*, quota_*, reconciliation_*). Entry: `app/main.py`, CLI `app/cli.py` (`receipts-lens`).
- `frontend/` Next.js 14 workspace (React 18, SWR, recharts, Tailwind).
- `tests/` pytest (traceability markers test_id/requirements/scenario); `tests/_disabled` is excluded.
- `alembic/` migrations; `app/product_migrations.py` for product DB. Local SQLite `receiptlens-product.db` in repo root.
- Docs: `docs/decisions/ADR-*.md` (decide before big code), `docs/engineering-standards.md`, `docs/specs/`, `docs/plans/`, `docs/lessons-learned.md`.
- Currency invariant: unmarked receipt with no history keeps null currency; never guess/write back provenance on read paths.
- Project CLAUDE.md is Hungarian; user talks Hungarian, written artifacts English.
- Stack/versions: `mem:tech_stack`. Commands: `mem:suggested_commands`. Style: `mem:conventions`. Done-gate: `mem:task_completion`.
