# BRIEF-rekonstrukciós tételes lefedettségi és bizonyítékmátrix

**Dátum:** 2026-08-31  
**Módszertan:** METHODOLOGY.md (3.1 és 4. fejezetek)  
**Dokumentált BRIEF-ek:** 29 db  
**Lefedett felhasználói történetek:** 147 db  

Ez a mátrix tételesen összekapcsolja a 29 rekonstruált BRIEF-et és 147 felhasználói történetüket a forráskódban, felhasználói felületen, tesztkészletben és dokumentációban található konkrét megvalósítási bizonyítékokkal és állapotátmenetekkel.

---

## BRIEF-001: Nyilvános bemutatkozás és belépési útvonal
- **Kapcsolódó feature:** FEAT-001
- **BRIEF elérési út:** `.product/briefs/BRIEF-001-nyilvanos-bemutatkozas-es-belepesi-utvonal.md`
- **Történetek száma:** 4 (US-001-01 .. US-001-04)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/page.tsx` (Főoldali bemutatkozó landing oldal)
  - `frontend/components/Topbar.tsx` (Navigációs sáv bejelentkezési és regisztrációs hivatkozásokkal)
  - `frontend/components/ThemeToggle.tsx` (Téma váltó gomb a fejlécben)
  - `frontend/components/LanguageSwitcher.tsx` (Nyelvválasztó komponens)
  - `frontend/components/MobileNav.tsx` (Reszponzív mobilos menü)
- **Backend route-ok / Külső műveletek:**
  - `GET /` (Nyilvános kezdőlap HTML / JSON válasz)
  - `GET /health` (Rendszer elérhetőségi állapot)
- **Domain- és szolgáltatáslogika:**
  - `app/homepage.py` (Önálló kezdőlap renderelés és funkcionalitás ismertető)
  - `app/main.py` (Alkalmazás belépési pont és root routerek)
- **Lényeges állapotátmenetek:**
  - `ANONYMOUS_VISITOR` -> `EXPLORING_LANDING` -> `NAVIGATE_TO_AUTH` (Login / Register) vagy `DIRECT_WORKSPACE_ACCESS`
- **Kapcsolódó tesztek:**
  - `tests/test_homepage.py`
  - `tests/test_frontend.py`
  - `tests/test_windows_guide.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/WINDOWS_GUIDE_HU.md`
  - `docs/decisions/ADR-001-pre-login-language-switcher.md`
  - `docs/decisions/ADR-002-pre-login-dark-mode.md`
  - `README.md`

---

## BRIEF-002: Fiók létrehozása és munkamenet
- **Kapcsolódó feature:** FEAT-002
- **BRIEF elérési út:** `.product/briefs/BRIEF-002-fiok-letrehozasa-es-munkamenet.md`
- **Történetek száma:** 6 (US-002-01 .. US-002-06)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(auth)/register/page.tsx` (Regisztrációs űrlap)
  - `frontend/app/(auth)/login/page.tsx` (Bejelentkező űrlap)
  - `frontend/app/auth/magic-link/page.tsx` (Varázslink belépési oldal)
- **Backend route-ok / Külső műveletek:**
  - `POST /api/v2/auth/register` (Új fiók létrehozása jelszó hash-sel)
  - `POST /api/v2/auth/login` (Hitelesítés és JWT token kiadás)
  - `POST /api/v2/auth/magic-link` (Jelszó nélküli belépési kérelem)
  - `POST /api/v2/auth/refresh` (Munkamenet frissítés sliding sessionnel)
  - `POST /api/v2/auth/logout` (Munkamenet érvénytelenítése)
  - `GET /api/v2/auth/me` (Aktuális bejelentkezett felhasználó lekérdezése)
- **Domain- és szolgáltatáslogika:**
  - `app/auth_api.py` (Hitelesítési végpontok, token ellenőrzés)
  - `app/security.py` (Jelszó hashing, JWT generálás, rate limiting)
- **Lényeges állapotátmenetek:**
  - `UNAUTHENTICATED` -> `REGISTERED` -> `AUTHENTICATED_SESSION` -> `SESSION_REFRESHED` -> `LOGGED_OUT`
- **Kapcsolódó tesztek:**
  - `tests/test_auth_flow.py`
  - `tests/test_session_sliding.py`
  - `tests/test_bug003_006_store_split_auth.py`
  - `tests/test_security_headers.py`
  - `tests/test_rate_limiting.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/engineering-standards.md`
  - `docs/plans/user-stories-consumer-pivot.md`

---

## BRIEF-003: Google-belépés és fiók-összekapcsolás
- **Kapcsolódó feature:** FEAT-003
- **BRIEF elérési út:** `.product/briefs/BRIEF-003-google-belepes-es-fiok-osszekapcsolas.md`
- **Történetek száma:** 4 (US-003-01 .. US-003-04)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(auth)/login/page.tsx` (Google belépési gomb)
  - `frontend/app/auth/google/callback/page.tsx` (OAuth visszahívási oldal és állapotjelző)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/auth/google/login` (Google OAuth átirányítás kezdeményezése)
  - `GET /api/v2/auth/google/callback` (Google OIDC token csere és ellenőrzés)
  - `POST /api/v2/auth/google/exchange` (Frontend token érvényesítés)
- **Domain- és szolgáltatáslogika:**
  - `app/google_oidc.py` (OIDC állapot, PKCE, Google ID token hitelesítés és fiók-összerendelés)
  - `app/auth_api.py` (Munkamenet generálás Google SSO után)
- **Lényeges állapotátmenetek:**
  - `ANONYMOUS` -> `OAUTH_REDIRECT` -> `OIDC_EXCHANGE` -> `ACCOUNT_LINKED` -> `AUTHENTICATED`
