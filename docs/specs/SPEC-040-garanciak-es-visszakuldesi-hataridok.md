---
id: FEAT-040
title: Garanciák és visszaküldési határidők
status: ready_for_dev
version: 1
risk: medium
owner: documenter
related_brief: BRIEF-040
---

# FEAT-040: Garanciák és visszaküldési határidők

> Visszamenőleges (kód→spec) specifikáció. A megvalósítás már szállítva;
> ez a dokumentum a tényleges kódviselkedést rögzíti a VERITAS 1.1 §4.5
> 16-fejezetes szerkezetében. Ahol a BRIEF többet állít, azt a 14. fejezet
> SPEC-GAP listája jelöli.

## 1. Cél és felhasználói eredmény

A felhasználó a nyugtatételekhez garanciális/visszaküldési esetet rögzít,
javasolt határidőt lát és felülbírál, kapcsolódó bizonylatot és
hivatkozást csatol, az ügy életciklusát végigköveti, és a határidő előtt
deduplikált emlékeztetőt kap. Csak a ténylegesen sikeres művelet jelenik
meg befejezettként; a tévesen jelzett probléma nem tér vissza
indokolatlanul.

Mérhető készültségi feltétel: mind a 8 REQ-hez tartozik AC-scenario és
végrehajtható E2E-teszt (`.agent-pipeline/03_e2e_suites/test_e2e_040.py`,
8/8 PASS a 2026-08-31 verifikáció szerint).

## 2. Kontextus és források

Kanonikus források:

- `briefs/BRIEF-040-garanciak-es-visszakuldesi-hataridok.md` (9 US: US-040-01..US-040-09)
- `VERITAS_1_1_adaptiv_egyseges_fejlesztesi_modszertan.md` §4.5
- `05_docs/2026-08-31-phase2-feat038-048-verification-report.md`
- `.agent-pipeline/02_specs/done/SPEC-040-garanciak-es-visszakuldesi-hataridok.md` (előd pipeline-spec)

Kódforrások (leltár):

- `app/warranty_api.py` — router + 5 route (`:8` prefix `/api/v2/warranties`; route-ok `:21`, `:24`, `:28`, `:32`, `:36-38`)
- `app/warranty_models.py` — `Status` (`:8-15`), `CreateRequest` (`:17-21`), `CommandRequest` (`:23-28`), `WarrantyCase` (`:30-39`), hibák (`:44-51`)
- `app/warranty_service.py` — `WarrantyCaseService` (`:7`), kezdő `DRAFT` (`:21`), action-leképezés (`:32`)
- `app/api_v2.py` — bekötés (`:16` import, `:152` include_router)

Kapcsolódó domain-invariánsok: tenant-izoláció, javaslat felülbírálhatósága,
deduplikált jelzés, idempotens létrehozás, revíziózott állapotváltás.

## 3. Scope és non-scope

### Benne van

- Garanciális/visszaküldési eset létrehozása, listája, részlete, revíziózott módosítása és confirm-útja.
- Javasolt dátum/forrás és felülbírálás adata a szabad `data` payloadban; bizonylat-, sorozatszám- és hivatkozás-adat ugyanott.
- Ügy-életciklus nyilvántartása a `Status` sémával (lásd 9. fejezet).
- Tenant-izoláció, idempotencia, optimistic locking, `application/problem+json` hibák.

### Nincs benne

- Javasolt határidőt számító motor a szerveren — lásd SPEC-GAP-040-01.
- Emlékeztető-küldő motor — lásd SPEC-GAP-040-02.
- Jogi garanciafeltétel-meghatározás és automatikus reklamációbenyújtás (a BRIEF non-scope-ja is kizárja).
- Perzisztens tárolás: folyamat-memória (lásd 10. és 15. fejezet).

## 4. Szereplők és előfeltételek

- ACT-040-01: felhasználó (esetet rögzít, dátumot bírál felül, ügyet követ).
- ACT-040-02: könyvelő/háztartási tag (visszakeres, visszatérítést köt az ügyhöz).

- PRE-040-01: érvényes `Authorization` + `X-Tenant-ID` (különben 401 — `app/warranty_api.py:10-13`).
- PRE-040-02: `X-Role` ∈ {admin, owner, member, accountant} (különben 403).
- PRE-040-03: módosításhoz `Idempotency-Key` (min. 16 karakter, különben 422 — `:15-17`).
- PRE-040-04: állapotváltáshoz ismert `expected_revision` (különben 409).

