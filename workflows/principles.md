# ReceiptLens — Munkaelvek (Principles)

> Minden agent ezt olvassa belépéskor. Rövid, verifikálható.

## Workdir
- Root: `~/receipts-lens`
- Stack: **FastAPI + Next.js workspace** (élő v1.4 — lásd AGENTS.md). Új stack-döntés → ADR
- Teszt: `pytest -q` (BE, `tests/`), `npm run build` + `tsc` (FE, `frontend/`). Indítás: `docker compose up` vagy `./start-dev.sh`

> **Új agent?** `docs/methodology/AGENT-BOOTSTRAP-PROMPT.md` — másold egyben az ELSŐ üzenetbe.

## Validációs scope
| Változás | Mit kell futtatni |
|---|---|
| `app/**/*.py` | `python -m compileall -q app tests` + `pytest -q` (vagy releváns `tests/test_*.py`) + `ruff check app tests` |
| `frontend/**` | `npm run build` (Next) + `tsc --noEmit` ha TS, + `ruff` ha Python is érintett |
| `alembic/**` | `alembic upgrade head` + `alembic downgrade -1` smoke |
| `docs/*.md` | példa-ellenőrzés, nem teszt |
| Bármelyik | commit előtt `git diff --stat` ellenőrzés |

## Szerepek (funkciók, bármelyik LLM eljátszhatja)
- researcher: kutatás → `docs/research/YYYY-MM-DD-*.md` (max 5 oldal, comparison table)
- analyst: szintézis → `docs/decisions/ADR-*.md` (max 1 oldal)
- developer: max 3 file/kártya, RED→GREEN bizonyítás
- tester: teljes suite zöld mielőtt "kész"
- release-manager: CHANGELOG + tag
- documenter: docs frissítés minden feature-rel (`docs/decisions/`, `docs/engineering-standards.md` ha UX/API érintett)

## Tudás forrása (prioritás)
1. Ez a file + `AGENTS.md` + `METHODOLOGY.md`
2. `docs/decisions/ADR-*.md`
3. Kódgráf / `git log`

## Állj meg emberi döntésig ha
- ADR-nélküli nagy döntés (stack, architektúra)
- Több mint 3 file-t érintene a változtatás
- Teszt piros és nem világos miért

## Eszköz-függetlenség
A fentiek **funkciók**, nem szoftverek. "Állj meg" = issue/comment/üzenet bárhol. RED→GREEN = bármilyen teszt-keretrendszer. Az LLM válassza meg a saját eszközét — a kimenet számít: **docs + tesztek + git history**.

## Engineering standards
`docs/engineering-standards.md` a UX/API/adat/kódminőség checklist. Agent-barát kód: rationale docstring + edge-case + complexity-cap — CI gate.


## Deep research mód (mély kutatás — VOC + konkurencia + feature-siker)

Mély kutatásnál a „keress rá” nem elég — **bányássz + bizonyíts** (verbatim idézet + URL + dátum).

### Forrásmix (ICP szerint — ne csak Google)
| ICP / projekt | Kötelező watering hole-ok |
|---|---|
| B2C / SMB (swiss_p_map, mealmind, receipts-lens) | Reddit (releváns subok), App Store / Play 1-3★, Trustpilot / G2 / Capterra, Product Hunt, YouTube komment, IndieHackers |
| Tech / B2B | HackerNews (Algolia), r/devops / r/programming, LinkedIn, job postingok (trigger events), Stack Overflow |
| Hír / trend | `agent-reach` RSS + `competitor-news-monitor` heti cron + Google News + defuddle |

Minden idézet: `Forrás | Verbatim (szó szerint, "...") | Kontextus | Dátum | URL | Érzelem | Téma (pain/trigger/desired_outcome/alternative/praise/complaint/JTBD)`. Nincs parafrázis — ha nincs pontos idézet: `no source found`.

### Forrás-hűség (grounded-citations — kötelező)
- Minden külső tényhez `scripts/sources.py` ledger: `reset` → `add <url>` → írás közben `[n]` per mondat (max 3) → `render --cited-in draft.md` → `verify` (és `--evidence` + `quote --from` ha fact-check).
- Ledger párhuzamos subagenteknél: közös `--ledger` path (különben ID-ütközés).
- Keresési snippet ≠ forrás — csak `web_extract` / `defuddle` utáni oldalra hivatkozz.

