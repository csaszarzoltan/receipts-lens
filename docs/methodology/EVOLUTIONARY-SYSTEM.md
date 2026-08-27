# Evolúciós Fejlesztési Rendszer — Behavior-First, Teszt-Központú Módszertan

> **Státusz:** draft (review-re) — 2026-08-26
> **Szerző:** Hermes + Zoltán (swiss_p_map / mealmind / receipts-lens)
> **Cél:** Az E2E tesztkörnyezet a fejlesztés **legfontosabb szereplője** legyen — 100% lefedettség, pont úgy, ahogy a felhasználó használná. A kutatástól a prototípuson át a kódig minden lépés egy futtatható viselkedés-kontraktushoz mér.

---

## 1) Alapelvek

1. **Viselkedés az első artefakt.** Előbb írjuk le mit *tegyen* az app a user szemével (GUI útvonalon), mint hogy hogyan néz ki vagy hogyan van implementálva.
2. **Teszt előbb, kód utána — mindig.** Minden feature-hez előbb piros E2E skeleton (RED), csak utána prototípus, csak utána GREEN.
3. **100% = mérhető, nem szlogen.** Minden US-hez 1 E2E spec, minden AC-triplához 1 teszt — gate blokkol ha hiányzik.
4. **Evolúciós hurok.** Az élő canary piros futása nem „hiba", hanem új research-input — visszamegy a backlogba és újra rangsoroljuk.
5. **Forrás-hűség.** Minden külső tény verbatim idézet + URL + ledger. Nincs parafrázis.
6. **Resilient bányászat.** Ha egy miner (Gemini/agy/web) nem ad adatot, a többi adatából dolgozunk — nem blokkolunk.
7. **Emberi stop-gate a prototípuson.** Kód nem indul prototípus-jóváhagyás nélkül.

---

## 2) Miért nem elég az ADR — és miért nem dobjuk ki

| Kérdés | Felelős artefakt | Példa |
|---|---|---|
| *Miért éri meg?* (VOC, piac, gap) | **Research deep-dive** | „Steuerfuss összehasonlítás JTBD erős — Comparis + Reddit 2.5k CHF pain" |
| *Mivel / hogyan?* (stack, architektúra) | **ADR** | „Next.js + MapLibre + Python ETL + PostGIS" |
| ***Mit tegyen az app — a user szemével?*** | **US + gui_flow (HIÁNYZOTT)** | „Lakáskeresőként egy térképen látom az adót, zajt, ÖV-t” |
| *Hogyan bizonyítjuk?* | **E2E spec (RED)** | `e2e/us_001_place_map.spec.ts` pirosan fut |
| *Hogy néz ki?* | **Prototípus** | Figma / Next.js preview, emberi OK |
| *Megvalósítás* | **Kód (GREEN)** | `src/services/place_service.py` stub→valós |
| *Mindig működik még?* | **Continuous E2E** | nightly + prod canary |

Az **ADR marad** — a *hogyan*-t dönti el. A hiányzó láncszem a **US + gui_flow** — a *mit*-et rögzíti futtatható formában. E nélkül az E2E csak utólagos ellenőrzés, nem tervezési eszköz.

---

## 3) Artefaktok, file-helyek, gate-ek

| # | Artefakt | File | Mikor születik | Gate |
|---|---|---|---|---|
| 1 | Research deep-dive | `docs/research/YYYY-MM-DD-{tema}-deep-dive.md` | ötletkor | evaluator rangsor + ledger `verify` |
| 2 | ADR | `docs/decisions/ADR-NNN-{slug}.md` | döntéskor | `proposed → accepted` (max 1 oldal) |
| 3 | **US + gui_flow** | `docs/stories/US-NNN-{slug}.md` | research után, kód ELŐTT | min. 4 story: happy / edge / error / **gui** |
| 4 | **E2E skeleton — RED** | `frontend/e2e/us_NNN_*.spec.ts` + `tests/test_us_NNN_*.py` (API) | US után, prototípus előtt | `npx playwright test` = piros (nincs implementáció) |
| 5 | Prototípus | `frontend/` preview / Figma link a US-ben | RED után | **emberi jóváhagyás — stop-gate** |
| 6 | Fejlesztés | `src/` / `app/` / `frontend/src/` | jóváhagyás után | GREEN + `ruff` + `mypy` + push gate |
| 7 | Continuous E2E | CI + cron (lásd 7. fejezet) | örökre | nightly + prod canary zöld |

