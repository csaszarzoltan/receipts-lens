---
id: FEAT-043
title: Megosztott vásárlások és költségfelosztás
status: ready_for_dev
version: 1
risk: medium
owner: documenter
related_brief: BRIEF-043
---

# FEAT-043: Megosztott vásárlások és költségfelosztás

> Visszamenőleges (kód→spec) specifikáció. A megvalósítás már szállítva;
> ez a dokumentum a tényleges kódviselkedést rögzíti a VERITAS 1.1 §4.5
> 16-fejezetes szerkezetében. Ahol a BRIEF többet állít, azt a 14. fejezet
> SPEC-GAP listája jelöli.

## 1. Cél és felhasználói eredmény

A felhasználó egy nyugta vagy tranzakció összegét több részre osztja
(fix, százalékos, egyenlő vagy tételalapú módszerrel), a részeket
személyhez/csoporthoz/kategóriához/projekthez rendeli, mentés előtt látja
az összeg-egyezést, a kerekítési maradványt explicit kezeli, a résztvevő
jóváhagyhat vagy vitathat, a módosítás pedig visszakereshető marad. A
riportok és exportok az eredetit és a részeket kettős számolás nélkül
mutatják.

Mérhető készültségi feltétel: mind a 8 REQ-hez tartozik AC-scenario és
végrehajtható E2E-teszt (`.agent-pipeline/03_e2e_suites/test_e2e_043.py`,
8/8 PASS a 2026-08-31 verifikáció szerint).

## 2. Kontextus és források

Kanonikus források:

- `briefs/BRIEF-043-megosztott-vasarlasok-es-koltsegfelosztas.md` (9 US: US-043-01..US-043-09)
- `VERITAS_1_1_adaptiv_egyseges_fejlesztesi_modszertan.md` §4.5
- `05_docs/2026-08-31-phase2-feat038-048-verification-report.md`
- `.agent-pipeline/02_specs/done/SPEC-043-megosztott-vasarlasok-es-koltsegfelosztas.md` (előd pipeline-spec)

Kódforrások (leltár):

- `app/cost_split_api.py` — router + 5 route (`:8` prefix `/api/v2/cost-splits`; route-ok `:21`, `:24`, `:28`, `:32`, `:36-38`)
- `app/cost_split_models.py` — `Status` (`:8-14`), `CreateRequest` (`:16-20`), `CommandRequest` (`:22-27`), `CostSplit` (`:29-38`), hibák (`:43-50`)
- `app/cost_split_service.py` — `CostSplitService` (`:7`), kezdő `DRAFT` (`:21`), action-leképezés (`:32`)
- `app/api_v2.py` — bekötés (`:19` import, `:155` include_router)

Kapcsolódó domain-invariánsok: tenant-izoláció, összeg-konzisztencia
(részek = forrás), explicit kerekítés-kezelés, rejtett kötelezettség
tilalma (résztvevő látja/jóváhagyja), verziózott módosítás, kettős
számolás tilalma riportokban.

## 3. Scope és non-scope

### Benne van

- Felosztás létrehozása, listája, részlete, revíziózott módosítása és confirm-útja.
- Módszer (fix/százalék/egyenlő/tétel), kedvezményezettek, kerekítési maradvány-viselő és sablon-hivatkozás a szabad `data` payloadban.
- Résztvevői jóváhagyás/vita szemantikája a `Status` sémában (lásd 9. fejezet).
- Tenant-izoláció, idempotencia, optimistic locking, `application/problem+json` hibák.

### Nincs benne

- Pénz automatikus beszedése/átutalása résztvevők között; követeléskezelő/adósságbehajtó rendszer (a BRIEF non-scope-ja is kizárja).
- Összeg-egyezés és kerekítés szerveroldali validációja — lásd SPEC-GAP-043-01.
- Perzisztens tárolás: folyamat-memória (lásd 10. és 15. fejezet).

## 4. Szereplők és előfeltételek

- ACT-043-01: felhasználó (feloszt, kedvezményezettet rendel, kerekítést kezel, módosít).
- ACT-043-02: érintett háztartási tag (részét látja, jóváhagyja vagy vitatja).

- PRE-043-01: érvényes `Authorization` + `X-Tenant-ID` (különben 401 — `app/cost_split_api.py:10-13`).
- PRE-043-02: `X-Role` ∈ {admin, owner, member, accountant} (különben 403).
- PRE-043-03: módosításhoz `Idempotency-Key` (min. 16 karakter, különben 422 — `:15-17`).
- PRE-043-04: módosításhoz ismert `expected_revision` (különben 409).

