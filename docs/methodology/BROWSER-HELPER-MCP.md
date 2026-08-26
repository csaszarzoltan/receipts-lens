# Browser Helper MCP — Technikai Függelék
## Behavior-First, Autonóm E2E Teszt-Központú Szoftvertervezési Rendszer

> **Dokumentum státusz:** Technikai Függelék — Browser Helper MCP (v2.1, javított)
> **Master:** `docs/methodology/EVOLUTIONARY-SYSTEM.md` (behavior-first rendszer)  
> **Készült:** 2026-08-26  
> **Szerzők:** Hermes Rendszerarchitektúra & Zoltán  
> **Célrendszerek:** `swiss_p_map`, `mealmind`, `receipts-lens` (3 projekt).

---

## Tartalomjegyzék
1. [Vezetői Összefoglaló és Filozófia](#1-vezetői-összefoglaló-és-filozófia)
2. [A Fejlesztési Életciklus 7 Fázisa](#2-a-fejlesztési-életciklus-7-fázisa)
3. [A `browser_helper` MCP Részletes Architektúrája és Specifikációja](#3-a-browser_helper-mcp-részletes-architektúrája-és-specifikációja)
4. [Multi-Agent Szerepkörök és Kontextus-Izoláció](#4-multi-agent-szerepkörök-és-kontextus-izoláció)
5. [Artefaktumok, Szerződések és Sablonok](#5-artefaktumok-szerződések-és-sablonok)
6. [Gyakorlati Végigjátszás: Valós Esettanulmány](#6-gyakorlati-végigjátszás-valós-esettanulmány)
7. [Stabilitási Szabályok, Flakiness Megelőzés és Anti-Minták](#7-stabilitási-szabályok-flakiness-megelőzés-és-anti-minták)

---

## 1. Vezetői Összefoglaló és Filozófia

A hagyományos szoftverfejlesztésben az End-to-End (E2E) tesztelés gyakran a folyamat legvégén elhelyezkedő, nehezen karbantartható, törékeny utóellenőrzésként jelenik meg. Autonóm AI-fejlesztési környezetben ez a megközelítés katasztrofális hibákhoz vezet: a fejlesztő agentek szintaktikailag helyes, de a felhasználói élmény szempontjából működésképtelen vagy széteső felületeket építenek, a tesztelő agentek pedig nem létező szelektorokra és hallucinált állapotokra írnak specifikációkat.

Jelen módszertan alapja a **Behavior-First** és **Evolutionary Loop** paradigma:
* **A viselkedés az elsődleges artefaktum:** Mielőtt bármilyen kód vagy architektúra megszületne, a felhasználói felület viselkedését pontos, strukturált szerződésben (`US + gui_flow`) rögzítjük.
* **RED-First Tesztvezéreltség:** Nincs kódírás meglévő, determinisztikusan elbukó (RED) E2E teszt nélkül. A teszt az egyetlen elfogadott definíciója a készenlétnek.
* **Kettéosztott Intelligencia-Réteg (Hibrid Tesztelési Modell):**
  * **Alkotás és Feltárás:** A `browser_helper` MCP-n keresztül az AI interaktívan, élő böngésző-hozzáféréssel, akadálymentességi fa (A11y tree) bejárással és vizuális visszacsatolással hozza létre a teszteket és javítja a hibákat.
  * **Végrehajtás és Kapuk:** A CI/CD és a folyamatos felügyelet során determinisztikus, 0-tokenes, natív **Playwright CLI** fut, biztosítva a sziklaszilárd, olcsó és gyors kapurendszert.
* **Evolúciós Visszacsatolási Hurok:** A termelési környezetben (canary) tapasztalt hibák vagy külső API-változások (schema drift) nem izolált incidensek, hanem azonnal visszacsatolt kutatási inputokká válnak a backlogban.

---

## 2. A Fejlesztési Életciklus 7 Fázisa

Az autonóm rendszer egy 7 lépéses zárt hurkú folyamatot követ:

```
[ 1. Research / VOC ] ──► [ 2. US + gui_flow ] ──► [ 3. MCP Tesztgenerálás (RED) ]
                                                            │
[ 5. Dev GREEN ] ◄── [ 4. Emberi Stop-Gate ] ◄──────────────┘
       │
       ├──► [ 6. CI/CD BDD Gate (0-token Playwright CLI) ]
       │
       └──► [ 7. Continuous Canary ] ──► (Hiba esetén visszacsatolás az 1. pontba ⟲)
```

### 1. Fázis: Deep Research & VOC Bányászat
* **Cél:** Valós felhasználói fájdalompontok (Voice of Customer), piaci rések és JTBD (Jobs to Be Done) feltárása.
* **Módszer:** Multi-miner keresés (Hermes 6-fokú létra + Gemini/Agy bányászok).
* **Kimenet:** Forrás-hű kutatási dokumentum (`docs/research/YYYY-MM-DD-*.md`) megerősített forrás-ledgerrel és egy előzetes *Feltételezett gui_flow drafttal*.

### 2. Fázis: Felhasználói Történet (US) és gui_flow Szerződés
* **Cél:** A követelmények leírása a felhasználó szemszögéből, szigorú formális struktúrában.
* **Követelmény:** Minden funkcióhoz minimum 4 történet (Happy path, Edge case, Error state, GUI flow).
* **Kimenet:** `docs/stories/US-NNN-{slug}.md`, amelyben a `gui_flow` kötelező érvényű szerződésként írja le az útvonalat, a szemantikus interakciókat és az elvárt állapotokat.

### 3. Fázis: E2E Skeleton Generálás (RED) `browser_helper` Segítségével
* **Cél:** Futtatható, garantáltan elbukó tesztek előállítása a kódírás megkezdése előtt.
* **Módszer:** A tesztelő agent a `browser_helper` MCP-n keresztül interaktívan bejárja a helyi dev szerveren futó prototípust vagy scaffoldot, megkeresi a szemantikus elemeket, és kimenti a Playwright `.spec.ts` kódot.
* **Kimenet:** `frontend/e2e/us_NNN_*.spec.ts` és `tests/test_us_NNN_*.py`. A kapu ellenőrzi, hogy a teszt lefut és elbukik (RED bizonyíték).

### 4. Fázis: Prototípus és Emberi Stop-Gate
* **Cél:** Annak biztosítása, hogy ne épüljön fel felesleges vagy rossz UX-szel rendelkező kód.
* **Szabály:** Fejlesztési kód (`src/`) nem módosítható, amíg az emberi felhasználó jóvá nem hagyja a prototípus felületet és a tesztszerződést.
* **Kivétel (Fast-Track):** Meglévő felületek tiszta logikai/backend javítása esetén a teszt-kapuk automatikusan engedélyezhetik a továbblépést.

### 5. Fázis: Autonóm Fejlesztés (GREEN)
* **Cél:** A minimálisan szükséges kód megírása, ami zöldre állítja a RED teszteket (TDD elv).
* **Módszer:** A fejlesztő agent legfeljebb 3 fájlt módosít lépésenként. Fejlesztés közben a `browser_helper` eszközzel diagnosztizálja a konzolhibákat, a hálózati forgalmat és a renderelési hibákat.
* **Kimenet:** Zöld Playwright tesztek, sikeres `ruff`, `mypy` és linter ellenőrzések.

### 6. Fázis: Determinisztikus CI/CD Kapuk (Push Gate & BDD Gate)
* **Cél:** Gyors, megbízható integrációs ellenőrzés emberi vagy token-költség nélkül.
* **Módszer:** `npx playwright test` headless módban (<2 perc).
* **Szabály:** Fájlnév-alapú BDD kapu (`scripts/bdd-gate.sh`): ha nincs az adott US azonosítójához tartozó spec fájl, a commit és a PR blokkolva van.

### 7. Fázis: Folyamatos Canary és Evolúciós Hurok
* **Cél:** Éles környezet (prod) és külső adatforrások (OGD / harmadik fél API-k) monitorozása.
* **Módszer:** 0-tokenes, ütemezett cron futtatások (`hermes cron --no-agent`) éles URL-en.
* **Evolúciós mechanizmus:** Ha a canary teszt elbukik (pl. megváltozott egy külső önkormányzati API formátuma), automatikusan létrejön egy `BLOCKED` kártya és egy új kutatási feladat. A hiba így közvetlenül az 1. fázisba áramlik vissza.

---

## 3. A `browser_helper` MCP Részletes Architektúrája és Specifikációja

A `browser_helper` egy dedikált **Model Context Protocol (MCP)** szerver, amely hídként szolgál az LLM agentek és a valós böngészőmotor (Chromium / WebKit) között.

### 3.1. Architekturális Szereposztás
```
+-------------------------------------------------------------+
|                     LLM Multi-Agent Rendszer                |
|        (Behavior-Analyst, Developer, Tester Agents)         |
+-------------------------------------------------------------+
                              │  MCP Eszközhívások (JSON-RPC)
                              ▼
+-------------------------------------------------------------+
|                 browser_helper MCP Szerver                  |
|  - A11y Tree elemző          - Network & Console Watcher    |
|  - Interakciós Vezérlő       - Playwright Kódexportáló      |
|  - Állapot & Tenant Izolátor - Képernyőkép / Multimodal Engine |
+-------------------------------------------------------------+
                              │  Playwright / CDP Protocol
                              ▼
+-------------------------------------------------------------+
|           Böngésző Példány (Chromium Headless/UI)           |
|            http://localhost:3000 (Next.js / FastAPI)        |
+-------------------------------------------------------------+
```

### 3.2. A 6 Alapvető Képességcsoport és Valós Eszköz-Specifikáció (Browser Helper REST API)

> Valós endpointok: `http://localhost:8000` (REST proxy) + CDP 9555. A korábbi `browser_get_*` nevek kitaláltak voltak — az alábbiak a `browser-helper` skill tényleges API-ja.

#### 1. Szemantikus DOM és Akadálymentességi Fa (A11y Tree) Introspekció
Az agent nem törékeny CSS-osztályok (`.btn-blue-400`) alapján navigál, hanem a felhasználó által észlelt akadálymentességi fa szerint.

* **`POST /agent/observe` — token-budgeted observation**
  * *Paraméterek:* `mode: "accessibility" | "legacy"` (ajánlott: `accessibility`), `max_nodes`, `fallback: "accessibility"`, `include_hidden`, `auto_modal`
  * *Vissza:* `snapshot_id` + `element_id` hivatkozások, hierarchikus fa (role, name, value, state). Token-optimalizált.
* **`POST /page/analyze` — comprehensive snapshot**
  * *Vissza:* `buttons[]`, `form_fields[]` (checked state-tel), `modals[]` (role, aria_label, focus_trap), `iframes[]`, `alerts[]`, `text_preview`
* **`POST /page/outline` — heading hierarchy**
  * *Vissza:* `h1–h6` hierarchia + snippet + pozíció

#### 2. Determinisztikus Interakciós Primitívek és Művelet-Ellenőrzés
Minden interakció előtt automatikus *Actionability check* (látható, stabil, kattintható, nem takarja overlay).

* **`POST /agent/act` — high-level actions**
  * *Akciók:* `click`, `fill`, `select`, `wait`, `wait_for_element`, `select_tab`, `evaluate`, `workflow`, stb.
  * *Target:* `{"snapshot_id": "...", "element_id": "e4"}` vagy `{"backend_node_id": 4023}` (snapshot-free)
  * *Opciók:* `auto_recover: true` (stale snapshot → friss accessibility), `pin_snapshot`, `verify_after: {type: "text_visible", text: "Success"}`
* **`POST /click/text`, `/click/label`, `/click/coordinates`, `/type`, `/form/fill`, `/form/select` — smart interaction**
  * *Mikor:* `/click/label` kötelező radios/checkboxokhoz (framework-safe), `/click/text` submit gombokhoz, `/type` beviteli mezőkhöz
* **`POST /wait`, `/wait/text`, `/wait/visible`, `/wait/network-idle` — várakozás**
  * *Szabály:* SPA-nál `domcontentloaded + 2s settle`, ne `networkidle` (polling miatt timeout)

#### 3. Diagnosztika: Hálózati Forgalom és Konzol Naplózás
* **`POST /agent/act` + `browser_get_console_logs` / `browser_get_network_activity` minták**
  * *Használat:* fejlesztés közben `POST /agent/observe` után konzol- és network-log lekérdezés a háttérben elbukó hívásokhoz
  * *Példa:* `js_expression: "window.map?.loaded() === true"` — térképrétegek kirajzolásának megvárása (`/agent/act wait_for_element` + `verify_after`)

#### 4. Vizuális és Strukturális Bizonyítékok (Multimodal Grounding)
* **`POST /headless/screenshot` → `GET /artifacts/{id}` — screenshot workflow**
  * *Paraméterek:* `scope: "viewport" | "full_page" | "element"`, `selector`
* **`POST /screenshot`, `/full_screenshot`, `/element_screenshot` — gyors screenshotok**
  * *Használat:* elrendezés és vizuális hibák multimodális ellenőrzése

#### 5. Automatikus Playwright Kódexport (`record → replay`)
A sikeres feltáró munkamenetből emberi beavatkozás nélkül futtatható Playwright teszt szülessen.

* **`POST /agent/record` (`{"start": true}`) → `POST /agent/record/stop` → `POST /agent/replay`**
  * *Paraméterek:* `recorded_id`, `on_error: "stop"`, `data_overrides`
* **`POST /agent/execute-task` — bounded micro-workflow**
  * *Paraméterek:* `goal`, `constraints: {max_steps: 5}` — observe → discover → fill → verify egyben
* **`POST /agent/extract` — structured data by schema**
  * *Paraméterek:* `schema`, `snapshot_id` — bizonyítékkal, nem fabricate

#### 6. Munkamenet, Adatbázis és Tenant Izoláció
* **`POST /session/save` / `POST /session/restore` — cookies + localStorage + sessionStorage**
  * *Használat:* előre generált JWT / `seedAuth` beillesztése (`addInitScript`), elkerülve a lassú UI login ciklust
* **`POST /agent/forms/discover` + `POST /agent/forms/fill` — semantic form handling**
  * *Paraméterek:* `snapshot_id`, `scope: "page_with_history"` (SPA lazy-loading), `form_ref` + `resolver: "autocomplete"`



---

## 4. Multi-Agent Szerepkörök és Kontextus-Izoláció

Az evolúciós rendszerben a feladatok szigorúan elhatárolt agent-szerepkörök között oszlanak meg, megakadályozva a fejlesztési és tesztelési logikák összefonódását:

| Szerepkör | Felelősség | `browser_helper` Használat | Kimeneti Artefaktum |
|---|---|---|---|
| **`researcher`** | VOC bányászat, piacfelmérés | Weboldalak és fórumok bejárása JS-rendereléssel | `docs/research/*-deep-dive.md` |
| **`behavior-analyst`** | Követelmény- és `gui_flow` specifikáció | Prototípus DOM vizsgálata, A11y fa ellenőrzés | `docs/stories/US-*.md` |
| **`tester`** | E2E Skeleton generálás és audit | **Elsődleges:** Interaktív végrehajtás + `record_to_spec` | `frontend/e2e/us_*.spec.ts` (RED) |
| **`developer`** | Kódimplementáció (GREEN) | Konzol- és hálózati hibakeresés fejlesztés közben | `src/`, `frontend/src/` |
| **`evaluator`** | Backlog rangsorolás, hibaértékelés | Nincs közvetlen böngészőhasználat | Súlyozott backlog mátrix |
| **`release-manager`** | Kapuk és release validáció | Playwright CLI jelentések ellenőrzése | Verziózott kiadás |

---

## 5. Artefaktumok, Szerződések és Sablonok

### 5.1. Bővített User Story Sablon (`docs/stories/US-000-template.md`)

```markdown
# US-NNN: {Cím — Felhasználói cél / JTBD megfogalmazás}

- Epic: {Térkép / Adatkezelés / Hitelesítés / ...}
- Prioritás: P0 / P1 / P2
- Forrás: docs/research/YYYY-MM-DD-*.md + ADR-NNN
- Prototípus / Mockup: {URL / Link} — Státusz: draft | approved

## Story
As a {felhasználói szerepkör}
I want {funkcionalitás leírása}
So that {elérhető üzleti / használhatósági érték}.

## Előfeltételek és Tenant Izoláció (Given State)
- Tenant: `demo-e2e-${RUN_ID}`
- Fixture: `tests/fixtures/user_state.json`
- Auth: `seedAuth` beállítva

## Acceptance Criteria (Gherkin BDD)
- AC1 (Happy path): given {kiinduló állapot} | when {felhasználói cselekvés} | then {elvárt viselkedés és visszajelzés}
- AC2 (Edge case): given {határeset/lassú hálózat} | when {cselekvés} | then {helyes kezelés / skeleton}
- AC3 (Error state): given {érvénytelen bemenet/szerverhiba} | when {cselekvés} | then {szemantikus hibaüzenet}
- AC4 (GUI Flow Contract): given {nyitóoldal betöltve} | when {felületi bejárás} | then {UI állapotkonzisztencia}

## gui_flow (Kötelező Érvényű Felületi Szerződés)
1. Navigate to: `/{route}` -> Vizuális ellenőrzés: Heading látható (`role=heading[name="{Title}"]`)
2. Interact: Fill `input[name="{field_name}"]` értékkel: `{test_data}`
3. Interact: Click `button[name="{CTA_Button}"]` -> Esemény indítása
4. Wait for: Network response `200 OK` a `/api/v1/{endpoint}` végponton
5. Assert: Modal / Toast / Kártya megjelenik pontos szöveggel: `{Visszajelzés}`
6. Accessibility: `axe-core` audit 0 kritikus hibát ad
```

### 5.2. Generált Playwright Specifikáció Sablon (`frontend/e2e/us_NNN.spec.ts`)

```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('US-010: Place-first térkép és adóinformációk', () => {
  const runId = process.env.RUN_ID || 'local';
  const tenantId = `demo-e2e-${runId}`;

  test.beforeEach(async ({ page }) => {
    // Tenant és auth állapot izoláció
    await page.addInitScript((tenant) => {
      window.localStorage.setItem('DEMO_TENANT_ID', tenant);
    }, tenantId);
    
    // Navigáció settle stratégiával
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
  });

  test('AC1: Irányítószám keresés megjeleníti az adókártyát (Happy Path)', async ({ page }) => {
    // Szemantikus lokátorok a browser_helper feltárása alapján
    const postcodeInput = page.getByRole('textbox', { name: /irányítószám|postcode/i });
    const searchButton = page.getByRole('button', { name: /keresés|search/i });

    await expect(postcodeInput).toBeVisible();
    await postcodeInput.fill('8004');
    await searchButton.click();

    // Hálózati és állapot ellenőrzés
    const taxCard = page.getByTestId('tax-info-card');
    await expect(taxCard).toBeVisible({ timeout: 5000 });
    await expect(taxCard).toContainText('Steuerfuss');
  });

  test('AC4: Akadálymentességi audit a felületen', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });
});
```

---

## 6. Gyakorlati Végigjátszás: Valós Esettanulmány

Az alábbi példa bemutatja egy valós funkció (`swiss_p_map`: Községi adókulcs és zajterhelési adatok megjelenítése) életciklusát a rendszerben:

1. **Research Fázis:**
   * A `researcher` agent a `browser_helper` segítségével feltérképezi a svájci nyílt adatportál (OGD) végpontjait és a lakáskeresők panaszait a Redditen.
   * Elkészül a kutatási riport 10 szó szerinti forráshivatkozással.
2. **Követelménymeghatározás:**
   * A `behavior-analyst` megírja az `US-010: Place kártya térképen` specifikációt a fenti sablon alapján.
3. **MCP Tesztgenerálás (RED):**
   * A `tester` agent elindítja a `browser_helper` MCP-t a lokális dev szerveren (`http://localhost:3000`).
   * Végrehajtja a lépéseket: beírja a `8004`-es kódot, rögzíti a kapott Playwright szelektorokat.
   * Kimenti a `frontend/e2e/us_010_place_map.spec.ts` fájlt.
   * Lefut a CLI teszt: `npx playwright test` -> **RED (Piros, mert a backend szolgáltatás még nem létezik).**
4. **Emberi Jóváhagyás (Stop-Gate):**
   * A fejlesztő megmutatja a felületi tervet és a tesztszerződést -> Emberi jóváhagyás megadva.
5. **Autonóm Fejlesztés (GREEN):**
   * A `developer` agent megvalósítja a `PlaceService` osztályt és beköti a MapLibre réteget.
   * Fejlesztés közben a `browser_helper.browser_get_console_logs` hívással ellenőrzi, hogy nincsenek-e kezeletlen Promise hibák.
   * A teszt újra lefut -> **GREEN (Zöld).**
6. **Integráció és Éles Üzem (Canary):**
   * A GitHub Actions BDD kapu átengedi a kódot.
   * A termelési környezetben a `hermes cron` óránként lefuttatja a 0-tokenes canary tesztet az éles OGD API-val szemben.

---

## 7. Stabilitási Szabályok, Flakiness Megelőzés és Anti-Minták

### 7.1. Stabilitási és Anti-Flakiness Szabályok
* **Tilos a `networkidle` használata modern SPA-knál:** A folyamatos WebSocket vagy háttér polling miatt a `networkidle` gyakran timeoutot okoz. Helyette a `domcontentloaded` + explicit állapotvárakozás (`waitForSelector` vagy `expect(locator).toBeVisible()`) a kötelező.
* **Canvas és Térkép Renderelés:** WebGL és MapLibre térképek esetén mindig a térkép belső állapotjelzőjét kell megvárni (`window.map.loaded() === true`), nem pedig tetszőleges időzített alvást (`sleep`).
* **Idempotens Tesztadatok:** Minden tesztfuttatás egyedi azonosítójú tenanthoz kapcsolódik (`demo-e2e-$RUN_ID`). A tesztek futásuk után automatikusan feltakarítanak.

### 7.2. Kerülendő Anti-Minták (Mit NE tegyünk)
1. **Soha ne használjunk vizuális CSS osztályokat lokátorként!** A `.bg-blue-500` vagy `.flex-row` szelektorok stílusmódosításkor azonnal eltörnek. Mindig ARIA szerepköröket vagy `data-testid`-t használjunk.
2. **Ne futtassunk MCP böngészőt a CI/CD futószalagon!** Az MCP böngésző magas token- és időköltséggel bír; kizárólag a tesztkészítés és a helyi hibakeresés eszköze. A CI-ben natív Playwright CLI fut.
3. **Nincs kódírás RED teszt nélkül!** Ha egy kód a teszt megírása előtt készül el, a teszt megbízhatósága nem bizonyított.
4. **Nincs tesztkihagyás gyorsjavításnál sem!** A legapróbb javításnak is rendelkeznie kell egy azonosítható és reprodukálható teszttel.

---

## Függelék A — Evaluator Súlyozás és Ledger (az eredeti EVOLUTIONARY-SYSTEM.md-ből visszaemelve)

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

**Kimenet:** Rangsorolt backlog tábla + Top 5 részletezés (1 mondat pitch + 3 verbatim idézet URL+dátum + kockázat + következő `Research → ADR → Kanban kártya + AC` lépés)
Prompt/runbookok: `docs/research/prompts/hermes-miner.md` + `gemini-miner.md` + `agy-scorer.md` + `evaluator.md`.

### Ledger (grounded-citations — kötelező)

```bash
S=~/.hermes/skills/research/grounded-citations/scripts/sources.py
HERMES_CITATION_LEDGER=/tmp/ledger-deep-YYYY-MM-DD.json
HERMES_CITATION_LEDGER=$LEDGER python "$S" reset
HERMES_CITATION_LEDGER=$LEDGER python "$S" add <url1> <url2>   # minden web_extract URL-nél
# írás közben: per mondat [n] (max 3)
HERMES_CITATION_LEDGER=$LEDGER python "$S" render --cited-in draft.md   # Sources blokk géppel
HERMES_CITATION_LEDGER=$LEDGER python "$S" verify draft.md --evidence --min-coverage 0.5
# párhuzamos subagenteknél: közös HERMES_CITATION_LEDGER (különben ID-ütközés)
```

### Reviewer kérdések

1. A 7 réteg lefedi a mit–mivel–hogyan–bizonyítjuk láncot? Hiányzik artefakt?
2. A 4× story minimum (happy/edge/error/gui) elég a 100%-hoz, vagy kell 5. (pl. a11y)?
3. A súlyozás (30/25/20/15/10) reális, vagy más súly kellene (pl. megvalósíthatóság fel)?
4. A stop-gate (prototípus jóváhagyás) nem lassítja túl a kis fixeket? Kell-e „kis fix” kivétel (Fast-Track)?
5. A canary freq (30m/60m) és értesítés (Telegram + BLOCKED) arányos?
Plusz: 1 legnagyobb kockázat + 1 leggyorsabb win szerinted.

---

*Ez a file a `EVOLUTIONARY-SYSTEM.md` technikai függeléke. Master: `docs/methodology/EVOLUTIONARY-SYSTEM.md` — részletek itt, rendszer-áttekintés ott.*