> **Research kiegészítés:** a research sablon kap egy „*Feltételezett gui_flow draft*” szekciót — már kutatáskor végiggondoljuk milyen felületi útvonalon használná a user az ötletet. Ez még nem kontraktus, de a US írását gyorsítja.

---

## 4) Az evolúciós hurok

```
research (VOC bányászat, több módszer)
   │
   ▼
US-ek + gui_flow  ─────────┐  (behavior-analyst írja, 1 US = 1 JTBD)
   │                       │
   ▼                       │  ha UX-et változtatnál, előbb a US-t frissítsd
E2E skeleton RED           │  (1 AC = 1 teszt, gate: fájlnév = US-xxx)
   │                       │
   ▼                       │
prototípus ──► EMBERI OK ──┘  (stop-gate: nincs kód jóváhagyás nélkül)
   │
   ▼
dev GREEN (stub→valós, max 3 file / lépés, RED→GREEN)
   │
   ├──► push gate (2p smoke, chromium, PR/push)
   ├──► nightly full (15p, all journeys + axe + trace + mobile)
   └──► prod canary (30-60p, hermes cron no_agent, élő URL)
            │
            └── piros canary = új pain → vissza a research backlogba ⟲
                 (freq×intensity, mint a VOC-nál — így lesz evolúciós)
```

---

## 5) 100% lefedettség — definíció (mérhető)

- **Minden feature ≥ 1 US.** Nincs US nélküli kód.
- **Minden US ≥ 4 AC-tripla** (`given | when | then`) + **`gui_flow`** (szó szerint UI-kontraktus).
- **Minden US-hez 1 Playwright spec** (`frontend/e2e/us_NNN_<slug>.spec.ts`) — ha van backend, plusz 1 API teszt (`tests/test_us_NNN_*.py`).
- **1 AC = 1 teszt** — a hiba pontosan megmondja melyik AC bukott.
- **BDD-gate blokkolja a release-t**, ha nincs `test_<US-id>*` vagy `us_<id>*.spec.ts` fájl. (`scripts/bdd-gate.sh` — fájlnév-alapú, LLM-független).
- **Coverage report:** `story-manager validate` / `bdd-gate --report` — melyik US-nek nincs tesztje, az látszik.

Ez nem „törekvés 100%-ra”, hanem bináris gate: vagy van spec, vagy nem mehet ki.

---

## 6) Viselkedés-kontraktus: US + gui_flow + AC (BDD)

### Sablon — `docs/stories/US-000-template.md`

```markdown
# US-001: {Rövid cím — JTBD nyelven}

- Epic: {Place / Politics / Planning / …}
- Priority: P0 / P1 / P2
- Source: docs/research/YYYY-MM-DD-*.md + ADR-NNN
- Prototípus: {Figma link / preview URL} — státusz: draft | approved

## Story (As a … I want … So that …)
As a {szerep} I want {mit} So that {miért — JTBD}.

## Acceptance Criteria (Gherkin — given/when/then)
- AC1: given {előfeltétel} | when {akció} | then {elvárás, mérhető}
- AC2: given {edge} | when {akció} | then {elvárás}
- AC3: given {hibaállapot} | when {akció} | then {hibaüzenet, kód}
- AC4: given {…} | when {…} | then {…}

## gui_flow (UI kontraktus — a developer EZT követi, nem talál ki újat)
1. Open /{route} → látom: {heading / CTA / térkép}
2. Click {gomb — pozíció, szín, label} → {mi történik}
3. Modal/Toast: {pontos szöveg} → {következő lépés}
4. Assert: {URL / toast / canvas / lista tartalma}

## Megjegyzés
- Max 400 sor / file, type hints + docstring (METH-COD-001…008 ahol releváns).
- „gui_flow lépést csak US-frissítéssel szabad változtatni.”
```

