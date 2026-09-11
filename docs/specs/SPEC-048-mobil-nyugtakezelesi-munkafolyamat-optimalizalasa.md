---
id: FEAT-048
title: Mobil nyugtakezelési munkafolyamat optimalizálása
status: ready_for_dev
version: 1
risk: medium
owner: documenter
related_brief: BRIEF-048
---

# FEAT-048: Mobil nyugtakezelési munkafolyamat optimalizálása

> Visszamenőleges (kód→spec) specifikáció. A megvalósítás már szállítva;
> ez a dokumentum a tényleges kódviselkedést rögzíti a VERITAS 1.1 §4.5
> 16-fejezetes szerkezetében. Ahol a BRIEF többet állít, azt a 14. fejezet
> SPEC-GAP listája jelöli.

## 1. Cél és felhasználói eredmény

A mobilos felhasználó a kamerás nyugtarögzítést a lehető legkevesebb
döntéssel indítja, előnézet/újrafotózás/elfogadás után a kép lassú
kapcsolaton is ésszerűen, olvashatóan töltődik fel, az állapot
(várakozás/feltöltés/feldolgozás/ellenőrzésre-vár/siker/hiba)
nyugtánként követhető, a kép és a felismert adat kis képernyőn
összevethető, a bizonytalan mezők nagy célokkal és megfelelő
billentyűzettel javíthatók, a fő műveletek egy kézzel elérhetők, a
megszakítás (hálózatvesztés/hívás/zár/háttér/véletlen navigáció) nem
veszít munkát, a piszkozat félbehagyható és folytatható, a folyamat
képernyőolvasóval is végigvihető, a jóváhagyott nyugta azonnal
visszakereshető — és mindez valódi telefonméreteken E2E-vel ellenőrzött.

Mérhető készültségi feltétel: mind a 8 REQ-hez tartozik AC-scenario és
végrehajtható E2E-teszt (`.agent-pipeline/03_e2e_suites/test_e2e_048.py`,
8/8 PASS a 2026-08-31 verifikáció szerint).

## 2. Kontextus és források

Kanonikus források:

- `briefs/BRIEF-048-mobil-nyugtakezelesi-munkafolyamat-optimalizalasa.md` (13 US: US-048-01..US-048-13)
- `VERITAS_1_1_adaptiv_egyseges_fejlesztesi_modszertan.md` §4.5
- `05_docs/2026-08-31-phase2-feat038-048-verification-report.md`
- `.agent-pipeline/02_specs/done/SPEC-048-mobil-nyugtakezelesi-munkafolyamat-optimalizalasa.md` (előd pipeline-spec)

Kódforrások (leltár):

- `app/mobile_receipt_api.py` — router + 5 route (`:8` prefix `/api/v2/mobile-receipts`; route-ok `:21`, `:24`, `:28`, `:32`, `:36-38`)
- `app/mobile_receipt_models.py` — `Status` (`:8-16`), `CreateRequest` (`:18-22`), `CommandRequest` (`:24-29`), `MobileReceiptJourney` (`:31-40`), hibák (`:45-52`)
- `app/mobile_receipt_service.py` — `MobileReceiptJourneyService` (`:7`), kezdő `CAPTURING` (`:21`), action-leképezés (`:32`)
- `app/api_v2.py` — bekötés (`:24` import, `:160` include_router)
- `frontend/app/receipts/capture/page.tsx`, `frontend/components/mobile/MobileCaptureFlow.tsx`, `frontend/components/mobile/ThumbActionBar.tsx`, `frontend/components/MobileNav.tsx`

Kapcsolódó domain-invariánsok: tenant-izoláció, munka nem vész el
megszakításkor, idempotens resume/approve, bizonytalanság jelzése,
hozzáférhetőség (képernyőolvasó, egykezes), telefonméretű E2E-lefedés.

## 3. Scope és non-scope

### Benne van

- Mobil nyugta-életút (journey) létrehozása, listája, részlete, revíziózott állapotváltása és confirm-útja a rögzítés→feltöltés→feldolgozás→javítás→jóváhagyás→visszakeresés nyilvántartására.
- Kép/bináris-hivatkozás, tömörítési és adatforgalmi adat, mező-bizonytalanság, piszkozat-állapot és folytatási pont a szabad `data` payloadban.
- Capture/preview/retake/accept, kép-adat összevetés, mező-javítás, alsó műveletsáv, megszakítás-tűrés és képernyőolvasó-támogatás a kliensben.
- Tenant-izoláció, idempotencia, optimistic locking, `application/problem+json` hibák.

