---
id: FEAT-038
title: Bank- és kártyatranzakciók párosítása
status: ready_for_dev
version: 1
risk: high
owner: documenter
related_brief: BRIEF-038
---

# FEAT-038: Bank- és kártyatranzakciók párosítása

> Visszamenőleges (kód→spec) specifikáció. A megvalósítás már szállítva;
> ez a dokumentum a tényleges kódviselkedést rögzíti a VERITAS 1.1 §4.5
> 16-fejezetes szerkezetében. Ahol a BRIEF többet állít, azt a 14. fejezet
> SPEC-GAP listája jelöli.

## 1. Cél és felhasználói eredmény

A felhasználó a párosítatlan nyugták és bank-/kártyatranzakciók egyeztetési
hátralékát egy helyen látja, a rendszer javaslatait megérti (bizonyosság,
egyező/eltérő jellemzők), majd jóváhagy, elutasít, kézzel kapcsol vagy
indoklással felbont. Javaslat soha nem válik észrevétlenül végleges
pénzügyi döntéssé; csak a ténylegesen sikeres művelet jelenik meg
befejezettként.

Mérhető készültségi feltétel: mind a 8 REQ-hez tartozik AC-scenario és
végrehajtható E2E-teszt (`.agent-pipeline/03_e2e_suites/test_e2e_038.py`,
8/8 PASS a 2026-08-31 verifikáció szerint).

## 2. Kontextus és források

Kanonikus források:

- `briefs/BRIEF-038-bank-es-kartyatranzakciok-parositasa.md` (10 US: US-038-01..US-038-10)
- `VERITAS_1_1_adaptiv_egyseges_fejlesztesi_modszertan.md` §4.5 (kötelező 16 fejezet)
- `05_docs/2026-08-31-phase2-feat038-048-verification-report.md` (88 REST + 33 GUI PASS)
- `.agent-pipeline/02_specs/done/SPEC-038-bank-es-kartyatranzakciok-parositasa.md` (előd pipeline-spec, 14 fejezet)

Kódforrások (leltár):

- `app/reconciliation_api.py` — router + 5 route (`:8`, `:21`, `:24`, `:28`, `:32`, `:36-38`)
- `app/reconciliation_models.py` — `Status`, `CreateRequest`, `CommandRequest`, `TransactionMatch`, hibák
- `app/reconciliation_service.py` — `TransactionMatchService` + idempotencia/revízió logika
- `app/api_v2.py` — bekötés (`:14` import, `:150` include_router)

Kapcsolódó domain-invariánsok: szerveroldali tenant-izoláció, explicit
jóváhagyás pénzügyi döntéshez, hiba nem jelenthet sikert, idempotens
újrapróbálás, más háztartás adatának elkülönítése.

## 3. Scope és non-scope

### Benne van

- Tenant-szűrt párosítási lista, létrehozás, részlet, revíziózott módosítás, kontrollált állapotátmenet (confirm).
- `expected_revision` alapú optimistic locking; `Idempotency-Key` (min. 16 karakter).
- Egy-egy, egy-több és több-egy kapcsolatok nyilvántartása szabad formátumú `data`/`evidence` payloadban.
- Kapcsolatbontás indoklással (`reason` mező a `CommandRequest`-ben).
- `application/problem+json` hibaválaszok korrelációs azonosítóval.

### Nincs benne

- Valós banki import-csatorna vagy hitelesítőadat-kezelés (a BRIEF non-scope-ja is kizárja).
- Automatikus pontszámító/magyarázó motor a szerveren — lásd SPEC-GAP (14. fejezet).
- Főkönyvi egyeztetés vagy automatikus könyvelési döntés felhasználói kontroll nélkül.
- Perzisztens adatbázis-tárolás: a service folyamat-memóriában dolgozik (lásd 10. és 15. fejezet).

## 4. Szereplők és előfeltételek

- ACT-038-01: háztartási felhasználó / pénzügyi felelős (egyeztet, jóváhagy, bont).
- ACT-038-02: könyvelő (visszakeres, bizonyítékot ellenőriz).