- **Kapcsolódó tesztek:**
  - `tests/test_us_002_google_sso.py`
  - `tests/test_google_oidc.py`
  - `tests/test_google_auth_routes.py`
  - `frontend/e2e/us_002_google_sso.spec.ts`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/stories/US-002-google-sso.md`
  - `docs/plans/google-sso-2026-08-26.md`

---

## BRIEF-004: Kezdeti beállítás és első nyugta
- **Kapcsolódó feature:** FEAT-004
- **BRIEF elérési út:** `.product/briefs/BRIEF-004-kezdeti-beallitas-es-elso-nyugta.md`
- **Történetek száma:** 5 (US-004-01 .. US-004-05)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/onboarding/page.tsx` (3 lépéses onboarding varázsló)
  - `frontend/components/Onboarding.tsx` (Onboarding lépéskezelő komponens)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/onboarding/status` (Onboarding állapot lekérdezése)
  - `POST /api/v2/onboarding/complete` (Onboarding befejezése)
  - `POST /api/v2/onboarding/first-receipt` (Első mintanyugta rögzítése)
- **Domain- és szolgáltatáslogika:**
  - `app/product_service.py` (Kezdő konfiguráció, alapértelmezett kategóriák)
  - `app/consumer_dashboard.py` (Onboarding előrehaladás nyilvántartása)
- **Lényeges állapotátmenetek:**
  - `NEW_USER` -> `STEP_1_WELCOME` -> `STEP_2_CAPTURE_FIRST` -> `STEP_3_FIRST_RESULT` -> `WORKSPACE_READY`
- **Kapcsolódó tesztek:**
  - `tests/test_us_onboarding_f15.py`
  - `tests/test_stories.py`
  - `tests/test_development_stories.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/stories/US-003-nyugta-feltoltes.md`
  - `docs/plans/consumer-pivot-2026-08-13.md`

---

## BRIEF-005: Háztartási áttekintő és napi teendők
- **Kapcsolódó feature:** FEAT-005
- **BRIEF elérési út:** `.product/briefs/BRIEF-005-haztartasi-attekinto-es-napi-teendok.md`
- **Történetek száma:** 5 (US-005-01 .. US-005-05)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/dashboard/page.tsx` (Fő vezérlőpult)
  - `frontend/components/KpiCard.tsx` (Havi költés és átlag mutató kártyák)
  - `frontend/components/QuotaBar.tsx` (Havi kvótahasználat sáv)
  - `frontend/components/NotificationPanel.tsx` (Értesítési és teendő panel)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/dashboard/summary` (Összesített KPI mutatók)
  - `GET /api/v2/dashboard/kpis` (Kategória és költségvetési aggregációk)
  - `GET /api/v2/dashboard/actions` (Függőben lévő jóváhagyási és ellenőrzési teendők)
- **Domain- és szolgáltatáslogika:**
  - `app/consumer_dashboard.py` (Háztartási KPI-k és akciólista generálása)
  - `app/dashboard.py` (Vezérlőpult adatösszesítés)
- **Lényeges állapotátmenetek:**
  - `DASHBOARD_LOADING` -> `DATA_AGGREGATED` -> `ACTION_REQUIRED_HIGHLIGHTED` -> `ITEM_NAVIGATED`
- **Kapcsolódó tesztek:**
  - `tests/test_us_001_dashboard.py`
  - `tests/test_us_023_consumer_dashboard_contract.py`
  - `tests/test_consolidated_workspace.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/stories/US-001-dashboard-megnyitas.md`
  - `docs/consolidated-v1-workspace.md`

---

## BRIEF-006: Nyugta feltöltése és feldolgozási sor
- **Kapcsolódó feature:** FEAT-006
- **BRIEF elérési út:** `.product/briefs/BRIEF-006-nyugta-feltoltese-es-feldolgozasi-sor.md`
- **Történetek száma:** 7 (US-006-01 .. US-006-07)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/upload/page.tsx` (Nyugtafeltöltési oldal)
  - `frontend/components/DropZone.tsx` (Drag-and-drop és kamera feltöltési zóna)
  - `frontend/components/UploadQueue.tsx` (Feltöltési tétellista és folyamatjelzők)
  - `frontend/components/AiScanToggle.tsx` (AI Vision OCR mód kapcsoló)
- **Backend route-ok / Külső műveletek:**
  - `POST /api/v1/receipts/upload` (Egyedi képfeltöltés és azonnali feldolgozás)
  - `POST /api/v1/receipts/upload-url` (Kép letöltése URL-ről SSRF védelemmel)
  - `POST /api/v1/batch/upload` (Kötegelt feltöltés)
  - `GET /api/v1/batch/{batch_id}/status` (Köteg feldolgozási állapot lekérdezése)
- **Domain- és szolgáltatáslogika:**
  - `app/preprocessing.py` (Képformátum ellenőrzés, magic bytes vizsgálat, normalizálás)
  - `app/batch.py` (Kötegelt feladatok aszinkron koordinációja)
  - `app/ssrf_guard.py` (Hálózati egress és privát IP védelem URL feltöltésnél)
- **Lényeges állapotátmenetek:**
  - `FILES_SELECTED` -> `VALIDATING_MAGIC_BYTES` -> `UPLOADING` -> `QUEUED_IN_BATCH` -> `OCR_PROCESSING` -> `COMPLETED` / `FAILED_ITEM_RETRYABLE`
- **Kapcsolódó tesztek:**
  - `tests/test_us_003_upload.py`
  - `tests/test_batch_processing.py`
  - `tests/test_batch_processor.py`
  - `tests/test_magic_bytes.py`
  - `tests/test_ssrf_guard.py`
  - `tests/test_async_nonblocking_fetch.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/ocr-pipeline.md`
  - `specs/batch_processing_v0.3.md`

---

## BRIEF-007: AI-alapú nyugtafelismerés és bizonytalanság
- **Kapcsolódó feature:** FEAT-007
- **BRIEF elérési út:** `.product/briefs/BRIEF-007-ai-alapu-nyugtafelismeres-es-bizonytalansag.md`
- **Történetek száma:** 6 (US-007-01 .. US-007-06)
- **Felhasználói felület / Belépési pont:**
  - `frontend/components/AiResultPanel.tsx` (Felismerési mezők és megbízhatósági pontszámok panelje)
  - `frontend/components/ConfidenceBadge.tsx` (Magas, közepes, bizonytalan színjelvény)
  - `frontend/components/AiScanToggle.tsx` (Vision Pro vs Standard Tesseract választó)
