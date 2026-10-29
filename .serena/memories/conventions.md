# Conventions
- Commit subject: `<scope>: <description>` (log uses `fix(scope):`, `feat(scope):`, `test(scope):`). Stage by explicit path.
- Max 400 lines/file; type hints; docstrings where meaningful.
- Feature flow: research -> ADR -> test idea -> RED -> GREEN; small fixes direct.
- Every schema change needs an Alembic migration.
- No "done" without docs + tests.
- Module triple pattern api/service/models per feature.
