---
id: FEAT-041
title: Háztartási bevásárlási árfigyelés
status: ready_for_dev
version: 1
risk: low
owner: documenter
related_brief: BRIEF-041
---

# FEAT-041: Háztartási bevásárlási árfigyelés

> Visszamenőleges (kód→spec) specifikáció. A megvalósítás már szállítva;
> ez a dokumentum a tényleges kódviselkedést rögzíti a VERITAS 1.1 §4.5
> 16-fejezetes szerkezetében. Ahol a BRIEF többet állít, azt a 14. fejezet
> SPEC-GAP listája jelöli.

## 1. Cél és felhasználói eredmény

A felhasználó az ismétlődően vásárolt termékek árát követi: a rendszer
jelölteket javasol, a hasonló neveket összevonhatja/szétválaszthatja, az
ártrend forrásmegfigyelésekkel látható, a szokatlan drágulás jelzést ad,
a becslés pedig soha nem jelenik meg tényként. Kevés vagy bizonytalan
adat esetén a rendszer ezt jelzi, nem ad túl magabiztos állítást.

Mérhető készültségi feltétel: mind a 8 REQ-hez tartozik AC-scenario és
végrehajtható E2E-teszt (`.agent-pipeline/03_e2e_suites/test_e2e_041.py`,
8/8 PASS a 2026-08-31 verifikáció szerint).

## 2. Kontextus és források

Kanonikus források:

- `briefs/BRIEF-041-haztartasi-bevasarlasi-arfigyeles.md` (9 US: US-041-01..US-041-09)
- `VERITAS_1_1_adaptiv_egyseges_fejlesztesi_modszertan.md` §4.5
- `05_docs/2026-08-31-phase2-feat038-048-verification-report.md`
- `.agent-pipeline/02_specs/done/SPEC-041-haztartasi-bevasarlasi-arfigyeles.md` (előd pipeline-spec)

Kódforrások (leltár):

- `app/price_tracking_api.py` — router + 5 route (`:8` prefix `/api/v2/price-tracking`; route-ok `:21`, `:24`, `:28`, `:32`, `:36-38`)
- `app/price_tracking_models.py` — `Status` (`:8-13`), `CreateRequest` (`:15-19`), `CommandRequest` (`:21-27`), `TrackedProduct` (`:28-37`), hibák (`:42-49`)
- `app/price_tracking_service.py` — `TrackedProductService` (`:7`), kezdő `CANDIDATE` (`:21`), action-leképezés (`:32`)
- `app/api_v2.py` — bekötés (`:17` import, `:153` include_router)

Kapcsolódó domain-invariánsok: tenant-izoláció, bizonytalanság jelzése
(becslés ≠ tény), felhasználói felülbírálhatóság, deduplikált riasztás,
idempotens elemzési futás.

## 3. Scope és non-scope

### Benne van

- Követett termék-jelölt létrehozása, listája, részlete, revíziózott módosítása és confirm-útja.
- Alias-összevonás/szétválasztás, egységár-normalizálás, kizárások és küszöb-felülbírálat adata a szabad `data` payloadban.
- Trend- és riasztás-nyilvántartás a `Status` sémával (lásd 9. fejezet).
- Tenant-izoláció, idempotencia, optimistic locking, `application/problem+json` hibák.

### Nincs benne

- Nyugtatételből jelöltet képező, egységárat számító és trendet aggregáló motor a szerveren — lásd SPEC-GAP-041-01.
- Külső ár-összehasonlító forrás vagy bolti árfigyelő integráció (a BRIEF non-scope-ja is a háztartási vásárlási múltra szorítkozik).
- Perzisztens tárolás: folyamat-memória (lásd 10. és 15. fejezet).

## 4. Szereplők és előfeltételek

- ACT-041-01: felhasználó (jelöltet jóváhagy, aliast rendez, küszöböt bírál felül, kizár).
- ACT-041-02: háztartási tag (közös követett termékeket néz).

- PRE-041-01: érvényes `Authorization` + `X-Tenant-ID` (különben 401 — `app/price_tracking_api.py:10-13`).
- PRE-041-02: `X-Role` ∈ {admin, owner, member, accountant} (különben 403).
- PRE-041-03: módosításhoz `Idempotency-Key` (min. 16 karakter, különben 422 — `:15-17`).
- PRE-041-04: állapotváltáshoz ismert `expected_revision` (különben 409).