### Szabályok

- **`gui_flow` a szerződés.** Pl. „Open /delivery → select project”, „Click Publish (top-right, cyan)”, „Modal: OAuth2 → success toast” — a developer nem talál ki gombot, a story írja elő.
- **4 story / feature a minimum:** happy + edge + error + gui. A gui-sztori a felületi útvonalat fedi.
- **E2E skeleton azonnal, RED-en.** `story-manager export-bdd --id US-001 --out specs/` → `e2e/us_001.spec.ts` generálás, fut = piros amíg nincs kód. Kick-start: `story-manager generate-tests`.

---

## 7) E2E piramis — folyamatos (4 réteg) + Browser Helper szolgáltatások

### 7.1 A 4 réteg (folyamatos felmérés)

| Réteg | Mikor | Hol | Mit | Költség | Ha piros |
|---|---|---|---|---|---|
| **Push gate** (smoke, <2p) | `git push` / PR | GitHub Actions `e2e-smoke` | `chromium` only, 1-2 spec, `reuseExistingServer:true` | olcsó, gyors | PR blokkolva |
| **Nightly full** (deep, 10-15p) | `02:00 UTC` schedule | GitHub `schedule` + hermes cron fallback | all BDD journeys + `axe` a11y + trace + mobile | ~22h/hó (3 projekt) | artifact `playwright-report/` 30 nap |
| **Prod canary** (élő, 30-60p) | folyamatos | **hermes cron `no_agent`** (`scripts/e2e-canary-*.sh`) | `playwright.prod.config.ts` (`baseURL=https://prod`, nincs webServer) + `/health` probe | 0 LLM-token | Telegram + kanban `BLOCKED` kártya + `notepad` freq |
| **Local watch** (dev) | fejlesztés közben | `npx playwright test --watch` | `webServer reuseExistingServer:true` | 0 | lokális |

> A 4 réteg együtt adja a „folyamatos felmérést” — a canary piros futása nem incidens, hanem evolúciós input (vissza az 1. fázisba ⟲).

### 7.2 Browser Helper — tényleges szolgáltatások (REST `http://localhost:8000` + CDP 9555)

Az E2E rendszer **hibrid**: **browser_helper = alkotás & feltárás** (interaktív, token-költséges, élő böngésző), **Playwright CLI = végrehajtás & kapuk** (determinisztikus, 0 token, CI/canary). Tilos MCP böngészőt futtatni a CI-ben — az csak a spec-generálás és a helyi hibakeresés eszköze.

**1. Szemantikus A11y fa introspekció** — nem CSS-osztály (`.btn-blue-400`) alapján, hanem a felhasználó által látott fa szerint:
- `POST /agent/observe` — `mode: "accessibility" | "legacy"` (ajánlott: `accessibility`), `max_nodes`, `fallback: "accessibility"`, `include_hidden`, `auto_modal` → `snapshot_id` + `element_id` hivatkozások, token-optimalizált hierarchia (role, name, value, state)
- `POST /page/analyze` — `buttons[]`, `form_fields[]` (checked state-tel), `modals[]` (role, aria_label, focus_trap), `iframes[]`, `alerts[]`, `text_preview`
- `POST /page/outline` — `h1–h6` hierarchia + snippet + pozíció

**2. Determinisztikus interakciós primitívek + actionability check** (látható, stabil, kattintható, nem takarja overlay):
- `POST /agent/act` — `click | fill | select | wait | wait_for_element | select_tab | evaluate | workflow` + `target: {snapshot_id, element_id}` vagy `{backend_node_id: 4023}` (snapshot-free) + `auto_recover: true` (stale → friss accessibility) + `verify_after: {type: "text_visible" | "element_visible", text: "Success"}`
- `POST /click/text`, `/click/label` (**kötelező** radios/checkboxokhoz — framework-safe), `/click/coordinates`, `/type`, `/form/fill`, `/form/select`, `/dropdown/select`
- `POST /wait`, `/wait/text`, `/wait/visible`, `/wait/network-idle` — SPA-nál kötelező: `domcontentloaded + 2s settle`, tilos `networkidle` (polling miatt timeout)

