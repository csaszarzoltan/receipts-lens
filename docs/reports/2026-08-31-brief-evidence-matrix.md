# BRIEF reconstruction evidence matrix

Dátum: 2026-08-31

A mátrix a felhasználói képesség, a kapcsolódó belépési pont, a működési bizonyíték és a BRIEF kapcsolatát rögzíti. Az endpointok és belső fájlok itt auditbizonyítékok, nem kerülnek a user story-kba.

## BRIEF-001 / FEAT-001: Nyilvános bemutatkozás és belépési útvonal
- BRIEF: `.product/briefs/BRIEF-001-nyilvanos-bemutatkozas-es-belepesi-utvonal.md`
- User story-k: 4 darab, `US-001-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-002 / FEAT-002: Fiók létrehozása és munkamenet
- BRIEF: `.product/briefs/BRIEF-002-fiok-letrehozasa-es-munkamenet.md`
- User story-k: 6 darab, `US-002-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-003 / FEAT-003: Google-belépés és fiók-összekapcsolás
- BRIEF: `.product/briefs/BRIEF-003-google-belepes-es-fiok-osszekapcsolas.md`
- User story-k: 4 darab, `US-003-01` kezdetű azonosítókkal
- Bizonyítékok:
  - `tests/test_us_002_google_sso.py`
  - `tests/test_google_oidc.py`
  - `tests/test_google_auth_routes.py`
  - `frontend/e2e/us_002_google_sso.spec.ts`
  - `frontend/app/auth/google/callback/page.tsx`
  - `docs/stories/US-002-google-sso.md`
  - `docs/plans/google-sso-2026-08-26.md`
  - `app/google_oidc.py`
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-004 / FEAT-004: Kezdeti beállítás és első nyugta
- BRIEF: `.product/briefs/BRIEF-004-kezdeti-beallitas-es-elso-nyugta.md`
- User story-k: 5 darab, `US-004-01` kezdetű azonosítókkal
- Bizonyítékok:
  - `docs/stories/US-003-nyugta-feltoltes.md`
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-005 / FEAT-005: Háztartási áttekintő és napi teendők
- BRIEF: `.product/briefs/BRIEF-005-haztartasi-attekinto-es-napi-teendok.md`
- User story-k: 5 darab, `US-005-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-006 / FEAT-006: Nyugta feltöltése és feldolgozási sor
- BRIEF: `.product/briefs/BRIEF-006-nyugta-feltoltese-es-feldolgozasi-sor.md`
- User story-k: 7 darab, `US-006-01` kezdetű azonosítókkal
- Bizonyítékok:
  - `docs/stories/US-003-nyugta-feltoltes.md`
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-007 / FEAT-007: AI-alapú nyugtafelismerés és bizonytalanság
- BRIEF: `.product/briefs/BRIEF-007-ai-alapu-nyugtafelismeres-es-bizonytalansag.md`
- User story-k: 6 darab, `US-007-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-008 / FEAT-008: Nyugták listája, keresése és részletei
- BRIEF: `.product/briefs/BRIEF-008-nyugtak-listaja-keresese-es-reszletei.md`
- User story-k: 5 darab, `US-008-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-009 / FEAT-009: Nyugtaellenőrzés és javítás
- BRIEF: `.product/briefs/BRIEF-009-nyugtaellenorzes-es-javitas.md`
- User story-k: 6 darab, `US-009-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-010 / FEAT-010: Ismétlődő és duplikált nyugták kezelése
- BRIEF: `.product/briefs/BRIEF-010-ismetlodo-es-duplikalt-nyugtak-kezelese.md`
- User story-k: 5 darab, `US-010-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-011 / FEAT-011: Kategorizálás és háztartási könyvelési besorolás
- BRIEF: `.product/briefs/BRIEF-011-kategorizalas-es-haztartasi-konyvelesi-besorolas.md`
- User story-k: 4 darab, `US-011-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-012 / FEAT-012: Háztartási keretek és riasztások
- BRIEF: `.product/briefs/BRIEF-012-haztartasi-keretek-es-riasztasok.md`
- User story-k: 5 darab, `US-012-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-013 / FEAT-013: Költési elemzés és előrejelzés
- BRIEF: `.product/briefs/BRIEF-013-koltesi-elemzes-es-elorejelzes.md`
- User story-k: 5 darab, `US-013-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-014 / FEAT-014: Jelentések létrehozása és letöltése
- BRIEF: `.product/briefs/BRIEF-014-jelentesek-letrehozasa-es-letoltese.md`
- User story-k: 4 darab, `US-014-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-015 / FEAT-015: Export-előkészítés és adatátadás
- BRIEF: `.product/briefs/BRIEF-015-export-elokeszites-es-adatatadas.md`
- User story-k: 6 darab, `US-015-01` kezdetű azonosítókkal
- Bizonyítékok:
  - `tests/test_export_readiness_workflow.py`
  - `tests/test_export_profiles.py`
  - `frontend/app/(app)/exports/runs/[id]/page.tsx`
  - `frontend/app/(app)/exports/prepare/page.tsx`
  - `frontend/app/(app)/exports/page.tsx`
  - `docs/accounting-export-guide.md`
  - `app/provider_export_service.py`
  - `app/export_workflow.py`
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-016 / FEAT-016: Háztartási együttműködés és családi postafiók
- BRIEF: `.product/briefs/BRIEF-016-haztartasi-egyuttmukodes-es-csaladi-postafiok.md`
- User story-k: 6 darab, `US-016-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-017 / FEAT-017: Könyvelő meghívása és biztonságos megosztás
- BRIEF: `.product/briefs/BRIEF-017-konyvelo-meghivasa-es-biztonsagos-megosztas.md`
- User story-k: 5 darab, `US-017-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-018 / FEAT-018: Külső szolgáltatások csatlakoztatása
- BRIEF: `.product/briefs/BRIEF-018-kulso-szolgaltatasok-csatlakoztatasa.md`
- User story-k: 5 darab, `US-018-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-019 / FEAT-019: Szinkronizálás és egyeztetés
- BRIEF: `.product/briefs/BRIEF-019-szinkronizalas-es-egyeztetes.md`
- User story-k: 5 darab, `US-019-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-020 / FEAT-020: Jóváhagyások és kontrollált változtatások
- BRIEF: `.product/briefs/BRIEF-020-jovahagyasok-es-kontrollalt-valtoztatasok.md`
- User story-k: 5 darab, `US-020-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-021 / FEAT-021: Automatizálások és feldolgozási szabályok
- BRIEF: `.product/briefs/BRIEF-021-automatizalasok-es-feldolgozasi-szabalyok.md`
- User story-k: 5 darab, `US-021-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-022 / FEAT-022: Előfizetés, kvóta és használati korlátok
- BRIEF: `.product/briefs/BRIEF-022-elofizetes-kvota-es-hasznalati-korlatok.md`
- User story-k: 5 darab, `US-022-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-023 / FEAT-023: Adózási munkaterület és auditcsomag
- BRIEF: `.product/briefs/BRIEF-023-adozasi-munkaterulet-es-auditcsomag.md`
- User story-k: 5 darab, `US-023-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-024 / FEAT-024: Profil, nyelv, pénznem és megjelenés
- BRIEF: `.product/briefs/BRIEF-024-profil-nyelv-penznem-es-megjelenes.md`
- User story-k: 6 darab, `US-024-01` kezdetű azonosítókkal
- Bizonyítékok:
  - `tests/test_export_profiles.py`
  - `frontend/components/ProfileMenu.tsx`
  - `frontend/app/(app)/settings/profile/page.tsx`
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-025 / FEAT-025: Adatvédelem, megőrzés és törlés
- BRIEF: `.product/briefs/BRIEF-025-adatvedelem-megorzes-es-torles.md`
- User story-k: 5 darab, `US-025-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-026 / FEAT-026: Értesítések és állapotüzenetek
- BRIEF: `.product/briefs/BRIEF-026-ertesitesek-es-allapotuzenetek.md`
- User story-k: 5 darab, `US-026-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-027 / FEAT-027: Hozzáférhetőség és reszponzív navigáció
- BRIEF: `.product/briefs/BRIEF-027-hozzaferhetoseg-es-reszponziv-navigacio.md`
- User story-k: 5 darab, `US-027-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-028 / FEAT-028: Rendszerállapot, biztonság és működési átláthatóság
- BRIEF: `.product/briefs/BRIEF-028-rendszerallapot-biztonsag-es-mukodesi-atlathatosag.md`
- User story-k: 4 darab, `US-028-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.

## BRIEF-029 / FEAT-029: OCR-minőség és adminisztratív diagnosztika
- BRIEF: `.product/briefs/BRIEF-029-ocr-minoseg-es-adminisztrativ-diagnosztika.md`
- User story-k: 4 darab, `US-029-01` kezdetű azonosítókkal
- Bizonyítékok:
- Állapotátmenetek: a BRIEF fő, üres, hibás, részleges, megerősítési vagy helyreállítási történeteiben rögzítve, ahol a működés indokolja.