### Nincs benne

- Általános reszponzív navigáció (BRIEF-027 hatásköre); kötelező natív iOS/Android app, ha web/PWA teljesíti a célt; a BRIEF-045 szinkronmotor megismétlése; OCR-modell vagy párosítási logika újradefiniálása (a BRIEF non-scope-ja is kizárja).
- Képtömörítő és feltöltő motor a szerveren — a szerver az életutat tartja nyilván (lásd SPEC-GAP-048-01).
- Perzisztens szerver-tárolás: folyamat-memória (lásd 10. és 15. fejezet).

## 4. Szereplők és előfeltételek

- ACT-048-01: mobilos felhasználó (rögzít, előnéz, feltölt, összevet, javít, jóváhagy, visszakeres, piszkozatot folytat).
- ACT-048-02: képernyőolvasót használó mobilos felhasználó (ugyanaz érthető nevekkel és bejelentésekkel).
- ACT-048-03: termékfelelős (telefonméretű E2E-lefedést ellenőriz).

- PRE-048-01: érvényes `Authorization` + `X-Tenant-ID` a szerver-műveletekhez (különben 401 — `app/mobile_receipt_api.py:10-13`).
- PRE-048-02: `X-Role` ∈ {admin, owner, member, accountant} (különben 403).
- PRE-048-03: szerver-módosításhoz `Idempotency-Key` (min. 16 karakter, különben 422 — `:15-17`).
- PRE-048-04: állapotváltáshoz ismert `expected_revision` (különben 409).

## 5. Funkcionális követelmények

- REQ-048-01 [MUST]: A mobil kamerás rögzítés capture, preview, retake és accept lépésekkel működik.
- REQ-048-02 [MUST]: A feltöltési és feldolgozási állapot mobilon folytathatóan látható.
- REQ-048-03 [MUST]: A kép és felismert adat kis képernyőn gyorsan összevethető.
- REQ-048-04 [MUST]: A bizonytalan mezők nagy célterülettel és megfelelő billentyűzettel javíthatók.
- REQ-048-05 [MUST]: Hálózatvesztés vagy háttérbe helyezés nem veszít piszkozatot.
- REQ-048-06 [MUST]: A teljes folyamat képernyőolvasóval és egykezes elrendezéssel használható.
- REQ-048-07 [MUST]: Azonos resume vagy approve kérés nem duplikál nyugtát.
- REQ-048-08 [MUST]: Valódi telefonméretű E2E út lefedi a rögzítéstől a visszakeresésig tartó folyamatot.

## 6. Nem funkcionális követelmények

- NFR-048-01 [PERFORMANCE]: a rögzítés indítása azonnali (500 ms-on belüli UI-visszajelzés); nagy kép lassú kapcsolaton tömörítve, olvashatóan töltődik; az adatforgalmi hatás látható.
- NFR-048-02 [ACCESSIBILITY]: kamera, előrehaladás, bizonytalanság, mezőhiba és jóváhagyás képernyőolvasó-nevekkel és bejelentésekkel; nagy érintési célok; alsó műveletsáv egykezes eléréshez; billentyűzet nem takarja az aktív mezőt/mentést.
- NFR-048-03 [SECURITY]: szerveroldali `context()` az autoritatív; más tenant journey-azonosítója nem használható.
- NFR-048-04 [PRIVACY]: képbináris hibaválaszban/naplóban nem jelenhet meg; csak journey-azonosító és állapot.
- NFR-048-05 [RELIABILITY]: megszakítás (hálózat/hívás/zár/háttér/véletlen navigáció) után kép, javítások és folyamatállapot megmaradnak; resume/approve idempotens.

## 7. UI-szerződés