- **Backend route-ok / Külső műveletek:**
  - `POST /api/v1/receipts/parse` (OCR szövegkivonatolás és mezőfelismerés)
  - `POST /api/v1/receipts/vision-parse` (Multimodális AI Vision struktúrált kinyerés)
  - `GET /api/v1/receipts/{id}/ocr-result` (Mezőszintű konfidencia pontszámok)
- **Domain- és szolgáltatáslogika:**
  - `app/ocr.py` (Tesseract motor, mintaillesztés és bizonytalanság számítás)
  - `app/vision_ocr.py` (Vision Pro integráció struktúrált kinyeréssel és fallback mechanizmussal)
  - `app/normalization.py` (Dátum, összeg, pénznem és kereskedő normalizálás)
  - `app/taxonomy.py` (Kereskedő és tételszintű entitásfelismerés)
- **Lényeges állapotátmenetek:**
  - `RAW_IMAGE` -> `TEXT_EXTRACTION` -> `KEY_VALUE_PARSING` -> `FIELD_CONFIDENCE_SCORED` -> `UNCERTAINTY_FLAGGED` -> `NORMALIZED`
- **Kapcsolódó tesztek:**
  - `tests/test_vision_ocr.py`
  - `tests/test_api_vision.py`
  - `tests/test_async_confidence.py`
  - `tests/test_bug001_confidence.py`
  - `tests/test_us_022_ocr_confidence_contract.py`
  - `tests/test_multilang_ocr.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/ai-vision-ocr.md`
  - `docs/ocr.md`
  - `docs/decisions/ADR-005-vision-pro-ocr.md`
  - `specs/async_confidence_v0.2.md`

---

## BRIEF-008: Nyugták listája, keresése és részletei
- **Kapcsolódó feature:** FEAT-008
- **BRIEF elérési út:** `.product/briefs/BRIEF-008-nyugtak-listaja-keresese-es-reszletei.md`
- **Történetek száma:** 5 (US-008-01 .. US-008-05)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/receipts/page.tsx` (Nyugták listanézete)
  - `frontend/app/(app)/receipts/[id]/page.tsx` (Egyedi nyugta részletes nézete)
  - `frontend/components/FilterBar.tsx` (Kereső, szűrő és rendező sáv)
  - `frontend/components/ReceiptCard.tsx` (Nyugta kártya előnézettel és státusszal)
  - `frontend/components/Pagination.tsx` (Lapozó komponens)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/receipts` (Szűrt, rendezett és lapozott nyugtalista)
  - `GET /api/v2/receipts/{id}` (Egyedi nyugta tételei és képadatai)
  - `DELETE /api/v2/receipts/{id}` (Nyugta törlése)
- **Domain- és szolgáltatáslogika:**
  - `app/product_service.py` (Keresési szűrők, lapozás, aggregációk)
  - `app/receipt_parsing.py` (Nyugta tételek és metaadatok kezelése)
- **Lényeges állapotátmenetek:**
  - `RECEIPTS_LISTED` -> `FILTER_APPLIED` -> `RECEIPT_SELECTED` -> `DETAIL_INSPECTED` -> `RECEIPT_DELETED`
- **Kapcsolódó tesztek:**
  - `tests/test_receipt_detail_api.py`
  - `tests/test_receipt_crud_runtime.py`
  - `tests/test_product_features.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/gui-workspace.md`
  - `docs/consolidated-v1-workspace.md`

---

## BRIEF-009: Nyugtaellenőrzés és javítás
- **Kapcsolódó feature:** FEAT-009
- **BRIEF elérési út:** `.product/briefs/BRIEF-009-nyugtaellenorzes-es-javitas.md`
- **Történetek száma:** 6 (US-009-01 .. US-009-06)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/review/page.tsx` (Ellenőrzésre váró nyugták munkaterülete)
  - `frontend/components/WorkflowState.tsx` (Munkafolyamat állapotjelző)
  - `frontend/components/ConfidenceBadge.tsx` (Bizonytalan mezők vizuális kiemelése)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/review/pending` (Ellenőrzésre váró bizonytalan tételek listája)
  - `PUT /api/v2/receipts/{id}/correct` (Felhasználói adatjavítás rögzítése)
  - `POST /api/v2/receipts/{id}/confirm` (Nyugta jóváhagyása és lezárása)
  - `POST /api/v2/receipts/{id}/reject` (Érvénytelenített elutasítás)
- **Domain- és szolgáltatáslogika:**
  - `app/quality_service.py` (Alacsony megbízhatóságú tételek válogatása)
  - `app/product_service.py` (Kézi mezőfelülbírálás, könyvelési lezárás)
- **Lényeges állapotátmenetek:**
  - `PENDING_REVIEW` -> `FIELD_MANUALLY_EDITED` -> `CONFIRMED_VERIFIED` vagy `REJECTED`
- **Kapcsolódó tesztek:**
  - `tests/test_review_workflow.py`
  - `tests/test_us_022_ocr_confidence_contract.py`
  - `tests/test_quality_service.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/product-workflows.md`
  - `docs/consolidated-v1-workspace.md`

---

## BRIEF-010: Ismétlődő és duplikált nyugták kezelése
- **Kapcsolódó feature:** FEAT-010
- **BRIEF elérési út:** `.product/briefs/BRIEF-010-ismetlodo-es-duplikalt-nyugtak-kezelese.md`
- **Történetek száma:** 5 (US-010-01 .. US-010-05)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/duplicates/page.tsx` (Duplikáció feloldó képernyő)
  - `frontend/components/ReceiptCard.tsx` (Egymás melletti összehasonlító kártyák)
  - `frontend/components/Modal.tsx` (Összevonási megerősítő párbeszédablak)
- **Backend route-ok / Külső műveletek:**
  - `POST /api/v1/duplicates/detect` (Duplikációk detektálása ujjlenyomat és összeg alapján)
  - `GET /api/v2/duplicates` (Gyanús párok és csoportok lekérdezése)
  - `POST /api/v2/duplicates/resolve` (Döntés érvényesítése: összevonás / megtartás / elvetés)
- **Domain- és szolgáltatáslogika:**
  - `app/duplicate_detection.py` (Kereskedő, dátum, végösszeg és képi ujjlenyomat illesztés)
  - `app/product_service.py` (Duplikáció feloldási műveletek végrehajtása)
- **Lényeges állapotátmenetek:**
  - `DUPLICATE_SUSPECTED` -> `SIDE_BY_SIDE_COMPARISON` -> `RESOLUTION_CHOSEN` (Merge / Archive / Dismiss) -> `RESOLVED`
- **Kapcsolódó tesztek:**
  - `tests/test_duplicate_detection.py`
  - `tests/test_product_features.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `specs/duplicate_detection_v0.4.md`
  - `docs/product-workflows.md`

