# ReceiptLens — Agent Bootstrap Prompt

> Másold egyben egy új agent session ELSŐ üzeneteként (Hermes, Gemini CLI, Claude, GPT, Codex, agy — bármelyik).

```
Te a ReceiptLens agentje vagy. Workdir: ~/receipts-lens — NE kódolj mielőtt elolvasod a kötelező docokat.

1. KÖTELEZŐ OLVASÁSI SORREND (ebben a sorrendben, ne ugorj):
   - AGENTS.md (30 sor — mi ez + hol mi van)
   - workflows/principles.md (workdir, validációs scope, szerepek, bug protokoll 3 tier)
   - docs/methodology/EVOLUTIONARY-SYSTEM.md — MASTER (7 fázis, behavior-first, US+gui_flow → RED → stop-gate → GREEN → continuous E2E 4 réteg, 11b bug protokoll)
   - docs/methodology/BROWSER-HELPER-MCP.md — FÜGGELÉK (6 képességcsoport VALÓS endpointokkal: POST /agent/observe accessibility, POST /agent/act auto_recover+verify_after, POST /page/analyze, POST /page/outline, POST /headless/screenshot→/artifacts, POST /session/*, POST /agent/record→replay)
   - METHODOLOGY.md + docs/engineering-standards.md (kódolási/API/git/teszt szabályok)
   - docs/decisions/ + git log --oneline -10

2. STACK: FastAPI (app/) + Next.js workspace (frontend/) + Tesseract/pytesseract + reportlab + Alembic. Fut: docker compose up vagy uvicorn + next dev. Tesztek: pytest + Playwright + ruff.

3. DEEP RESEARCH: Hermes 6-fokú létra + gemini párhuzamos + agy soros, verbatim + ledger, prompts: docs/research/prompts/, evaluator súlyozás.

4. BEHAVIOR-FIRST: Research → US-ek (docs/stories/US-NNN-*.md, min 4) → E2E RED → Prototípus → EMBERI OK (stop-gate) → GREEN (max 3 file) → Continuous (push gate + nightly + canary 60m). BDD-gate: nincs us_NNN spec → blokkolva.

5. BUG PROTOKOLL: T1 nincs ticket, T2 5 sor tanulság, T3 kanban ticket + ADR. Canary piros = T3.

6. INDÍTÁS: 2-3 mondat összefoglaló (stack + hol tart + következő lépés), aztán várd a feladatot.
```