- PRE-038-01: érvényes `Authorization` header és `X-Tenant-ID` header (különben 401 — `app/reconciliation_api.py:10-13`).
- PRE-038-02: `X-Role` ∈ {admin, owner, member, accountant} (különben 403).
- PRE-038-03: módosító kéréshez `Idempotency-Key` header (min. 16 karakter, különben 422 — `:15-17`).
- PRE-038-04: PATCH/confirm kéréshez ismert `expected_revision` (különben 409).

## 5. Funkcionális követelmények

- REQ-038-01 [MUST]: A rendszer rangsorolt, magyarázható párosítási javaslatokat ad.
- REQ-038-02 [MUST]: A felhasználó javaslatot jóváhagyhat, elutasíthat vagy kézzel másik kapcsolatot választhat.
- REQ-038-03 [MUST]: Az egy-több és több-egy kapcsolat összege és pénzneme validált.
- REQ-038-04 [MUST]: A kapcsolat felbontása indokolt és auditált.
- REQ-038-05 [MUST]: A tranzakció állapotváltozása duplikáció nélkül újraértékelődik.
- REQ-038-06 [MUST]: Más tenant adata nem olvasható és nem módosítható.
- REQ-038-07 [MUST]: Azonos idempotens kérés nem hoz létre második kapcsolatot.
- REQ-038-08 [MUST]: Párhuzamos döntésből legfeljebb egy érvényes revízió nyer.

## 6. Nem funkcionális követelmények

- NFR-038-01 [PERFORMANCE]: lista és részlet lekérés UI-visszajelzése 500 ms-on belül; hosszabb feldolgozás állapotjelzéssel.
- NFR-038-02 [ACCESSIBILITY]: a fő folyamat billentyűzettel végigvihető; állapotváltozás segítő technológiával érzékelhető.
- NFR-038-03 [SECURITY]: a szerveroldali `context()` az autoritatív (401/403); kliens által küldött szerepkör önmagában nem elég — csak a 4 engedélyezett érték fogadható el.
- NFR-038-04 [PRIVACY]: hibaválasz és napló nem tartalmaz hitelesítő adatot vagy teljes pénzügyi payloadot; az audit csak aggregátum-azonosítót, revíziót, aktort, okot és correlation ID-t rögzít.
- NFR-038-05 [RELIABILITY]: sikertelen írás nem hagy részleges állapotot; idegen tenant erőforrás 404-szerű választ ad, adatot nem szivárogtat.

## 7. UI-szerződés

- UI-038-01: `frontend/app/reconciliation/page.tsx` — párosítatlan nyugták és tranzakciók közös hátralék-nézete (US-038-01).
- UI-038-02: ugyanott javaslat-kártya bizonyossággal és egyező/eltérő jellemzőkkel (US-038-02, US-038-03); jóváhagy / elutasít / kézi keresés akciók (US-038-04..US-038-06).
- UI-038-03: kapcsolatbontó felület indoklás-mezővel (US-038-08); könyvelői visszakereső nézet ki/mikor/milyen-alapon adatokkal (US-038-10).
- UI-038-04: E2E GUI-lefedés: `frontend/e2e/gui_e2e_038_039_042_reconciliation.spec.ts`.

## 8. Felhasználói és GUI-folyamat

1. A felhasználó megnyitja a `/reconciliation` oldalt; a rendszer csak az aktív tenant párosítatlan nyugtáit és könyvelt/függő tranzakcióit kéri le (`GET /api/v2/reconciliation/matches`).
2. A jelöltlista javaslat-bizonyossággal és magyarázattal jelenik meg; üres hátralék esetén üres állapot látszik.
3. A felhasználó egy javaslatot jóváhagy (`POST .../{id}/confirm`), elutasít vagy kézzel másik kapcsolatot választ (`PATCH .../{id}` + `expected_revision`).
4. Egy-több / több-egy esetben a felület az összeg- és pénznem-konzisztenciát kéri/ellenőrzi mentés előtt.
5. Felbontáskor a rendszer indoklást kér, és a változást auditbejegyzéssel rögzíti.
6. Tranzakció-állapotváltozás (függő→könyvelt→visszavont) után a lista újraértékelődik, duplikált kapcsolat nem keletkezik.
7. Hiba (401/403/404/409/422) esetén a felület megőrzi a bemenetet, újrapróbálást kínál, sikert nem állít.