---

## BRIEF-011: Kategorizálás és háztartási könyvelési besorolás
- **Kapcsolódó feature:** FEAT-011
- **BRIEF elérési út:** `.product/briefs/BRIEF-011-kategorizalas-es-haztartasi-konyvelesi-besorolas.md`
- **Történetek száma:** 4 (US-011-01 .. US-011-04)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/review/page.tsx` (Kategória választó lenyíló menü)
  - `frontend/app/(app)/receipts/[id]/page.tsx` (Kategória és adólevonási címke módosító)
- **Backend route-ok / Külső műveletek:**
  - `POST /api/v1/categorize` (Kulcsszavas és kereskedői kategória javaslat)
  - `GET /api/v2/categories` (Háztartási kategóriafa lekérdezése)
  - `PUT /api/v2/receipts/{id}/category` (Kézi kategória és címke felülírás)
- **Domain- és szolgáltatáslogika:**
  - `app/categorizer.py` (Szabály- és kulcsszóalapú kategóriabesorolás)
  - `app/taxonomy.py` (Szabványos háztartási és adózási taxonómia struktúra)
- **Lényeges állapotátmenetek:**
  - `UNCATEGORIZED` -> `AUTO_CATEGORIZED_BY_RULE` -> `USER_RECLASSIFIED` -> `CATEGORY_PERSISTED`
- **Kapcsolódó tesztek:**
  - `tests/test_categorize.py`
  - `tests/test_taxonomy.py`
  - `tests/test_product_features.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/categorization.md`

---

## BRIEF-012: Háztartási keretek és riasztások
- **Kapcsolódó feature:** FEAT-012
- **BRIEF elérési út:** `.product/briefs/BRIEF-012-haztartasi-keretek-es-riasztasok.md`
- **Történetek száma:** 5 (US-012-01 .. US-012-05)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/budget/page.tsx` (Költségvetés-kezelő oldal)
  - `frontend/components/QuotaBar.tsx` (Keret felhasználási mutató sáv)
  - `frontend/components/NotificationPanel.tsx` (Kerettúllépési figyelmeztetések)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/budgets` (Havi kategóriakeretek listája és aktuális egyenlege)
  - `POST /api/v2/budgets` (Új kategóriakeret létrehozása)
  - `PUT /api/v2/budgets/{id}` (Keretösszeg módosítása)
  - `GET /api/v2/alerts` (Aktív túllépési riasztások lekérdezése)
- **Domain- és szolgáltatáslogika:**
  - `app/budgets.py` (Költségvetési küszöbök számítása és 80% / 100% riasztáskiváltás)
  - `app/alerts.py` (Riasztási események kezelése és prioritási sorrendje)
  - `app/subscription_alerts.py` (Kritikus túllépési értesítések)
- **Lényeges állapotátmenetek:**
  - `BUDGET_SET` -> `SPEND_ACCUMULATING` -> `THRESHOLD_WARNING_80_PERCENT` -> `BUDGET_EXCEEDED_ALERT` -> `ACKNOWLEDGED`
- **Kapcsolódó tesztek:**
  - `tests/test_budgets.py`
  - `tests/test_alerts.py`
  - `tests/test_subscription_alerts.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/budgets-and-analytics.md`
  - `docs/alerts.md`

---

## BRIEF-013: Költési elemzés és előrejelzés
- **Kapcsolódó feature:** FEAT-013
- **BRIEF elérési út:** `.product/briefs/BRIEF-013-koltesi-elemzes-es-elorejelzes.md`
- **Történetek száma:** 5 (US-013-01 .. US-013-05)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/forecast/page.tsx` (Költéselemző és előrejelző képernyő)
  - `frontend/components/Charts.tsx` (Idősoros és kategóriadiagramok)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/analytics/spending` (Időszaki költési statisztikák és kategóriabontás)
  - `GET /api/v2/forecast/monthly` (Hóvégi várható költés és trend becslés)
- **Domain- és szolgáltatáslogika:**
  - `app/analytics.py` (Aggregált költési idősorok és kategóriaarányok)
  - `app/forecast.py` (Idősoros trendanalízis, szezonalitás és előrejelzési sáv)
- **Lényeges állapotátmenetek:**
  - `ANALYTICS_PERIOD_SELECTED` -> `HISTORICAL_TREND_CALCULATED` -> `PROJECTION_GENERATED` -> `CHART_RENDERED`
- **Kapcsolódó tesztek:**
  - `tests/test_analytics.py`
  - `tests/test_forecast.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/budgets-and-analytics.md`

---

## BRIEF-014: Jelentések létrehozása és letöltése
- **Kapcsolódó feature:** FEAT-014
- **BRIEF elérési út:** `.product/briefs/BRIEF-014-jelentesek-letrehozasa-es-letoltese.md`
- **Történetek száma:** 4 (US-014-01 .. US-014-04)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/reports/page.tsx` (Pénzügyi jelentéskészítő munkaterület)
  - `frontend/components/Charts.tsx` (Jelentés előnézeti diagramok)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v1/reports/summary` (Összesített kimutatás adott időszakra)
  - `POST /api/v1/reports/generate-pdf` (Formázott PDF jelentés generálása)
  - `GET /api/v1/reports/download/{id}` (Elkészült jelentés letöltése)
- **Domain- és szolgáltatáslogika:**
  - `app/reports.py` (Jelentés adathalmaz összeállítása)
  - `app/report_generator.py` (ReportLab alapú PDF formázás és táblázatépítés)
- **Lényeges állapotátmenetek:**
  - `REPORT_CRITERIA_SELECTED` -> `SUMMARY_AGGREGATED` -> `PDF_COMPILED` -> `DOWNLOAD_READY`
- **Kapcsolódó tesztek:**
  - `tests/test_reports.py`
  - `tests/test_report_generator.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/budgets-and-analytics.md`

---

## BRIEF-015: Export-előkészítés és adatátadás
- **Kapcsolódó feature:** FEAT-015
- **BRIEF elérési út:** `.product/briefs/BRIEF-015-export-elokeszites-es-adatatadas.md`
- **Történetek száma:** 6 (US-015-01 .. US-015-06)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/exports/page.tsx` (Exportkezelő főoldal)
  - `frontend/app/(app)/exports/prepare/page.tsx` (Export előkészítő varázsló)
  - `frontend/app/(app)/exports/runs/[id]/page.tsx` (Export futtatás auditnaplója és letöltése)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/exports/profiles` (Támogatott exportsémák: CSV, JSON, Könyvelői ZIP)
  - `POST /api/v2/exports/prepare` (Export felkészültség validáció és hiánylista)
  - `POST /api/v2/exports/execute` (Export generálás futtatása és csomagolás)
  - `GET /api/v2/exports/runs/{id}` (Export állapot és csomag letöltése)
- **Domain- és szolgáltatáslogika:**
  - `app/export.py` (CSV / JSON struktúrázás)
  - `app/export_workflow.py` (Többlépcsős export előkészítés, hiányzó mezők ellenőrzése)
  - `app/provider_export_service.py` (Könyvelői formátumok és csomagolt képek generálása)
- **Lényeges állapotátmenetek:**
  - `EXPORT_INITIATED` -> `PROFILE_SELECTED` -> `READINESS_VALIDATED` -> `GENERATING_PACKAGE` -> `EXPORT_READY_FOR_DOWNLOAD`
- **Kapcsolódó tesztek:**
  - `tests/test_export_profiles.py`
  - `tests/test_export_readiness_workflow.py`
  - `tests/test_export_service.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/accounting-export-guide.md`

---

## BRIEF-016: Háztartási együttműködés és családi postafiók
- **Kapcsolódó feature:** FEAT-016
- **BRIEF elérési út:** `.product/briefs/BRIEF-016-haztartasi-egyuttmukodes-es-csaladi-postafiok.md`
- **Történetek száma:** 6 (US-016-01 .. US-016-06)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/inbox/page.tsx` (Közös családi bejövő postafiók)
  - `frontend/app/(app)/settings/members/page.tsx` (Háztartási tagok kezelése és szerepkörök)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/inbox` (Közös beérkező nyugták listája)
  - `POST /api/v2/inbox/upload` (Nyugta beküldése a közös postafiókba)
  - `GET /api/v2/household/members` (Háztartás tagjainak lekérdezése)
  - `POST /api/v2/household/invite` (Új családtagsági meghívó küldése)
- **Domain- és szolgáltatáslogika:**
  - `app/inbox_service.py` (Családi postafiók beérkezési logika és hozzárendelés)
  - `app/consumer_dashboard.py` (Tagok aktivitásának és beküldéseinek követése)
- **Lényeges állapotátmenetek:**
  - `ITEM_DROPPED_TO_INBOX` -> `ASSIGNED_TO_CONTRIBUTOR` -> `MOVED_TO_REVIEW` -> `CONSOLIDATED_IN_HOUSEHOLD`
- **Kapcsolódó tesztek:**
  - `tests/test_inbox_service.py`
  - `tests/test_us_019_consumer_navigation.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/plans/consumer-pivot-2026-08-13.md`

---

## BRIEF-017: Könyvelő meghívása és biztonságos megosztás
- **Kapcsolódó feature:** FEAT-017
- **BRIEF elérési út:** `.product/briefs/BRIEF-017-konyvelo-meghivasa-es-biztonsagos-megosztas.md`
- **Történetek száma:** 5 (US-017-01 .. US-017-05)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/accountant/[token]/page.tsx` (Könyvelői dedikált olvasási munkaterület)
  - `frontend/app/(app)/settings/permissions/page.tsx` (Könyvelői hozzáférések kezelése)
  - `frontend/components/InviteAccountantModal.tsx` (Könyvelő meghívása párbeszédablak)
