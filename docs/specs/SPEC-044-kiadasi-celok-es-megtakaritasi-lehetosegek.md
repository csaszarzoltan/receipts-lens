---
id: FEAT-044
title: Kiadási célok és megtakarítási lehetőségek
status: ready_for_dev
version: 1
risk: medium
owner: documenter
related_brief: BRIEF-044
---

# FEAT-044: Kiadási célok és megtakarítási lehetőségek

> Visszamenőleges (kód→spec) specifikáció. A megvalósítás már szállítva;
> ez a dokumentum a tényleges kódviselkedést rögzíti a VERITAS 1.1 §4.5
> 16-fejezetes szerkezetében. Ahol a BRIEF többet állít, azt a 14. fejezet
> SPEC-GAP listája jelöli.

## 1. Cél és felhasználói eredmény

A felhasználó kategóriánként időszakos kiadási célt és kívánt
megtakarítást tűz ki, a haladást a visszatérítésekkel és felosztásokkal
korrigált tényleges költéshez méri, az eltérés okait látja, saját adatain
alapuló, számszerűsített (hatás/időtáv/bizonytalanság/evidencia)
javaslatokat kap, és minden javaslatról maga dönt (elfogad/módosít/
elhalaszt/elutasít). Kevés vagy torz adat esetén a rendszer ezt jelzi,
és nem ad túl magabiztos tanácsot.

Mérhető készültségi feltétel: mind a 8 REQ-hez tartozik AC-scenario és
végrehajtható E2E-teszt (`.agent-pipeline/03_e2e_suites/test_e2e_044.py`,
8/8 PASS a 2026-08-31 verifikáció szerint).

## 2. Kontextus és források

Kanonikus források:

- `briefs/BRIEF-044-kiadasi-celok-es-megtakaritasi-lehetosegek.md` (10 US: US-044-01..US-044-10)
- `VERITAS_1_1_adaptiv_egyseges_fejlesztesi_modszertan.md` §4.5
- `05_docs/2026-08-31-phase2-feat038-048-verification-report.md`
- `.agent-pipeline/02_specs/done/SPEC-044-kiadasi-celok-es-megtakaritasi-lehetosegek.md` (előd pipeline-spec)

Kódforrások (leltár):

- `app/savings_api.py` — router + 5 route (`:8` prefix `/api/v2/savings-goals`; route-ok `:21`, `:24`, `:28`, `:32`, `:36-38`)
- `app/savings_models.py` — `Status` (`:8-15`), `CreateRequest` (`:17-21`), `CommandRequest` (`:23-28`), `SpendingGoal` (`:30-39`), hibák (`:44-51`)
- `app/savings_service.py` — `SpendingGoalService` (`:7`), kezdő `DRAFT` (`:21`), action-leképezés (`:32`)
- `app/api_v2.py` — bekötés (`:20` import, `:156` include_router)

Kapcsolódó domain-invariánsok: tenant-izoláció, javaslat ≠ ígéret
(hatás/bizonytalanság/evidencia kötelező), döntés a felhasználónál,
kevés adat esetén magabiztosság-korlát, idempotens generálás, revíziózott
célmódosítás.

## 3. Scope és non-scope

### Benne van

- Kiadási cél létrehozása, listája, részlete, revíziózott módosítása és confirm-útja.
- Cél-paraméterek (kategória, időszak, tervösszeg), korrigált haladás, ajánlások (hatás/időtáv/bizonytalanság/evidencia), kizárások és visszajelzés a szabad `data` payloadban.
- Ajánlás-döntés (elfogad/módosít/halaszt/elutasít) és cél-állapot nyilvántartása a `Status` sémában.
- Tenant-izoláció, idempotencia, optimistic locking, `application/problem+json` hibák.

### Nincs benne

- Befektetési/hitel/adó-tanácsadás; automatikus vásárláslemondás vagy pénzügyi döntés jóváhagyás nélkül; garantált megtakarítás ígérete (a BRIEF non-scope-ja is kizárja).
- Haladás-számító és ajánló-motor a szerveren — lásd SPEC-GAP-044-01.
- Perzisztens tárolás: folyamat-memória (lásd 10. és 15. fejezet).

## 4. Szereplők és előfeltételek

- ACT-044-01: felhasználó (célt tűz ki, javaslatról dönt, kizár, visszajelez).
- ACT-044-02: háztartási szereplő (megosztott/korlátozott cél-nézet a szerepkör szerint).

