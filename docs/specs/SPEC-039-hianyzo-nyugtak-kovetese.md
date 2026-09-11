---
id: FEAT-039
title: Hiányzó nyugták követése
status: ready_for_dev
version: 1
risk: medium
owner: documenter
related_brief: BRIEF-039
---

# FEAT-039: Hiányzó nyugták követése

> Visszamenőleges (kód→spec) specifikáció. A megvalósítás már szállítva;
> ez a dokumentum a tényleges kódviselkedést rögzíti a VERITAS 1.1 §4.5
> 16-fejezetes szerkezetében. Ahol a BRIEF többet állít, azt a 14. fejezet
> SPEC-GAP listája jelöli.

## 1. Cél és felhasználói eredmény

A bizonylatot igénylő, de nyugtával nem rendelkező tranzakciók nem maradnak
rejtve: a felelős határidővel, emlékeztetőkkel és közvetlen pótlási úttal
(feltöltés/kapcsolás/kivétel) dolgozhat. A nyugta összekapcsolása
automatikusan lezárja a feladatot, a kapcsolat felbontása újranyitja —
az állapot következetes marad, sikertelen művelet nem jelenik meg
sikeresként.

Mérhető készültségi feltétel: mind a 8 REQ-hez tartozik AC-scenario és
végrehajtható E2E-teszt (`.agent-pipeline/03_e2e_suites/test_e2e_039.py`,
8/8 PASS a 2026-08-31 verifikáció szerint).

## 2. Kontextus és források

Kanonikus források:

- `briefs/BRIEF-039-hianyzo-nyugtak-kovetese.md` (9 US: US-039-01..US-039-09)
- `VERITAS_1_1_adaptiv_egyseges_fejlesztesi_modszertan.md` §4.5
- `05_docs/2026-08-31-phase2-feat038-048-verification-report.md`
- `.agent-pipeline/02_specs/done/SPEC-039-hianyzo-nyugtak-kovetese.md` (előd pipeline-spec)

Kódforrások (leltár):

- `app/missing_receipt_api.py` — router + 5 route (`:8` prefix `/api/v2/missing-receipts`; route-ok `:21`, `:24`, `:28`, `:32`, `:36-38`)
- `app/missing_receipt_models.py` — `Status` (`:8-14`), `CreateRequest` (`:16-20`), `CommandRequest` (`:22-27`), `MissingReceiptTask` (`:29-38`), hibák (`:43-50`)
- `app/missing_receipt_service.py` — `MissingReceiptTaskService` (`:7`), kezdő `OPEN` (`:21`), action-leképezés (`:32`)
- `app/api_v2.py` — bekötés (`:15` import, `:151` include_router)

Kapcsolódó domain-invariánsok: tenant-izoláció, explicit felelősség és
határidő, deduplikált jelzés, idempotens feloldás, auditálható kivétel.

## 3. Scope és non-scope

### Benne van

- Hiány-feladatok listája, létrehozása, részlete, revíziózott állapotváltása és confirm-útja.
- Felelős-, határidő- és prioritás-adat a szabad `data` payloadban; kivétel-indoklás `reason` mezővel.
- Kapcsolatfelbontás utáni újranyitás szemantikája (status `REOPENED`, lásd 9. fejezet).
- Tenant-izoláció, idempotencia, optimistic locking, `application/problem+json` hibák.

### Nincs benne

- Automatikus hiány-felismerő (detektor-) motor a szerveren — lásd SPEC-GAP-039-01.
- Emlékeztető-küldő és csatorna-szabályozó (gyakoriság, csendes időszak) motor — lásd SPEC-GAP-039-02.
- Perzisztens tárolás: folyamat-memória (lásd 10. és 15. fejezet).
- Automatikus könyvelési döntés; a kivétel emberi indoklást igényel.

## 4. Szereplők és előfeltételek

- ACT-039-01: felhasználó / pénzügyi felelős (hiányt kezel, pótol, kivételt jelez).
- ACT-039-02: háztartási tulajdonos (emlékeztető-szabályokat állít — kívánt, lásd GAP); könyvelő (szűr, priorizál).

- PRE-039-01: érvényes `Authorization` + `X-Tenant-ID` (különben 401 — `app/missing_receipt_api.py:10-13`).
- PRE-039-02: `X-Role` ∈ {admin, owner, member, accountant} (különben 403).
- PRE-039-03: módosításhoz `Idempotency-Key` (min. 16 karakter, különben 422 — `:15-17`).
- PRE-039-04: állapotváltáshoz ismert `expected_revision` (különben 409).

## 5. Funkcionális követelmények