## 9. Állapotmodell

Tényleges gépi állapotok (`app/reconciliation_models.py:8-14`):

- `UNMATCHED` (kezdő — `app/reconciliation_service.py:21`), `SUGGESTED`, `CONFIRMED`, `REJECTED`, `REVERSED`.

Megfigyelt átmenetek (`app/reconciliation_service.py:32`, `CommandRequest.action` → célállapot):

- `confirm` → `REJECTED`; `reject` → `REVERSED`; `resolve` → `REJECTED`; `reopen` → `UNMATCHED`.
- Ismeretlen action: állapot változatlan, de a revízió így is +1-gyel nő és az idempotencia-kulcs rögzül.
- Minden átmenet feltétele: `expected_revision` egyezik, különben `StaleRevisionError` (409), írás nélkül.
- Lásd SPEC-GAP-038-01: a `confirm→REJECTED` leképezés nem a BRIEF "jóváhagyás" nyelvét tükrözi.

## 10. API-, esemény- és adatszerződés

### REST (mind `app/reconciliation_api.py`)

| Route | Kódhely | Szerződés |
| :--- | :--- | :--- |
| `GET /api/v2/reconciliation/matches` | `:21-22` | tenant-szűrt lista; 200 / 401 / 403 |
| `POST /api/v2/reconciliation/matches` | `:24-26` | `CreateRequest`; kötelező `Idempotency-Key`; 201 / 400 / 401 / 403 / 409 / 422 |
| `GET /api/v2/reconciliation/matches/{id}` | `:28-30` | részlet + `evidence`; idegen tenantnál 404-szerű `NOT_FOUND` |
| `PATCH /api/v2/reconciliation/matches/{id}` | `:32-34` | `CommandRequest` + `expected_revision`; 200 / 409 / 422 |
| `POST /api/v2/reconciliation/matches/{id}/confirm` | `:36-38` | `action="confirm"` kényszerítéssel `patch_item`-re delegál; 200 / 403 / 409 / 422 |

Hibák: minden hiba `application/problem+json` (`ApiProblem`: `code`, `message`, `retryable=False`, `correlation_id` — `:19`, modellek `:39-41`).
Bekötés: `app/api_v2.py:14` (import) és `:150` (`include_router`).

### Események

Nincs eseménybusz: a service szinkron, folyamat-memóriában dolgozik; külső feliratkozó (webhook/értesítés) nincs bekötve.

### Adatmodell

- `TransactionMatch` (`app/reconciliation_models.py:28-37`): `id`, `tenant_id`, `status`, `revision`, `client_reference`, `data: dict`, `evidence: dict`, `created_at`, `updated_at`.
- `CreateRequest` (`:15-19`): `expected_revision` (default 0), `client_reference` (1–128), `payload: dict`.
- `CommandRequest` (`:21-27`): `expected_revision`, `action` (1–64), `reason` (max 1000), `payload: dict`.
- Hibák: `NotFoundError` 404 (`:45-46`), `StaleRevisionError` 409 (`:47-48`), `IdempotencyConflictError` 409 (`:49-50`).
- Tárolás: `TransactionMatchService._items` + `_keys` dict `threading.RLock` mögött (`app/reconciliation_service.py:7-9`); idempotencia-kulcs = sha256(request-json), tenant-scope (`:12-20`); migráció nincs.

## 11. Acceptance scenario-k

### AC-038-01: javaslatlista és jóváhagyás (REQ-038-01, REQ-038-02)