**3. Diagnosztika: hálózati forgalom & konzol naplózás** — a fejlesztő agent azonnal látja a háttérben elbukó hívásokat:
- `POST /network/start|stop`, `GET /network/log`, `POST /page/diff` (változás-detekció), `POST /agent/act` + konzol-log lekérdezés
- `js_expression: "window.map?.loaded() === true"` — MapLibre/WebGL canvas megvárása (nem `sleep`)

**4. Vizuális & strukturális bizonyítékok (multimodal grounding):**
- `POST /headless/screenshot` (`full_page`, `quality`) → `GET /artifacts/{id}`, `POST /screenshot`, `/full_screenshot`, `/element_screenshot`
- `POST /agent/highlight` — piros keret az elemek köré (Bizonyíték hogy jó komponensre mutat)

**5. Automatikus Playwright kódexport (`record → replay`):**
- `POST /agent/record` `{"start": true}` → `POST /agent/record/stop` → `POST /agent/replay` (`recorded_id`, `on_error`, `data_overrides`)
- `POST /agent/execute-task` — bounded micro-workflow (`goal`, `constraints: {max_steps: 5}`: observe → discover → fill → verify)
- `POST /agent/extract` — schema szerinti kinyerés bizonyítékkal, nem fabrikál

**6. Munkamenet, adatbázis & tenant izoláció:**
- `POST /session/save|restore` — cookies + localStorage + sessionStorage; `POST /agent/forms/discover` (`scope: "page_with_history"` SPA lazy-loadinghoz) + `POST /agent/forms/fill` (`form_ref`, `resolver: "autocomplete"`)
- `POST /agent/available-actions`, `POST /tabs/scan`, `POST /page/iframe/switch` (`index: -1` vissza a főoldalra)

> **Részletes referencia:** `docs/methodology/BROWSER-HELPER-MCP.md` — 6 képességcsoport teljes specifikációval, példa-workflow-kkel, hibaelhárítással.

### 7.3 Hibrid modell — mikor melyiket használd

| Feladat | Eszköz | Miért |
|---|---|---|
| US `gui_flow` validálás, spec generálás (RED) | **browser_helper** (`/agent/observe` + `/agent/act` + `/agent/record`) | élő A11y fa + szemantikus lokátor (`getByRole('button', {name: "Keresés"})`) |
| Fejlesztés közbeni hibakeresés | **browser_helper** (`/network/log` + konzol + screenshot) | azonnali visszacsatolás |
| CI push gate, nightly, prod canary | **Playwright CLI** (`npx playwright test`) | 0 token, determinisztikus, gyors |

### 7.4 Config konvenció

- `playwright.config.ts` = dev (BE+FE `webServer`, `workers:1`, `timeout:25s`)
- `playwright.prod.config.ts` = prod (nincs `webServer`, `baseURL: $PROD_URL`, `workers:1`, `retries:1`)
- `tests/e2e` = API contract (`TestClient`), `frontend/e2e` = UI (Playwright) — ne keverd.

### 7.5 Stabilitási szabályok (különben flaky és kikapcsolod)

- Minden E2E izolált tenantban (`demo-e2e-$RUN_ID`), utána cleanup — ne a prod DB-t piszkáld.
- Külső OGD **nightly-n mockolva**, **canary-n élesen** (pont azt teszteli, él-e a PARIS/sonBASE/Swisstopo).
- `domcontentloaded + 2s settle` a MapLibre canvas-ra, ne `networkidle` (SPA-nál timeout) — swiss `app.spec.ts` már így csinálja.
- Idempotens: ugyanaz a spec 2× futtatva is zöld (receipts `seedAuth` localStorage-val már idempotens).
- Soha ne használj vizuális CSS osztályt lokátorként (`.bg-blue-500` stílusváltáskor törik) — mindig `getByRole` / `data-testid`.
---

