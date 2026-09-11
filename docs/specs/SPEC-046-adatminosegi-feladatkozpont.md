---
id: FEAT-046
title: Adatminőségi feladatközpont
status: ready_for_dev
version: 1
risk: medium
owner: documenter
related_brief: BRIEF-046
---

# FEAT-046: Adatminőségi feladatközpont

> Visszamenőleges (kód→spec) specifikáció. A megvalósítás már szállítva;
> ez a dokumentum a tényleges kódviselkedést rögzíti a VERITAS 1.1 §4.5
> 16-fejezetes szerkezetében. Ahol a BRIEF többet állít, azt a 14. fejezet
> SPEC-GAP listája jelöli.

## 1. Cél és felhasználói eredmény

A felhasználó a nyugták, tranzakciók, párosítások, kategóriák és
kapcsolódó dokumentumok adatminőségi problémáit egyetlen közös javítási
listában látja, súlyosság/felelős/hatás/forrás szerint szűrve és
rendezve. Minden feladatnál érthető a magyarázat, a bizonyosság és a
hatás; a feladatból közvetlen javítófelület indul, a mentés után a
következő releváns feladattal folytatható. A téves jelzés indoklással
kivételként lezárható, a forrásadat változása automatikusan újraértékel,
és jogosultság hiányában csak az engedélyezett adat látszik.

Mérhető készültségi feltétel: mind a 8 REQ-hez tartozik AC-scenario és
végrehajtható E2E-teszt (`.agent-pipeline/03_e2e_suites/test_e2e_046.py`,
8/8 PASS a 2026-08-31 verifikáció szerint).

## 2. Kontextus és források

Kanonikus források:

- `briefs/BRIEF-046-adatminosegi-feladatkozpont.md` (10 US: US-046-01..US-046-10)
- `VERITAS_1_1_adaptiv_egyseges_fejlesztesi_modszertan.md` §4.5
- `05_docs/2026-08-31-phase2-feat038-048-verification-report.md`
- `.agent-pipeline/02_specs/done/SPEC-046-adatminosegi-feladatkozpont.md` (előd pipeline-spec)

Kódforrások (leltár):

- `app/quality_task_api.py` — router + 5 route (`:8` prefix `/api/v2/quality-tasks`; route-ok `:21`, `:24`, `:28`, `:32`, `:36-38`)
- `app/quality_task_models.py` — `Status` (`:8-15`), `CreateRequest` (`:17-21`), `CommandRequest` (`:23-28`), `QualityTask` (`:30-39`), hibák (`:44-51`)
- `app/quality_task_service.py` — `QualityTaskService` (`:7`), kezdő `OPEN` (`:21`), action-leképezés (`:32`)
- `app/api_v2.py` — bekötés (`:22` import, `:158` include_router)

Kapcsolódó domain-invariánsok: tenant-izoláció, érzékeny evidencia
védelme, tömeges művelet csak előnézettel és visszavonhatósággal,
stale javítás nem ír részállapotot, automatikus újraértékelés a lista
elavulása ellen.

## 3. Scope és non-scope

### Benne van

- Minőségi feladat létrehozása, listája, részlete, revíziózott állapotváltása és confirm-útja.
- Típus/súlyosság/határidő/összeg/felelős/forrás/blokkolt-folyamat szűrési dimenziók a szabad `data` payloadban; magyarázat/bizonyosság/hatás ugyanott.
- Felelőshöz rendelés, továbbadás, halasztás, indokolt kivétel-lezárás és tömeges művelet szemantikája a `Status` sémában.
- Tenant-izoláció, idempotencia, optimistic locking, `application/problem+json` hibák.

### Nincs benne

- Általános célú kanban/projektmenedzsment; bizonytalan adat automatikus véglegesítése kontroll nélkül; forrásrendszerek minden hibájának automatikus javítása (a BRIEF non-scope-ja is kizárja).
- Detektor-motor (probléma-felismerés) és automatikus újraértékelő a szerveren — lásd SPEC-GAP-046-01.
- Perzisztens tárolás: folyamat-memória (lásd 10. és 15. fejezet).

## 4. Szereplők és előfeltételek

- ACT-046-01: felhasználó (feladatot feldolgoz, javít, továbbad, halaszt, kivételt zár le, tömegesen műveletet végez).
- ACT-046-02: könyvelő (hátralék-alakulást, öregedő és zárást blokkoló tételeket néz).

- PRE-046-01: érvényes `Authorization` + `X-Tenant-ID` (különben 401 — `app/quality_task_api.py:10-13`).
- PRE-046-02: `X-Role` ∈ {admin, owner, member, accountant} (különben 403).
- PRE-046-03: módosításhoz `Idempotency-Key` (min. 16 karakter, különben 422 — `:15-17`).
- PRE-046-04: javításhoz ismert `expected_revision` (különben 409).