- **Backend route-ok / Külső műveletek:**
  - `POST /api/v2/accountant/invite` (Időkorlátos meghívó token generálása)
  - `GET /api/v2/accountant/access/{token}` (Könyvelői hozzáférés érvényesítése és adatok betöltése)
  - `DELETE /api/v2/accountant/access/{id}` (Könyvelői jogosultság azonnali visszavonása)
- **Domain- és szolgáltatáslogika:**
  - `app/accountant_invite.py` (Biztonságos tokenkezelés, olvasási jogosultság delegálás)
  - `app/security.py` (Izolált könyvelői munkamenet biztosítása)
- **Lényeges állapotátmenetek:**
  - `INVITATION_CREATED` -> `TOKEN_DELIVERED` -> `ACCOUNTANT_ACCESSED` -> `ACCESS_EXPIRED_OR_REVOKED`
- **Kapcsolódó tesztek:**
  - `tests/test_accountant_invite.py`
  - `tests/test_us_024_auth_contract.py`
  - `tests/test_us_024b_role_gate_gaps.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/decisions/ADR-006-qbo-xero-sync-accountant-invite.md`

---

## BRIEF-018: Külső szolgáltatások csatlakoztatása
- **Kapcsolódó feature:** FEAT-018
- **BRIEF elérési út:** `.product/briefs/BRIEF-018-kulso-szolgaltatasok-csatlakoztatasa.md`
- **Történetek száma:** 5 (US-018-01 .. US-018-05)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/integrations/page.tsx` (Integrációk áttekintő oldala)
  - `frontend/app/(app)/integrations/[id]/page.tsx` (Egyedi integrációs beállító és OAuth indító oldal)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/integrations` (Elérhető és csatlakoztatott integrációk listája)
  - `POST /api/v2/integrations/{id}/connect` (OAuth2 kapcsolat kezdeményezése)
  - `GET /api/v2/integrations/{id}/callback` (OAuth visszahívás és token tárolás)
  - `DELETE /api/v2/integrations/{id}/disconnect` (Kapcsolat bontása és token törlése)