- UI-048-01: `frontend/app/receipts/capture/page.tsx` + `frontend/components/mobile/MobileCaptureFlow.tsx` — capture→preview→retake→accept (US-048-01, US-048-02), nyugtánkénti állapot (US-048-04), kép-adat összevető (US-048-05), bizonytalan-mező sorrend nagy célokkal (US-048-06).
- UI-048-02: `frontend/components/mobile/ThumbActionBar.tsx` + `frontend/components/MobileNav.tsx` — alsó műveletsáv (US-048-08), mobilbillentyűzet-kezelés (US-048-07), piszkozat-félbehagyás/folytatás (US-048-10), azonnali visszakeresés jóváhagyás után (US-048-12).
- UI-048-03: E2E GUI-lefedés telefonméreteken: `frontend/e2e/gui_e2e_045_048_offline_mobile.spec.ts` (US-048-13).

## 8. Felhasználói és GUI-folyamat

1. A felhasználó a mobil capture-nézetet minimális döntéssel indítja; a kamera rögzít (`CAPTURING`).
2. Előnézet után újrafotóz vagy elfogad (`PREVIEW`→`DRAFT`); a kép lassú kapcsolaton tömörítve, olvashatóan töltődik, az adatforgalmi hatás látszik.
3. A nyugtánkénti állapot (várakozás/feltöltés/feldolgozás/ellenőrzésre-vár/siker/hiba) az oldal elhagyása után is követhető.
4. A képet és a felismert adatot gyorsan váltva/nagyítva összeveti; elsőként a bizonytalan/hibás mezőket járja végig nagy célokkal és megfelelő billentyűzettel.
5. A fő műveletek az alsó sávból egy kézzel elérhetők; a billentyűzet nem takar.
6. Hálózatvesztés/hívás/zár/háttér/véletlen navigáció után a kép, a javítások és az állapot megmaradnak; a piszkozat tudatosan félbehagyható és ugyanonnan folytatható.
7. Képernyőolvasóval minden lépés (kamera, haladás, bizonytalanság, hiba, jóváhagyás) érthető névvel és bejelentéssel elérhető.
8. A jóváhagyott nyugta azonnal visszakereshető és megnyitható.
9. Hiba esetén a felület a bevitelet megőrzi, újrapróbálást kínál, duplikátum nem keletkezik.

## 9. Állapotmodell

Tényleges gépi állapotok (`app/mobile_receipt_models.py:8-16`):

- `CAPTURING` (kezdő — `app/mobile_receipt_service.py:21`), `PREVIEW`, `DRAFT`, `UPLOADING`, `PROCESSING`, `NEEDS_REVIEW`, `APPROVED`, `FAILED`.

Megfigyelt átmenetek (`app/mobile_receipt_service.py:32`):

- `confirm` → `APPROVED`; `reject` → `FAILED`; `resolve` → `APPROVED`; `reopen` → `CAPTURING`.
- Feltétel: `expected_revision` egyezik, különben 409 írás nélkül.
- Megjegyzés: a `CAPTURING`→`PREVIEW`→`DRAFT`→`UPLOADING`→`PROCESSING`→`NEEDS_REVIEW` életút a sémában létezik, de a generikus leképezés közvetlenül nem vezérli — a kliens (`MobileCaptureFlow.tsx`) tartja nyilván a `data` payloadon és a hívássorrenden keresztül (lásd GAP).

## 10. API-, esemény- és adatszerződés

### REST (mind `app/mobile_receipt_api.py`)

| Route | Kódhely | Szerződés |
| :--- | :--- | :--- |
| `GET /api/v2/mobile-receipts` | `:21-22` | tenant-szűrt lista; 200 / 401 / 403 |
| `POST /api/v2/mobile-receipts` | `:24-26` | `CreateRequest`; kötelező `Idempotency-Key`; 201 / 400 / 401 / 403 / 409 / 422 |
| `GET /api/v2/mobile-receipts/{id}` | `:28-30` | részlet + `evidence`; idegen tenantnál 404-szerű `NOT_FOUND` |
| `PATCH /api/v2/mobile-receipts/{id}` | `:32-34` | `CommandRequest` + `expected_revision`; 200 / 409 / 422 |
| `POST /api/v2/mobile-receipts/{id}/confirm` | `:36-38` | `action="confirm"` kényszerítéssel delegál; 200 / 403 / 409 / 422 |

Hibák: `application/problem+json` (`:19`; modellek `:42-44`). Bekötés: `app/api_v2.py:24`, `:160`.