- PRE-044-01: érvényes `Authorization` + `X-Tenant-ID` (különben 401 — `app/savings_api.py:10-13`).
- PRE-044-02: `X-Role` ∈ {admin, owner, member, accountant} (különben 403).
- PRE-044-03: módosításhoz `Idempotency-Key` (min. 16 karakter, különben 422 — `:15-17`).
- PRE-044-04: célmódosításhoz ismert `expected_revision` (különben 409).

## 5. Funkcionális követelmények

- REQ-044-01 [MUST]: Kategória- és időszakalapú kiadási cél hozható létre.
- REQ-044-02 [MUST]: A haladás korrigált tényleges költésből számolódik.
- REQ-044-03 [MUST]: Ajánlás becsült hatással, bizonytalansággal és evidenciával jelenik meg.
- REQ-044-04 [MUST]: A felhasználó ajánlást elfogadhat, módosíthat, halaszthat vagy elutasíthat.
- REQ-044-05 [MUST]: Kevés adat nem eredményez túl magabiztos javaslatot.
- REQ-044-06 [MUST]: Más tenant céljai és evidenciái nem hozzáférhetők.
- REQ-044-07 [MUST]: Azonos generálási kérés nem duplikál ajánlást.
- REQ-044-08 [MUST]: Párhuzamos célmódosítás stale revision hibát ad.

## 6. Nem funkcionális követelmények

- NFR-044-01 [PERFORMANCE]: cél- és haladás-nézet UI-visszajelzése 500 ms-on belül.
- NFR-044-02 [ACCESSIBILITY]: a célkezelés és a javaslat-döntés billentyűzettel végigvihető; haladás-változás bejelentett.
- NFR-044-03 [SECURITY]: szerveroldali `context()` az autoritatív; érzékeny pénzügyi döntés csak szerepkör szerint megosztott.
- NFR-044-04 [PRIVACY]: más tenant céljai és evidenciái nem jelenhetnek meg; hibaválasz minimális.
- NFR-044-05 [RELIABILITY]: ajánlás soha nem jelenik meg biztos ígéretként; idegen tenant azonosítóra 404-szerű válasz.

## 7. UI-szerződés

- UI-044-01: `frontend/app/savings-goals/page.tsx` — cél-lista haladás-sávval (korrigált költésből), eltérés-okokkal (US-044-01..US-044-03).
- UI-044-02: ugyanott javaslat-kártyák hatás/időtáv/bizonytalanság/evidencia adatokkal (US-044-04, US-044-05), elfogad/módosít/halaszt/elutasít akciók (US-044-06), kizárás-kezelő (US-044-07), eredmény-értékelő és visszajelző (US-044-08), kevés-adat jelzés (US-044-09), szerepkör szerinti megosztás (US-044-10).
- UI-044-03: E2E GUI-lefedés: `frontend/e2e/gui_e2e_043_044_split_goals.spec.ts`.

## 8. Felhasználói és GUI-folyamat

1. A felhasználó a `/savings-goals` oldalon kategóriához időszakos kiadási célt és kívánt megtakarítást rögzít (`POST /api/v2/savings-goals`).
2. A haladás a visszatérítésekkel és felosztásokkal korrigált tényleges költésből látszik; az eltérés okai (költések, trendek) feltárhatók.
3. A rendszer számszerűsített javaslatokat mutat hatás/időtáv/bizonytalanság/adat-alappal; a felhasználó mindegyikről dönt.
4. Az alapvető/nem csökkenthető kiadások kizárhatók; a rendszer nem ismétel irreális javaslatot.
5. Elfogadott javaslat eredménye később értékelhető, visszajelzés adható.
6. Kevés/bizonytalan/torz adatnál "nem megbízható" jelzés látszik, túl magabiztos tanács nélkül.
7. Célok és ajánlások háztartási szerepkör szerint megosztottak/korlátozottak.
8. Hiba esetén a felület a bevitelet megőrzi, újrapróbálást kínál, hamis haladás nem jelenik meg.

## 9. Állapotmodell

Tényleges gépi állapotok (`app/savings_models.py:8-15`):

- `DRAFT` (kezdő — `app/savings_service.py:21`), `ACTIVE`, `ON_TRACK`, `AT_RISK`, `ACHIEVED`, `PAUSED`, `ARCHIVED`.

Megfigyelt átmenetek (`app/savings_service.py:32`):

- `confirm` → `PAUSED`; `reject` → `ARCHIVED`; `resolve` → `PAUSED`; `reopen` → `DRAFT`.
- Feltétel: `expected_revision` egyezik, különben 409 írás nélkül.
- Megjegyzés: az `ON_TRACK`/`AT_RISK`/`ACHIEVED` haladás-szemantika és az ajánlás-döntések a `data` payloadban élnek; a generikus leképezés nem számol haladást (lásd GAP).

