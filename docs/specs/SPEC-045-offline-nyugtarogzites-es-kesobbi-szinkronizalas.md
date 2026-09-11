---
id: FEAT-045
title: Offline nyugtarögzítés és későbbi szinkronizálás
status: ready_for_dev
version: 1
risk: high
owner: documenter
related_brief: BRIEF-045
---

# FEAT-045: Offline nyugtarögzítés és későbbi szinkronizálás

> Visszamenőleges (kód→spec) specifikáció. A megvalósítás már szállítva;
> ez a dokumentum a tényleges kódviselkedést rögzíti a VERITAS 1.1 §4.5
> 16-fejezetes szerkezetében. Ahol a BRIEF többet állít, azt a 14. fejezet
> SPEC-GAP listája jelöli.

## 1. Cél és felhasználói eredmény

A felhasználó kapcsolat nélkül is rögzít nyugtát (fénykép/fájl +
minimális metaadat + megjegyzés piszkozatként), egyértelműen látja, mi
csak az eszközön van / feltöltésre vár / szinkronizálódott, a kapcsolat
visszatérésekor a feltöltés biztonságosan folytatódik, az elemhiba nem
blokkolja a sort, az ismételt küldés nem duplikál, a konfliktus
összehasonlíthatóan feloldható, és a fel nem töltött adat eszközcsere/
kijelentkezés/törlés előtt figyelmeztetéssel kezelhető.

Mérhető készültségi feltétel: mind a 8 REQ-hez tartozik AC-scenario és
végrehajtható E2E-teszt (`.agent-pipeline/03_e2e_suites/test_e2e_045.py`,
8/8 PASS a 2026-08-31 verifikáció szerint).

## 2. Kontextus és források

Kanonikus források:

- `briefs/BRIEF-045-offline-nyugtarogzites-es-kesobbi-szinkronizalas.md` (10 US: US-045-01..US-045-10)
- `VERITAS_1_1_adaptiv_egyseges_fejlesztesi_modszertan.md` §4.5
- `05_docs/2026-08-31-phase2-feat038-048-verification-report.md`
- `.agent-pipeline/02_specs/done/SPEC-045-offline-nyugtarogzites-es-kesobbi-szinkronizalas.md` (előd pipeline-spec)

Kódforrások (leltár):

- `app/offline_sync_api.py` — router + 5 route (`:8` prefix `/api/v2/offline-sync`; route-ok `:21`, `:24`, `:28`, `:32`, `:36-38`)
- `app/offline_sync_models.py` — `Status` (`:8-16`), `CreateRequest` (`:18-22`), `CommandRequest` (`:24-29`), `OfflineReceiptDraft` (`:31-40`), hibák (`:45-52`)
- `app/offline_sync_service.py` — `OfflineReceiptDraftService` (`:7`), kezdő `LOCAL_ONLY` (`:21`), action-leképezés (`:32`)
- `app/api_v2.py` — bekötés (`:21` import, `:157` include_router)
- `frontend/app/receipts/offline/page.tsx`, `frontend/components/offline/OfflineQueue.tsx`

Kapcsolódó domain-invariánsok: tenant-izoláció, munka nem vész el
(piszkozat túléli a háttérbe helyezést/újraindítást), idempotens
feltöltés, csendes felülírás tilalma, adatvesztés előtti figyelmeztetés.

## 3. Scope és non-scope

### Benne van

- Offline piszkozat (draft) létrehozása, listája, részlete, revíziózott állapotváltása és confirm-útja a szinkron-életút nyilvántartására.
- Helyi várólista-állapot, hálózati szabály (szünet/Wi-Fi-korlát), elemszintű újrapróbálás, konfliktus-összehasonlítás és duplikációvédelem adatszinten.
- Tenant-izoláció (tenantváltás nem szinkronizál más háztartásba), idempotencia, optimistic locking, `application/problem+json` hibák.

