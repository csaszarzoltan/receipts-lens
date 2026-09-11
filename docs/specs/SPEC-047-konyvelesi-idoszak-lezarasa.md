---
id: FEAT-047
title: Könyvelési időszak lezárása
status: ready_for_dev
version: 1
risk: high
owner: documenter
related_brief: BRIEF-047
---

# FEAT-047: Könyvelési időszak lezárása

> Visszamenőleges (kód→spec) specifikáció. A megvalósítás már szállítva;
> ez a dokumentum a tényleges kódviselkedést rögzíti a VERITAS 1.1 §4.5
> 16-fejezetes szerkezetében. Ahol a BRIEF többet állít, azt a 14. fejezet
> SPEC-GAP listája jelöli.

## 1. Cél és felhasználói eredmény

A könyvelő a lezárandó időszak készültségét látja, automatikus
előellenőrzést futtat (hiányzó nyugta, párosítatlan tranzakció,
bizonytalan adat, duplikátum, visszatérítés, hibás felosztás), a
blokkoló hibákat forrással és javítási úttal hárítja el, a megengedett
kivételeket dokumentált indokkal elfogadja, az összesítések és
egyenlegek előnézetét ellenőrzi, majd külön megerősítéssel lezár. A
lezárt időszak csendes módosítástól védett, a szabályozott újranyitás
indoklással és jóváhagyással történik, a zárás lezárási bizonyítékkal
auditálható, az újranyitás előtti/utáni eredmény összehasonlítható és új
verzióként zárható.

Mérhető készültségi feltétel: mind a 8 REQ-hez tartozik AC-scenario és
végrehajtható E2E-teszt (`.agent-pipeline/03_e2e_suites/test_e2e_047.py`,
8/8 PASS a 2026-08-31 verifikáció szerint).

## 2. Kontextus és források

Kanonikus források:

- `briefs/BRIEF-047-konyvelesi-idoszak-lezarasa.md` (10 US: US-047-01..US-047-10)
- `VERITAS_1_1_adaptiv_egyseges_fejlesztesi_modszertan.md` §4.5
- `05_docs/2026-08-31-phase2-feat038-048-verification-report.md`
- `.agent-pipeline/02_specs/done/SPEC-047-konyvelesi-idoszak-lezarasa.md` (előd pipeline-spec)

Kódforrások (leltár):

- `app/period_close_api.py` — router + 5 route (`:8` prefix `/api/v2/accounting-periods`; route-ok `:21`, `:24`, `:28`, `:32`, `:36-38`)
- `app/period_close_models.py` — `Status` (`:8-17`), `CreateRequest` (`:18-22`), `CommandRequest` (`:24-29`), `AccountingPeriod` (`:31-40`), hibák (`:45-52`)
- `app/period_close_service.py` — `AccountingPeriodService` (`:7`), kezdő `OPEN` (`:21`), action-leképezés (`:32`)
- `app/api_v2.py` — bekötés (`:23` import, `:159` include_router)
- `frontend/app/accounting/period-close/page.tsx`, `frontend/components/accounting/PeriodCloseWizard.tsx`

Kapcsolódó domain-invariánsok: tenant-izoláció, blokkoló hiba mellett
zárás tilalma, explicit megerősítés visszafordíthatatlan művelethez,
lezárt adat módosításvédelme, szabályozott újranyitás, auditálható
bizonyíték, idempotens close, verziózott újrazárás.

## 3. Scope és non-scope

### Benne van

- Könyvelési időszak létrehozása, listája, részlete, revíziózott állapotváltása és confirm-útja.
- Készültség, előellenőrzés-eredmény, blokkoló/figyelmeztetés lista, kivétel-elfogadás, összesítés-előnézet és bizonyíték-hivatkozás a szabad `data`/`evidence` payloadban.
- Lezárás/újranyitás/újrazárás szemantikája a `Status` sémában (lásd 9. fejezet).
- Tenant-izoláció, idempotencia, optimistic locking, `application/problem+json` hibák.