Given párosítatlan nyugta és tranzakció az aktív tenantban
When a felhasználó lekéri a javaslatokat és az egyiket jóváhagyja
Then a kapcsolat ellenőrzött állapotba kerül, bizonyossággal és magyarázattal
And más tenant adata nem jelenik meg.

### AC-038-02: kézi kapcsolat és kardinalitás (REQ-038-02, REQ-038-03)

Given az automatikus keresés nem talál jelöltet / részfizetés esete
When a felhasználó kézzel kapcsol egy nyugtát és terhelést
Then az összeg- és pénznem-konzisztencia ellenőrzött, a kapcsolat létrejön.

### AC-038-03: indokolt felbontás (REQ-038-04)

Given jóváhagyott párosítás
When a felhasználó indoklással felbontja
Then a kapcsolat felbomlik és a változás auditálható (aktor, ok, revízió).

### AC-038-04: állapotváltozás duplikáció nélkül (REQ-038-05)

Given létező párosítás
When a banki tétel függő→könyvelt→visszavont állapotba vált
Then a párosítás újraértékelődik, második kapcsolat nem jön létre.

### AC-038-05: tenant-izoláció (REQ-038-06)

Given két tenant (A, B) és B-beli párosítás-azonosító
When A ezzel az azonosítóval részletet/módosítást kér
Then 404-szerű válasz érkezik, B adata nem olvasható és nem módosítható.

### AC-038-06: idempotens retry (REQ-038-07)

Given létrehozó kérés `Idempotency-Key`-jel
When ugyanaz a kérés (azonos payload) megismétlődik
Then ugyanaz az erőforrás tér vissza, második kapcsolat nem jön létre; eltérő payload esetén 409 `IDEMPOTENCY_CONFLICT`.

### AC-038-07: párhuzamos döntés (REQ-038-08)

Given azonos revíziójú párosítás
When két módosítás érkezik ugyanazzal az `expected_revision`-nel
Then pontosan egy nyer, a másik determinisztikus 409 `STALE_REVISION`-t kap.

### AC-038-08: hiba nem siker (összes REQ)

Given érvénytelen payload / lejárt auth / elavult revízió
When a művelet végrehajtódik
Then `application/problem+json` hibaválasz érkezik, sikeres állapot nem jelenik meg, részleges írás nem marad.

## 12. Tesztleképezés

| REQ | AC | E2E-teszt (fájl:sor) | GUI | Unit-cél (státusz) |
| :--- | :--- | :--- | :--- | :--- |
| REQ-038-01 | AC-038-01 | `test_e2e_038_ac_01_positive_path` (`.agent-pipeline/03_e2e_suites/test_e2e_038.py:24`) | `gui_e2e_038_039_042_reconciliation.spec.ts` | `tests/unit/test_reconciliation_service.py::test_req_038_01` — HIÁNYZIK |
| REQ-038-02 | AC-038-01/02 | `test_e2e_038_ac_02_contract_state` (`test_e2e_038.py:29`) | ugyanaz | `...::test_req_038_02` — HIÁNYZIK |
| REQ-038-03 | AC-038-02 | `test_e2e_038_ac_03_invalid_payload_is_safe` (`test_e2e_038.py:33`) | ugyanaz | `...::test_req_038_03` — HIÁNYZIK |
| REQ-038-04 | AC-038-03 | `test_e2e_038_ac_04_detail_contract` (`test_e2e_038.py:37`) | ugyanaz | `...::test_req_038_04` — HIÁNYZIK |
| REQ-038-05 | AC-038-04 | `test_e2e_038_ac_05_no_silent_success` (`test_e2e_038.py:41`) | ugyanaz | `...::test_req_038_05` — HIÁNYZIK |
| REQ-038-06 | AC-038-05 | `test_e2e_038_ac_06_tenant_and_auth_isolation` (`test_e2e_038.py:45`) | ugyanaz | `...::test_req_038_06` — HIÁNYZIK |
| REQ-038-07 | AC-038-06 | `test_e2e_038_ac_07_idempotent_retry` (`test_e2e_038.py:50`) | ugyanaz | `...::test_req_038_07` — HIÁNYZIK |
| REQ-038-08 | AC-038-07 | `test_e2e_038_ac_08_concurrent_revision` (`test_e2e_038.py:58`) | ugyanaz | `...::test_req_038_08` — HIÁNYZIK |