### Nincs benne

- A teljes alkalmazás offline elérhetősége; korlátlan/garantált helyi tárolás; elveszett eszköz adat-visszaállítási garanciája (a BRIEF non-scope-ja is kizárja).
- Tényleges eszköz-oldali perzisztencia (IndexedDB/képbináris) és hálózat-érzékelő a szerveren — a szerver a draft-életutat tartja nyilván (lásd SPEC-GAP-045-01).
- Perzisztens szerver-tárolás: folyamat-memória (lásd 10. és 15. fejezet).

## 4. Szereplők és előfeltételek

- ACT-045-01: felhasználó (offline rögzít, várólistát kezel, feltölt, konfliktust old fel).

- PRE-045-01: érvényes `Authorization` + `X-Tenant-ID` a szerver-műveletekhez (különben 401 — `app/offline_sync_api.py:10-13`); a tisztán helyi rögzítéshez nincs szerver-előfeltétel.
- PRE-045-02: `X-Role` ∈ {admin, owner, member, accountant} (különben 403).
- PRE-045-03: szerver-módosításhoz `Idempotency-Key` (min. 16 karakter, különben 422 — `:15-17`).
- PRE-045-04: állapotváltáshoz ismert `expected_revision` (különben 409).

## 5. Funkcionális követelmények

- REQ-045-01 [MUST]: Nyugta és minimális metaadat hálózat nélkül piszkozatként megőrizhető.
- REQ-045-02 [MUST]: A helyi várólista állapota egyértelműen látható.
- REQ-045-03 [MUST]: Kapcsolat visszatérésekor a feltöltés folytatható.
- REQ-045-04 [MUST]: Elemhiba nem blokkolja a teljes batch-et.
- REQ-045-05 [MUST]: Konfliktusnál mindkét változat összehasonlítható és nincs csendes felülírás.
- REQ-045-06 [MUST]: Tenantváltás nem szinkronizál adatot más háztartásba.
- REQ-045-07 [MUST]: Azonos draft ismételt szinkronja nem duplikál nyugtát.
- REQ-045-08 [MUST]: Háttérbe helyezés és újraindítás után a draft és progressz megmarad.

## 6. Nem funkcionális követelmények

- NFR-045-01 [PERFORMANCE]: várólista-nézet azonnal (500 ms-on belül) tükrözi a helyi állapotot; a feltöltés folytatása nem igényel újraindítást.
- NFR-045-02 [ACCESSIBILITY]: a szinkronállapot (eszközön/várakozik/szinkronizálódott) szövegesen is érzékelhető, nem csak színnel.
- NFR-045-03 [SECURITY]: szerveroldali `context()` az autoritatív; tenantváltáskor a sor nem szivároghat át.
- NFR-045-04 [PRIVACY]: képbináris hibaválaszban/naplóban nem jelenhet meg; csak draft-azonosító és állapot.
- NFR-045-05 [RELIABILITY]: elemhiba izolált; ugyanazon draft ismételt küldése idempotens; konfliktus csendes felülírás nélkül oldható fel.

## 7. UI-szerződés

- UI-045-01: `frontend/app/receipts/offline/page.tsx` + `frontend/components/offline/OfflineQueue.tsx` — várólista eszközön/várakozik/szinkronizálódott állapotokkal (US-045-03), szünet/Wi-Fi-korlát kapcsolóval (US-045-05), elemszintű újrapróbálással (US-045-07).
- UI-045-02: ugyanott konfliktus-összehasonlító (US-045-09), adatvesztés-figyelmeztetés eszközcsere/kijelentkezés/törlés előtt (US-045-10).
- UI-045-03: E2E GUI-lefedés: `frontend/e2e/gui_e2e_045_048_offline_mobile.spec.ts`.

## 8. Felhasználói és GUI-folyamat