## 10. API-, esemény- és adatszerződés

### REST (mind `app/savings_api.py`)

| Route | Kódhely | Szerződés |
| :--- | :--- | :--- |
| `GET /api/v2/savings-goals` | `:21-22` | tenant-szűrt lista; 200 / 401 / 403 |
| `POST /api/v2/savings-goals` | `:24-26` | `CreateRequest`; kötelező `Idempotency-Key`; 201 / 400 / 401 / 403 / 409 / 422 |
| `GET /api/v2/savings-goals/{id}` | `:28-30` | részlet + `evidence`; idegen tenantnál 404-szerű `NOT_FOUND` |
| `PATCH /api/v2/savings-goals/{id}` | `:32-34` | `CommandRequest` + `expected_revision`; 200 / 409 / 422 |
| `POST /api/v2/savings-goals/{id}/confirm` | `:36-38` | `action="confirm"` kényszerítéssel delegál; 200 / 403 / 409 / 422 |

Hibák: `application/problem+json` (`:19`; modellek `:41-43`). Bekötés: `app/api_v2.py:20`, `:156`.

### Események

Nincs eseménybusz; ajánló-futás és haladás-számítás szerveroldalon nincs bekötve (GAP).

### Adatmodell

- `SpendingGoal` (`app/savings_models.py:30-39`): `id`, `tenant_id`, `status`, `revision`, `client_reference`, `data: dict`, `evidence: dict`, `created_at`, `updated_at`.
- `CreateRequest` (`:17-21`), `CommandRequest` (`:23-28`) — generikus alak.
- Hibák: `NotFoundError` 404 (`:47-48`), `StaleRevisionError` 409 (`:49-50`), `IdempotencyConflictError` 409 (`:51-52`).
- Tárolás: `SpendingGoalService._items` + `_keys`, `threading.RLock` (`app/savings_service.py:7-9`); létrehozáskor `evidence={"source": "FEAT-044"}` (`:21`); migráció nincs.

## 11. Acceptance scenario-k

### AC-044-01: cél létrehozása (REQ-044-01)

Given kategória és időszak
When a felhasználó kiadási célt és kívánt megtakarítást rögzít
Then a cél `DRAFT` állapotban létrejön, a terv mérhető.

### AC-044-02: korrigált haladás (REQ-044-02)

Given visszatérítések és felosztások a célidőszakban
When a haladás kiértékelődik
Then a mutató a korrigált tényleges költésből számolódik, az eltérés okai látszanak. (Szerver-számításra lásd GAP.)

### AC-044-03: evidenciás ajánlás és döntés (REQ-044-03, REQ-044-04)

Given elegendő adat
When a rendszer javaslatot mutat
Then hatás/időtáv/bizonytalanság/evidencia látszik; a felhasználó elfogad/módosít/halaszt/elutasít; ígéret-állítás nincs.

### AC-044-04: kevés-adat korlát (REQ-044-05)

Given kevés/bizonytalan/torz adat
When a javaslat kérődik
Then "nem megbízható" jelzés látszik, túl magabiztos tanács nélkül.

### AC-044-05: tenant-izoláció (REQ-044-06)

Given B-tenantbeli cél-azonosító
When A-tenant kéri/módosítja
Then 404-szerű válasz, evidencia-szivárgás nélkül.

### AC-044-06: idempotens generálás (REQ-044-07)

Given generálási kérés `Idempotency-Key`-jel
When a kérés megismétlődik (azonos payload)
Then új ajánlás nem duplikálódik; eltérő payloadra 409.

### AC-044-07: párhuzamos célmódosítás (REQ-044-08)

Given azonos revíziójú cél
When két módosítás érkezik ugyanazzal az `expected_revision`-nel
Then pontosan egy nyer, a másik 409 `STALE_REVISION`-t kap.

### AC-044-08: hiba nem siker (összes REQ)

Given érvénytelen payload / auth-hiba / elavult revízió
When a művelet fut
Then `application/problem+json` hiba, hamis haladás nélkül.

## 12. Tesztleképezés