### Események

Nincs eseménybusz; feltöltés-feldolgozás pipeline szerveroldalon nincs bekötve — a kliens vezérli (GAP).

### Adatmodell

- `MobileReceiptJourney` (`app/mobile_receipt_models.py:31-40`): `id`, `tenant_id`, `status`, `revision`, `client_reference`, `data: dict`, `evidence: dict`, `created_at`, `updated_at`.
- `CreateRequest` (`:18-22`), `CommandRequest` (`:24-29`) — generikus alak.
- Hibák: `NotFoundError` 404 (`:48-49`), `StaleRevisionError` 409 (`:50-51`), `IdempotencyConflictError` 409 (`:52-53`).
- Tárolás: `MobileReceiptJourneyService._items` + `_keys`, `threading.RLock` (`app/mobile_receipt_service.py:7-9`); létrehozáskor `evidence={"source": "FEAT-048"}` (`:21`); migráció nincs. A képbináris nem a szerver-journeyben tárolódik.

## 11. Acceptance scenario-k

### AC-048-01: capture→preview→accept (REQ-048-01)

Given mobil capture-nézet
When a felhasználó rögzít, előnéz, szükség esetén újrafotóz, majd elfogad
Then olvasható kép kerül be `DRAFT` szemantikával, minimális döntésszámmal.

### AC-048-02: látható, folytatható állapot (REQ-048-02)

Given feltöltés/feldolgozás alatt álló nyugta
When a felhasználó az oldalt elhagyja és visszatér
Then a nyugtánkénti állapot látszik és folytatható.

### AC-048-03: kép-adat összevetés (REQ-048-03)

Given felismert adat és forráskép
When a felhasználó kis képernyőn összeveti
Then gyors váltás/nagyítás mellett megbízhatóan javítható.

### AC-048-04: mező-javítás mobil ergonómiával (REQ-048-04)

Given bizonytalan/hibás mezők
When a felhasználó végigviszi a javítást
Then nagy célok, megfelelő billentyűzet, nem takart mentés; kevés görgetés.

### AC-048-05: megszakítás-tűrés (REQ-048-05)

Given hálózatvesztés/hívás/zár/háttér/véletlen navigáció
When a folyamat megszakad
Then kép, javítások és állapot megmaradnak; a piszkozat ugyanonnan folytatható. (Eszköz-oldali perzisztenciára lásd GAP.)

### AC-048-06: hozzáférhetőség és egykezes használat (REQ-048-06)

Given képernyőolvasó / egykezes használat
When a felhasználó végigviszi a folyamatot
Then érthető nevek/bejelentések, alsó műveletsáv, nagy célok.

### AC-048-07: idempotens resume/approve (REQ-048-07)

Given resume/approve kérés `Idempotency-Key`-jel
When a kérés megismétlődik (azonos payload)
Then új nyugta nem duplikálódik; eltérő payloadra 409.

### AC-048-08: telefonméretű E2E (REQ-048-08)

Given valódi telefonméretek és mobilos megszakítások
When a fényképezés→feltöltés→feldolgozás→javítás→jóváhagyás→visszakeresés út E2E-ben fut
Then az út zöld (`gui_e2e_045_048_offline_mobile.spec.ts`).

## 12. Tesztleképezés