## 5. Funkcionális követelmények

- REQ-040-01 [MUST]: Nyugtatételből garanciális vagy visszaküldési eset hozható létre.
- REQ-040-02 [MUST]: A javasolt határidő forrással látható és felülbírálható.
- REQ-040-03 [MUST]: Kapcsolódó bizonylat, sorozatszám és hivatkozás rögzíthető.
- REQ-040-04 [MUST]: Közelgő határidőhöz deduplikált emlékeztető tartozik.
- REQ-040-05 [MUST]: Az ügy teljes életciklusa követhető.
- REQ-040-06 [MUST]: Más tenant esete nem hozzáférhető.
- REQ-040-07 [MUST]: Azonos létrehozási kérés egy esetet eredményez.
- REQ-040-08 [MUST]: Párhuzamos állapotváltás revíziókonfliktust ad.

## 6. Nem funkcionális követelmények

- NFR-040-01 [PERFORMANCE]: lista és határidő-nézet UI-visszajelzése 500 ms-on belül.
- NFR-040-02 [ACCESSIBILITY]: az esetrögzítés és az ügykövetés billentyűzettel végigvihető; határidő-állapotváltozás bejelentett.
- NFR-040-03 [SECURITY]: szerveroldali `context()` az autoritatív; csak a 4 engedélyezett szerep.
- NFR-040-04 [PRIVACY]: emlékeztető és hibaválasz csak a szükséges adatot tartalmazza; teljes nyugtatartalom nem naplózható.
- NFR-040-05 [RELIABILITY]: sikertelen rögzítés nem hoz létre félig kitöltött esetet; idegen tenant azonosítóra 404-szerű válasz.

## 7. UI-szerződés

- UI-040-01: `frontend/app/warranties/page.tsx` — esetlista határidő-nézettel; esetrögzítés nyugtatételből (US-040-01).
- UI-040-02: ugyanott javasolt dátum forrással + felülbíráló mezők (US-040-02, US-040-03), ügy-életciklus sáv (US-040-07), visszatérítés-kapcsoló (US-040-08), garanciatípus-választó (US-040-09).
- UI-040-03: E2E GUI-lefedés: `frontend/e2e/gui_e2e_040_041_warranties_prices.spec.ts`.

## 8. Felhasználói és GUI-folyamat

1. A felhasználó a `/warranties` oldalon nyugtatételből esetet hoz létre (`POST /api/v2/warranties`).
2. A felület a vásárlási dátumból javasolt visszaküldési/garanciális határidőt mutat forrással; a felhasználó dátumot és feltételt felülbírálhat (`PATCH .../{id}`).
3. Terméknév, sorozatszám, kereskedői hivatkozás és dokumentum-hivatkozások rögzíthetők (szabad `payload`).
4. A határidő előtt szabályozható emlékeztetők érkeznek (kívánt viselkedés, lásd GAP).
5. Az ügy állapota (elindított→elküdött→elfogadott→elutasított→lezárt szemantika) a `Status` sémában követhető; a visszatérítés az ügyhöz és az eredeti vásárláshoz köthető.
6. Hiba esetén a felület a bevitelet megőrzi, újrapróbálást kínál, részleges eset nem marad.

## 9. Állapotmodell

Tényleges gépi állapotok (`app/warranty_models.py:8-15`):

- `DRAFT` (kezdő — `app/warranty_service.py:21`), `ACTIVE`, `RETURN_STARTED`, `CLAIM_STARTED`, `RESOLVED`, `EXPIRED`, `CANCELLED`.

Megfigyelt átmenetek (`app/warranty_service.py:32`):

- `confirm` → `EXPIRED`; `reject` → `CANCELLED`; `resolve` → `EXPIRED`; `reopen` → `DRAFT`.
- Feltétel: `expected_revision` egyezik, különben 409 írás nélkül.
- Megjegyzés: a BRIEF "elindított/elküldött/elfogadott/elutasított/lezárt" nyelvezete és a gyártói/kereskedői/önkéntes megkülönböztetés a `data` payloadban él, nem gépi átmenetként (lásd GAP).

## 10. API-, esemény- és adatszerződés

### REST (mind `app/warranty_api.py`)

