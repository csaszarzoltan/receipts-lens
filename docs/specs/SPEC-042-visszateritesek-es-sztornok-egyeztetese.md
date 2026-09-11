---
id: FEAT-042
title: Visszatérítések és sztornók egyeztetése
status: ready_for_dev
version: 1
risk: high
owner: documenter
related_brief: BRIEF-042
---

# FEAT-042: Visszatérítések és sztornók egyeztetése

> Visszamenőleges (kód→spec) specifikáció. A megvalósítás már szállítva;
> ez a dokumentum a tényleges kódviselkedést rögzíti a VERITAS 1.1 §4.5
> 16-fejezetes szerkezetében. Ahol a BRIEF többet állít, azt a 14. fejezet
> SPEC-GAP listája jelöli.

## 1. Cél és felhasználói eredmény

A felhasználó a jóváírásokat és sztornókat az eredeti vásárláshoz köti:
a rendszer lehetséges visszatérítést ismer fel, rangsorolt eredeti
jelölteket mutat indokkal és bizonyossággal, a teljes/részleges és
többlépcsős visszatérítés nettó hatása helyesen számolódik, és csak a
tényleges pénzmozgás csökkenti a költést. A hibás kapcsolat felbontható
vagy újra hozzárendelhető, a javítás auditálható.

Mérhető készültségi feltétel: mind a 8 REQ-hez tartozik AC-scenario és
végrehajtható E2E-teszt (`.agent-pipeline/03_e2e_suites/test_e2e_042.py`,
8/8 PASS a 2026-08-31 verifikáció szerint).

## 2. Kontextus és források

Kanonikus források:

- `briefs/BRIEF-042-visszateritesek-es-sztornok-egyeztetese.md` (9 US: US-042-01..US-042-09)
- `VERITAS_1_1_adaptiv_egyseges_fejlesztesi_modszertan.md` §4.5
- `05_docs/2026-08-31-phase2-feat038-048-verification-report.md`
- `.agent-pipeline/02_specs/done/SPEC-042-visszateritesek-es-sztornok-egyeztetese.md` (előd pipeline-spec)

Kódforrások (leltár):

- `app/refund_api.py` — router + 5 route (`:8` prefix `/api/v2/refunds`; route-ok `:21`, `:24`, `:28`, `:32`, `:36-38`)
- `app/refund_models.py` — `Status` (`:8-14`), `CreateRequest` (`:16-20`), `CommandRequest` (`:22-27`), `RefundMatch` (`:29-38`), hibák (`:43-50`)
- `app/refund_service.py` — `RefundMatchService` (`:7`), kezdő `DETECTED` (`:21`), action-leképezés (`:32`)
- `app/api_v2.py` — bekötés (`:18` import, `:154` include_router)
- `frontend/components/reconciliation/RefundWorkbench.tsx`, `frontend/app/reconciliation/refunds/page.tsx`

Kapcsolódó domain-invariánsok: tenant-izoláció, javaslat nem válik
észrevétlenül döntéssé, nettó-hatás konzisztencia, túlvisszatérítés
tilalma, idempotens allokáció, auditálható javítás.

## 3. Scope és non-scope

### Benne van

- Jóváírás/sztornó felismerési jelölt nyilvántartása, kapcsolása eredeti vásárláshoz/nyugtához/tételhez/terheléshez, állapotkövetése.
- Teljes, részleges és többlépcsős visszatérítés, eltérő fizetési eszköz/pénznem kezelése adatszinten.
- Függő/teljesült/meghiúsult/visszavont megkülönböztetés a `Status` sémában; kapcsolatjavítás indoklással.
- Tenant-izoláció, idempotencia, optimistic locking, `application/problem+json` hibák.

### Nincs benne

- Visszatérítés kezdeményezése kereskedőnél/banknál; chargeback-folyamat automatizálása; jövőbeni jóváírás előre könyvelése (a BRIEF non-scope-ja is kizárja).
- Jóváírás-felismerő és nettó-számító motor a szerveren — lásd SPEC-GAP-042-01.
- Perzisztens tárolás: folyamat-memória (lásd 10. és 15. fejezet).

## 4. Szereplők és előfeltételek

- ACT-042-01: felhasználó (jóváírást kapcsol, részleteket követ, hibás kapcsolatot javít).
- ACT-042-02: könyvelő (bruttó/kapcsolt/nettó összesítést ellenőriz exporthoz és záráshoz).