### Nincs benne

- Hivatalos könyvvizsgálat vagy adóbevallás benyújtása; országonkénti adatmegőrzési jogi meghatározás; lezárt forrásadat visszafordíthatatlan törlése (a BRIEF non-scope-ja is kizárja).
- Előellenőrző motor (hiány/duplikátum/nettó-szkenner) és bizonyíték-generátor a szerveren — lásd SPEC-GAP-047-01.
- Perzisztens tárolás: folyamat-memória (lásd 10. és 15. fejezet).

## 4. Szereplők és előfeltételek

- ACT-047-01: könyvelő (készültséget néz, előellenőriz, blokkolót hárít, előnézetet ellenőriz, lezár, bizonyítékot kér).
- ACT-047-02: jogosult felhasználó (kivételt fogad el, újranyitást indít/jóváhagy).

- PRE-047-01: érvényes `Authorization` + `X-Tenant-ID` (különben 401 — `app/period_close_api.py:10-13`).
- PRE-047-02: `X-Role` ∈ {admin, owner, member, accountant} (különben 403); a lezárás/újranyitás tipikusan accountant/admin/owner hatáskör (kliens-szabály, lásd GAP).
- PRE-047-03: módosításhoz `Idempotency-Key` (min. 16 karakter, különben 422 — `:15-17`).
- PRE-047-04: zárási/nyitási művelethez ismert `expected_revision` (különben 409).

## 5. Funkcionális követelmények

- REQ-047-01 [MUST]: A lezárandó időszak készültsége és előellenőrzése látható.
- REQ-047-02 [MUST]: Blokkoló hibával az időszak nem zárható le.
- REQ-047-03 [MUST]: Figyelmeztetés csak dokumentált elfogadással vihető tovább.
- REQ-047-04 [MUST]: Lezárás explicit megerősítést, jogosultságot és evidence hash-t igényel.
- REQ-047-05 [MUST]: Lezárt időszak csendes pénzügyi módosítása tiltott.
- REQ-047-06 [MUST]: Más tenant időszaka nem hozzáférhető.
- REQ-047-07 [MUST]: Azonos close kérés egy lezárási verziót eredményez.
- REQ-047-08 [MUST]: Újranyitás jóváhagyott, indokolt és verziózott újrazárást tesz lehetővé.

## 6. Nem funkcionális követelmények

- NFR-047-01 [PERFORMANCE]: készültség- és előnézet-képernyő UI-visszajelzése 500 ms-on belül; az előellenőrzés hosszú futása állapotjelzéssel történik.
- NFR-047-02 [ACCESSIBILITY]: a zárási varázsló billentyűzettel végigvihető; a lezárás következménye érthetően bejelentett a megerősítés előtt.
- NFR-047-03 [SECURITY]: szerveroldali `context()` az autoritatív; a zárás/újranyitás jogosultsági mátrixa termékdöntés szerint érvényesítendő (lásd GAP).
- NFR-047-04 [PRIVACY]: a bizonyíték csak a záráshoz szükséges adatot tartalmazza; más tenant időszaka nem jelenhet meg.
- NFR-047-05 [RELIABILITY]: blokkoló hiba mellett a zárás technikailag is megakadályozandó (lásd GAP); lezárt adat csendes módosítása tilos; idegen tenant azonosítóra 404-szerű válasz.

## 7. UI-szerződés

- UI-047-01: `frontend/app/accounting/period-close/page.tsx` + `frontend/components/accounting/PeriodCloseWizard.tsx` — időszak-választó készültséggel (US-047-01), előellenőrzés-indító és eredménylista forrással/javítási úttal (US-047-02, US-047-03).
- UI-047-02: ugyanott kivétel-elfogadó indoklással (US-047-04), összesítés/egyenleg/import/export előnézet (US-047-05), külön megerősítő zárás (US-047-06), bizonyíték-nézet (US-047-09), újranyitás előtti/utáni összehasonlító és verziózott újrazárás (US-047-08, US-047-10).
- UI-047-03: E2E GUI-lefedés: `frontend/e2e/gui_e2e_046_047_quality_lock.spec.ts`.

