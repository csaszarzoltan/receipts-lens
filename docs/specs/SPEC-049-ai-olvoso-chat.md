---
id: FEAT-049
title: AI olvasó-chat a saját nyugták felett ("kérdezd a számláidat")
status: ready_for_dev
version: 1
risk: medium
owner: documenter
related_brief: docs/research/2026-09-11-ai-chat-deep-dive.md
---

# FEAT-049: AI olvasó-chat a saját nyugták felett ("kérdezd a számláidat")

> Előretekintő (kutatás→spec) specifikáció. A megvalósítás még nem
> szállítva; ez a dokumentum a `docs/research/2026-09-11-ai-chat-deep-dive.md`
> 5. fejezet SPEC-vázlatát rögzíti a VERITAS 1.1 §4.5 16-fejezetes
> szerkezetében (a SPEC-038..048 által bevezetett sablon szerint).
> Normatív alap: VERITAS 1.1. Kockázat: R2.

## 1. Cél és felhasználói eredmény

A felhasználó a saját nyugtáiról természetes nyelven (magyarul és angolul)
kérdezhet ("mennyit költöttem ételre júliusban?"), és összeget plusz
megnyitható forrás-nyugtákat kap válaszul — szűrők építgetése nélkül.
Számot kizárólag determinisztikus lekérdezés/aggregáció állít elő; az LLM
csak fordít (NL→lekérdezés) és fogalmaz (eredmény→válasz). Minden számadat
mögött forrás-sor áll; kevés vagy hiányzó adat esetén a rendszer ezt
expliciten jelzi, nem találgat; sikertelen LLM/DB-hívás soha nem jelenik
meg válaszként.

Mérhető készültségi feltétel: a 11. fejezet 5 acceptance-pontja teljesül —
10 mintakérdés-bank (HU/EN) ≥9 determinisztikus egyezéssel, negatív
kereszt-tenant teszt, PII-mentes prompt-log, "nincs adat" + hibaág UI-teszt,
és havi költség a 6. fejezet becslési sávján belül 1 000 kérdésen.

## 2. Kontextus és források

Kanonikus források:

- `docs/research/2026-09-11-ai-chat-deep-dive.md` (RL RESEARCH-1, t_e8a9057c,
  commit d0a229e) — 1) versenytárs-tábla (Dext, Sage, Veryfi, Ramp, Expensify),
  2) scope-opciók (a/b/c), 3) LLM-költségbecslés, 4) privacy/R3, 5) RICE +
  SPEC-vázlat (REQ-049-01..08, NFR, acceptance).
- `VERITAS_1_1_adaptiv_egyseges_fejlesztesi_modszertan.md` §4.5 (SPEC-sablon),
  §6 (kockázati osztályok R2/R3).
- `docs/specs/SPEC-008-*.md` — REQ-008-06 (tenant-izoláció MUST NOT-minta),
  NFR-008-01 (500 ms UI-visszajelzés minta).
- `docs/specs/SPEC-033-*.md` — REQ-033-04 (kevés-adat jelzés minta),
  REQ-033-05 (téves-jelzés visszajelzés, a proaktív követőhöz).

Adatmodell-kontextus (kutatás 2a): `receipts(tenant_id, payload JSON,
blob_ref)`; OCR-szöveg + kategóriák léteznek (FEAT-007/011); keresés/szűrés
(FEAT-008), költéselemzés/aggregátumok (FEAT-013), anomália-jelzés (FEAT-033),
adatmegőrzés/törlés (FEAT-025) adott.

Kapcsolódó domain-invariánsok: tenant-izoláció, determinisztikus számítás,
hallucináció-tilalom pénzügyi számokra, prompt-minimalizálás (PII),
írás-tilalom olvasó módban.

## 3. Scope és non-scope

### Benne van

- NL-kérdés → determinisztikus lekérdezés/aggregáció → verbalizált válasz
  forrás-hivatkozásokkal, a Nyugták-lista (FEAT-008) kontextusába ágyazott
  chat-panelben.
- Válaszonkénti forrás-sorok (nyugta-részlet FEAT-008 szerint), "nincs elég
  adat" jelzés (REQ-033-04 minta), újrapróbálás + naplózott hibaág.
- Privacy-boríték: csak a kérdéshez szükséges tenant-szelet a promptban;
  teljes OCR/kép soha; kérdésenkénti token-limit + havi kvóta.