## 5. Funkcionális követelmények

- REQ-046-01 [MUST]: Minden támogatott adatminőségi hiba közös listában jelenik meg.
- REQ-046-02 [MUST]: A feladatok súlyosság, felelős, hatás és forrás szerint szűrhetők.
- REQ-046-03 [MUST]: A feladatból közvetlen javítófolyamat indítható.
- REQ-046-04 [MUST]: Biztonságos tömeges művelet előnézettel végezhető.
- REQ-046-05 [MUST]: Indokolt kivétel és automatikus újraértékelés támogatott.
- REQ-046-06 [MUST]: Más tenant feladata és érzékeny evidenciája nem hozzáférhető.
- REQ-046-07 [MUST]: Azonos detektor- vagy bulk kérés nem duplikál állapotot.
- REQ-046-08 [MUST]: Forrásrevízió változásakor a stale javítás nem ír részállapotot.

## 6. Nem funkcionális követelmények

- NFR-046-01 [PERFORMANCE]: közös lista és szűrés UI-visszajelzése 500 ms-on belül; nagy hátralék lapozható marad.
- NFR-046-02 [ACCESSIBILITY]: a lista, a szűrők és a javító-útvonal billentyűzettel végigvihető; feladat-állapotváltozás bejelentett.
- NFR-046-03 [SECURITY]: szerveroldali `context()` az autoritatív; jogosultság hiányában csak engedélyezett adat + továbbítási lehetőség látszik.
- NFR-046-04 [PRIVACY]: érzékeny evidencia más tenant vagy jogosulatlan szerep felé nem jelenhet meg; hibaválasz minimális.
- NFR-046-05 [RELIABILITY]: tömeges művelet visszavonható; stale javítás nem ír részállapotot; idegen tenant azonosítóra 404-szerű válasz.

## 7. UI-szerződés

- UI-046-01: `frontend/app/quality-inbox/page.tsx` — közös javítási lista szűrőkkel és rendezéssel (US-046-01, US-046-02), magyarázat/bizonyosság/hatás kártyánként (US-046-03).
- UI-046-02: ugyanott közvetlen javító-ugrás + "következő feladat" folytatás (US-046-04), felelős/halaszd/továbbad akciók (US-046-05), előnézetes tömeges művelet visszavonással (US-046-06), indokolt kivétel-lezárás (US-046-07), hátralék-trend és zárás-blokkoló nézet (US-046-09).
- UI-046-03: E2E GUI-lefedés: `frontend/e2e/gui_e2e_046_047_quality_lock.spec.ts`.

## 8. Felhasználói és GUI-folyamat

1. A felhasználó megnyitja a `/quality-inbox` oldalt; a rendszer az aktív tenant minőségi feladatait listázza (`GET /api/v2/quality-tasks`).
2. Típus/súlyosság/határidő/összeg/felelős/forrás/blokkolt-folyamat szerint szűr és rendez; a könyvelői nézet a hátralék-alakulást mutatja.
3. Minden feladatnál magyarázat, bizonyosság és hatás látszik; a feladatból a megfelelő javítófelület nyílik, mentés után a következő releváns feladattal folytatódik.
4. A feladat felelőshöz rendelhető, megjegyzéssel továbbadható vagy halasztható.
5. Több hasonló, biztonságosan javítható tétel tömegesen, előnézettel és visszavonhatósággal javítható.
6. A téves jelzés indoklással kivételként lezárható; a forrásadat változása automatikusan újraértékel (megnyit/lezár).
7. Jogosultság hiányában csak az engedélyezett adat és a továbbítási lehetőség látszik.
8. Hiba esetén a felület a bevitelet megőrzi, újrapróbálást kínál, részleges tömeges írás nem marad.

## 9. Állapotmodell

Tényleges gépi állapotok (`app/quality_task_models.py:8-15`):

- `OPEN` (kezdő — `app/quality_task_service.py:21`), `ASSIGNED`, `IN_PROGRESS`, `SNOOZED`, `EXEMPTED`, `RESOLVED`, `REOPENED`.

Megfigyelt átmenetek (`app/quality_task_service.py:32`):

- `confirm` → `RESOLVED`; `reject` → `REOPENED`; `resolve` → `RESOLVED`; `reopen` → `OPEN`.
- Feltétel: `expected_revision` egyezik, különben 409 írás nélkül.
- Megjegyzés: az `ASSIGNED`/`IN_PROGRESS`/`SNOOZED`/`EXEMPTED` finom-állapotok a sémában léteznek, de a generikus leképezés közvetlenül nem állítja be őket — a felelősség/halasztás/kivétel szemantikája a `data` payloadban él (lásd GAP).