## 8) Research → proto → dev sorrend + stop-gate

1. **Research** (VOC bányászat + evaluator rangsor) — már itt draftoljuk a *feltételezett gui_flow*-t.
2. **US-ek** (behavior-analyst) — formalizáljuk a gui_flow-t kontraktussá (4 story min.).
3. **E2E skeleton RED** — bizonyíték hogy hiányzik a feature (futtatható, piros).
4. **Prototípus** — hogy néz ki (Figma / Next.js preview). **Emberi jóváhagyás — stop-gate.** Kód nem indulhat nélküle.
5. **Fejlesztés GREEN** — stub→valós, max 3 file / lépés, RED→GREEN, `ruff`/`mypy` gate.

Minden lépésnél a **meglevő E2E-hez mérünk**: a prototípus a RED specet kell kielégítse, a kód a prototípust.

---

## 9) Forrás-hűség, resilience, kiértékelés

### Hermes natív miner — 6-fokú létra (mindegyik próbáld, ha egyik üres → következő)

1. `web_search` + `web_extract`
2. `agent-reach` (`exa.web_search_exa`, `opencli reddit search` stb.)
3. `jina` / `defuddle` (paywall nélküli full text)
4. `browser_helper` (JS-heavy oldal)
5. `blocked-page-recovery` (Wayback → archive.today → Google cache) 403/429/paywall esetén
6. `research-toolkit` / arXiv (tech téma, kiegészítés)

Minden idézet: `Forrás | Verbatim ("…") | Kontextus | Dátum | URL | Érzelem | Téma (pain/trigger/desired_outcome/alternative/praise/complaint/JTBD)` — nincs parafrázis, ha nincs pontos idézet: `no source found`.

### Ledger (grounded-citations — kötelező)

```bash
S=~/.hermes/skills/research/grounded-citations/scripts/sources.py
HERMES_CITATION_LEDGER=/tmp/ledger-deep-YYYY-MM-DD.json

HERMES_CITATION_LEDGER=$LEDGER python "$S" reset
HERMES_CITATION_LEDGER=$LEDGER python "$S" add <url1> <url2>   # minden web_extract URL-nél
# írás közben: per mondat [n] (max 3)
HERMES_CITATION_LEDGER=$LEDGER python "$S" render --cited-in draft.md   # Sources blokk géppel
HERMES_CITATION_LEDGER=$LEDGER python "$S" verify draft.md --evidence --min-coverage 0.5
# párhuzamos subagenteknél: közös --ledger (különben ID-ütközés)
```

### Orchestration — resiliense

```
Koordinátor: Hermes (ledger reset)
 ├─ Hermes natív miner (6 létra, mind próbáld → /tmp/voc-hermes-*.md)
 ├─ gemini #1: Reddit + HN  (párhuzamos, GEMINI_CLI_TRUST_WORKSPACE=true) — ha kvóta → "no data" és tovább
 ├─ gemini #2: Twitter/X + PH + App Store (párhuzamos) — ha kvóta → "no data" és tovább
 └─ agy: competitor scrape + szintézis (SZEKVENCIÁLISAN — egyszerre 1, kvóta!)

→ Evaluator (analyst, Hermes): deduplikál → klaszter → ötlet-jelöltek → pontozás → rangsor
```

### Evaluator — rangsoroló (hermes-miner + gemini + agy bemenetből, hiány esetén is megy)

1. **Deduplikál + klaszter** (`pain / JTBD / feature-gap`) → `freq×intensity` (hány forrás × frustrated arány).
2. **Ötlet-jelölt / klaszter:** `Név | JTBD | Pain | Bizonyíték (2-3 verbatim URL) | Gap`.
3. **Pontozás 1-5:**