## 5. Funkcionális követelmények

- REQ-043-01 [MUST]: A vásárlás fix, százalékos, egyenlő vagy tételes módon felosztható.
- REQ-043-02 [MUST]: A részek összege pontosan a forrásösszeggel egyezik.
- REQ-043-03 [MUST]: A kerekítési maradvány explicit módon kezelhető.
- REQ-043-04 [MUST]: A résztvevő jóváhagyhat vagy vitathat.
- REQ-043-05 [MUST]: A módosítás verziózott és auditálható.
- REQ-043-06 [MUST]: Más tenant kedvezményezettje vagy forrása nem használható.
- REQ-043-07 [MUST]: Azonos mentési kérés egy felosztást eredményez.
- REQ-043-08 [MUST]: Riport és export nem számolja kétszer az eredetit és részeit.

## 6. Nem funkcionális követelmények

- NFR-043-01 [PERFORMANCE]: felosztó-nézet és összeg-egyezés UI-visszajelzése 500 ms-on belül.
- NFR-043-02 [ACCESSIBILITY]: a felosztás és a jóváhagyás billentyűzettel végigvihető; összeg-állapot bejelentett.
- NFR-043-03 [SECURITY]: szerveroldali `context()` az autoritatív; csak a 4 engedélyezett szerep.
- NFR-043-04 [PRIVACY]: külső költségviselő adata csak hozzájárulással/meghívással kezelhető; hibaválasz minimális.
- NFR-043-05 [RELIABILITY]: sikertelen mentés nem hagy félig felosztott állapotot; idegen tenant azonosítóra 404-szerű válasz.

## 7. UI-szerződés

- UI-043-01: `frontend/app/cost-splits/page.tsx` — felosztó-nézet módszer-választóval (US-043-02), kedvezményezett-rendeléssel (US-043-03), összeg-egyezés jelzéssel (US-043-04), kerekítés-viselő választóval (US-043-05), sablon-használattal (US-043-06).
- UI-043-02: ugyanott résztvevői jóváhagyó/vitató felület (US-043-07), verzió-előzmény (US-043-08), kettős-számolás mentes riport-nézet (US-043-09).
- UI-043-03: E2E GUI-lefedés: `frontend/e2e/gui_e2e_043_044_split_goals.spec.ts`.

## 8. Felhasználói és GUI-folyamat

1. A felhasználó megnyitja a `/cost-splits` oldalt, és egy nyugtához/tranzakcióhoz felosztást hoz létre (`POST /api/v2/cost-splits`).
2. Módszert választ (fix/százalék/egyenlő/tétel), részeket és kedvezményezetteket rendel; mentés előtt az összeg-egyezést látja.
3. A kerekítési maradvány viselőjét kiválasztja; a felület a konzisztenciát jelzi.
4. Ismétlődő vásárlásnál korábbi felosztást sablonként tölt be.
5. Az érintett tag a részét látja, jóváhagyja vagy vitatja (`PATCH .../{id}` / `POST .../{id}/confirm`).
6. Későbbi módosítás új verziót hoz; a korábbi állapot visszakereshető.
7. A riport/export az eredetit és a részeket kettős számolás nélkül mutatja.
8. Hiba esetén a felület a bevitelet megőrzi, újrapróbálást kínál, hiány/túlosztás nem mentődik csendben.

## 9. Állapotmodell

Tényleges gépi állapotok (`app/cost_split_models.py:8-14`):

- `DRAFT` (kezdő — `app/cost_split_service.py:21`), `PENDING_APPROVAL`, `APPROVED`, `DISPUTED`, `SUPERSEDED`, `CANCELLED`.

Megfigyelt átmenetek (`app/cost_split_service.py:32`):

- `confirm` → `SUPERSEDED`; `reject` → `CANCELLED`; `resolve` → `SUPERSEDED`; `reopen` → `DRAFT`.
- Feltétel: `expected_revision` egyezik, különben 409 írás nélkül.
- Megjegyzés: a `PENDING_APPROVAL`/`APPROVED`/`DISPUTED` célállapotok a sémában léteznek, de a generikus leképezés közvetlenül nem állítja be őket — a jóváhagyás/vita szemantikája a `data` payloadban él (lásd GAP).

## 10. API-, esemény- és adatszerződés