## 10. API-, esemény- és adatszerződés

### REST (mind `app/quality_task_api.py`)

| Route | Kódhely | Szerződés |
| :--- | :--- | :--- |
| `GET /api/v2/quality-tasks` | `:21-22` | tenant-szűrt lista; 200 / 401 / 403 |
| `POST /api/v2/quality-tasks` | `:24-26` | `CreateRequest`; kötelező `Idempotency-Key`; 201 / 400 / 401 / 403 / 409 / 422 |
| `GET /api/v2/quality-tasks/{id}` | `:28-30` | részlet + `evidence`; idegen tenantnál 404-szerű `NOT_FOUND` |
| `PATCH /api/v2/quality-tasks/{id}` | `:32-34` | `CommandRequest` + `expected_revision`; 200 / 409 / 422 |
| `POST /api/v2/quality-tasks/{id}/confirm` | `:36-38` | `action="confirm"` kényszerítéssel delegál; 200 / 403 / 409 / 422 |

Hibák: `application/problem+json` (`:19`; modellek `:41-43`). Bekötés: `app/api_v2.py:22`, `:158`.

### Események

Nincs eseménybusz; detektor-futás és forrásváltozás-érzékelő szerveroldalon nincs bekötve (GAP).

### Adatmodell

- `QualityTask` (`app/quality_task_models.py:30-39`): `id`, `tenant_id`, `status`, `revision`, `client_reference`, `data: dict`, `evidence: dict`, `created_at`, `updated_at`.
- `CreateRequest` (`:17-21`), `CommandRequest` (`:23-28`) — generikus alak.
- Hibák: `NotFoundError` 404 (`:47-48`), `StaleRevisionError` 409 (`:49-50`), `IdempotencyConflictError` 409 (`:51-52`).
- Tárolás: `QualityTaskService._items` + `_keys`, `threading.RLock` (`app/quality_task_service.py:7-9`); létrehozáskor `evidence={"source": "FEAT-046"}` (`:21`); migráció nincs.

## 11. Acceptance scenario-k

### AC-046-01: közös lista (REQ-046-01)

Given több forrásból származó minőségi problémák
When a felhasználó a feladatközpontot megnyitja
Then minden támogatott hiba a közös listában megjelenik, nem kell több helyen keresni.

### AC-046-02: szűrés és rendezés (REQ-046-02)

Given vegyes hátralék
When a felhasználó súlyosság/felelős/hatás/forrás szerint szűr és rendez
Then a megfelelő sorrendű, releváns részhalmaz látszik.

### AC-046-03: közvetlen javítás (REQ-046-03)

Given kiválasztott feladat magyarázattal és hatással
When a felhasználó a javítófelületre ugrik, ment, majd folytatja
Then a javítás revíziózottan mentődik, a következő releváns feladat következik.

### AC-046-04: tömeges művelet (REQ-046-04)

Given több hasonló, biztonságosan javítható tétel
When a felhasználó közös műveletet indít
Then előnézet látszik, a művelet visszavonható; hiba esetén részleges írás nem marad.

### AC-046-05: kivétel és újraértékelés (REQ-046-05)

Given tévesen jelzett probléma / megváltozott forrásadat
When a felhasználó indoklással kivételt zár le, illetve a forrás változik
Then a kivétel nem tér vissza indokolatlanul; a lista automatikusan újraértékelődik. (Szerver-oldali újraértékelőre lásd GAP.)

### AC-046-06: tenant- és jogosultság-izoláció (REQ-046-06)

Given B-tenantbeli feladat / jogosulatlan szerep
When hozzáférési kísérlet történik
Then 404-szerű válasz vagy csak engedélyezett adat + továbbítási lehetőség látszik.

### AC-046-07: deduplikált detektor/bulk (REQ-046-07)

Given detektor- vagy bulk-kérés `Idempotency-Key`-jel
When a kérés megismétlődik (azonos payload)
Then új állapot nem duplikálódik; eltérő payloadra 409.

### AC-046-08: stale javítás védelme (REQ-046-08)

Given megváltozott forrásrevízió melletti javítási kísérlet
When a javítás elavult `expected_revision`-nel érkezik
Then 409 `STALE_REVISION`, részleges írás nélkül.

## 12. Tesztleképezés