- Chat-előzmény FEAT-025 hatálya alatt (megőrzési idő, tulajdonosi törlés,
  törlési előnézet + külön megerősítés).

### Nincs benne

- Író-chat (kategória-javítás, szabály-állítás, megőrzési beállítás
  módosítása) — ez FEAT-050, R3, külön SPEC; kizárását REQ-049-06 rögzíti.
- Proaktív insight-értesítések ("ez a hónap kilóg") — FEAT-033
  kiterjesztéseként, olcsó követőként szállítandó (kutatás 5. fejezet
  javaslata); a chat-panel csak "nyisd meg a chatben" mélylink-célpontként
  vesz részt benne.
- Nyílt MCP-réteg külső LLM-ekhez (Expensify-minta) — későbbi differenciáló,
  nem része FEAT-049-nek.
- Self-hosted LLM bevezetése — roadmap-opció R3-adatrezidens igényre, nem
  alapértelmezett.

## 4. Szereplők és előfeltételek

- ACT-049-01: háztartási felhasználó (magyarul/angolul kérdez, forrást nyit
  meg, kevés-adat jelzést értelmez).
- ACT-049-02: háztartási tulajdonos (chat-előzmény megőrzését/törlését
  kezeli FEAT-025 szerint; megosztott adatoknál tulajdonosi kontroll).
- ACT-049-03: termékfelelős/adatvédelmi felülvizsgáló (prompt-log
  PII-mentességét és kereszt-tenant negativitást ellenőriz; R2
  privacy-review kötelező).

- PRE-049-01: érvényes `Authorization` + `X-Tenant-ID` minden chat-művelethez
  (FEAT-008 auth-minta; különben 401).
- PRE-049-02: a tenant `receipts`-szelete lekérdezhető (FEAT-008/FEAT-013
  aggregációs alap adott).
- PRE-049-03: külső LLM-szerződés EU-adatrezidenciával +
  "trainingre nem használható" (zero-retention/opt-out) záradékkal; enélkül
  R3-blokkoló (kutatás 4. fejezet).
- PRE-049-04: havi kvóta- és token-limit konfigurálva a költség-plafonhoz.

## 5. Funkcionális követelmények

- REQ-049-01 [MUST]: Felhasználóként természetes nyelven kérdezhetek a saját
  nyugtáimról (pl. "mennyit költöttem ételre júliusban?"), és összeget +
  forrás-nyugtákat kapok.
- REQ-049-02 [MUST]: A válasz minden számadatához megnyitható forrás-sor
  tartozik (nyugta-részlet, FEAT-008 szerint).
- REQ-049-03 [MUST]: A chat csak a saját háztartás adatait látja; más tenant
  adata nem szivároghat (FEAT-008 REQ-008-06 minta).
- REQ-049-04 [MUST]: Számítást kizárólag determinisztikus
  lekérdezés/aggregáció végez; az LLM eredményt nem "emlékezetből" mond.
  Csak olvasó statement hajtódhat végre (AgentNLQ guardrail-minta [14]).
- REQ-049-05 [MUST]: Kevés/nincs adat esetén a rendszer ezt expliciten
  jelzi, nem találgat (REQ-033-04 minta).
- REQ-049-06 [MUST NOT]: A chat nem módosíthat adatot, szabályt vagy
  megőrzési beállítást (írás = FEAT-050, R3, külön SPEC).
- REQ-049-07 [ALWAYS]: Sikertelen LLM/DB-hívás nem jelenhet meg válaszként;
  újrapróbálás + naplózott hibaág.
- REQ-049-08 [CONCURRENCY]: Párhuzamos kérdés nem okoz duplikált
  mellékhatást (olvasó-volta miatt triviális, de tesztelt).

## 6. Nem funkcionális követelmények

- NFR-049-01 [PERFORMANCE]: UI-visszajelzés a kérdés elküldésétől 500 ms-on
  belül (NFR-008-01 minta); hosszabb LLM/DB-futás alatt folyamatos
  állapotjelzés (gépelés/frissítés-jelző).
- NFR-049-02 [PRIVACY]: promptba csak a kérdéshez szükséges tenant-szelet
  kerülhet (kereskedő, dátum, összeg, kategória, szűkített OCR-részlet);
  teljes OCR-blob és nyugta-kép **soha**. Prompt-naplózás tiltott vagy
  PII-maszkolt; szolgáltatói oldalon tárolt prompt-log max 30 nap vagy
  kikapcsolt.