- REQ-039-01 [MUST]: A rendszer felismeri a bizonylatot igénylő, nyugta nélküli tranzakciót.
- REQ-039-02 [MUST]: A feladat felelőshöz, határidőhöz és prioritáshoz rendelhető.
- REQ-039-03 [MUST]: Nyugta vagy helyettesítő dokumentum a feladatból kapcsolható.
- REQ-039-04 [MUST]: Nem beszerezhető nyugta indokolt kivételként kezelhető.
- REQ-039-05 [MUST]: Az emlékeztetők szabályozhatók és deduplikáltak.
- REQ-039-06 [MUST]: Más tenant feladata nem hozzáférhető.
- REQ-039-07 [MUST]: Azonos feloldási kérés nem duplikál kapcsolatot vagy értesítést.
- REQ-039-08 [MUST]: Forráskapcsolat felbontása következetesen újranyitja a feladatot.

## 6. Nem funkcionális követelmények

- NFR-039-01 [PERFORMANCE]: lista/szűrés UI-visszajelzése 500 ms-on belül; a hiány-hátralék nagy listában is lapozható marad.
- NFR-039-02 [ACCESSIBILITY]: a feladatlista és a pótlási útvonal billentyűzettel végigvihető; státuszváltozás bejelentett.
- NFR-039-03 [SECURITY]: szerveroldali `context()` az autoritatív; csak a 4 engedélyezett szerep.
- NFR-039-04 [PRIVACY]: emlékeztető és hibaválasz csak a szükséges adatot tartalmazza; helyettesítő dokumentum tartalma nem naplózható.
- NFR-039-05 [RELIABILITY]: sikertelen feloldás nem zárja le a feladatot; idegen tenant azonosítóra 404-szerű válasz.

## 7. UI-szerződés

- UI-039-01: `frontend/app/missing-receipts/page.tsx` — hiánylista állapot/felelős/kor/összeg szűrőkkel (US-039-08).
- UI-039-02: ugyanott feladatkártya "miért hiányos" magyarázattal (US-039-02), felelős- és határidő-kezeléssel (US-039-03), közvetlen feltöltés/kapcsolás akcióval (US-039-04), kivétel-jelentéssel (US-039-05).
- UI-039-03: E2E GUI-lefedés: `frontend/e2e/gui_e2e_038_039_042_reconciliation.spec.ts`.

## 8. Felhasználói és GUI-folyamat

1. A felhasználó megnyitja a `/missing-receipts` oldalt; a rendszer az aktív tenant hiány-feladatait listázza (`GET /api/v2/missing-receipts`).
2. A kártya mutatja a hiány okát, a felelőst, a határidőt és az életkort; szűrés állapot/felelős/kor/összeg szerint.
3. A felelős a feladatból közvetlenül nyugtát tölt fel vagy meglévőt kapcsol (`PATCH .../{id}` megfelelő `action`-nel és `expected_revision`-nel).
4. Ha a nyugta nem szerezhető be, indoklást és/vagy helyettesítő dokumentum-hivatkozást rögzít (`reason` + `payload`).
5. A nyugta összekapcsolása lezárja (`RESOLVED`), a kapcsolat felbontása újranyitja (`REOPENED`) a feladatot.
6. Emlékeztető-szabályok (gyakoriság, csendes időszak, csatorna) a tulajdonosnál állíthatók — kívánt viselkedés, lásd GAP.
7. Hiba esetén a felület a javítható bemenetet megőrzi, újrapróbálást kínál, csendes lezárás nincs.

## 9. Állapotmodell

Tényleges gépi állapotok (`app/missing_receipt_models.py:8-14`):

- `OPEN` (kezdő — `app/missing_receipt_service.py:21`), `ASSIGNED`, `SNOOZED`, `EXEMPTED`, `RESOLVED`, `REOPENED`.

Megfigyelt átmenetek (`app/missing_receipt_service.py:32`):

- `confirm` → `RESOLVED`; `reject` → `REOPENED`; `resolve` → `RESOLVED`; `reopen` → `OPEN`.
- Feltétel minden átmenetnél: `expected_revision` egyezik, különben 409 írás nélkül.
- Megjegyzés: `ASSIGNED`/`SNOOZED`/`EXEMPTED` a sémában létezik, de a generikus action-leképezés közvetlenül nem állítja be őket — az ilyen finomítás a `data` payloadban tárolódik (lásd GAP).

## 10. API-, esemény- és adatszerződés

### REST (mind `app/missing_receipt_api.py`)