1. A felhasználó kapcsolat nélkül fényképez/fájlt ad hozzá, minimális metaadatot és megjegyzést ment piszkozatként (`LOCAL_ONLY`).
2. A várólista mutatja: csak eszközön / feltöltésre vár / szinkronizálódott.
3. A felhasználó a képfeltöltést szüneteltetheti vagy Wi-Fi-re korlátozhatja.
4. Kapcsolat visszatérésekor a feltöltés biztonságosan folytatódik (`QUEUED`→`UPLOADING`→`PROCESSING`→`SYNCED` szemantika); háttérbe helyezés/bezárás/újraindítás után a piszkozat és az előrehaladás megmarad.
5. Sikertelen elem külön újrapróbálható; egyetlen hiba nem blokkolja a sort.
6. Ugyanazon draft ismételt küldése nem duplikál (idempotencia).
7. Helyi–szerver ütközéskor mindkét változat összehasonlítható, a választás explicit; csendes felülírás nincs.
8. Fel nem töltött adat birtokában eszközcsere/kijelentkezés/törlés előtt figyelmeztetés és biztonságos döntés jelenik meg.

## 9. Állapotmodell

Tényleges gépi állapotok (`app/offline_sync_models.py:8-16`):

- `LOCAL_ONLY` (kezdő — `app/offline_sync_service.py:21`), `QUEUED`, `UPLOADING`, `PROCESSING`, `CONFLICT`, `SYNCED`, `FAILED`, `DISCARDED`.

Megfigyelt átmenetek (`app/offline_sync_service.py:32`):

- `confirm` → `FAILED`; `reject` → `DISCARDED`; `resolve` → `FAILED`; `reopen` → `LOCAL_ONLY`.
- Feltétel: `expected_revision` egyezik, különben 409 írás nélkül.
- Megjegyzés: a `QUEUED`→`UPLOADING`→`PROCESSING`→`SYNCED` feltöltési életút és a `CONFLICT` feloldási szemantika a sémában létezik, de a generikus action-leképezés közvetlenül nem vezérli őket — a kliens az állapotot a `data` payloadon és az API-hívások sorrendjén keresztül tartja nyilván (lásd GAP).

## 10. API-, esemény- és adatszerződés

### REST (mind `app/offline_sync_api.py`)

| Route | Kódhely | Szerződés |
| :--- | :--- | :--- |
| `GET /api/v2/offline-sync` | `:21-22` | tenant-szűrt lista; 200 / 401 / 403 |
| `POST /api/v2/offline-sync` | `:24-26` | `CreateRequest`; kötelező `Idempotency-Key`; 201 / 400 / 401 / 403 / 409 / 422 |
| `GET /api/v2/offline-sync/{id}` | `:28-30` | részlet + `evidence`; idegen tenantnál 404-szerű `NOT_FOUND` |
| `PATCH /api/v2/offline-sync/{id}` | `:32-34` | `CommandRequest` + `expected_revision`; 200 / 409 / 422 |
| `POST /api/v2/offline-sync/{id}/confirm` | `:36-38` | `action="confirm"` kényszerítéssel delegál; 200 / 403 / 409 / 422 |

Hibák: `application/problem+json` (`:19`; modellek `:42-44`). Bekötés: `app/api_v2.py:21`, `:157`.

### Események

Nincs eseménybusz; automatikus feltöltés-újraindítás és konfliktus-érzékelés szerveroldalon nincs bekötve — a kliens (`OfflineQueue.tsx`) vezérli a sorrendet és az újrapróbálást (GAP).

### Adatmodell