## 5. Funkcionális követelmények

- REQ-041-01 [MUST]: A rendszer követhető termékjelölteket képez nyugtatételekből.
- REQ-041-02 [MUST]: A felhasználó aliasokat összevonhat vagy szétválaszthat.
- REQ-041-03 [MUST]: Kompatibilis mennyiségek egységárra normalizálhatók.
- REQ-041-04 [MUST]: A trend forrásmegfigyelésekkel és mintanagysággal látható.
- REQ-041-05 [MUST]: Szokatlan drágulás csak megfelelő adat és küszöb esetén jelezhető.
- REQ-041-06 [MUST]: Más tenant termék- és ártörténete nem hozzáférhető.
- REQ-041-07 [MUST]: Azonos elemzési futás nem duplikál riasztást.
- REQ-041-08 [MUST]: Felhasználói kizárás után a trend konzisztensen újraszámolódik.

## 6. Nem funkcionális követelmények

- NFR-041-01 [PERFORMANCE]: trend-nézet UI-visszajelzése 500 ms-on belül; nagy tételtörténet lapozható marad.
- NFR-041-02 [ACCESSIBILITY]: a trend és a riasztás billentyűzettel elérhető; árváltozás-jelzés bejelentett.
- NFR-041-03 [SECURITY]: szerveroldali `context()` az autoritatív; csak a 4 engedélyezett szerep.
- NFR-041-04 [PRIVACY]: más háztartás vásárlási múltja nem jelenhet meg; hibaválasz minimális adatot hordoz.
- NFR-041-05 [RELIABILITY]: bizonytalan adat nem jelenhet meg tényként; idegen tenant azonosítóra 404-szerű válasz.

## 7. UI-szerződés

- UI-041-01: `frontend/app/price-tracking/page.tsx` — követett termékek listája trenddel (legutóbbi/tipikus/legalacsonyabb ár), forrásnyugtákkal (US-041-04, US-041-06).
- UI-041-02: ugyanott alias-összevonó/szétválasztó (US-041-02), egységár-kapcsoló (US-041-03), kizárás-kezelő (US-041-07), küszöb-felülbíráló (US-041-08), kevés-adat jelzés (US-041-09).
- UI-041-03: E2E GUI-lefedés: `frontend/e2e/gui_e2e_040_041_warranties_prices.spec.ts`.

## 8. Felhasználói és GUI-folyamat

1. A felhasználó megnyitja a `/price-tracking` oldalt; a rendszer az aktív tenant követett termékeit listázza (`GET /api/v2/price-tracking`), jelöltekkel (`CANDIDATE`).
2. A hasonló termékneveket jóváhagyja, összevonja vagy szétválasztja (`PATCH .../{id}`).
3. Eltérő kiszereléseknél egységár-nézetet kapcsol; az akciós/kuponos/hibás/nem összehasonlítható vásárlást kizárja — a trend újraszámolódik.
4. A trend időbeli alakulása a legutóbbi, tipikus és korábbi legalacsonyabb árral, alátámasztó nyugtákkal és mintanagysággal látszik.
5. Szokatlan drágulás csak megfelelő adat és küszöb esetén jelez; kevés/bizonytalan adatnál "nem megállapítható" jelzés látszik.
6. Hiba esetén a felület a beállításokat megőrzi, újrapróbálást kínál, téves riasztás nem marad.

## 9. Állapotmodell

Tényleges gépi állapotok (`app/price_tracking_models.py:8-13`):

- `CANDIDATE` (kezdő — `app/price_tracking_service.py:21`), `TRACKED`, `NEEDS_REVIEW`, `PAUSED`, `ARCHIVED`.

Megfigyelt átmenetek (`app/price_tracking_service.py:32`):

- `confirm` → `PAUSED`; `reject` → `ARCHIVED`; `resolve` → `PAUSED`; `reopen` → `CANDIDATE`.
- Feltétel: `expected_revision` egyezik, különben 409 írás nélkül.
- Megjegyzés: a jelölt→követett, riasztási és kizárási szemantika a `data` payloadban él; a generikus leképezés nem számol trendet (lásd GAP).

## 10. API-, esemény- és adatszerződés

### REST (mind `app/price_tracking_api.py`)