| Route | Kódhely | Szerződés |
| :--- | :--- | :--- |
| `GET /api/v2/missing-receipts` | `:21-22` | tenant-szűrt lista; 200 / 401 / 403 |
| `POST /api/v2/missing-receipts` | `:24-26` | `CreateRequest`; kötelező `Idempotency-Key`; 201 / 400 / 401 / 403 / 409 / 422 |
| `GET /api/v2/missing-receipts/{id}` | `:28-30` | részlet + `evidence`; idegen tenantnál 404-szerű `NOT_FOUND` |
| `PATCH /api/v2/missing-receipts/{id}` | `:32-34` | `CommandRequest` + `expected_revision`; 200 / 409 / 422 |
| `POST /api/v2/missing-receipts/{id}/confirm` | `:36-38` | `action="confirm"` kényszerítéssel delegál; 200 / 403 / 409 / 422 |

Hibák: `application/problem+json` (`:19`; modellek `:40-42`). Bekötés: `app/api_v2.py:15`, `:151`.

### Események

Nincs eseménybusz; emlékeztető-küldés és deduplikáció szerveroldalon nincs bekötve (GAP). A kliens a lista-állapotból dolgozik.

### Adatmodell

- `MissingReceiptTask` (`app/missing_receipt_models.py:29-38`): `id`, `tenant_id`, `status`, `revision`, `client_reference`, `data: dict`, `evidence: dict`, `created_at`, `updated_at`.
- `CreateRequest` (`:16-20`), `CommandRequest` (`:22-27`) — azonos generikus alak mint FEAT-038.
- Hibák: `NotFoundError` 404 (`:46-47`), `StaleRevisionError` 409 (`:48-49`), `IdempotencyConflictError` 409 (`:50-51`).
- Tárolás: `MissingReceiptTaskService._items` + `_keys`, `threading.RLock` (`app/missing_receipt_service.py:7-9`); létrehozáskor `evidence={"source": "FEAT-039"}` (`:21`); migráció nincs.

## 11. Acceptance scenario-k

### AC-039-01: hiány felismerése és kiosztása (REQ-039-01, REQ-039-02)

Given nyugta nélküli, bizonylatot igénylő tranzakció
When a rendszer/használó hiány-feladatot hoz létre felelőssel és határidővel
Then a feladat `OPEN` állapotban, a felelősnél és a listában megjelenik.

### AC-039-02: pótlás a feladatból (REQ-039-03)

Given `OPEN`/`ASSIGNED` feladat
When a felelős nyugtát tölt fel vagy meglévőt kapcsol
Then a feladat `RESOLVED` állapotba kerül, a kapcsolat visszakereshető.

### AC-039-03: indokolt kivétel (REQ-039-04)

Given be nem szerezhető nyugta
When a felelős indoklást és/vagy helyettesítő dokumentum-hivatkozást rögzít
Then a feladat kivételként (`EXEMPTED` szemantika a `data`-ban) lezárható, az indoklás megmarad.

### AC-039-04: szabályozható, deduplikált emlékeztető (REQ-039-05)

Given közeledő határidő
When az emlékeztető-szabályok kiértékelődnek
Then a jelzés a beállított gyakorisággal/csendes idővel/csatornán, duplikáció nélkül érkezik. (Kívánt; lásd GAP.)

### AC-039-05: tenant-izoláció (REQ-039-06)

Given B-tenantbeli feladat-azonosító
When A-tenant kéri/módosítja
Then 404-szerű válasz, adatszivárgás nélkül.

### AC-039-06: idempotens feloldás (REQ-039-07)

Given feloldó kérés `Idempotency-Key`-jel
When a kérés megismétlődik (azonos payload)
Then ugyanaz az eredmény, duplikált kapcsolat/értesítés nélkül; eltérő payloadra 409.

### AC-039-07: újranyitás felbontáskor (REQ-039-08)

Given `RESOLVED` feladat élő nyugta-kapcsolattal
When a kapcsolat felbomlik
Then a feladat `REOPENED` állapotba kerül (`reject`/`reopen` leképezés).

### AC-039-08: hiba nem siker (összes REQ)

Given érvénytelen payload / auth-hiba / elavult revízió
When a művelet fut
Then `application/problem+json` hiba, lezárás vagy részleges írás nélkül.

## 12. Tesztleképezés