## 8. Felhasználói és GUI-folyamat

1. A könyvelő kiválasztja a lezárandó időszakot; a készültség látszik (`GET /api/v2/accounting-periods`, `OPEN` szemantika).
2. Automatikus előellenőrzés fut a hat hibatípusra; blokkolók és figyelmeztetések forrással és javítási úttal jelennek meg.
3. A blokkolókat a könyvelő elhárítja; a megengedett kivételeket a jogosult dokumentált indokkal elfogadja (`PATCH .../{id}` + `reason`).
4. Lezárás előtt az összesítések, nyitó/záró egyenlegek, importok és exportok előnézete ellenőrizhető.
5. A lezárás külön megerősítéssel, jogosultsággal és evidence-hash-sel történik (`POST .../{id}/confirm` szemantika).
6. Lezárt időszak adata alapértelmezetten védett a csendes módosítástól.
7. Szabályozott újranyitás indoklással és jóváhagyással; az előtte/utána eredmény összehasonlítható, majd új verzióként zárható.
8. Lezárási bizonyíték (időszak, ellenőrzések, kivételek, felelősök, forrásverziók) kérhető.
9. Hiba esetén a felület az állapotot megőrzi, újrapróbálást kínál, véletlen zárás nem történhet.

## 9. Állapotmodell

Tényleges gépi állapotok (`app/period_close_models.py:8-17`):

- `OPEN` (kezdő — `app/period_close_service.py:21`), `PRECHECK_RUNNING`, `BLOCKED`, `READY_TO_CLOSE`, `CLOSED`, `REOPEN_PENDING`, `REOPENED`, `RECLOSED`.

Megfigyelt átmenetek (`app/period_close_service.py:32`):

- `confirm` → `REOPENED`; `reject` → `RECLOSED`; `resolve` → `REOPENED`; `reopen` → `OPEN`.
- Feltétel: `expected_revision` egyezik, különben 409 írás nélkül.
- Megjegyzés: a `PRECHECK_RUNNING`/`BLOCKED`/`READY_TO_CLOSE`/`CLOSED` zárási életút és a `REOPEN_PENDING` jóváhagyási szemantika a sémában létezik, de a generikus leképezés közvetlenül nem vezérli őket — a varázsló a `data` payloadon és a hívássorrenden keresztül tartja nyilván (lásd GAP).

## 10. API-, esemény- és adatszerződés

### REST (mind `app/period_close_api.py`)

| Route | Kódhely | Szerződés |
| :--- | :--- | :--- |
| `GET /api/v2/accounting-periods` | `:21-22` | tenant-szűrt lista; 200 / 401 / 403 |
| `POST /api/v2/accounting-periods` | `:24-26` | `CreateRequest`; kötelező `Idempotency-Key`; 201 / 400 / 401 / 403 / 409 / 422 |
| `GET /api/v2/accounting-periods/{id}` | `:28-30` | részlet + `evidence`; idegen tenantnál 404-szerű `NOT_FOUND` |
| `PATCH /api/v2/accounting-periods/{id}` | `:32-34` | `CommandRequest` + `expected_revision`; 200 / 409 / 422 |
| `POST /api/v2/accounting-periods/{id}/confirm` | `:36-38` | `action="confirm"` kényszerítéssel delegál; 200 / 403 / 409 / 422 |

Hibák: `application/problem+json` (`:19`; modellek `:42-44`). Bekötés: `app/api_v2.py:23`, `:159`.

### Események

Nincs eseménybusz; előellenőrző-futás és zárás-jóváhagyási workflow szerveroldalon nincs bekötve (GAP).

### Adatmodell