- **Domain- és szolgáltatáslogika:**
  - `app/integrations.py` (Integrációs katalógus és állapotok)
  - `app/connection_service.py` (Kapcsolat életciklus kezelése)
  - `app/credential_store.py` (Titkosított token tárolás)
  - `app/intuit_oauth.py` és `app/quickbooks_connector.py` (QuickBooks Online integráció)
- **Lényeges állapotátmenetek:**
  - `DISCONNECTED` -> `OAUTH_INITIATED` -> `CALLBACK_VERIFIED` -> `CONNECTED_AND_ACTIVE` -> `DISCONNECTED`
- **Kapcsolódó tesztek:**
  - `tests/test_qbo_oauth_config.py`
  - `tests/test_qbo_live_callback.py`
  - `tests/test_connection_service.py`
  - `tests/test_us_010_012_connection_completion.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/quickbooks-online.md`
  - `docs/decisions/ADR-006-qbo-xero-sync-accountant-invite.md`

---

## BRIEF-019: Szinkronizálás és egyeztetés
- **Kapcsolódó feature:** FEAT-019
- **BRIEF elérési út:** `.product/briefs/BRIEF-019-szinkronizalas-es-egyeztetes.md`
- **Történetek száma:** 5 (US-019-01 .. US-019-05)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/accounting/page.tsx` (Könyvelési szinkronizációs és egyeztetési munkaterület)
- **Backend route-ok / Külső műveletek:**
  - `POST /api/v2/sync/trigger` (Szinkronizáció indítása külső főkönyvbe)
  - `GET /api/v2/sync/status` (Szinkronizációs folyamat állapota)
  - `POST /api/v2/reconciliation/run` (Tranzakcióegyeztetési vizsgálat futtatása)
- **Domain- és szolgáltatáslogika:**
  - `app/sync_service.py` (Kétirányú adatmozgás, hibaújrapróbálás)
  - `app/reconciliation_service.py` (Főkönyvi tételek és nyugták automatikus párosítása)
  - `app/accounting_projection.py` (Könyvelési kontírozási vetület előállítása)
- **Lényeges állapotátmenetek:**
  - `SYNC_IDLE` -> `SYNC_IN_PROGRESS` -> `DISCREPANCY_DETECTED` -> `MANUAL_RECONCILIATION` -> `FULLY_SYNCED`
- **Kapcsolódó tesztek:**
  - `tests/test_sync_service.py`
  - `tests/test_reconciliation_service.py`
  - `tests/test_us_010_018_api_completion.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/decisions/ADR-006-qbo-xero-sync-accountant-invite.md`

---

## BRIEF-020: Jóváhagyások és kontrollált változtatások
- **Kapcsolódó feature:** FEAT-020
- **BRIEF elérési út:** `.product/briefs/BRIEF-020-jovahagyasok-es-kontrollalt-valtoztatasok.md`
- **Történetek száma:** 5 (US-020-01 .. US-020-05)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/approvals/page.tsx` (Jóváhagyási várólista oldal)
  - `frontend/components/WorkflowState.tsx` (Munkafolyamat és jóváhagyási lépés jelző)
  - `frontend/components/Modal.tsx` (Indoklással ellátott jóváhagyási párbeszédablak)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/approvals/pending` (Jóváhagyásra váró tételek listája)
  - `POST /api/v2/approvals/{id}/approve` (Tétel jóváhagyása indoklással)
  - `POST /api/v2/approvals/{id}/reject` (Tétel visszautasítása javításra)
- **Domain- és szolgáltatáslogika:**
  - `app/governance.py` (Nagy összegű költések kétlépcsős jóváhagyási szabályai)
  - `app/product_service.py` (Jóváhagyási auditnapló és státuszváltoztatás)
- **Lényeges állapotátmenetek:**
  - `SUBMITTED_FOR_APPROVAL` -> `PENDING_REVIEW` -> `APPROVED_WITH_AUDIT` vagy `REJECTED_WITH_REASON`
- **Kapcsolódó tesztek:**
  - `tests/test_governance.py`
  - `tests/test_product_features.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/product-workflows.md`

---

## BRIEF-021: Automatizálások és feldolgozási szabályok
- **Kapcsolódó feature:** FEAT-021
- **BRIEF elérési út:** `.product/briefs/BRIEF-021-automatizalasok-es-feldolgozasi-szabalyok.md`
- **Történetek száma:** 5 (US-021-01 .. US-021-05)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/automations/page.tsx` (Szabálykezelő központ)
  - `frontend/app/(app)/automations/[id]/page.tsx` (Feltétel- és akciószerkesztő oldal)
  - `frontend/app/(app)/automations/[id]/runs/page.tsx` (Szabálylefutási előzmények)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/automations` (Konfigurált szabályok listája)
  - `POST /api/v2/automations` (Új if-then feldolgozási szabály mentése)
  - `PUT /api/v2/automations/{id}` (Szabályfeltételek és akciók frissítése)
  - `GET /api/v2/automations/{id}/runs` (Végrehajtási napló lekérdezése)
- **Domain- és szolgáltatáslogika:**
  - `app/automation_service.py` (Feltételkiértékelő motor: kereskedő egyezés, értékhatár, automatikus címkézés és áthelyezés)
- **Lényeges állapotátmenetek:**
  - `RULE_DEFINED` -> `RECEIPT_ARRIVED` -> `CONDITION_EVALUATED` -> `ACTION_EXECUTED` -> `RUN_AUDIT_LOGGED`
- **Kapcsolódó tesztek:**
  - `tests/test_automation_service.py`
  - `tests/test_product_features.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/product-workflows.md`

---

## BRIEF-022: Előfizetés, kvóta és használati korlátok
- **Kapcsolódó feature:** FEAT-022
- **BRIEF elérési út:** `.product/briefs/BRIEF-022-elofizetes-kvota-es-hasznalati-korlatok.md`
- **Történetek száma:** 5 (US-022-01 .. US-022-05)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/subscriptions/page.tsx` (Csomagkezelő és előfizetési oldal)
  - `frontend/components/QuotaBar.tsx` (Felhasznált havi szkennelési kvóta sáv)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/subscriptions/me` (Aktuális előfizetési csomag és érvényesség)
  - `GET /api/v2/quota/usage` (Havi OCR szkennelési kvótahasználat)
  - `POST /api/v2/subscriptions/upgrade` (Csomagváltás kezdeményezése)
- **Domain- és szolgáltatáslogika:**
  - `app/quota.py` (Díjcsomag-limitek érvényesítése, túllépési korlátok)
  - `app/subscription_alerts.py` (Kvóta fogyási és lejárati figyelmeztetések)
- **Lényeges állapotátmenetek:**
  - `ACTIVE_PLAN` -> `QUOTA_CONSUMED` -> `WARNING_THRESHOLD_REACHED` -> `LIMIT_REACHED_GRACEFUL_BLOCK` -> `PLAN_UPGRADED`
- **Kapcsolódó tesztek:**
  - `tests/test_quota.py`
  - `tests/test_subscription_alerts.py`
  - `tests/test_configurable_limits.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/subscription-alerts.md`
  - `docs/research/2026-08-27-receipt-lens-revenue-features.md`

---

## BRIEF-023: Adózási munkaterület és auditcsomag
- **Kapcsolódó feature:** FEAT-023
- **BRIEF elérési út:** `.product/briefs/BRIEF-023-adozasi-munkaterulet-es-auditcsomag.md`
- **Történetek száma:** 5 (US-023-01 .. US-023-05)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/tax/page.tsx` (Adózási összesítő munkaterület)
  - `frontend/components/TaxBadge.tsx` (Adólevonható tétel jelvény)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/tax/summary` (Adóévi levonások és kategóriaösszesítések)
  - `GET /api/v2/tax/deductions` (Levonható nyugták tételes kimutatása)
  - `POST /api/v2/tax/audit-pack` (Adóhatósági auditcsomag generálása képekkel és metaadatokkal)
- **Domain- és szolgáltatáslogika:**
  - `app/tax_service.py` (Adóalap-csökkentő tételek számítása és szabályai)
  - `app/tax_audit.py` (Auditcsomag összeállítása ZIP formátumban hitelesítési ujjlenyomatokkal)
- **Lényeges állapotátmenetek:**
  - `TAX_YEAR_SELECTED` -> `DEDUCTIONS_COMPILED` -> `MISSING_PROOFS_HIGHLIGHTED` -> `AUDIT_PACK_ZIP_BUILT`
- **Kapcsolódó tesztek:**
  - `tests/test_tax_service.py`
  - `tests/test_tax_audit.py`
  - `.agent-pipeline/03_e2e_suites/test_e2e_adr_004.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/decisions/ADR-004-tax-pro-pack.md`
  - `.agent-pipeline/02_specs/done/SPEC-ADR-004.md`

---

## BRIEF-024: Profil, nyelv, pénznem és megjelenés
- **Kapcsolódó feature:** FEAT-024
- **BRIEF elérési út:** `.product/briefs/BRIEF-024-profil-nyelv-penznem-es-megjelenes.md`
- **Történetek száma:** 6 (US-024-01 .. US-024-06)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/settings/profile/page.tsx` (Profilbeállítások képernyő)
  - `frontend/components/ProfileMenu.tsx` (Felhasználói profilmenü)
  - `frontend/components/LanguageSwitcher.tsx` (Nyelvválasztó felület)
  - `frontend/components/ThemeToggle.tsx` (Sötét / világos mód kapcsoló)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/settings/profile` (Profiladatok, nyelv és preferenciák lekérése)
  - `PUT /api/v2/settings/profile` (Profil, alapértelmezett pénznem és felületi nyelv mentése)
- **Domain- és szolgáltatáslogika:**
  - `app/product_service.py` (Felhasználói profil preferenciák perzisztálása)
  - `app/normalization.py` (Pénznem- és számformázási lokalizációs szabályok)
- **Lényeges állapotátmenetek:**
  - `PREFERENCES_OPENED` -> `LOCALE_THEME_CHANGED` -> `UI_RERENDERED_IMMEDIATELY` -> `SETTINGS_SAVED`
- **Kapcsolódó tesztek:**
  - `tests/test_multilang_ocr.py`
  - `tests/test_export_profiles.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/multi-language-guide.md`
  - `docs/plans/dark-mode-2026-08-12.md`
  - `docs/decisions/ADR-001-pre-login-language-switcher.md`
  - `docs/decisions/ADR-002-pre-login-dark-mode.md`
  - `docs/decisions/ADR-003-full-translation.md`

---

## BRIEF-025: Adatvédelem, megőrzés és törlés
- **Kapcsolódó feature:** FEAT-025
- **BRIEF elérési út:** `.product/briefs/BRIEF-025-adatvedelem-megorzes-es-torles.md`
- **Történetek száma:** 5 (US-025-01 .. US-025-05)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/settings/privacy/page.tsx` (Adatvédelmi és megőrzési beállítások képernyője)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/privacy/data-export` (Teljes személyes adatexport letöltése)
  - `DELETE /api/v2/privacy/account` (Fiók és kapcsolódó adatok végleges törlése)
  - `POST /api/v2/privacy/retention` (Automatikus adatmegőrzési időkorlát beállítása)
- **Domain- és szolgáltatáslogika:**
  - `app/governance.py` (GDPR adatexport összeállítása és törlési kaszkádok)
  - `app/security.py` (Képadatok biztonságos felülírása és anonimizálás)
- **Lényeges állapotátmenetek:**
  - `PRIVACY_PANEL_VIEWED` -> `DATA_EXPORT_REQUESTED` -> `DELETION_INITIATED` -> `CONFIRMATION_BARRIER_PASSED` -> `ACCOUNT_PURGED`
- **Kapcsolódó tesztek:**
  - `tests/test_security.py`
  - `tests/test_security_integration.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/engineering-standards.md`

---

## BRIEF-026: Értesítések és állapotüzenetek
- **Kapcsolódó feature:** FEAT-026
- **BRIEF elérési út:** `.product/briefs/BRIEF-026-ertesitesek-es-allapotuzenetek.md`
- **Történetek száma:** 5 (US-026-01 .. US-026-05)
- **Felhasználói felület / Belépési pont:**
  - `frontend/components/NotificationPanel.tsx` (Gördülő értesítési központ)
  - `frontend/components/Toast.tsx` (Globális toast értesítő komponens)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/notifications` (Olvasatlan és korábbi értesítések lekérdezése)
  - `PUT /api/v2/notifications/{id}/read` (Értesítés olvasottnak jelölése)
  - `POST /api/v2/notifications/mark-all-read` (Összes értesítés együttes olvasottá tétele)