| REQ | AC | E2E-teszt (fájl:sor) | GUI | Unit-cél (státusz) |
| :--- | :--- | :--- | :--- | :--- |
| REQ-044-01 | AC-044-01 | `test_e2e_044_ac_01_positive_path` (`.agent-pipeline/03_e2e_suites/test_e2e_044.py:24`) | `gui_e2e_043_044_split_goals.spec.ts` | `tests/unit/test_savings_goals_service.py::test_req_044_01` — HIÁNYZIK |
| REQ-044-02 | AC-044-02 | `test_e2e_044_ac_02_contract_state` (`test_e2e_044.py:29`) | ugyanaz | `...::test_req_044_02` — HIÁNYZIK |
| REQ-044-03 | AC-044-03 | `test_e2e_044_ac_03_invalid_payload_is_safe` (`test_e2e_044.py:33`) | ugyanaz | `...::test_req_044_03` — HIÁNYZIK |
| REQ-044-04 | AC-044-03 | `test_e2e_044_ac_04_detail_contract` (`test_e2e_044.py:37`) | ugyanaz | `...::test_req_044_04` — HIÁNYZIK |
| REQ-044-05 | AC-044-04 | `test_e2e_044_ac_05_no_silent_success` (`test_e2e_044.py:41`) | ugyanaz | `...::test_req_044_05` — HIÁNYZIK |
| REQ-044-06 | AC-044-05 | `test_e2e_044_ac_06_tenant_and_auth_isolation` (`test_e2e_044.py:45`) | ugyanaz | `...::test_req_044_06` — HIÁNYZIK |
| REQ-044-07 | AC-044-06 | `test_e2e_044_ac_07_idempotent_retry` (`test_e2e_044.py:50`) | ugyanaz | `...::test_req_044_07` — HIÁNYZIK |
| REQ-044-08 | AC-044-07 | `test_e2e_044_ac_08_concurrent_revision` (`test_e2e_044.py:58`) | ugyanaz | `...::test_req_044_08` — HIÁNYZIK |

E2E-eredmény: 8/8 PASS (2026-08-31 jelentés). Unit-célok nem léteznek — SPEC-GAP-044-04.

## 13. Kockázatok és emberi döntések

- HR-044-01: szabályozott pénzügyi tanácsadás határának átlépése — ezért a scope kizárja a befektetési/hitel/adó-tanácsadást és a garantált ígéretet; minden javaslat hatás/bizonytalanság/evidencia jelölést hordoz.
- HR-044-02: túl magabiztos tanács kevés adatból — a "nem megbízható" jelzés kötelező; a küszöb termékdöntés (GAP).
- Adatvédelem: célok és ajánlások csak szerepkör szerint megosztottak; más tenant evidenciája nem jelenhet meg.

## 14. Nyitott kérdések és SPEC-GAP

Nincs implementációt blokkoló nyitott kérdés (kód szállítva, E2E zöld).

SPEC-GAP (a BRIEF többet állít, mint a kód):

- SPEC-GAP-044-01: US-044-02 szerinti korrigált haladás-számítás, US-044-03 szerinti eltérés-ok feltárás, US-044-04 szerinti ajánló (hatás/időtáv/bizonytalanság) és US-044-09 szerinti kevés-adat korlát **egyike sincs a szerverkódban**; a logika kliens/`data` eredetű, validáció nélkül.
- SPEC-GAP-044-02: US-044-07 szerinti kizárás-érvényesítés, US-044-08 szerinti eredmény-értékelés és US-044-10 szerinti szerepkör-megosztás szerveroldali kikényszerítése nincs; `data`-szemantika.
- SPEC-GAP-044-03: az `ON_TRACK`/`AT_RISK`/`ACHIEVED` haladás-állapotok nem gépi átmenetek (a generikus leképezés nem éri el őket).
- SPEC-GAP-044-04: az előd pipeline-spec unit-céljai (`tests/unit/test_savings_goals_service.py`) **nem léteznek**; elsődleges bizonyíték az E2E-suite.

## 15. Rollback és megfigyelhetőség

- Rollback: migráció nincs; folyamat-memória — újraindítás a célokat törli. Visszaállítás telepítéssel, adatmigráció nélkül.
- Megfigyelhetőség: `application/problem+json` `correlation_id`-val; válaszokban tenant- és revízió-azonosító. Haladás- és ajánlás-metrika nincs.

## 16. Definition of Done

- [x] mind a 8 REQ-hez AC és E2E-teszt (8/8 PASS, 2026-08-31).
- [x] célzott E2E + GUI-suite zöld a jelentés szerint.
- [ ] unit-célok pótlása — nyitott (SPEC-GAP-044-04).
- [ ] SPEC-GAP-044-01/02 termékdöntése (haladás- és ajánló-motor helye).
- [x] visszamutatás BRIEF-044 ↔ SPEC-044 ↔ kód ↔ tesztek (`docs/traceability-index.md`).
- [x] production kód nem változott (docs-only).