- `AccountingPeriod` (`app/period_close_models.py:31-40`): `id`, `tenant_id`, `status`, `revision`, `client_reference`, `data: dict`, `evidence: dict`, `created_at`, `updated_at`.
- `CreateRequest` (`:18-22`), `CommandRequest` (`:24-29`) — generikus alak.
- Hibák: `NotFoundError` 404 (`:48-49`), `StaleRevisionError` 409 (`:50-51`), `IdempotencyConflictError` 409 (`:52-53`).
- Tárolás: `AccountingPeriodService._items` + `_keys`, `threading.RLock` (`app/period_close_service.py:7-9`); létrehozáskor `evidence={"source": "FEAT-047"}` (`:21`); migráció nincs.

## 11. Acceptance scenario-k

### AC-047-01: készültség és előellenőrzés (REQ-047-01)

Given kiválasztott időszak
When a könyvelő a készültséget és az előellenőrzést kéri
Then a hat hibatípus eredménye forrással és javítási úttal látszik.

### AC-047-02: blokkoló megakadályozza a zárást (REQ-047-02)

Given fel nem oldott blokkoló hiba
When zárási kísérlet történik
Then a zárás nem hajtható végre; a felület a blokkolóra mutat. (Szerveroldali kikényszerítésre lásd GAP.)

### AC-047-03: dokumentált kivétel (REQ-047-03)

Given megengedett figyelmeztetés
When a jogosult indoklással elfogadja
Then a zárás folytatható, az indoklás a bizonyíték része.

### AC-047-04: megerősített lezárás (REQ-047-04)

Given `READY_TO_CLOSE` szemantika, ellenőrzött előnézet
When a könyvelő külön megerősítéssel lezár
Then az időszak `CLOSED` szemantikába kerül evidence-hash-sel; véletlen zárás kizárt.

### AC-047-05: módosításvédelem (REQ-047-05)

Given lezárt időszak
When csendes pénzügyi módosítási kísérlet érkezik
Then a módosítás elutasított; csak szabályozott újranyitás után lehetséges.

### AC-047-06: tenant-izoláció (REQ-047-06)

Given B-tenantbeli időszak-azonosító
When A-tenant kéri/módosítja
Then 404-szerű válasz, adatszivárgás nélkül.

### AC-047-07: idempotens close (REQ-047-07)

Given close-kérés `Idempotency-Key`-jel
When a kérés megismétlődik (azonos payload)
Then egy lezárási verzió létezik; eltérő payloadra 409.

### AC-047-08: szabályozott újranyitás és újrazárás (REQ-047-08)

Given lezárt időszak és korrekciós igény
When a jogosult indoklással és jóváhagyással újranyit, majd az előtte/utána összehasonlítás után újrazár
Then a változás története megmarad, az új verzió bizonyítékkal lezárt.

## 12. Tesztleképezés

| REQ | AC | E2E-teszt (fájl:sor) | GUI | Unit-cél (státusz) |
| :--- | :--- | :--- | :--- | :--- |
| REQ-047-01 | AC-047-01 | `test_e2e_047_ac_01_positive_path` (`.agent-pipeline/03_e2e_suites/test_e2e_047.py:24`) | `gui_e2e_046_047_quality_lock.spec.ts` | `tests/unit/test_period_close_service.py::test_req_047_01` — HIÁNYZIK |
| REQ-047-02 | AC-047-02 | `test_e2e_047_ac_02_contract_state` (`test_e2e_047.py:29`) | ugyanaz | `...::test_req_047_02` — HIÁNYZIK |
| REQ-047-03 | AC-047-03 | `test_e2e_047_ac_03_invalid_payload_is_safe` (`test_e2e_047.py:33`) | ugyanaz | `...::test_req_047_03` — HIÁNYZIK |
| REQ-047-04 | AC-047-04 | `test_e2e_047_ac_04_detail_contract` (`test_e2e_047.py:37`) | ugyanaz | `...::test_req_047_04` — HIÁNYZIK |
| REQ-047-05 | AC-047-05 | `test_e2e_047_ac_05_no_silent_success` (`test_e2e_047.py:41`) | ugyanaz | `...::test_req_047_05` — HIÁNYZIK |
| REQ-047-06 | AC-047-06 | `test_e2e_047_ac_06_tenant_and_auth_isolation` (`test_e2e_047.py:45`) | ugyanaz | `...::test_req_047_06` — HIÁNYZIK |
| REQ-047-07 | AC-047-07 | `test_e2e_047_ac_07_idempotent_retry` (`test_e2e_047.py:50`) | ugyanaz | `...::test_req_047_07` — HIÁNYZIK |
| REQ-047-08 | AC-047-08 | `test_e2e_047_ac_08_concurrent_revision` (`test_e2e_047.py:58`) | ugyanaz | `...::test_req_047_08` — HIÁNYZIK |