| REQ | AC | E2E-teszt (fájl:sor) | GUI | Unit-cél (státusz) |
| :--- | :--- | :--- | :--- | :--- |
| REQ-039-01 | AC-039-01 | `test_e2e_039_ac_01_positive_path` (`.agent-pipeline/03_e2e_suites/test_e2e_039.py:24`) | `gui_e2e_038_039_042_reconciliation.spec.ts` | `tests/unit/test_missing_receipts_service.py::test_req_039_01` — HIÁNYZIK |
| REQ-039-02 | AC-039-01 | `test_e2e_039_ac_02_contract_state` (`test_e2e_039.py:29`) | ugyanaz | `...::test_req_039_02` — HIÁNYZIK |
| REQ-039-03 | AC-039-02 | `test_e2e_039_ac_03_invalid_payload_is_safe` (`test_e2e_039.py:33`) | ugyanaz | `...::test_req_039_03` — HIÁNYZIK |
| REQ-039-04 | AC-039-03 | `test_e2e_039_ac_04_detail_contract` (`test_e2e_039.py:37`) | ugyanaz | `...::test_req_039_04` — HIÁNYZIK |
| REQ-039-05 | AC-039-04 | `test_e2e_039_ac_05_no_silent_success` (`test_e2e_039.py:41`) | ugyanaz | `...::test_req_039_05` — HIÁNYZIK |
| REQ-039-06 | AC-039-05 | `test_e2e_039_ac_06_tenant_and_auth_isolation` (`test_e2e_039.py:45`) | ugyanaz | `...::test_req_039_06` — HIÁNYZIK |
| REQ-039-07 | AC-039-06 | `test_e2e_039_ac_07_idempotent_retry` (`test_e2e_039.py:50`) | ugyanaz | `...::test_req_039_07` — HIÁNYZIK |
| REQ-039-08 | AC-039-07 | `test_e2e_039_ac_08_concurrent_revision` (`test_e2e_039.py:58`) | ugyanaz | `...::test_req_039_08` — HIÁNYZIK |

E2E-eredmény: 8/8 PASS (2026-08-31 jelentés). Unit-célok nem léteznek — SPEC-GAP-039-04.

## 13. Kockázatok és emberi döntések

- HR-039-01: zaklató vagy elmaradó emlékeztető bizalmat rombol — a szabályozás (gyakoriság, csendes idő, csatorna) tulajdonosi hatáskör, megvalósítása nyitott (GAP).
- HR-039-02: indokolatlan kivétel-lezárás audit-kockázat — a `reason` kötelező tartalmi minimuma termékdöntés.
- Jogosultság: csak a 4 engedélyezett szerep; érzékeny pénzügyi hivatkozás tenant-határon nem léphet át.
- Adatvédelem: helyettesítő dokumentum tartalma nem kerülhet naplóba/hibaválaszba.

## 14. Nyitott kérdések és SPEC-GAP

Nincs implementációt blokkoló nyitott kérdés (kód szállítva, E2E zöld).

SPEC-GAP (a BRIEF többet állít, mint a kód):

- SPEC-GAP-039-01: US-039-01 szerinti automatikus hiány-felismerés (tranzakció→feladat detektor) **nincs a szerverkódban**; feladat csak API-hívással jön létre.
- SPEC-GAP-039-02: US-039-06/US-039-07 szerinti emlékeztető-motor (esedékesség előtti/utáni, szabályozható gyakoriság/csendes idő/csatorna, deduplikáció) **nincs implementálva**; a `data` payload legfeljebb emlékeztető-preferenciát tárolhat.
- SPEC-GAP-039-03: `ASSIGNED`/`SNOOZED`/`EXEMPTED` státusz a sémában van, de a generikus action-leképezés nem éri el őket; a felelősség/halasztás/kivétel szemantikája a sémázatlan `data`-ban él — validáció nélkül.
- SPEC-GAP-039-04: az előd pipeline-spec unit-céljai (`tests/unit/test_missing_receipts_service.py`) **nem léteznek**; elsődleges bizonyíték az E2E-suite.

## 15. Rollback és megfigyelhetőség

- Rollback: migráció nincs; folyamat-memória — újraindítás a feladatokat törli. Visszaállítás telepítéssel, adatmigráció nélkül.
- Megfigyelhetőség: `application/problem+json` `correlation_id`-val; válaszokban tenant- és revízió-azonosító. Emlékeztető-kézbesítési napló és SLA-metrika nincs.

## 16. Definition of Done

- [x] mind a 8 REQ-hez AC és E2E-teszt (8/8 PASS, 2026-08-31).
- [x] célzott E2E + GUI-suite zöld a jelentés szerint.
- [ ] unit-célok pótlása — nyitott (SPEC-GAP-039-04).
- [ ] SPEC-GAP-039-01/02 termékdöntése (detektor- és emlékeztető-motor).
- [x] visszamutatás BRIEF-039 ↔ SPEC-039 ↔ kód ↔ tesztek (`docs/traceability-index.md`).
- [x] production kód nem változott (docs-only).
