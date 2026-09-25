# ADR-007: Pre-commit hook — a VERITAS gate legyen, ne a pre-commit framework

> A [ZOO-23](/ZOO/issues/ZOO-23) finding alapján. 1 oldal.

- **Dátum:** 2026-09-25
- **Státusz:** accepted
- **Szerző:** Architect
- **Kanban:** ZOO-23

## Kontextus
A `.git/hooks/pre-commit` (Aug 1) egy **pre-commit framework** stub volt, ami egy
nem létező `.pre-commit-config.yaml`-ra mutatott, és így **minden commitot blokkolt**
(`No .pre-commit-config.yaml file was found`) — a fejlesztők `PRE_COMMIT_ALLOW_NO_CONFIG=1`
mellett kerülték meg. A finding jogos: a gate „nézett ki, mintha lenne", de nem kényszerített ki.

A vizsgálat azonban **megfordította a findinget**: a repóban már létezik egy valódi,
trackelt lokális gate — `.githooks/pre-commit` (a `c3899af` commit vezette be 2026-09-11),
amely `scripts/veritas_gate.py --verify-diff --verify-metadata --staged` módban fut, és
fail-closed. Ez **egyetlen commitot sem futott**, mert a `core.hooksPath` nem volt beállítva
— a git a `.git/hooks/`-ot nézi, a `.githooks/` inert volt.

## Döntés
- A **trackelt `.githooks/pre-commit`** (VERITAS staged gate) legyen az egyetlen lokális gate.
- **`git config core.hooksPath .githooks`** — ez kapcsolja be (lokális, `.git/config`).
- A döng pre-commit-framework stub **törölve** (nem volt configja, nem is kell).
- `pre-commit` framework **nem** kerül a projektbe: a `pre-commit` nincs függőség
  (`pyproject.toml`), és a duplikált konfig divergens minőségkaput okozna.

## Elvetve
| Opció | Miért nem |
|---|---|
| Megírni egy `.pre-commit-config.yaml`-t | A `pre-commit` nincs a projekt függőségei között; a duplikált konfig két divergens minőségkaput hozna létre a VERITAS mellett. |
| Csak törölni a stubot, `core.hooksPath` nélkül | Ez a valódi félállapot: a trackelt VERITAS gate továbbra sem futna → a finding valódi problémája megmarad. |
| Csak `PRE_COMMIT_ALLOW_NO_CONFIG` | A commitok „átmennek" egy semmit sem kényszerítő kapuval. Nem megoldás. |

## Következmény
- **Kötelező egyszer lépés klón után:** `git config core.hooksPath .githooks` (lokális, nem
  kerül be a repóba) — dokumentálva az `AGENTS.md`-ben. E nélkül a gate inaktív.
- A hook `--no-verify`-jal megkerülhető (lokális kényelmi kontroll); a **valódi kényszer a CI**
  (`.github/workflows/veritas.yml`), ami push-ra és PR-re is fut.
- Validálva (ZOO-23): negatív teszt — vegyes `app/`+`tests/` diff → `git commit` exit 1,
  gate blokkolt; pozitív teszt — tiszta doc-commit → exit 0, commit létrejött.

## Kapcsolódó
- Kód: `.githooks/pre-commit`, `scripts/veritas_gate.py`, `.github/workflows/veritas.yml`
- Következő ADR: —