E2E-eredmény: 8/8 PASS (2026-08-31 jelentés). Unit-célok nem léteznek — SPEC-GAP-047-04.

## 13. Kockázatok és emberi döntések

- HR-047-01: hibás zárás (rejtett blokkolóval) pénzügyi/audit-kockázat — ezért a blokkoló melletti zárás tilalma és a külön megerősítés kötelező; a szerveroldali kikényszerítés termékdöntés (GAP).
- HR-047-02: jogosulatlan újranyitás a reprodukálhatóságot sérti — az indoklás + jóváhagyás + verziózott újrazárás kötelező.
- Adatvédelem: más tenant időszaka sem listában, sem bizonyítékban nem jelenhet meg.

## 14. Nyitott kérdések és SPEC-GAP

Nincs implementációt blokkoló nyitott kérdés (kód szállítva, E2E zöld).

SPEC-GAP (a BRIEF többet állít, mint a kód):

- SPEC-GAP-047-01: US-047-02 szerinti hat-típusú előellenőrző motor (hiány/párosítatlan/bizonytalan/duplikátum/visszatérítés/felosztás szkenner), US-047-05 szerinti összesítés/egyenleg-előnézet számítása és US-047-09 szerinti bizonyíték-generálás (evidence hash) **egyike sincs a szerverkódban**; a logika kliens/`data` eredetű.
- SPEC-GAP-047-02: REQ-047-02/REQ-047-05 szerinti szerveroldali zárás-blokkolás és módosításvédelem **nincs kikényszerítve** (a generikus PATCH bármely `data`-t elfogad); a védelem kliens-szabály.
- SPEC-GAP-047-03: a `PRECHECK_RUNNING`/`BLOCKED`/`READY_TO_CLOSE`/`CLOSED`/`REOPEN_PENDING` állapotok nem gépi átmenetek; a zárási jogosultsági mátrix szerveroldali érvényesítése nincs.
- SPEC-GAP-047-04: az előd pipeline-spec unit-céljai (`tests/unit/test_period_close_service.py`) **nem léteznek**; elsődleges bizonyíték az E2E-suite.

## 15. Rollback és megfigyelhetőség

- Rollback: migráció nincs; folyamat-memória — újraindítás az időszakokat törli (lezárási bizonyíték is elvész — kritikus kockázat, lásd GAP). Visszaállítás telepítéssel, adatmigráció nélkül.
- Megfigyelhetőség: `application/problem+json` `correlation_id`-val; válaszokban tenant- és revízió-azonosító. Zárási audit-napló és bizonyíték-archívum nincs.

## 16. Definition of Done

- [x] mind a 8 REQ-hez AC és E2E-teszt (8/8 PASS, 2026-08-31).
- [x] célzott E2E + GUI-suite zöld a jelentés szerint.
- [ ] unit-célok pótlása — nyitott (SPEC-GAP-047-04).
- [ ] SPEC-GAP-047-01/02 termékdöntése (előellenőrző-motor, szerveroldali zárás-őrzés, perzisztencia).
- [x] visszamutatás BRIEF-047 ↔ SPEC-047 ↔ kód ↔ tesztek (`docs/traceability-index.md`).
- [x] production kód nem változott (docs-only).