### Feature-siker rubrika (1-5, minden vizsgált feature-re)
| Dimenzió | Jel | Forrás |
|---|---|---|
| Kereslet | hányan kérik / panaszkodnak rá (freq × intensity) | Reddit/HN verbatim gyakoriság |
| Elégedettség | G2/Capterra rating + 1-3★ arány | scraped reviews |
| Organikus vonzerő | traffic becslés | DataForSEO / SimilarWeb free / site: keresés |
| Árazási validáció | melyik tierben van, van-e felár | pricing page |
| Fejlesztési tempó | changelog commits / hó | changelog scrape |
Átlag = feature siker-score. Az ADR „Elvetve” táblája mellé tedd — onnantól szám, nem vélemény.

### Orchestration — Hermes is bányászik (resilient) + evaluator rangsorol
```
Koordinátor: Hermes (ledger reset: /tmp/ledger-deep-YYYY-MM-DD.json)
 ├─ Hermes natív miner (TÖBB MÓDSZER, mind próbáld, ha egyik üres → következő):
 │   1) web_search + web_extract  2) agent-reach (exa / opencli reddit)  3) jina/defuddle
 │   4) browser_helper (JS-heavy)  5) blocked-page-recovery (Wayback)  6) research-toolkit arXiv
 │   → /tmp/voc-hermes-*.md (8-12 verbatim + no source found ahol üres — NE állj le)
 ├─ gemini #1: Reddit + HN  (párhuzamos, GEMINI_CLI_TRUST_WORKSPACE=true) — ha kvóta → "no data" és tovább
 ├─ gemini #2: Twitter/X + Product Hunt + App Store  (párhuzamos) — ha kvóta → "no data" és tovább
 └─ agy: competitor scrape + szintézis  (SZEKVENCIÁLISAN — egyszerre 1, kvóta!)

→ Evaluator (analyst, Hermes): deduplikál + klaszter (pain/JTBD/feature-gap) + freq×intensity
  → ötlet-jelöltek → 1-5 pontozás (Kereslet 30% + Gap 25% + Hatás 20% + Megvalósíthatóság 15% + Bevétel 10%)
  → Rangsorolt backlog tábla + Top 5 részletezés (pitch, 3 idézet, kockázat, következő Research/ADR/Kanban lépés)
  → docs/research/YYYY-MM-DD-deep-dive.md (ledger Sources + evidence quotes, --min-coverage 0.5)
  → docs/decisions/ADR-NNN.md (prioritás alapján)
Resilience: ha egy miner nem tér vissza adattal (kvóta/hiba), a többi adatából dolgozunk — hiányt jelöljük, nem blokkolunk.
```
Prompt/runbookok: `docs/research/prompts/hermes-miner.md` (többmódszeres létra + ledger) + `gemini-miner.md` + `agy-scorer.md` + **`evaluator.md`** (rangsoroló + grooming-ready Top 5 + képlet).


## Bug-kezelés — Lean (3 tier, fix-first)

| Tier | Mikor | Ticket? | Dokumentálás |
|---|---|---|---|
| **T1 Micro-fix** (<30p, 1-3 file) | typo, import, guard | ❌ | commit `fix:` + CHANGELOG |
| **T2 Pattern-bug** (ismétlődhet, API/UX) | Caddy strip, schema drift, auth header | ❌ de **5 sor tanulság kötelező** | `docs/decisions/BUG-NNN-*.md` vagy `engineering-standards` 1 sor |
| **T3 Rendszer-bug** (>3 file, archi) | canary piros, adatvesztés kockázat | ✅ `hermes kanban create --board X "bug: ..."` | ticket + ADR ha kell |

Canary piros = automatikus T3 (BLOCKED kártya). Részletek: `docs/methodology/EVOLUTIONARY-SYSTEM.md` 11b.

## Session elveszett? Nem baj
Minden tudás git-ben. Session = beszélgetés history, nem storage.

## Evolúciós rendszer (kötelező — röviden)
- **Master:** `docs/methodology/EVOLUTIONARY-SYSTEM.md` — 7 fázis (research → US+gui_flow → RED → stop-gate → GREEN → CI gate → canary)
- **Függelék:** `docs/methodology/BROWSER-HELPER-MCP.md` — valós Browser Helper endpointok, nem kitalált `browser_get_*` nevek
- **Stop-gate:** prototípus emberi OK nélkül nincs `src/`/`app/` módosítás (kivétel: tiszta backend/logikai fix — Fast-Track)
- **BDD-gate:** `scripts/bdd-gate.sh` — nincs `us_NNN` spec → release blokkolva
- **Continuous:** push gate (<2p) + nightly (15p) + canary (`hermes cron --no-agent`, 30-60p) + local watch