### REST (mind `app/cost_split_api.py`)

| Route | Kódhely | Szerződés |
| :--- | :--- | :--- |
| `GET /api/v2/cost-splits` | `:21-22` | tenant-szűrt lista; 200 / 401 / 403 |
| `POST /api/v2/cost-splits` | `:24-26` | `CreateRequest`; kötelező `Idempotency-Key`; 201 / 400 / 401 / 403 / 409 / 422 |
| `GET /api/v2/cost-splits/{id}` | `:28-30` | részlet + `evidence`; idegen tenantnál 404-szerű `NOT_FOUND` |
| `PATCH /api/v2/cost-splits/{id}` | `:32-34` | `CommandRequest` + `expected_revision`; 200 / 409 / 422 |
| `POST /api/v2/cost-splits/{id}/confirm` | `:36-38` | `action="confirm"` kényszerítéssel delegál; 200 / 403 / 409 / 422 |

Hibák: `application/problem+json` (`:19`; modellek `:40-42`). Bekötés: `app/api_v2.py:19`, `:155`.

### Események

Nincs eseménybusz; résztvevő-értesítés szerveroldalon nincs bekötve (GAP).

### Adatmodell

- `CostSplit` (`app/cost_split_models.py:29-38`): `id`, `tenant_id`, `status`, `revision`, `client_reference`, `data: dict`, `evidence: dict`, `created_at`, `updated_at`.
- `CreateRequest` (`:16-20`), `CommandRequest` (`:22-27`) — generikus alak.
- Hibák: `NotFoundError` 404 (`:46-47`), `StaleRevisionError` 409 (`:48-49`), `IdempotencyConflictError` 409 (`:50-51`).
- Tárolás: `CostSplitService._items` + `_keys`, `threading.RLock` (`app/cost_split_service.py:7-9`); létrehozáskor `evidence={"source": "FEAT-043"}` (`:21`); migráció nincs.

## 11. Acceptance scenario-k

### AC-043-01: felosztás négy módszerrel (REQ-043-01)

Given vásárlás ismert forrásösszeggel
When a felhasználó fix/százalékos/egyenlő/tételalapú felosztást készít
Then a részek kedvezményezettekhez rendelve létrejönnek `DRAFT` állapotban.

### AC-043-02: összeg-egyezés és kerekítés (REQ-043-02, REQ-043-03)

Given készülő felosztás
When a felhasználó mentés előtt ellenőrzi
Then a részek összege pontosan a forrásösszeg; a maradvány explicit viselőnél van; hiány/túlosztás nem menthető. (Szervervalidációra lásd GAP.)

### AC-043-03: jóváhagyás/vita (REQ-043-04)

Given érintett tag része
When a tag jóváhagy vagy vitat
Then a döntés rögzül, rejtett kötelezettség nem keletkezik.

### AC-043-04: verziózott módosítás (REQ-043-05)

Given jóváhagyott felosztás
When a felhasználó módosítja
Then új verzió jön létre, a korábbi állapot visszakereshető (`reason` + revízió).

### AC-043-05: tenant-izoláció (REQ-043-06)

Given B-tenantbeli forrás/kedvezményezett
When A-tenant felosztásban használná
Then 404-szerű válasz, kereszt-tenant hivatkozás nélkül.

### AC-043-06: idempotens mentés (REQ-043-07)

Given mentési kérés `Idempotency-Key`-jel
When a kérés megismétlődik (azonos payload)
Then egy felosztás létezik; eltérő payloadra 409.

### AC-043-07: kettős számolás tilalma (REQ-043-08)

Given felosztott vásárlás
When riport/export készül
Then az eredeti és a részek összege nem duplázódik. (Kliens/riport-felelősség; lásd GAP.)

### AC-043-08: hiba nem siker (összes REQ)

Given érvénytelen payload / auth-hiba / elavult revízió
When a művelet fut
Then `application/problem+json` hiba, részleges felosztás nélkül.

## 12. Tesztleképezés