| REQ | AC | E2E-teszt (fájl:sor) | GUI | Unit-cél (státusz) |
| :--- | :--- | :--- | :--- | :--- |
| REQ-048-01 | AC-048-01 | `test_e2e_048_ac_01_positive_path` (`.agent-pipeline/03_e2e_suites/test_e2e_048.py:24`) | `gui_e2e_045_048_offline_mobile.spec.ts` | `tests/unit/test_mobile_receipts_service.py::test_req_048_01` — HIÁNYZIK |
| REQ-048-02 | AC-048-02 | `test_e2e_048_ac_02_contract_state` (`test_e2e_048.py:29`) | ugyanaz | `...::test_req_048_02` — HIÁNYZIK |
| REQ-048-03 | AC-048-03 | `test_e2e_048_ac_03_invalid_payload_is_safe` (`test_e2e_048.py:33`) | ugyanaz | `...::test_req_048_03` — HIÁNYZIK |
| REQ-048-04 | AC-048-04 | `test_e2e_048_ac_04_detail_contract` (`test_e2e_048.py:37`) | ugyanaz | `...::test_req_048_04` — HIÁNYZIK |
| REQ-048-05 | AC-048-05 | `test_e2e_048_ac_05_no_silent_success` (`test_e2e_048.py:41`) | ugyanaz | `...::test_req_048_05` — HIÁNYZIK |
| REQ-048-06 | AC-048-06 | `test_e2e_048_ac_06_tenant_and_auth_isolation` (`test_e2e_048.py:45`) | ugyanaz | `...::test_req_048_06` — HIÁNYZIK |
| REQ-048-07 | AC-048-07 | `test_e2e_048_ac_07_idempotent_retry` (`test_e2e_048.py:50`) | ugyanaz | `...::test_req_048_07` — HIÁNYZIK |
| REQ-048-08 | AC-048-08 | `test_e2e_048_ac_08_concurrent_revision` (`test_e2e_048.py:58`) | ugyanaz | `...::test_req_048_08` — HIÁNYZIK |

E2E-eredmény: 8/8 PASS (2026-08-31 jelentés). Unit-célok nem léteznek — SPEC-GAP-048-04.

## 13. Kockázatok és emberi döntések

- HR-048-01: olvashatatlan feltöltött kép feldolgozási hibát és újrafotózási kört okoz — ezért a tömörítés csak az olvashatóság megőrzésével megengedett, az adatforgalmi hatás látható.
- HR-048-02: megszakítás miatti adatvesztés az üzletben rögzítő felhasználónál kritikus — a túlélési garancia és a folytatási pont kötelező.
- Adatvédelem: képbináris nem kerülhet hibaválaszba/naplóba; más tenant journey-adata nem jelenhet meg.

## 14. Nyitott kérdések és SPEC-GAP

Nincs implementációt blokkoló nyitott kérdés (kód szállítva, E2E zöld).

SPEC-GAP (a BRIEF többet állít, mint a kód):

- SPEC-GAP-048-01: US-048-03 szerinti képtömörítés/adatforgalom-szabályozás és US-048-09 szerinti eszköz-oldali állapot-túlélés **szerveroldalon nem értelmezhető**; a szerver az életutat tartja nyilván, a média-kezelés kliens-felelősség (`MobileCaptureFlow.tsx`, `OfflineQueue.tsx`).
- SPEC-GAP-048-02: a `CAPTURING`→`PREVIEW`→`DRAFT`→`UPLOADING`→`PROCESSING`→`NEEDS_REVIEW` életút nem gépi átmenet a szerveren (a generikus leképezés csak `confirm/reject/resolve/reopen`-t ismer).
- SPEC-GAP-048-03: US-048-13 szerinti telefonméretű E2E-lefedés elsődleges bizonyítéka a GUI-suite; a szerver-E2E (`test_e2e_048.py`) a journey-szerződést fedi, nem a kamerát/tömörítést.
- SPEC-GAP-048-04: az előd pipeline-spec unit-céljai (`tests/unit/test_mobile_receipts_service.py`) **nem léteznek**; elsődleges bizonyíték az E2E-suite.

## 15. Rollback és megfigyelhetőség

- Rollback: migráció nincs; folyamat-memória — újraindítás a journey-életutakat törli (a kliens helyi piszkozata ettől független). Visszaállítás telepítéssel, adatmigráció nélkül.
- Megfigyelhetőség: `application/problem+json` `correlation_id`-val; válaszokban tenant- és revízió-azonosító. Feltöltési siker-metrika és eszköz-napló nincs.

## 16. Definition of Done

- [x] mind a 8 REQ-hez AC és E2E-teszt (8/8 PASS, 2026-08-31).
- [x] célzott E2E + GUI-suite zöld a jelentés szerint.
- [ ] unit-célok pótlása — nyitott (SPEC-GAP-048-04).
- [ ] SPEC-GAP-048-01 termékdöntése (kliens média-szerződés rögzítése).
- [x] visszamutatás BRIEF-048 ↔ SPEC-048 ↔ kód ↔ tesztek (`docs/traceability-index.md`).
- [x] production kód nem változott (docs-only).