| Route | Kódhely | Szerződés |
| :--- | :--- | :--- |
| `GET /api/v2/warranties` | `:21-22` | tenant-szűrt lista; 200 / 401 / 403 |
| `POST /api/v2/warranties` | `:24-26` | `CreateRequest`; kötelező `Idempotency-Key`; 201 / 400 / 401 / 403 / 409 / 422 |
| `GET /api/v2/warranties/{id}` | `:28-30` | részlet + `evidence`; idegen tenantnál 404-szerű `NOT_FOUND` |
| `PATCH /api/v2/warranties/{id}` | `:32-34` | `CommandRequest` + `expected_revision`; 200 / 409 / 422 |
| `POST /api/v2/warranties/{id}/confirm` | `:36-38` | `action="confirm"` kényszerítéssel delegál; 200 / 403 / 409 / 422 |

Hibák: `application/problem+json` (`:19`; modellek `:41-43`). Bekötés: `app/api_v2.py:16`, `:152`.

### Események

Nincs eseménybusz; emlékeztető-ütemezés szerveroldalon nincs bekötve (GAP).

### Adatmodell

- `WarrantyCase` (`app/warranty_models.py:30-39`): `id`, `tenant_id`, `status`, `revision`, `client_reference`, `data: dict`, `evidence: dict`, `created_at`, `updated_at`.
- `CreateRequest` (`:17-21`), `CommandRequest` (`:23-28`) — generikus alak (vö. FEAT-038).
- Hibák: `NotFoundError` 404 (`:47-48`), `StaleRevisionError` 409 (`:49-50`), `IdempotencyConflictError` 409 (`:51-52`).
- Tárolás: `WarrantyCaseService._items` + `_keys`, `threading.RLock` (`app/warranty_service.py:7-9`); létrehozáskor `evidence={"source": "FEAT-040"}` (`:21`); migráció nincs.

## 11. Acceptance scenario-k

### AC-040-01: eset létrehozása tételből (REQ-040-01)

Given feldolgozott nyugta tétellel
When a felhasználó garanciális/visszaküldési esetet hoz létre
Then az eset `DRAFT` állapotban, a tételre hivatkozva létrejön.

### AC-040-02: javasolt határidő felülbírálata (REQ-040-02, REQ-040-03)

Given létező eset javasolt dátummal és forrással
When a felhasználó a kereskedő tényleges szabálya szerint módosít, bizonylatot és hivatkozást csatol
Then a módosítás revíziózottan mentődik, az előzmény nem vész el.

### AC-040-03: deduplikált emlékeztető (REQ-040-04)

Given közelgő határidő
When az emlékeztető-szabályok kiértékelődnek
Then a jelzés szabályozhatóan, duplikáció nélkül érkezik. (Kívánt; lásd GAP.)

### AC-040-04: életciklus-követés (REQ-040-05)

Given futó ügy
When az ügy előrehalad (visszaküldés/claim események)
Then az állapot a `Status` sémában követhető, a visszatérítés az ügyhöz köthető.

### AC-040-05: tenant-izoláció (REQ-040-06)

Given B-tenantbeli eset-azonosító
When A-tenant kéri/módosítja
Then 404-szerű válasz, adatszivárgás nélkül.

### AC-040-06: idempotens létrehozás (REQ-040-07)

Given létrehozó kérés `Idempotency-Key`-jel
When a kérés megismétlődik (azonos payload)
Then ugyanaz az eset tér vissza; eltérő payloadra 409 `IDEMPOTENCY_CONFLICT`.

### AC-040-07: párhuzamos állapotváltás (REQ-040-08)

Given azonos revíziójú eset
When két állapotváltás érkezik ugyanazzal az `expected_revision`-nel
Then pontosan egy nyer, a másik 409 `STALE_REVISION`-t kap.

### AC-040-08: hiba nem siker (összes REQ)

Given érvénytelen payload / auth-hiba / elavult revízió
When a művelet fut
Then `application/problem+json` hiba, részleges eset nélkül.

## 12. Tesztleképezés