| REQ | AC | E2E-teszt (fájl:sor) | GUI | Unit-cél (státusz) |
| :--- | :--- | :--- | :--- | :--- |
| REQ-043-01 | AC-043-01 | `test_e2e_043_ac_01_positive_path` (`.agent-pipeline/03_e2e_suites/test_e2e_043.py:24`) | `gui_e2e_043_044_split_goals.spec.ts` | `tests/unit/test_cost_splits_service.py::test_req_043_01` — HIÁNYZIK |
| REQ-043-02 | AC-043-02 | `test_e2e_043_ac_02_contract_state` (`test_e2e_043.py:29`) | ugyanaz | `...::test_req_043_02` — HIÁNYZIK |
| REQ-043-03 | AC-043-02 | `test_e2e_043_ac_03_invalid_payload_is_safe` (`test_e2e_043.py:33`) | ugyanaz | `...::test_req_043_03` — HIÁNYZIK |
| REQ-043-04 | AC-043-03 | `test_e2e_043_ac_04_detail_contract` (`test_e2e_043.py:37`) | ugyanaz | `...::test_req_043_04` — HIÁNYZIK |
| REQ-043-05 | AC-043-04 | `test_e2e_043_ac_05_no_silent_success` (`test_e2e_043.py:41`) | ugyanaz | `...::test_req_043_05` — HIÁNYZIK |
| REQ-043-06 | AC-043-05 | `test_e2e_043_ac_06_tenant_and_auth_isolation` (`test_e2e_043.py:45`) | ugyanaz | `...::test_req_043_06` — HIÁNYZIK |
| REQ-043-07 | AC-043-06 | `test_e2e_043_ac_07_idempotent_retry` (`test_e2e_043.py:50`) | ugyanaz | `...::test_req_043_07` — HIÁNYZIK |
| REQ-043-08 | AC-043-07 | `test_e2e_043_ac_08_concurrent_revision` (`test_e2e_043.py:58`) | ugyanaz | `...::test_req_043_08` — HIÁNYZIK |

E2E-eredmény: 8/8 PASS (2026-08-31 jelentés). Unit-célok nem léteznek — SPEC-GAP-043-04.

## 13. Kockázatok és emberi döntések

- HR-043-01: hiány/túlosztás pénzügyi hibát okoz — ezért az összeg-egyezés mentés előtti ellenőrzése kötelező; szerveroldali őrzés bevezetése termékdöntés (GAP).
- HR-043-02: rejtett kötelezettség (tag nem látja a részét) bizalmi kockázat — a rész láthatósága és jóváhagyhatósága kötelező.
- Adatvédelem: külső költségviselő adata csak hozzájárulással/meghívással; más tenant forrása nem használható.

## 14. Nyitott kérdések és SPEC-GAP

Nincs implementációt blokkoló nyitott kérdés (kód szállítva, E2E zöld).

SPEC-GAP (a BRIEF többet állít, mint a kód):

- SPEC-GAP-043-01: US-043-04 szerinti összeg-egyezés, US-043-05 szerinti kerekítés- és US-043-09 szerinti kettős-számolás védelem **szerveroldali validációja nincs**; a `payload` sémázatlan, az ellenőrzés kliens-felelősség.
- SPEC-GAP-043-02: US-043-06 szerinti sablon-újrahasználat szerveroldali feloldása nincs; a sablon-hivatkozás `data`-szemantika.
- SPEC-GAP-043-03: US-043-07 szerinti jóváhagyás/vita nem gépi átmenet (a generikus leképezés nem éri el a `PENDING_APPROVAL`/`APPROVED`/`DISPUTED` állapotokat); US-043-08 szerinti verziótörténetnek nincs külön audit-táblája, csak revízió + `reason`.
- SPEC-GAP-043-04: az előd pipeline-spec unit-céljai (`tests/unit/test_cost_splits_service.py`) **nem léteznek**; elsődleges bizonyíték az E2E-suite.

## 15. Rollback és megfigyelhetőség

- Rollback: migráció nincs; folyamat-memória — újraindítás a felosztásokat törli. Visszaállítás telepítéssel, adatmigráció nélkül.
- Megfigyelhetőség: `application/problem+json` `correlation_id`-val; válaszokban tenant- és revízió-azonosító. Összeg-eltérés riasztás és verziónapló-végpont nincs.

## 16. Definition of Done

- [x] mind a 8 REQ-hez AC és E2E-teszt (8/8 PASS, 2026-08-31).
- [x] célzott E2E + GUI-suite zöld a jelentés szerint.
- [ ] unit-célok pótlása — nyitott (SPEC-GAP-043-04).
- [ ] SPEC-GAP-043-01 termékdöntése (szerveroldali összeg-őrzés).
- [x] visszamutatás BRIEF-043 ↔ SPEC-043 ↔ kód ↔ tesztek (`docs/traceability-index.md`).
- [x] production kód nem változott (docs-only).