- `OfflineReceiptDraft` (`app/offline_sync_models.py:31-40`): `id`, `tenant_id`, `status`, `revision`, `client_reference`, `data: dict`, `evidence: dict`, `created_at`, `updated_at`.
- `CreateRequest` (`:18-22`), `CommandRequest` (`:24-29`) — generikus alak.
- Hibák: `NotFoundError` 404 (`:48-49`), `StaleRevisionError` 409 (`:50-51`), `IdempotencyConflictError` 409 (`:52-53`).
- Tárolás: `OfflineReceiptDraftService._items` + `_keys`, `threading.RLock` (`app/offline_sync_service.py:7-9`); létrehozáskor `evidence={"source": "FEAT-045"}` (`:21`); migráció nincs. A képbináris nem a szerver-draftban tárolódik.

## 11. Acceptance scenario-k

### AC-045-01: offline rögzítés (REQ-045-01)

Given hálózat nélküli eszköz
When a felhasználó fényképez/fájlt ad hozzá metaadattal és megjegyzéssel
Then a piszkozat `LOCAL_ONLY` állapotban megőrződik, folytatható.

### AC-045-02: látható várólista (REQ-045-02)

Given vegyes állapotú piszkozatok
When a felhasználó a sort megnyitja
Then eszközön/várakozik/szinkronizálódott állapot egyértelműen látszik.

### AC-045-03: folytatható feltöltés (REQ-045-03)

Given `QUEUED` piszkozat és visszatérő kapcsolat
When a feltöltés folytatódik
Then a haladás folytatódik (nem indul elölről), siker esetén `SYNCED`.

### AC-045-04: izolált elemhiba (REQ-045-04)

Given több elemes sor egy hibás elemmel
When a hibás elem elutasítódik
Then a többi elem feldolgozása folytatódik; a hibás külön újrapróbálható.

### AC-045-05: konfliktus-összehasonlítás (REQ-045-05)

Given helyi és szerveroldali eltérő változat
When a felhasználó a konfliktust megnyitja
Then mindkét változat összehasonlítható, a választás explicit; csendes felülírás nincs.

### AC-045-06: tenant-határ (REQ-045-06)

Given A-tenantbeli draft és tenantváltás B-re
When szinkron indulna
Then A adata nem szinkronizálódik B háztartásába; idegen azonosítóra 404-szerű válasz.

### AC-045-07: idempotens szinkron (REQ-045-07)

Given draft `Idempotency-Key`-jel
When a szinkron megismétlődik (azonos payload)
Then új nyugta nem duplikálódik; eltérő payloadra 409.

### AC-045-08: túlélés és figyelmeztetés (REQ-045-08 + US-045-06/US-045-10)

Given háttérbe helyezés/bezárás/újraindítás
When az alkalmazás visszatér
Then a piszkozat és az előrehaladás megmarad; fel nem töltött adat birtokában kritikus művelet előtt figyelmeztetés jelenik meg. (Eszköz-oldali perzisztenciára lásd GAP.)

## 12. Tesztleképezés

| REQ | AC | E2E-teszt (fájl:sor) | GUI | Unit-cél (státusz) |
| :--- | :--- | :--- | :--- | :--- |
| REQ-045-01 | AC-045-01 | `test_e2e_045_ac_01_positive_path` (`.agent-pipeline/03_e2e_suites/test_e2e_045.py:24`) | `gui_e2e_045_048_offline_mobile.spec.ts` | `tests/unit/test_offline_sync_service.py::test_req_045_01` — HIÁNYZIK |
| REQ-045-02 | AC-045-02 | `test_e2e_045_ac_02_contract_state` (`test_e2e_045.py:29`) | ugyanaz | `...::test_req_045_02` — HIÁNYZIK |
| REQ-045-03 | AC-045-03 | `test_e2e_045_ac_03_invalid_payload_is_safe` (`test_e2e_045.py:33`) | ugyanaz | `...::test_req_045_03` — HIÁNYZIK |
| REQ-045-04 | AC-045-04 | `test_e2e_045_ac_04_detail_contract` (`test_e2e_045.py:37`) | ugyanaz | `...::test_req_045_04` — HIÁNYZIK |
| REQ-045-05 | AC-045-05 | `test_e2e_045_ac_05_no_silent_success` (`test_e2e_045.py:41`) | ugyanaz | `...::test_req_045_05` — HIÁNYZIK |
| REQ-045-06 | AC-045-06 | `test_e2e_045_ac_06_tenant_and_auth_isolation` (`test_e2e_045.py:45`) | ugyanaz | `...::test_req_045_06` — HIÁNYZIK |
| REQ-045-07 | AC-045-07 | `test_e2e_045_ac_07_idempotent_retry` (`test_e2e_045.py:50`) | ugyanaz | `...::test_req_045_07` — HIÁNYZIK |
| REQ-045-08 | AC-045-08 | `test_e2e_045_ac_08_concurrent_revision` (`test_e2e_045.py:58`) | ugyanaz | `...::test_req_045_08` — HIÁNYZIK |