- **Domain- és szolgáltatáslogika:**
  - `app/alerts.py` (Alkalmazáson belüli események és riasztások kézbesítése)
  - `app/subscription_alerts.py` (Rendszerszintű és előfizetési figyelmeztetések)
- **Lényeges állapotátmenetek:**
  - `EVENT_TRIGGERED` -> `TOAST_DISPLAYED` -> `NOTIFICATION_BADGE_INCREMENTED` -> `PANEL_OPENED` -> `MARKED_AS_READ`
- **Kapcsolódó tesztek:**
  - `tests/test_alerts.py`
  - `tests/test_subscription_alerts.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/alerts.md`

---

## BRIEF-027: Hozzáférhetőség és reszponzív navigáció
- **Kapcsolódó feature:** FEAT-027
- **BRIEF elérési út:** `.product/briefs/BRIEF-027-hozzaferhetoseg-es-reszponziv-navigacio.md`
- **Történetek száma:** 5 (US-027-01 .. US-027-05)
- **Felhasználói felület / Belépési pont:**
  - `frontend/components/AppShell.tsx` (Alkalmazáskeret ARIA attribútumokkal)
  - `frontend/components/Sidebar.tsx` (Összecsukható és billentyűzettel vezérelhető oldalsáv)
  - `frontend/components/MobileNav.tsx` (Alsó vagy lenyíló mobilnavigáció)
  - `frontend/components/Modal.tsx` (Fókuszcsapdával ellátott modális ablak)
