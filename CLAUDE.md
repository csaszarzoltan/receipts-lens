# ReceiptLens — Claude Instructions

> Ezt olvassa minden agent belépéskor. Rövid.

## Mi ez
**ReceiptLens** — receipt intelligence workspace (v1.4, élő). Számla OCR (Tesseract / vision), confidence-scored review, accounting export, automation rules. **Stack:** FastAPI (app/) + Next.js workspace (frontend/)

## Hol mi van
- `docs/decisions/ADR-*.md` — minden nagyobb döntés 1 oldal (template: ADR-000-template.md)
- `docs/decisions/` — archív döntések is itt (dátum-név: `2026-08-13-*.md`)
- `docs/research/` — kutatások (max 5 oldal, comparison table ha több opció)
- `docs/engineering-standards.md` — UX/API/adat/kódminőség checklist (ellenőrizhető követelmények)
- `docs/specs/` — feature-specifikációk
- `docs/plans/` — feature tervek
- `app/` / `frontend/` / `tests/` / `alembic/` — kód + migrációk + tesztek

## Szabályok (röviden)
- Döntés nélkül ne kódolj nagyot: kutatás → ADR → utána kód (kis fix mehet direktben)
- Minden feature: előbb teszt-ötlet, aztán kód (RED → GREEN pytest-tel)
- Max 400 sor/file; type hints + docstring ahol értelmes
- Commit: `<scope>: <leírás>` formátum
- Migráció: ahol van Alembic — minden séma-változás migrációval
- Docs + tesztek nélkül nincs „kész”

## Ellenőrzés
```bash
pytest -q
ruff check app tests
cd frontend && npm run typecheck && npm run build
```

## Tudás forrása (prioritás)
1. Ez a file
2. `docs/decisions/ADR-*.md` + `docs/engineering-standards.md`
3. Kódgráf (ha indexelve) / `git log`
