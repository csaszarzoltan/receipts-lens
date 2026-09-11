# ReceiptLens — Agent Context

> Ezt olvassa minden agent belépéskor (Hermes, Gemini CLI, Claude, GPT, Codex, agy...). Rövid — 30 sor.

## Mi ez
**ReceiptLens** — receipt intelligence workspace (v1.4, élő). Számla OCR (Tesseract / vision), confidence-scored review, accounting export, automation rules. **Stack:** FastAPI (app/) + Next.js workspace (frontend/) + Tesseract/pytesseract + reportlab. Fut: `docker compose up` vagy lokálisan BE `uvicorn` + FE `next dev`.

## Hol mi van
- `METHODOLOGY.md` — kódolási/API/git/teszt/doc szabályok (kanonikus, kötelező)
- `workflows/principles.md` — workdir, validációs scope, szerepek (funkciók)
- `docs/decisions/ADR-*.md` — minden nagyobb döntés 1 oldal (template: ADR-000-template.md)
- `docs/decisions/` — archív döntések is itt (dátum-név: `2026-08-13-*.md`)
- `docs/research/` — kutatások (max 5 oldal, comparison table ha több opció)
- `docs/competitor/` — heti scout jegyzetek
- `docs/engineering-standards.md` — UX/API/adat/kódminőség checklist (ellenőrizhető követelmények)
- `docs/plans/` — feature tervek
- `app/` / `frontend/` / `tests/` / `alembic/` — kód + migrációk + tesztek

## Szabályok (röviden)
- Döntés nélkül ne kódolj nagyot: research → ADR → utána kód (kis fix mehet direktben)
- Minden feature: előbb teszt-ötlet, aztán kód (RED→GREEN pytest-tel, lásd METHODOLOGY 3. fejezet)
- Max 400 sor/file; type hints + docstring ahol értelmes (METH-COD-001…008)
- Commit: `<scope>: <leírás>` formátum (lásd METHODOLOGY 4. fejezet)
- Migráció: ahol van Alembic — minden séma-változás migrációval
- Docs + tesztek nélkül nincs „kész”

## Tudás forrása (prioritás)
1. `workflows/principles.md` + ez a file
2. `docs/decisions/ADR-*.md` + `docs/engineering-standards.md`
3. Kódgráf (ha indexelve) / `git log`

## Bootstrap (új agentnek — másold egyben!)
> `docs/methodology/AGENT-BOOTSTRAP-PROMPT.md` — másolható prompt új session ELSŐ üzeneteként. Elmondja mit olvasson és hogyan dolgozzon (7 fázis + Browser Helper valós API + bug 3 tier).

## Módszertan (kötelező)
- **Evolúciós rendszer (master):** `docs/methodology/EVOLUTIONARY-SYSTEM.md` — 7 fázis, behavior-first, 100% E2E, stop-gate
- **Browser Helper függelék:** `docs/methodology/BROWSER-HELPER-MCP.md` — valós endpointok, 6 képességcsoport, tenant izoláció
- **Deep research runbookok:** `docs/research/prompts/` (hermes-miner, gemini-miner, agy-scorer, evaluator)

## LLM-függetlenség
A módszertan bármelyik LLM-mel megy. A szerepek funkciók, nem eszközök. Kötelező minimum: dokumentálj (`docs/`) + tesztelj. Eszközválasztás szabad.

## VERITAS 1.1 — szerep-határok + gate-használat (rövid)
Normatív alap: `VERITAS_1_1_adaptiv_egyseges_fejlesztesi_modszertan.md`. Projektspecifikus profil: `METHODOLOGY.md` (RVAD 1.1).
- Szerep-határok: Product Authority (értékdöntés) / Researcher (evidence, jóváhagyás nélkül) / Spec Author (spec, kód nélkül) / Test Author (teszt + RED, termékkód nélkül) / Implementer (minimális kód, spec/teszt-módosítás nélkül) / Reviewer (read-only) / Runner (determinisztikus gate-döntés) / Human Authority (termék, jog, security, production).
- Default deny: tiltott file/útvonal esetén stop + eszkaláció, nem workaround.
- Gate-sorrend: RED → célzott GREEN → teljes regresszió → traceability → független review → release. Cache-elt PASS csak Execution Equivalence mellett számítható be.
- Konfliktus: kód/teszt vs jóváhagyott spec → spec az irányadó, eltérést eszkalálni + ADR-be írni.