- PRE-042-01: érvényes `Authorization` + `X-Tenant-ID` (különben 401 — `app/refund_api.py:10-13`).
- PRE-042-02: `X-Role` ∈ {admin, owner, member, accountant} (különben 403).
- PRE-042-03: módosításhoz `Idempotency-Key` (min. 16 karakter, különben 422 — `:15-17`).
- PRE-042-04: allokáció-javításhoz ismert `expected_revision` (különben 409).

## 5. Funkcionális követelmények

- REQ-042-01 [MUST]: A rendszer lehetséges jóváírást vagy sztornót felismer.
- REQ-042-02 [MUST]: Az eredeti vásárlás jelöltjei magyarázhatóan rangsoroltak.
- REQ-042-03 [MUST]: Teljes és részleges visszatérítés kapcsolható nyugtához és tételhez.
- REQ-042-04 [MUST]: A teljesült visszatérítés nettó hatása helyesen számolódik.
- REQ-042-05 [MUST]: Reversed jóváírás visszavezeti a pénzügyi hatást.
- REQ-042-06 [MUST]: Más tenant tranzakciója nem kapcsolható.
- REQ-042-07 [MUST]: Azonos allokációs kérés nem duplikál összeget.
- REQ-042-08 [MUST]: Párhuzamos allokáció nem enged túlvisszatérítést.

## 6. Nem funkcionális követelmények

- NFR-042-01 [PERFORMANCE]: jelöltlista és nettó-nézet UI-visszajelzése 500 ms-on belül.
- NFR-042-02 [ACCESSIBILITY]: a kapcsolási folyamat billentyűzettel végigvihető; nettó-hatás változása bejelentett.
- NFR-042-03 [SECURITY]: szerveroldali `context()` az autoritatív; csak a 4 engedélyezett szerep.
- NFR-042-04 [PRIVACY]: más tenant tranzakció-azonosítója hibaválaszban sem szivároghat; minimális hibaválasz.
- NFR-042-05 [RELIABILITY]: meghiúsult/visszavont jóváírás nem csökkentheti a költést; idegen tenant azonosítóra 404-szerű válasz.

## 7. UI-szerződés

- UI-042-01: `frontend/app/reconciliation/refunds/page.tsx` + `frontend/components/reconciliation/RefundWorkbench.tsx` — jóváírás-jelöltek rangsorolva, indokkal és bizonyossággal (US-042-01..US-042-03).
- UI-042-02: ugyanott teljes/részleges kapcsolás nyugtához/tételhez/terheléshez (US-042-04), részlet-követés fennmaradó összeggel (US-042-05), eltérő eszköz/pénznem jelölése (US-042-06), állapot-megkülönböztetés (US-042-07), felbontás/újra-hozzárendelés (US-042-08), bruttó/kapcsolt/nettó nézet (US-042-09).
- UI-042-03: E2E GUI-lefedés: `frontend/e2e/gui_e2e_038_039_042_reconciliation.spec.ts`.

## 8. Felhasználói és GUI-folyamat

1. A felhasználó megnyitja a visszatérítési munkafelületet; a rendszer az aktív tenant jóváírás-jelöltjeit listázza (`GET /api/v2/refunds`).
2. Egy jóváíráshoz az összeg/pénznem/kereskedő/dátum/korábbi kapcsolat alapján rangsorolt eredeti jelöltek jelennek meg indokkal és bizonyossággal.
3. A felhasználó teljes vagy részleges visszatérítést kapcsol az eredeti nyugtához, tételeihez és terheléséhez (`POST` + `PATCH .../{id}` revízióval).
4. Több részlet külön követhető; a fennmaradó összeg látható; eltérő eszköz/pénznem jelölve, nem hibaként.
5. Csak a teljesült jóváírás csökkenti a nettó költést; a meghiúsult/visszavont nem; a reversed visszavezeti a hatást.
6. Hibás kapcsolat felbontható vagy újra hozzárendelhető indoklással; a könyvelői bruttó/kapcsolt/nettó nézet ellenőrizhető marad.
7. Hiba esetén a felület a bevitelet megőrzi, újrapróbálást kínál, túlvisszatérítés nem keletkezhet.

## 9. Állapotmodell

Tényleges gépi állapotok (`app/refund_models.py:8-14`):

- `DETECTED` (kezdő — `app/refund_service.py:21`), `SUGGESTED`, `PARTIALLY_MATCHED`, `MATCHED`, `REVERSED`, `DISPUTED`.

Megfigyelt átmenetek (`app/refund_service.py:32`):

- `confirm` → `REVERSED`; `reject` → `DISPUTED`; `resolve` → `REVERSED`; `reopen` → `DETECTED`.
- Feltétel: `expected_revision` egyezik, különben 409 írás nélkül.
- Megjegyzés: a függő/teljesült/meghiúsult/visszavont pénzügyi szemantika a `data` payloadban él; nettó-számítás a szerveren nincs (lásd GAP).

