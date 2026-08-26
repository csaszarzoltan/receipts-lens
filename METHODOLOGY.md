# Módszertani Elvárások — ReceiptLens

## 1. Kódolási szabályok
### Fájlstruktúra
- Új modul: `app/<modul>.py` vagy `app/<feature>.py` (pl. `app/ocr.py`, `app/accounting_workspace.py`)
- Új unit teszt: `tests/test_<modul>.py`
- API/E2E teszt: `tests/test_<feature>.py`, frontend E2E: `frontend/e2e/*.js`
- Frontend: `frontend/` (Next.js workspace) — `app/`, `components/`, `lib/`, `e2e/`
- Docs: `docs/research/YYYY-MM-DD-*.md`, `docs/decisions/ADR-*.md`, `docs/competitor/YYYY-Www-scan.md`

### Kódolási stílus
- Python 3.11+ (type hints kötelező, `from __future__ import annotations`)
- f-string használata
- Docstring minden publikus osztályon és metóduson
- Maximum 400 sor fájlonként; 200 felett bonts kisebb modulokra
- Konstansok fájl tetején
- Import sorrend: stdlib → third-party → local
- Frontend: `escapeHtml` minden felhasználói szövegnél

### Osztálytervezés
- Dependency injection (paraméterben kapja meg a függőségeket)
- Frozen dataclass / Pydantic BaseModel ahol értelmes
- Enum használata értéknaplózáshoz
- Protocol interfészek határozzák meg a szerződéseket

## 2. API endpoint szabályok

### Válasz formátum
```json
// Sikeres
{"status": "ok", "data": {...}}
// Lista
{"items": [...]}
// Hiba
{"error": "error_type"}
```

### HTTP státuszkódok
- 200: Sikeres művelet
- 201: Létrehozás
- 400: Hibás kérés (validálási hiba)
- 404: Nem található
- 409: Ütközés (pl. idempotencia)
- 500: Szerver hiba

### Security
- Bemeneti validálás minden POST endpointon (Pydantic / `field_validator`)
- XSS prevention (escapeHtml JavaScriptben)
- Security headers (X-Content-Type-Options, X-Frame-Options, CSP)

## 3. Tesztelési szabályok

### Teszt lefedettség
- Minden publikus metódusra legyen teszt
- Happy path + edge case + error case
- Mockoljuk a külső szolgáltatásokat (OpenAI vision OCR, Tesseract nem mock — lokális)
- Integrációs teszt a teljes láncra ahol értelmes (pl. `upload → OCR → review → export`)

### Teszt elnevezés
```python
class TestFeatureName:
    def test_happy_path_scenario(self):
        """Leírás mit tesztel."""
        pass

    def test_error_handling_when_X(self):
        """Hibakezelés tesztelése."""
        pass
```

### Teszt futtatás
```bash
# Összes teszt (pytest) — ez a valódi futtatás
PATH=.venv/bin:$PATH pytest -q
# Unit csak
PATH=.venv/bin:$PATH pytest tests/unit -q 2>/dev/null || PATH=.venv/bin:$PATH pytest tests -q -k "unit"
# E2E (böngésző/HTTP)
PATH=.venv/bin:$PATH pytest tests/e2e -q
# Szintaxis
python -m compileall -q app tests
# Típusellenőrzés
PATH=.venv/bin:$PATH mypy app tests --ignore-missing-imports  # pyproject szerint
```

## 4. Git szabályok

### Commit formátum
```
<scope>: <rövid leírás>

- Részletes leírás
- Miért kellett a változás
```

Példák:
- `feat: receipt OCR confidence review`
- `fix: OCR retry quarantine handling`
- `test: OCR pipeline tests`
- `docs: ADR-007 OCR pipeline`
- `chore: ruff + mypy CI gate`

### Branch kezelés
- `master`: Stabil, production-ready (közvetlen commit + push a kis scope-ú fixeknél)
- `feature/<név>`: Nagyobb funkciók (opcionális)
- Minden commit előtt: `git diff --stat`, `python -m compileall -q`, releváns tesztek zöldek
- Push után: `git status --short` tiszta

## 5. Dokumentáció szabályok — döntések és kutatás (kötelező)

### ADR és research kötelezés
- `researcher` nem zárhat kártyát ADR nélkül: minden nagyobb döntés → 1 `docs/decisions/ADR-NNN-{slug}.md` (max 1 oldal, template: `ADR-000-template.md`). `proposed → accepted` státusz, `docs/research/YYYY-MM-DD-*.md` linkkel.
- `researcher` nyers anyag: `docs/research/YYYY-MM-DD-{tema}.md` (max 5 oldal, **comparison table kötelező** ha több opció). Kanban comment csak linket tesz.
- Heti scout (cron): `docs/competitor/YYYY-Www-scan.md` (triage, BLOCKED emberi jóváhagyásig — ember nélkül nem indul dev).
- Evidence TTL: képernyőképek / időszakos riportok (pl. screenshots, futtatási bizonyítékok) 30 nap után törlődnek; docs/archive 90 nap után tömörítve. Monolit doc nem nőhet: `docs/API.md` új endpointja már `docs/api/<feature>.md`-be kerül.

### README.md
- Projekt leírás
- Telepítés
- Használat
- API referencia (link)

### CHANGELOG.md
- Új funkciók
- Hibajavítások
- Megszakító változások

### CODE docstring
- Osztály: Mi a felelőssége
- Metódus: Mit csinál, paraméterek, visszatérési érték
- Példa használat (ha nem egyértelmű)

## 6. Minőségi kapuk (Kötelező)

### Commit előtt
1. `python -m compileall -q app tests` → Szintaktikai hiba nélkül
2. `PATH=.venv/bin:$PATH pytest -q` vagy legalább a releváns `tests/test_*.py` zöld + `ruff check app tests` tiszta
3. `PATH=.venv/bin:$PATH mypy app tests --ignore-missing-imports  # pyproject szerint` ha Python változott (strict a pyproject.toml szerint)
4. `git diff --stat` → Ellenőrzés

### Push előtt
1. `git pull --rebase` → Merge conflict nélkül (opcionális kis repo-nál)
2. `git push` → Sikeres
3. `git status --short` → Tiszta

### Átadás előtt
1. Teszt szám pontosság
2. Fájlnevek egyeznek a tervekkel
3. Nincs nem tervezett módosítás

## 7. ReceiptLens specifikus

- Stack: FastAPI (app/) + Next.js workspace (frontend/) + Tesseract / OpenAI vision OCR. Indítás: `docker compose up` vagy lokálisan `uvicorn app.main:app` + `next dev`.
- OCR pipeline: Tesseract alapértelmezett, vision OCR opcionális (OpenAI-kompatibilis endpoint) — confidence-score + source box megőrzése.
- Review flow: `upload → OCR → low-confidence review → correction → validation → export` egyben tesztelendő.
- Export: immutable preparation + replay-safe CSV, activity history megmarad.
- Automation: versioned rules, preview → activate → rollback, conflict detection determinisztikus nyertes szabállyal.
- Engineering standards: `docs/engineering-standards.md` (UX/API/adat/kódminőség) — CI-ben ruff gate.