| Dimenzió | Súly | Jel | Forrás |
|---|---|---|---|
| Kereslet | 30% | freq×intensity | VOC táblák |
| Versenytárs-gap | 25% | senki nem adja = 5 (térkép-first, politika stb.) | competitor matrix |
| Hatás | 20% | napi fájdalmat old = 5 | JTBD + trigger |
| Megvalósíthatóság | 15% | napok, stabil OGD = 5 | tech becslés |
| Bevétel / alternatíva nyomás | 10% | fizetne érte / nincs alternatíva = 5 | pricing + alternative |

`Prioritás = 0.30*Kereslet + 0.25*Gap + 0.20*Hatás + 0.15*Megvalósíthatóság + 0.10*Bevétel` — rangsor csökkenő.

**Kimenet:**

- **A) Rangsorolt backlog tábla** (`Rank | Ötlet | 5 dimenzió | Prioritás | Top bizonyíték | Következő lépés`)
- **B) Top 5 részletezés** (1 mondat pitch + 3 verbatim idézet URL+dátum + kockázat + következő `Research → ADR → Kanban kártya + AC` lépés)

Prompt/runbookok: `docs/research/prompts/hermes-miner.md` + `gemini-miner.md` + `agy-scorer.md` + `evaluator.md`.

---

## 10) Szerepek (funkciók — bármelyik LLM eljátszhatja, LLM-független)

- **researcher:** VOC bányászat (Hermes létra + gemini párhuzamos) → `docs/research/*-deep-dive.md`
- **behavior-analyst:** research → US-ek + `gui_flow` + `evaluator` rangsor → `docs/stories/US-*.md`
- **analyst:** US + research → `docs/decisions/ADR-*.md` (max 1 oldal)
- **developer:** US + RED spec → prototípus → GREEN (max 3 file / kártya, RED→GREEN bizonyítás)
- **tester:** `bdd-gate` + E2E full + axe — teljes suite zöld mielőtt „kész"
- **release-manager:** CHANGELOG + tag + `story-manager status accepted`
- **documenter:** docs frissítés minden feature-rel

„Állj meg emberi döntésig ha: ADR-nélküli nagy döntés / >3 file / piros teszt érthetetlen / prototípus nincs jóváhagyva.”

---

## 11) Gate-ek — mikor blokkol, mikor mehet

| Gate | Hol | Mikor blokkol |
|---|---|---|
| Research ledger | `verify` | nincs `Sources:` blokk vagy `<50%` coverage és nincs `[unverified]` jelölés |
| US minimum | `workflows/principles.md` | <4 story / feature (happy/edge/error/gui) |
| E2E RED | `playwright test` | nincs `us_NNN*.spec.ts` vagy nem pirosan fut (nincs bizonyíték) |
| Prototípus stop-gate | kanban comment / ADR | nincs emberi „approved” — dev nem indulhat |
| BDD-gate | `scripts/bdd-gate.sh` | nincs `test_<US-id>*` fájl — release blokkolva |
| Push gate | GitHub Actions `e2e-smoke` | chromium smoke piros — PR nem merge-elhető |
| Canary | hermes cron `no_agent` | prod smoke piros — Telegram + BLOCKED kártya, de nem blokkolja a devet |

---

## 11b) Bug-kezelés — Lean protokoll (3 tier: fix-first, dokumentálj súly szerint)

> Cél: a board ne szemetelődjön, de a tanulság ne vesszen el.

| Tier | Mikor | Ticket? | Hogyan dokumentálj |
|---|---|---|---|
| **T1 — Micro-fix** (<30p, 1-3 file, nincs design) | elgépelés, import, typo, 1-soros guard | ❌ nincs ticket | commit `fix:` + CHANGELOG 1 sor |
| **T2 — Pattern-bug** (ismétlődhet, API/UX-t érint, szabály kell) | Caddy `/api/*` strip, OGD schema, auth header, stb. | ❌ nincs ticket, de **kötelező 5 sor tanulság** | `docs/decisions/BUG-NNN-*.md` (hiba / ok / javítás / tanulság) VAGY `docs/engineering-standards.md` 1 checklist sor |
| **T3 — Rendszer-bug** (>3 file, archi döntés, kutatás kell) | canary piros, schema drift, adatvesztés kockázat | ✅ **kötelező `hermes kanban create --board X "bug: ..." --priority high`** (+ research→ADR ha kell) | ticket = mikor/ki, BUG.md = mit tanultunk, commit = mit csináltunk |