E2E-eredmény: 8/8 PASS (2026-08-31 jelentés). A `tests/unit/` mappában egyik cél sem létezik — lásd SPEC-GAP-038-04.

## 13. Kockázatok és emberi döntések

- HR-038-01: téves automatikus összekapcsolás hibás elszámolást okozhat — ezért a javaslat soha nem véglegesül önmagától; a `confirm` explicit, revíziózott művelet.
- HR-038-02: a generikus `confirm→REJECTED` leképezés félreérthető; névválasztás-felülvizsgálat product-owner döntést igényel (GAP).
- Jogosultság: pénzügyi kapcsolatot csak admin/owner/member/accountant szerep hozhat létre/módosíthat (403 egyébként).
- Adatvédelem: `evidence` szabad dict — érzékeny teljes payload másolása tilos; csak azonosítók és indoklás tárolhatók.

## 14. Nyitott kérdések és SPEC-GAP

Nincs implementációt blokkoló nyitott kérdés (a kód szállítva, E2E zöld).

SPEC-GAP (a BRIEF többet állít, mint a kód):

- SPEC-GAP-038-01: US-038-02/US-038-03 szerinti összeg/pénznem/dátum/kereskedő/fizetési-mód alapú rangsorolt, magyarázható pontszámítás **nincs a szerverkódban**; a `data`/`evidence` szabad dict, az `evidence` létrehozáskor csak `{"source": "FEAT-038"}` (`app/reconciliation_service.py:21`).
- SPEC-GAP-038-02: borravaló-, részfizetés-, deviza- és dátumeltérés-validáció **nincs implementálva** (a `CommandRequest.payload` sémázatlan).
- SPEC-GAP-038-03: US-038-10 könyvelői "ki/mikor/milyen-javaslat-alapján" visszakereséshez **nincs audit-tábla**; csak `reason` szöveg és revíziószám marad meg.
- SPEC-GAP-038-04: az előd pipeline-spec unit-céljai (`tests/unit/test_reconciliation_service.py`) **nem léteznek** a repóban; elsődleges bizonyíték az E2E-suite.
- SPEC-GAP-038-05: megfigyelt viselkedés: `confirm` action `REJECTED` státuszt állít be (`app/reconciliation_service.py:32`) — a BRIEF "jóváhagyás" fogalmával ellentétes elnevezés/leképezés, felülvizsgálatra jelölve.

## 15. Rollback és megfigyelhetőség

- Rollback: migráció nincs; a service folyamat-memóriában tárol — újraindítás az összes `TransactionMatch`-et törli (adatvesztési kockázat, lásd GAP). Visszaállítás előző verzióra tisztán telepítéssel lehetséges, adatmigráció nem kell.
- Megfigyelhetőség: minden hiba `application/problem+json` `correlation_id`-val (`app/reconciliation_api.py:19`); sikeres válasz tenant- és revízió-azonosítót hordoz. Dedikált metrika-/audit-végpont nincs.

## 16. Definition of Done

- [x] mind a 8 REQ-hez AC és E2E-teszt tartozik (8/8 PASS, 2026-08-31).
- [x] célzott E2E-suite zöld; GUI-suite (`gui_e2e_038_039_042`) zöld a jelentés szerint.
- [ ] unit-célok (`tests/unit/test_reconciliation_service.py`) pótlása — nyitott, SPEC-GAP-038-04.
- [ ] SPEC-GAP-038-01/02/05 termékdöntése (pontszámító motor, confirm-szemantika).
- [x] visszamutatás: BRIEF-038 ↔ SPEC-038 ↔ kód ↔ tesztek (`docs/traceability-index.md`).
- [x] production kód nem változott (docs-only feladat).