- NFR-049-03 [SECURITY]: minden lekérdezés szerveroldali tenant-scopinggal
  fut; más tenant azonosítója nem használható; a végrehajtott statement
  olvasó-jellegét a futtató réteg kényszeríti ki.
- NFR-049-04 [COST]: költség-plafon — kérdésenkénti token-limit + havi
  kvóta. Becslési sáv (kutatás 3. fejezet, ~2 000 input / 300 output tok
  kérdésonként): GPT-4o mini sávban ~$0.0005/kérdés, azaz **~$1/hó
  2 000 kérdésen (100 user × 20 kérdés)** és **~$10/hó 20 000 kérdésen**;
  nehezebb érvelésre eszkaláció (Haiku/Sonnet) megengedett, de a havi
  költség 1 000 kérdésen nem lépheti túl a mini-sáv arányos értékét.
- NFR-049-05 [RELIABILITY]: LLM/DB-hiba esetén a bevitt kérdés megmarad,
  újrapróbálás kínált, duplikált költség-oldali mellékhatás nincs;
  kvóta-kimerüléskor a rendszer ezt expliciten jelzi (nem néma elutasítás).
- NFR-049-06 [PRIVACY]: chat-előzmény = FEAT-025 hatálya: látható megőrzési
  idő (REQ-025-02), törlési előnézet (REQ-025-03), külön megerősítéses
  végleges törlés (REQ-025-04).

## 7. UI-szerződés

- UI-049-01: chat-panel a Nyugták-listán (FEAT-008) belül — kérdés-bevitel,
  válasz-buborék összeggel + megnyitható forrás-sorokkal, "nincs elég adat"
  állapot, hibaág újrapróbálás-gombbal, kvóta-jelzés.
- UI-049-02: forrás-sor → nyugta-részlet navigáció (FEAT-008
  részlet-nézetre épül); minden szám kattinthatóan visszavezethető.
- UI-049-03: kétnyelvűség — HU/EN kérdés és válasz; a 10 mintakérdés-bank
  mindkét nyelven lefedi ugyanazt a 10 szándékot.
- UI-049-04: előzmény-nézet FEAT-025 szerint (megőrzési idő látszik, törlés
  előnézettel + külön megerősítéssel).

## 8. Felhasználói és GUI-folyamat

1. A felhasználó a Nyugták-listán megnyitja a chat-panelt és beírja
   (HU/EN) a kérdést; 500 ms-on belül visszajelzést kap (NFR-049-01).
2. A rendszer a kérdést determinisztikus lekérdezéssé fordítja a saját
   tenant-szelet felett; az LLM nem számol, csak fordít + fogalmaz.
3. A válasz összeget és megnyitható forrás-sorokat mutat; a felhasználó
   bármely számot visszakövetheti a nyugta-részletig.
4. Kevés/nincs adat esetén explicit "nincs elég adat" jelzés jelenik meg,
   találgatás nélkül (REQ-049-05).
5. Hiba (LLM/DB) esetén a kérdés megmarad, hibaág + újrapróbálás jelenik
   meg; sikertelen hívás soha nem látszik válasznak (REQ-049-07).
6. Kvóta-kimerüléskor explicit jelzés; az előzmény FEAT-025 szerint
   megőrizhető/törölhető.
7. Írás-kísérlet ("javítsd át a kategóriát…") elutasítva: a chat jelzi,
   hogy módosításra nem képes (FEAT-050 jön) — REQ-049-06.

## 9. Állapotmodell

Nincs perzisztens állapotgép a chat-válaszok mögött (olvasó-funkció).
Kliens-oldali panel-állapotok: `IDLE` → `ASKING` (500 ms visszajelzés) →
`ANSWERED` / `NO_DATA` / `ERROR` (újrapróbálható) / `QUOTA_EXHAUSTED`.
Szerver-oldalon: kérés-scoped végrehajtás (tenant-scoped SELECT +
aggregáció), mellékhatás-mentes; perzisztált entitás csak a chat-előzmény
(FEAT-025 életciklusa szerint: megőrzés → előnézetes törlés → végleges
törlés külön megerősítéssel).

## 10. API-, esemény- és adatszerződés

Tervezett szerződés (implementáció时 kötelező, eltérés SPEC-GAP):