| REQ | AC | E2E-teszt (fájl:sor) | GUI | Unit-cél (státusz) |
| :--- | :--- | :--- | :--- | :--- |
| REQ-040-01 | AC-040-01 | `test_e2e_040_ac_01_positive_path` (`.agent-pipeline/03_e2e_suites/test_e2e_040.py:24`) | `gui_e2e_040_041_warranties_prices.spec.ts` | `tests/unit/test_warranties_service.py::test_req_040_01` — HIÁNYZIK |
| REQ-040-02 | AC-040-02 | `test_e2e_040_ac_02_contract_state` (`test_e2e_040.py:29`) | ugyanaz | `...::test_req_040_02` — HIÁNYZIK |
| REQ-040-03 | AC-040-02 | `test_e2e_040_ac_03_invalid_payload_is_safe` (`test_e2e_040.py:33`) | ugyanaz | `...::test_req_040_03` — HIÁNYZIK |
| REQ-040-04 | AC-040-03 | `test_e2e_040_ac_04_detail_contract` (`test_e2e_040.py:37`) | ugyanaz | `...::test_req_040_04` — HIÁNYZIK |
| REQ-040-05 | AC-040-04 | `test_e2e_040_ac_05_no_silent_success` (`test_e2e_040.py:41`) | ugyanaz | `...::test_req_040_05` — HIÁNYZIK |
| REQ-040-06 | AC-040-05 | `test_e2e_040_ac_06_tenant_and_auth_isolation` (`test_e2e_040.py:45`) | ugyanaz | `...::test_req_040_06` — HIÁNYZIK |
| REQ-040-07 | AC-040-06 | `test_e2e_040_ac_07_idempotent_retry` (`test_e2e_040.py:50`) | ugyanaz | `...::test_req_040_07` — HIÁNYZIK |
| REQ-040-08 | AC-040-07 | `test_e2e_040_ac_08_concurrent_revision` (`test_e2e_040.py:58`) | ugyanaz | `...::test_req_040_08` — HIÁNYZIK |

E2E-eredmény: 8/8 PASS (2026-08-31 jelentés). Unit-célok nem léteznek — SPEC-GAP-040-04.

## 13. Kockázatok és emberi döntések

- HR-040-01: lejárt visszaküldési határidő pénzügyi veszteség — a javasolt dátum forrása és a felülbírálat termékfelelősség; a szerver nem validálja a dátum helyességét.
- HR-040-02: téves garanciatípus-besorolás (gyártói/kereskedői/önkéntes) ügyintézési kockázat — a besorolás szabad `data`, validáció nélkül.
- Adatvédelem: sorozatszám és kereskedői hivatkozás csak a saját tenantban tárolható és jeleníthető meg.

## 14. Nyitott kérdések és SPEC-GAP

Nincs implementációt blokkoló nyitott kérdés (kód szállítva, E2E zöld).

SPEC-GAP (a BRIEF többet állít, mint a kód):

- SPEC-GAP-040-01: US-040-02 szerinti vásárlási-dátumból javasolt határidő-számítás **nincs a szerverkódban**; a javaslat és forrása kliens/`data` eredetű.
- SPEC-GAP-040-02: US-040-05 szerinti több, szabályozható emlékeztető motorja **nincs implementálva**.
- SPEC-GAP-040-03: US-040-07 életciklus-nyelvezete és US-040-09 garanciatípusai nem gépi átmenetek, csak `data`-szemantika; US-040-08 visszatérítés-kapcsolat validáció nélkül, szabad hivatkozás.
- SPEC-GAP-040-04: az előd pipeline-spec unit-céljai (`tests/unit/test_warranties_service.py`) **nem léteznek**; elsődleges bizonyíték az E2E-suite.

## 15. Rollback és megfigyelhetőség

- Rollback: migráció nincs; folyamat-memória — újraindítás az eseteket törli. Visszaállítás telepítéssel, adatmigráció nélkül.
- Megfigyelhetőség: `application/problem+json` `correlation_id`-val; válaszokban tenant- és revízió-azonosító. Határidő-figyelő metrika és kézbesítési napló nincs.

## 16. Definition of Done

- [x] mind a 8 REQ-hez AC és E2E-teszt (8/8 PASS, 2026-08-31).
- [x] célzott E2E + GUI-suite zöld a jelentés szerint.
- [ ] unit-célok pótlása — nyitott (SPEC-GAP-040-04).
- [ ] SPEC-GAP-040-01/02 termékdöntése (javaslat- és emlékeztető-motor).
- [x] visszamutatás BRIEF-040 ↔ SPEC-040 ↔ kód ↔ tesztek (`docs/traceability-index.md`).
- [x] production kód nem változott (docs-only).