**Példa T2 (mai receipts-lens):** Caddy `/api/*` prefix levágása miatt a `/auth/google/*` 404 lett → fix: dual decorator `/auth` + `/api/auth` → tanulság: `engineering-standards` API szekció: „Minden Caddy mögötti route dual prefixet kap.”

**Canary piros = automatikus T3** — a canary `BLOCKED` kártyát hoz létre, nem kell kézzel ticketet nyitni.

## 12) Tooling és file-struktúra

```
docs/
├── research/
│   ├── README.md
│   ├── prompts/
│   │   ├── hermes-miner.md      # 6-fokú létra + ledger
│   │   ├── gemini-miner.md      # VOC bányász (verbatim táblázat)
│   │   ├── agy-scorer.md        # competitor + feature 1-5 rubrika
│   │   └── evaluator.md         # deduplikál→klaszter→rangsor (súlyozott)
│   └── YYYY-MM-DD-{tema}-deep-dive.md
├── decisions/
│   └── ADR-NNN-{slug}.md
├── stories/                     # ÚJ
│   ├── US-000-template.md
│   └── US-NNN-{slug}.md        # Gherkin AC + gui_flow
└── methodology/
    ├── BEHAVIOR-FIRST.md         # ez a file (1 oldalas kivonat: workflows/principles.md Deep szakasza)
    └── EVOLUTIONARY-SYSTEM.md    # ez a teljes rendszer (amit most olvasol)

workflows/principles.md           # Deep research mód + Continuous E2E + stop-gate (mindhárom projektre)
frontend/e2e/                     # UI E2E (Playwright)
tests/e2e/  vagy tests/           # API E2E (pytest TestClient)
playwright.config.ts              # dev (webServer)
playwright.prod.config.ts         # prod (baseURL, nincs webServer)
scripts/bdd-gate.sh               # BDD coverage gate
~/.hermes/scripts/e2e-canary-*.sh # prod canary watchdog (no_agent cron hívja)
```

---

## 13) Példa végigjátszás — swiss_p_map ADR-002 #1 ötlet