- `POST /api/v2/chat/ask` — `{ question: string, locale: hu|en }` +
  `Authorization` + `X-Tenant-ID`; 200 `{ answer, sources: [{ receipt_id,
  amount, merchant, date }], query_hash }` / 401 / 403 / 422 (üres kérdés,
  kvóta-kimerülés jelzése) / 503 (LLM/DB-hiba, újrapróbálható).
- Író-végpont **nincs** (REQ-049-06); a futtató réteg csak olvasó
  statementet engedélyez.
- Eseménybusz: nincs; költség/kvóta-metrika a megfigyelhetőségben (15. f.).
- Adatmodell-újdonság: chat-előzmény FEAT-025 szerint; a prompt-összeállítás
  bemenete kizárólag a tenant-szelet (`receipts.payload` mezők + FEAT-013
  aggregátumok), teljes OCR/kép kizárva.

## 11. Acceptance scenario-k

### AC-049-01: mintakérdés-bank determinisztikus egyezéssel (REQ-049-01, REQ-049-04)

Given 10 rögzített mintakérdés HU/EN nyelven (pl. havi étel-összeg,
kereskedő szerinti bontás, legnagyobb nyugta adott időszakban)
When mindegyik lefut a tenant-szeleten
Then ≥9 válasz összege pontosan egyezik a közvetlen DB-aggregációval, és
mind a 10-hez tartozik forrás-sor.

### AC-049-02: forrás-sor visszakövethetőség (REQ-049-02)

Given megválaszolt kérdés számadatokkal
When a felhasználó bármely számra kattint
Then megnyílik a hozzá tartozó nyugta-részlet (FEAT-008 nézet).

### AC-049-03: kereszt-tenant szivárgási teszt negatív (REQ-049-03)

Given két tenant átfedő kereskedőkkel/összegekkel
When A-tenant kérdést tesz fel B-tenant adataira utaló megfogalmazással
Then B-adat nem jelenik meg (üres/nincs-adat vagy csak A-szelet).

### AC-049-04: determinisztikus számítás (REQ-049-04)

Given szám-kérdés
When a végrehajtott statement naplózott
Then az csak olvasó lekérdezés/aggregáció; LLM-generált szám nincs a
válaszban DB-találat nélkül.

### AC-049-05: "nincs adat" jelzés találgatás nélkül (REQ-049-05)

Given üres/szűk tenant-szelet a kérdés tartományában
When a kérdés lefut
Then explicit "nincs elég adat" válasz érkezik, szám nélkül.

### AC-049-06: írás-elutasítás (REQ-049-06)

Given "javítsd át / állítsd be / töröld…" típusú kérdés
When a chat feldolgozza
Then adat-, szabály- és megőrzési módosítás nem történik; a válasz a
korlátot jelzi (FEAT-050-re utalva).

### AC-049-07: hibaág és párhuzamosság (REQ-049-07, REQ-049-08)

Given szimulált LLM/DB-hiba, majd párhuzamos azonos kérdések
When a hibás hívás lefut és a párhuzamosak megérkeznek
Then a hiba nem jelenik meg válaszként (újrapróbálás + naplózás), és nincs
duplikált mellékhatás.

### AC-049-08: prompt-log PII-mentesség + költség-sáv (NFR-049-02, NFR-049-04)

Given 1 000 kérdéses terhelési minta
When a prompt-logok auditálva és a költség összesítve
Then teljes OCR/kép sehol a logokban (PII-maszkolás igazolt), és a havi
költség ≤ a 6. fejezet mini-sávjának arányos értéke.

## 12. Tesztleképezés

Előretekintő leképezés — a tesztek a megvalósítással szállítandók
(eltérés esetén SPEC-GAP-bejegyzés kötelező):

| REQ | AC | E2E-teszt (tervezett) | GUI | Unit-cél |
| :--- | :--- | :--- | :--- | :--- |
| REQ-049-01 | AC-049-01 | `test_e2e_049_ac_01_question_bank` | chat-panel mintakérdés-futtatás | NL→lekérdezés fordító unit |
| REQ-049-02 | AC-049-02 | `test_e2e_049_ac_02_source_trace` | forrás-sor → részlet navigáció | forrás-kapcsoló unit |
| REQ-049-03 | AC-049-03 | `test_e2e_049_ac_03_cross_tenant_negative` | — | tenant-scoping unit |
| REQ-049-04 | AC-049-04 | `test_e2e_049_ac_04_readonly_statement` | — | statement-őr unit |
| REQ-049-05 | AC-049-05 | `test_e2e_049_ac_05_no_data` | "nincs adat" UI-állapot | kevés-adat detektor unit |
| REQ-049-06 | AC-049-06 | `test_e2e_049_ac_06_write_refused` | írás-elutasítás UI | intent-osztályozó unit |
| REQ-049-07 | AC-049-07a | `test_e2e_049_ac_07_error_branch` | hibaág + újrapróbálás UI | retry-naplózó unit |
| REQ-049-08 | AC-049-07b | `test_e2e_049_ac_08_concurrent_read` | — | idempotencia-ellenőrzés |