## 10. API-, esemény- és adatszerződés

### REST (mind `app/refund_api.py`)

| Route | Kódhely | Szerződés |
| :--- | :--- | :--- |
| `GET /api/v2/refunds` | `:21-22` | tenant-szűrt lista; 200 / 401 / 403 |
| `POST /api/v2/refunds` | `:24-26` | `CreateRequest`; kötelező `Idempotency-Key`; 201 / 400 / 401 / 403 / 409 / 422 |
| `GET /api/v2/refunds/{id}` | `:28-30` | részlet + `evidence`; idegen tenantnál 404-szerű `NOT_FOUND` |
| `PATCH /api/v2/refunds/{id}` | `:32-34` | `CommandRequest` + `expected_revision`; 200 / 409 / 422 |
| `POST /api/v2/refunds/{id}/confirm` | `:36-38` | `action="confirm"` kényszerítéssel delegál; 200 / 403 / 409 / 422 |

Hibák: `application/problem+json` (`:19`; modellek `:40-42`). Bekötés: `app/api_v2.py:18`, `:154`.

### Események

Nincs eseménybusz; jóváírás-felismerő futás szerveroldalon nincs bekötve (GAP).

### Adatmodell

- `RefundMatch` (`app/refund_models.py:29-38`): `id`, `tenant_id`, `status`, `revision`, `client_reference`, `data: dict`, `evidence: dict`, `created_at`, `updated_at`.
- `CreateRequest` (`:16-20`), `CommandRequest` (`:22-27`) — generikus alak.
- Hibák: `NotFoundError` 404 (`:46-47`), `StaleRevisionError` 409 (`:48-49`), `IdempotencyConflictError` 409 (`:50-51`).
- Tárolás: `RefundMatchService._items` + `_keys`, `threading.RLock` (`app/refund_service.py:7-9`); létrehozáskor `evidence={"source": "FEAT-042"}` (`:21`); migráció nincs.

## 11. Acceptance scenario-k

### AC-042-01: felismerés és rangsorolt jelöltek (REQ-042-01, REQ-042-02)

Given beérkező jóváírás
When a rendszer/felhasználó jelöltet képez
Then az eredeti vásárlások indokkal és bizonyossággal rangsorolva látszanak.

### AC-042-02: teljes/részleges kapcsolás (REQ-042-03)

Given jóváírás-jelölt és eredeti nyugta
When a felhasználó teljes vagy részleges visszatérítést kapcsol a nyugtához/tételekhez/terheléshez
Then a kapcsolat revíziózottan létrejön, a nettó hatás követhető.

### AC-042-03: nettó-hatás és reversed (REQ-042-04, REQ-042-05)

Given kapcsolt visszatérítések
When a jóváírás teljesül, majd reversed lesz
Then a teljesülés csökkenti a nettó költést; a reversed visszavezeti a hatást; meghiúsult/visszavont nem csökkent.

### AC-042-04: tenant-izoláció (REQ-042-06)

Given B-tenantbeli tranzakció-azonosító
When A-tenant kapcsolni próbálja
Then 404-szerű válasz, kereszt-tenant kapcsolat nélkül.

### AC-042-05: idempotens allokáció (REQ-042-07)

Given allokációs kérés `Idempotency-Key`-jel
When a kérés megismétlődik (azonos payload)
Then az összeg nem duplikálódik; eltérő payloadra 409.

### AC-042-06: túlvisszatérítés-védelem (REQ-042-08)

Given részben visszatérített eredeti
When két párhuzamos allokáció érkezik ugyanazzal a revízióval
Then pontosan egy nyer (másik 409), a visszatérített összeg nem haladja meg az eredetit. (Szerveroldali összeg-validációra lásd GAP.)

### AC-042-07: kapcsolatjavítás (REQ-042-03 kiterjesztése)

Given hibásan kapcsolt visszatérítés
When a felhasználó felbontja vagy újra hozzárendeli indoklással
Then a javítás auditálható (`reason` + revízió).

### AC-042-08: hiba nem siker (összes REQ)

Given érvénytelen payload / auth-hiba / elavult revízió
When a művelet fut
Then `application/problem+json` hiba, részleges allokáció nélkül.

## 12. Tesztleképezés