| Route | Kódhely | Szerződés |
| :--- | :--- | :--- |
| `GET /api/v2/price-tracking` | `:21-22` | tenant-szűrt lista; 200 / 401 / 403 |
| `POST /api/v2/price-tracking` | `:24-26` | `CreateRequest`; kötelező `Idempotency-Key`; 201 / 400 / 401 / 403 / 409 / 422 |
| `GET /api/v2/price-tracking/{id}` | `:28-30` | részlet + `evidence`; idegen tenantnál 404-szerű `NOT_FOUND` |
| `PATCH /api/v2/price-tracking/{id}` | `:32-34` | `CommandRequest` + `expected_revision`; 200 / 409 / 422 |
| `POST /api/v2/price-tracking/{id}/confirm` | `:36-38` | `action="confirm"` kényszerítéssel delegál; 200 / 403 / 409 / 422 |

Hibák: `application/problem+json` (`:19`; modellek `:39-41`). Bekötés: `app/api_v2.py:17`, `:153`.

### Események

Nincs eseménybusz; árelemző-futás és riasztás-deduplikáció szerveroldalon nincs bekötve (GAP).

### Adatmodell

- `TrackedProduct` (`app/price_tracking_models.py:28-37`): `id`, `tenant_id`, `status`, `revision`, `client_reference`, `data: dict`, `evidence: dict`, `created_at`, `updated_at`.
- `CreateRequest` (`:15-19`), `CommandRequest` (`:21-27`) — generikus alak.
- Hibák: `NotFoundError` 404 (`:45-46`), `StaleRevisionError` 409 (`:47-48`), `IdempotencyConflictError` 409 (`:49-50`).
- Tárolás: `TrackedProductService._items` + `_keys`, `threading.RLock` (`app/price_tracking_service.py:7-9`); létrehozáskor `evidence={"source": "FEAT-041"}` (`:21`); migráció nincs.

## 11. Acceptance scenario-k

### AC-041-01: jelöltképzés és jóváhagyás (REQ-041-01)

Given nyugtatételek ismétlődő termékkel
When a rendszer jelöltet képez és a felhasználó jóváhagyja
Then a termék követetté válik (`TRACKED` szemantika), a döntés visszakereshető.

### AC-041-02: alias-rendezés és egységár (REQ-041-02, REQ-041-03)

Given hasonló nevek / eltérő kiszerelések
When a felhasználó összevon/szétválaszt, egységár-nézetet kapcsol
Then az összehasonlítás torzításmentes, a beállítás megmarad.

### AC-041-03: trend evidenciával (REQ-041-04)

Given elegendő megfigyelés
When a felhasználó a trendet megnyitja
Then legutóbbi/tipikus/legalacsonyabb ár, alátámasztó nyugták és mintanagyság látszik.

### AC-041-04: drágulás-jelzés küszöbbel (REQ-041-05)

Given megfelelő adat és beállított küszöb
When szokatlan drágulás történik
Then jelzés érkezik; kevés/bizonytalan adatnál "nem megállapítható" jelzés, tényállítás nélkül.

### AC-041-05: tenant-izoláció (REQ-041-06)

Given B-tenantbeli termék-azonosító
When A-tenant kéri/módosítja
Then 404-szerű válasz, ártörténet-szivárgás nélkül.

### AC-041-06: deduplikált elemzési futás (REQ-041-07)

Given elemzési futás `Idempotency-Key`-jel
When a futás megismétlődik (azonos payload)
Then új riasztás nem duplikálódik; eltérő payloadra 409.

### AC-041-07: kizárás utáni újraszámolás (REQ-041-08)

Given kizárt (akciós/kuponos/hibás) vásárlás
When a felhasználó kizárja
Then a trend konzisztensen újraszámolódik, a kizárás visszakereshető.

### AC-041-08: hiba nem siker (összes REQ)

Given érvénytelen payload / auth-hiba / elavult revízió
When a művelet fut
Then `application/problem+json` hiba, részleges írás nélkül.

## 12. Tesztleképezés