AC-049-08 (prompt-log audit + költség) E2E-helyettese: tervezett
`test_e2e_049_ac_08_prompt_cost_audit` (log-minta PII-scan + kvóta-elszámolás
ellenőrzés).

## 13. Kockázatok és emberi döntések

- HR-049-01: hallucinált pénzügyi szám döntést terel — ezért REQ-049-04
  (determinisztikus számítás) és AC-049-04 (csak-olvasó statement) kötelező;
  szám-eltérés = hibaág.
- HR-049-02: promptba kerülő pénzügyi PII (kereskedő, összeg, dátum
  elkerülhetetlen) — NFR-049-02 minimalizálás + PII-maszkolt naplózás +
  kötelező privacy-review (R2-kapu); Human Authority nem kell (olvasó),
  de a felülvizsgálat igen.
- HR-049-03: hamis biztonságérzet kevés adatnál — REQ-049-05 explicit
  jelzés, találgatás-tilalom.
- HR-049-04: költség-elszállás skálázódáskor — NFR-049-04 token-limit +
  havi kvóta + mini-sáv indulás, eszkaláció csak nehezebb érvelésre.
- R3-határ: külső LLM-szerződés adatrezidencia/opt-out nélkül R3-blokkoló
  (PRE-049-03); írás-képesség hozzáadása TILOS e SPEC keretében (FEAT-050).

## 14. Nyitott kérdések és SPEC-GAP

Előretekintő SPEC — implementáció még nem létezik, ezért SPEC-GAP helyett
szállítási függőségek:

- OPEN-049-01: LLM-szolgáltató és modellválasztás (javaslat: GPT-4o mini /
  Gemini Flash-Lite sáv induláskor; döntés a megvalósításkor,
  költség-sáv tartásával).
- OPEN-049-02: mintakérdés-bank végleges 10 tétele (HU/EN párok) — a
  megvalósító PR-ban rögzítendő, AC-049-01 rájuk fut.
- OPEN-049-03: pontos token-limit és havi kvóta-értékek tenant-típusonként —
  termékdöntés a megvalósításkor (NFR-049-04 sávján belül).
- OPEN-049-04: chat-panel pontos helye és mélylink-szerződése a proaktív
  (FEAT-033-követő) insight-kártyák felé — FEAT-033 kiterjesztési
  SPEC-ben rögzítendő.

## 15. Rollback és megfigyelhetőség

- Rollback: olvasó-funkció, nincs séma-migrációs kényszer (előzmény FEAT-025
  szerint); visszaállítás feature-flag/kikapcsolással, adatmigráció nélkül.
- Megfigyelhetőség: kérdés-szám, determinisztikus-egyezési arány
  (AC-049-01 metrika), hibaarány + újrapróbálási napló (korrelációs
  azonosítóval), kereszt-tenant kísérletek riasztása, prompt-log PII-scan
  eredménye, token/költség-fogyás a kvóta ellenében. Válaszokban
  tenant-azonosító és `query_hash` a visszakövethetőséghez.

## 16. Definition of Done

- [ ] mind a 8 REQ-hez AC-scenario (AC-049-01..AC-049-08, kész ebben a SPEC-ben).
- [ ] E2E-tesztek (`test_e2e_049_ac_*`) + GUI-lefedés zöld a megvalósító PR-ban.
- [ ] 10 mintakérdés-bank HU/EN rögzítve, ≥9 determinisztikus egyezés igazolva.
- [ ] kereszt-tenant negatív teszt zöld; prompt-log PII-audit zöld.
- [ ] "nincs adat" + hibaág UI-teszt zöld; havi költség ≤ becslési sáv.
- [ ] privacy-review lezárva (R2-kapu); Human Authority nem szükséges (olvasó).
- [ ] visszamutatás kutatás ↔ SPEC-049 ↔ tesztek (`docs/traceability-index.md`).
- [ ] production kód csak a megvalósító (külön) feladatban változik.