- **Backend route-ok / Külső műveletek:**
  - Valamennyi frontend útvonal és állapot
- **Domain- és szolgáltatáslogika:**
  - `frontend/components/AppShell.tsx` (WCAG 2.1 AA megfelelőség, fókuszkezelés, képernyőolvasó címkék)
- **Lényeges állapotátmenetek:**
  - `KEYBOARD_TAB_FOCUS` -> `MODAL_FOCUS_TRAPPED` -> `ESCAPE_KEY_PRESSED` -> `FOCUS_RESTORED`
- **Kapcsolódó tesztek:**
  - `tests/test_accessible_actions_and_deep_links.py`
  - `tests/test_frontend.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/engineering-standards.md`

---

## BRIEF-028: Rendszerállapot, biztonság és működési átláthatóság
- **Kapcsolódó feature:** FEAT-028
- **BRIEF elérési út:** `.product/briefs/BRIEF-028-rendszerallapot-biztonsag-es-mukodesi-atlathatosag.md`
- **Történetek száma:** 4 (US-028-01 .. US-028-04)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/settings/diagnostics/page.tsx` (Rendszerdiagnosztikai és biztonsági áttekintő)
- **Backend route-ok / Külső műveletek:**
  - `GET /health` (Alapvető üzemképesség)
  - `GET /api/v2/system/status` (Adatbázis, OCR munkaszálak és háttérfolyamatok állapota)
  - `GET /api/v2/security/audit-log` (Biztonsági események és bejelentkezési auditnapló)
- **Domain- és szolgáltatáslogika:**
  - `app/main.py` (Egészség-ellenőrzési logika)
  - `app/security.py` (Biztonsági fejlécek, CSP szabályok, audit logolás)
  - `app/ssrf_guard.py` (Kimenő hálózati kérések felügyelete és tiltása)
- **Lényeges állapotátmenetek:**
  - `HEALTH_CHECK_PINGED` -> `SUBSYSTEMS_EVALUATED` -> `STATUS_METRICS_RENDERED` -> `AUDIT_TRAIL_INSPECTED`
- **Kapcsolódó tesztek:**
  - `tests/test_security.py`
  - `tests/test_security_headers.py`
  - `tests/test_security_egress_allowlist.py`
  - `tests/test_ssrf_guard.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/engineering-standards.md`
  - `docs/api.md`

---

## BRIEF-029: OCR-minőség és adminisztratív diagnosztika
- **Kapcsolódó feature:** FEAT-029
- **BRIEF elérési út:** `.product/briefs/BRIEF-029-ocr-minoseg-es-adminisztrativ-diagnosztika.md`
- **Történetek száma:** 4 (US-029-01 .. US-029-04)
- **Felhasználói felület / Belépési pont:**
  - `frontend/app/(app)/settings/diagnostics/quality/page.tsx` (OCR minőségellenőrző diagnosztikai felület)
- **Backend route-ok / Külső műveletek:**
  - `GET /api/v2/diagnostics/ocr-quality` (Karakterhiba-arány, felismerési pontosság és fallback arány)
  - `POST /api/v2/diagnostics/benchmark` (Minőségi benchmark futtatása mintakészleten)
- **Domain- és szolgáltatáslogika:**
  - `app/quality.py` (Képminőség és kontraszt analízis)
  - `app/quality_service.py` (Felismerési hibastatisztikák és összehasonlító benchmarkok)
- **Lényeges állapotátmenetek:**
  - `QUALITY_DASHBOARD_OPENED` -> `BENCHMARK_TRIGGERED` -> `SAMPLE_EVALUATED` -> `METRICS_REPORT_DISPLAYED`
- **Kapcsolódó tesztek:**
  - `tests/test_quality_service.py`
  - `tests/test_ocr_coverage.py`
- **Kapcsolódó dokumentáció / ADR-ek:**
  - `docs/ocr-pipeline.md`