| REQ | AC | E2E-teszt (fájl:sor) | GUI | Unit-cél (státusz) |
| :--- | :--- | :--- | :--- | :--- |
| REQ-046-01 | AC-046-01 | `test_e2e_046_ac_01_positive_path` (`.agent-pipeline/03_e2e_suites/test_e2e_046.py:24`) | `gui_e2e_046_047_quality_lock.spec.ts` | `tests/unit/test_data_quality_service.py::test_req_046_01` — HIÁNYZIK |
| REQ-046-02 | AC-046-02 | `test_e2e_046_ac_02_contract_state` (`test_e2e_046.py:29`) | ugyanaz | `...::test_req_046_02` — HIÁNYZIK |
| REQ-046-03 | AC-046-03 | `test_e2e_046_ac_03_invalid_payload_is_safe` (`test_e2e_046.py:33`) | ugyanaz | `...::test_req_046_03` — HIÁNYZIK |
| REQ-046-04 | AC-046-04 | `test_e2e_046_ac_04_detail_contract` (`test_e2e_046.py:37`) | ugyanaz | `...::test_req_046_04` — HIÁNYZIK |
| REQ-046-05 | AC-046-05 | `test_e2e_046_ac_05_no_silent_success` (`test_e2e_046.py:41`) | ugyanaz | `...::test_req_046_05` — HIÁNYZIK |
| REQ-046-06 | AC-046-06 | `test_e2e_046_ac_06_tenant_and_auth_isolation` (`test_e2e_046.py:45`) | ugyanaz | `...::test_req_046_06` — HIÁNYZIK |
| REQ-046-07 | AC-046-07 | `test_e2e_046_ac_07_idempotent_retry` (`test_e2e_046.py:50`) | ugyanaz | `...::test_req_046_07` — HIÁNYZIK |
| REQ-046-08 | AC-046-08 | `test_e2e_046_ac_08_concurrent_revision` (`test_e2e_046.py:58`) | ugyanaz | `...::test_req_046_08` — HIÁNYZIK |

E2E-eredmény: 8/8 PASS (2026-08-31 jelentés). Unit-célok nem léteznek — SPEC-GAP-046-04.

## 13. Kockázatok és emberi döntések

- HR-046-01: bizonytalan adat automatikus véglegesítése — tilos kontroll nélkül; a tömeges művelet csak előnézettel és visszavonhatósággal végezhető.
- HR-046-02: érzékeny evidencia szivárgása jogosulatlan szerep felé — a szűkített nézet + továbbítási lehetőség kötelező.
- Adatvédelem: más tenant feladata és érzékeny evidenciája sem listában, sem hibaválaszban nem jelenhet meg.

## 14. Nyitott kérdések és SPEC-GAP

Nincs implementációt blokkoló nyitott kérdés (kód szállítva, E2E zöld).

SPEC-GAP (a BRIEF többet állít, mint a kód):

- SPEC-GAP-046-01: US-046-01 szerinti probléma-felismerő (detektor) motor és US-046-08 szerinti automatikus újraértékelő **nincs a szerverkódban**; feladat csak API-hívással jön létre, az újraértékelés kliens-felelősség.
- SPEC-GAP-046-02: US-046-06 szerinti tömeges művelet szerveroldali atomi végrehajtása és visszavonása nincs; a `data`-szemantika nem garantálja.
- SPEC-GAP-046-03: az `ASSIGNED`/`IN_PROGRESS`/`SNOOZED`/`EXEMPTED` finom-állapotok nem gépi átmenetek (a generikus leképezés nem éri el őket); a US-046-09 szerinti hátralék-trend szerveroldali aggregációja nincs.
- SPEC-GAP-046-04: az előd pipeline-spec unit-céljai (`tests/unit/test_data_quality_service.py`) **nem léteznek**; elsődleges bizonyíték az E2E-suite.

## 15. Rollback és megfigyelhetőség

- Rollback: migráció nincs; folyamat-memória — újraindítás a feladatokat törli. Visszaállítás telepítéssel, adatmigráció nélkül.
- Megfigyelhetőség: `application/problem+json` `correlation_id`-val; válaszokban tenant- és revízió-azonosító. Hátralék-trend metrika és detektor-napló nincs.

## 16. Definition of Done

- [x] mind a 8 REQ-hez AC és E2E-teszt (8/8 PASS, 2026-08-31).
- [x] célzott E2E + GUI-suite zöld a jelentés szerint.
- [ ] unit-célok pótlása — nyitott (SPEC-GAP-046-04).
- [ ] SPEC-GAP-046-01/02 termékdöntése (detektor- és bulk-motor helye).
- [x] visszamutatás BRIEF-046 ↔ SPEC-046 ↔ kód ↔ tesztek (`docs/traceability-index.md`).
- [x] production kód nem változott (docs-only).