E2E-eredmény: 8/8 PASS (2026-08-31 jelentés). Unit-célok nem léteznek — SPEC-GAP-045-04.

## 13. Kockázatok és emberi döntések

- HR-045-01: adatvesztés (fel nem töltött piszkozat elveszik) — ezért a túlélési garancia és a kritikus művelet előtti figyelmeztetés kötelező; az eszköz-oldali tárolókorlát a BRIEF non-scope-ja, de a figyelmeztetés nem.
- HR-045-02: csendes felülírás konfliktuskor — a kétváltozatos összehasonlítás és az explicit választás kötelező.
- Adatvédelem: képbináris nem kerülhet hibaválaszba/naplóba; tenantváltáskor a sor nem szivároghat át.

## 14. Nyitott kérdések és SPEC-GAP

Nincs implementációt blokkoló nyitott kérdés (kód szállítva, E2E zöld).

SPEC-GAP (a BRIEF többet állít, mint a kód):

- SPEC-GAP-045-01: US-045-01/US-045-02/US-045-06 szerinti eszköz-oldali tartós tárolás (képbináris, piszkozat-túlélés újraindítás után) **szerveroldalon nem értelmezhető**; a szerver a draft-életutat tartja nyilván, a perzisztencia kliens-felelősség (`OfflineQueue.tsx`).
- SPEC-GAP-045-02: US-045-04 szerinti automatikus feltöltés-folytatás és US-045-05 szerinti Wi-Fi-korlát kikényszerítése szerveroldalon nincs; a kliens vezérli.
- SPEC-GAP-045-03: a `QUEUED`→`UPLOADING`→`PROCESSING`→`SYNCED` életút és a `CONFLICT` feloldás nem gépi átmenet a szerveren (a generikus leképezés nem éri el őket); US-045-10 szerinti figyelmeztetés kliens-felelősség.
- SPEC-GAP-045-04: az előd pipeline-spec unit-céljai (`tests/unit/test_offline_sync_service.py`) **nem léteznek**; elsődleges bizonyíték az E2E-suite.

## 15. Rollback és megfigyelhetőség

- Rollback: migráció nincs; folyamat-memória — újraindítás a draft-életutakat törli (a kliens helyi sora ettől független). Visszaállítás telepítéssel, adatmigráció nélkül.
- Megfigyelhetőség: `application/problem+json` `correlation_id`-val; válaszokban tenant- és revízió-azonosító. Feltöltési throughput-metrika és konfliktus-napló nincs.

## 16. Definition of Done

- [x] mind a 8 REQ-hez AC és E2E-teszt (8/8 PASS, 2026-08-31).
- [x] célzott E2E + GUI-suite zöld a jelentés szerint.
- [ ] unit-célok pótlása — nyitott (SPEC-GAP-045-04).
- [ ] SPEC-GAP-045-01 termékdöntése (kliens-perzisztencia szerződése).
- [x] visszamutatás BRIEF-045 ↔ SPEC-045 ↔ kód ↔ tesztek (`docs/traceability-index.md`).
- [x] production kód nem változott (docs-only).