| REQ | AC | E2E-teszt (fájl:sor) | GUI | Unit-cél (státusz) |
| :--- | :--- | :--- | :--- | :--- |
| REQ-042-01 | AC-042-01 | `test_e2e_042_ac_01_positive_path` (`.agent-pipeline/03_e2e_suites/test_e2e_042.py:24`) | `gui_e2e_038_039_042_reconciliation.spec.ts` | `tests/unit/test_refunds_service.py::test_req_042_01` — HIÁNYZIK |
| REQ-042-02 | AC-042-01 | `test_e2e_042_ac_02_contract_state` (`test_e2e_042.py:29`) | ugyanaz | `...::test_req_042_02` — HIÁNYZIK |
| REQ-042-03 | AC-042-02/07 | `test_e2e_042_ac_03_invalid_payload_is_safe` (`test_e2e_042.py:33`) | ugyanaz | `...::test_req_042_03` — HIÁNYZIK |
| REQ-042-04 | AC-042-03 | `test_e2e_042_ac_04_detail_contract` (`test_e2e_042.py:37`) | ugyanaz | `...::test_req_042_04` — HIÁNYZIK |
| REQ-042-05 | AC-042-03 | `test_e2e_042_ac_05_no_silent_success` (`test_e2e_042.py:41`) | ugyanaz | `...::test_req_042_05` — HIÁNYZIK |
| REQ-042-06 | AC-042-04 | `test_e2e_042_ac_06_tenant_and_auth_isolation` (`test_e2e_042.py:45`) | ugyanaz | `...::test_req_042_06` — HIÁNYZIK |
| REQ-042-07 | AC-042-05 | `test_e2e_042_ac_07_idempotent_retry` (`test_e2e_042.py:50`) | ugyanaz | `...::test_req_042_07` — HIÁNYZIK |
| REQ-042-08 | AC-042-06 | `test_e2e_042_ac_08_concurrent_revision` (`test_e2e_042.py:58`) | ugyanaz | `...::test_req_042_08` — HIÁNYZIK |

E2E-eredmény: 8/8 PASS (2026-08-31 jelentés). Unit-célok nem léteznek — SPEC-GAP-042-04.

## 13. Kockázatok és emberi döntések

- HR-042-01: rossz eredetihez kapcsolt jóváírás hibás nettó-költést mutat — ezért a javaslat indoka és bizonyossága kötelezően látható, a kapcsolás explicit.
- HR-042-02: túlvisszatérítés (visszatérített > eredeti) pénzügyi integritási kockázat — szerveroldali összeg-őrzés bevezetése termékdöntés (GAP).
- Adatvédelem: más tenant tranzakció-adata sem listában, sem hibaválaszban nem jelenhet meg.

## 14. Nyitott kérdések és SPEC-GAP

Nincs implementációt blokkoló nyitott kérdés (kód szállítva, E2E zöld).

SPEC-GAP (a BRIEF többet állít, mint a kód):

- SPEC-GAP-042-01: US-042-01 szerinti jóváírás-felismerő, US-042-02 szerinti rangsoroló, US-042-04 szerinti nettó-számító és US-042-05 szerinti többlépcsős fennmaradó-összeg logika **egyike sincs a szerverkódban**; a számítás kliens/`data` eredetű, validáció nélkül.
- SPEC-GAP-042-02: US-042-06 szerinti eltérő eszköz/pénznem konverziós kezelése a szerveren nincs; az eltérés jelölése `data`-szemantika.
- SPEC-GAP-042-03: US-042-07 függő/teljesült/meghiúsult/visszavont megkülönböztetése és US-042-09 bruttó/kapcsolt/nettó könyvelői nézete nem gépi átmenet/számítás, csak `data`-szemantika.
- SPEC-GAP-042-04: az előd pipeline-spec unit-céljai (`tests/unit/test_refunds_service.py`) **nem léteznek**; elsődleges bizonyíték az E2E-suite.

## 15. Rollback és megfigyelhetőség

- Rollback: migráció nincs; folyamat-memória — újraindítás a kapcsolatokat törli. Visszaállítás telepítéssel, adatmigráció nélkül.
- Megfigyelhetőség: `application/problem+json` `correlation_id`-val; válaszokban tenant- és revízió-azonosító. Nettó-eltérés riasztás és allokációs napló nincs.

## 16. Definition of Done

- [x] mind a 8 REQ-hez AC és E2E-teszt (8/8 PASS, 2026-08-31).
- [x] célzott E2E + GUI-suite zöld a jelentés szerint.
- [ ] unit-célok pótlása — nyitott (SPEC-GAP-042-04).
- [ ] SPEC-GAP-042-01/02 termékdöntése (felismerő- és nettó-motor helye, túlvisszatérítés-őrzés).
- [x] visszamutatás BRIEF-042 ↔ SPEC-042 ↔ kód ↔ tesztek (`docs/traceability-index.md`).
- [x] production kód nem változott (docs-only).