| REQ | AC | E2E-teszt (fájl:sor) | GUI | Unit-cél (státusz) |
| :--- | :--- | :--- | :--- | :--- |
| REQ-041-01 | AC-041-01 | `test_e2e_041_ac_01_positive_path` (`.agent-pipeline/03_e2e_suites/test_e2e_041.py:24`) | `gui_e2e_040_041_warranties_prices.spec.ts` | `tests/unit/test_price_tracking_service.py::test_req_041_01` — HIÁNYZIK |
| REQ-041-02 | AC-041-02 | `test_e2e_041_ac_02_contract_state` (`test_e2e_041.py:29`) | ugyanaz | `...::test_req_041_02` — HIÁNYZIK |
| REQ-041-03 | AC-041-02 | `test_e2e_041_ac_03_invalid_payload_is_safe` (`test_e2e_041.py:33`) | ugyanaz | `...::test_req_041_03` — HIÁNYZIK |
| REQ-041-04 | AC-041-03 | `test_e2e_041_ac_04_detail_contract` (`test_e2e_041.py:37`) | ugyanaz | `...::test_req_041_04` — HIÁNYZIK |
| REQ-041-05 | AC-041-04 | `test_e2e_041_ac_05_no_silent_success` (`test_e2e_041.py:41`) | ugyanaz | `...::test_req_041_05` — HIÁNYZIK |
| REQ-041-06 | AC-041-05 | `test_e2e_041_ac_06_tenant_and_auth_isolation` (`test_e2e_041.py:45`) | ugyanaz | `...::test_req_041_06` — HIÁNYZIK |
| REQ-041-07 | AC-041-06 | `test_e2e_041_ac_07_idempotent_retry` (`test_e2e_041.py:50`) | ugyanaz | `...::test_req_041_07` — HIÁNYZIK |
| REQ-041-08 | AC-041-07 | `test_e2e_041_ac_08_concurrent_revision` (`test_e2e_041.py:58`) | ugyanaz | `...::test_req_041_08` — HIÁNYZIK |

E2E-eredmény: 8/8 PASS (2026-08-31 jelentés). Unit-célok nem léteznek — SPEC-GAP-041-04.

## 13. Kockázatok és emberi döntések

- HR-041-01: félrevezető trend téves vásárlási döntéshez vezet — ezért a kizárás, a mintanagyság-jelzés és a "nem megállapítható" állapot kötelező; a küszöb felülbírálata felhasználói hatáskör.
- HR-041-02: márka/kiszerelés-összemosás torzít — az alias-döntés visszavonható kell legyen (kliens-felelősség).
- Adatvédelem: más háztartás ártörténete tenant-határon nem jelenhet meg.

## 14. Nyitott kérdések és SPEC-GAP

Nincs implementációt blokkoló nyitott kérdés (kód szállítva, E2E zöld).

SPEC-GAP (a BRIEF többet állít, mint a kód):

- SPEC-GAP-041-01: US-041-01 szerinti tétel→jelölt képzés, US-041-03 szerinti egységár-normalizálás, US-041-04 szerinti trend-aggregálás (legutóbbi/tipikus/minimum + mintanagyság) és US-041-05 szerinti küszöbös riasztás **egyike sincs a szerverkódban**; a számítás kliens/`data` eredetű, validáció nélkül.
- SPEC-GAP-041-02: US-041-07 szerinti kizárás utáni szerveroldali újraszámolás **nincs implementálva**; a konzisztencia kliens-felelősség.
- SPEC-GAP-041-03: US-041-08 szerinti termékazonosítás/riasztási-küszöb felülbírálatának szerveroldali érvényesítése nincs; a `data` sémázatlan.
- SPEC-GAP-041-04: az előd pipeline-spec unit-céljai (`tests/unit/test_price_tracking_service.py`) **nem léteznek**; elsődleges bizonyíték az E2E-suite.

## 15. Rollback és megfigyelhetőség

- Rollback: migráció nincs; folyamat-memória — újraindítás a követett termékeket törli. Visszaállítás telepítéssel, adatmigráció nélkül.
- Megfigyelhetőség: `application/problem+json` `correlation_id`-val; válaszokban tenant- és revízió-azonosító. Trendelemzési napló és riasztási metrika nincs.

## 16. Definition of Done

- [x] mind a 8 REQ-hez AC és E2E-teszt (8/8 PASS, 2026-08-31).
- [x] célzott E2E + GUI-suite zöld a jelentés szerint.
- [ ] unit-célok pótlása — nyitott (SPEC-GAP-041-04).
- [ ] SPEC-GAP-041-01/02 termékdöntése (elemző- és riasztó-motor helye).
- [x] visszamutatás BRIEF-041 ↔ SPEC-041 ↔ kód ↔ tesztek (`docs/traceability-index.md`).
- [x] production kód nem változott (docs-only).