**Ötlet (evaluator Rank #1, 4.15):** *Place-first térkép: Steuerfuss + sonBASE + ÖV egy kattintásra*

1. **Research:** `docs/research/2026-08-26-adr002-data-pipeline-deep-dive.md` — Hermes 9× `web_search` + jina fallback, 10 verbatim (Houzy „auf einen Blick" [1], smartconext „70'000" [2], PARIS CC-BY 4.0 [4], sonBASE [5], ÖV [6], Reddit 2.5k CHF pain), ledger `verify` OK, evaluator 5 ötlet → 4.15-tel #1.
2. **US-ek (behavior-analyst):**
   - `US-010: Place kártya térképen — happy` (postcode 8004 → Steuerfuss + zaj + ÖV látszik)
   - `US-011: Ismeretlen postcode — error` (404, magyar hibaüzenet)
   - `US-012: Zajréteg toggle — edge` (sonBASE ki/be, loading skeleton)
   - `US-013: gui_flow — térkép-first böngészés` (Open / → marker → kártya → toast)
3. **E2E RED:** `frontend/e2e/us_010_place_map.spec.ts` (4 AC = 4 teszt), `npx playwright test` = piros — nincs valós OGD kliens, csak stub.
4. **Prototípus:** Next.js preview + MapLibre placeholder — **emberi OK** után mehet a kód.
5. **Dev GREEN:** `src/services/place_service.py` stub→valós (ZH OGD próbahívás, schema rögzítés), `tests/test_us_010_*.py` zöld, `ruff`/`mypy` zöld.
6. **Continuous:** nightly mockolt OGD-vel zöld, canary éles OGD-vel figyeli a schema driftet.

---

## 14) Bevezetés 3 projektre

| Projekt | Stack | Mit kap most | Következő lépés |
|---|---|---|---|
| **swiss_p_map** | FastAPI (`src/`) + Next.js (MapLibre) | `hermes-miner` + `evaluator` + Deep szakasz már pusholva (`45e3bdd`), élő deep-dive `4e40d8f` | `US-010…013` + RED skeleton (Place OGD) — ez a fenti példa |
| **mealmind** | FastAPI (`app/`) + Next.js 14 PWA | ugyanez + validációs scope már pusholva (`346a247`) | `US` a következő nagy feature-re (poll→shopping lánc kiegészítés) |
| **receipts-lens** | FastAPI (`app/`) + Next.js workspace | `AGENTS.md` + `METHODOLOGY.md` pótlás + Deep már pusholva (`af5ae4a`) | `US` a következő workspace feature-re (OCR review → export) |

Mindegyikre: `playwright.prod.config.ts` pótlás (swiss+mealmind) + `ci.yml` `e2e-smoke` + `nightly` + `hermes cron no_agent` canary (swiss 30m, mealmind+receipts 60m) + `workflows/principles.md` „Continuous E2E” szakasz — ha kéred, egy lépésben viszem.

---

## 15) Anti-minták

- **Researchben már UI-t kitalálni kód nélkül?** Igen — de csak *draft* gui_flow, kontraktus csak a US-ben lesz.
- **4-nél kevesebb story?** Nem elég — a gui-sztori nélkül a felületi lefedettség lyukas.
- **E2E csak dev végén?** Akkor már nem tervezési eszköz, csak utólagos ellenőrzés — a RED-nek előbb kell lennie.
- **Prototípus skip?** Csak emberi OK után indulhat dev — különben 3× újraírod a UI-t.
- **Canary zaj?** Zöld = csend, piros = Telegram + BLOCKED kártya. Nem spam, hanem evolúciós input.

---

## 16) Mellékletek

### Parancsok

```bash
# BDD export + skeleton
python3 scripts/story-manager.py export-bdd --idea <idea_id> --id US-010 --out specs/
python3 scripts/story-manager.py generate-tests --idea <idea_id> --id US-010 --out tests/ --track

# BDD gate (release előtt kötelező)
bash scripts/bdd-gate.sh <repo> <idea> <story>

# Hermes miner (példa — swiss_p_map)
# 1) web_search + jina létra (lásd hermes-miner.md)
# 2) ledger
HERMES_CITATION_LEDGER=/tmp/ledger-deep-$(date +%F).json python ~/.hermes/skills/research/grounded-citations/scripts/sources.py reset
HERMES_CITATION_LEDGER=/tmp/ledger-deep-$(date +%F).json python ~/.hermes/skills/research/grounded-citations/scripts/sources.py add <url>...
HERMES_CITATION_LEDGER=/tmp/ledger-deep-$(date +%F).json python ~/.hermes/skills/research/grounded-citations/scripts/sources.py render --cited-in docs/research/2026-08-26-xxx.md

# Canary cron (no_agent — 0 token)
hermes cron create --name "swiss-p-map canary (prod 30m)" --schedule "30m" --no-agent --script e2e-canary-swiss.sh --deliver telegram
```

### Reviewer agenteknek — kérdések

1. A 7 réteg lefedi a „mit–mivel–hogyan–bizonyítjuk” láncot? Hiányzik artefakt?
2. A 4× story minimum (happy/edge/error/gui) elég a 100%-hoz, vagy kell 5. (pl. a11y)?
3. A súlyozás (30/25/20/15/10) reális, vagy más súly kellene (pl. megvalósíthatóság fel)?
4. A stop-gate (prototípus jóváhagyás) nem lassítja túl a kis fixeket? Kell-e „kis fix” kivétel?
5. A canary freq (30m vs 60m) és értesítés (Telegram + BLOCKED) arányos?

---

*Vége — review után a `workflows/principles.md` Deep + Continuous szakaszai + `docs/stories/US-000-template.md` + `scripts/bdd-gate.sh` beépítésével lesz teljes a bevezetés mindhárom projektre.*
