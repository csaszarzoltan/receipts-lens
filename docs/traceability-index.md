# Traceability index — BRIEF ↔ SPEC ↔ kód ↔ teszt

> VERITAS 1.1 §13 (Automatikus Traceability Graph) szerinti kézi összesítő.
> Lefedi a SPEC-001..SPEC-048 teljes állományt; a SPEC-038..048 visszamenőleges
> (kód→spec) pótlás, a többi a korábbi szállítmány része. Generálva: 2026-09-11.
> Forrás-leltár: `briefs/BRIEF-*.md`, `docs/specs/SPEC-*.md`, `app/*_{api,models,service}.py`,
> `app/api_v2.py`, `.agent-pipeline/03_e2e_suites/test_e2e_*.py`, `frontend/e2e/*.spec.ts`.

## 1. Összesítő

| Mutató | Érték |
| :--- | :--- |
| BRIEF-ek | 48 (BRIEF-001..048) |
| SPEC-ek | 48 (SPEC-001..048, mind `docs/specs/`) |
| 1:1 lefedettség | 100% |
| VERITAS 1.1 §4.5 fejezetek SPEC-038..048-ban | 16/16 |
| REQ→AC→E2E leképezés SPEC-038..048-ban | 88/88 |
| E2E REST (2026-08-31 jelentés) | 88/88 PASS |
| E2E GUI (2026-08-31 jelentés) | 33/33 PASS |
| Nyitott SPEC-GAP | 45 (lásd 4. fejezet) |
| Production kód változott | nem (docs-only) |

## 2. SPEC-038..048 mátrix (visszamenőleges pótlás)

| SPEC | BRIEF | Kód (api / models / service) | E2E REST (8 db) | GUI suite | FE oldal |
| :--- | :--- | :--- | :--- | :--- | :--- |
| SPEC-038 | BRIEF-038 | `app/reconciliation_api.py` / `app/reconciliation_models.py` (`TransactionMatch`) / `app/reconciliation_service.py` (`TransactionMatchService`) | `test_e2e_038.py:24,29,33,37,41,45,50,58` | `gui_e2e_038_039_042_reconciliation.spec.ts` | `frontend/app/reconciliation/page.tsx` |
| SPEC-039 | BRIEF-039 | `app/missing_receipt_api.py` / `app/missing_receipt_models.py` (`MissingReceiptTask`) / `app/missing_receipt_service.py` (`MissingReceiptTaskService`) | `test_e2e_039.py:24,29,33,37,41,45,50,58` | ugyanaz | `frontend/app/missing-receipts/page.tsx` |
| SPEC-040 | BRIEF-040 | `app/warranty_api.py` / `app/warranty_models.py` (`WarrantyCase`) / `app/warranty_service.py` (`WarrantyCaseService`) | `test_e2e_040.py:24,29,33,37,41,45,50,58` | `gui_e2e_040_041_warranties_prices.spec.ts` | `frontend/app/warranties/page.tsx` |
| SPEC-041 | BRIEF-041 | `app/price_tracking_api.py` / `app/price_tracking_models.py` (`TrackedProduct`) / `app/price_tracking_service.py` (`TrackedProductService`) | `test_e2e_041.py:24,29,33,37,41,45,50,58` | ugyanaz | `frontend/app/price-tracking/page.tsx` |
| SPEC-042 | BRIEF-042 | `app/refund_api.py` / `app/refund_models.py` (`RefundMatch`) / `app/refund_service.py` (`RefundMatchService`) | `test_e2e_042.py:24,29,33,37,41,45,50,58` | `gui_e2e_038_039_042_reconciliation.spec.ts` | `frontend/app/reconciliation/refunds/page.tsx` + `frontend/components/reconciliation/RefundWorkbench.tsx` |
| SPEC-043 | BRIEF-043 | `app/cost_split_api.py` / `app/cost_split_models.py` (`CostSplit`) / `app/cost_split_service.py` (`CostSplitService`) | `test_e2e_043.py:24,29,33,37,41,45,50,58` | `gui_e2e_043_044_split_goals.spec.ts` | `frontend/app/cost-splits/page.tsx` |
| SPEC-044 | BRIEF-044 | `app/savings_api.py` / `app/savings_models.py` (`SpendingGoal`) / `app/savings_service.py` (`SpendingGoalService`) | `test_e2e_044.py:24,29,33,37,41,45,50,58` | ugyanaz | `frontend/app/savings-goals/page.tsx` |
| SPEC-045 | BRIEF-045 | `app/offline_sync_api.py` / `app/offline_sync_models.py` (`OfflineReceiptDraft`) / `app/offline_sync_service.py` (`OfflineReceiptDraftService`) | `test_e2e_045.py:24,29,33,37,41,45,50,58` | `gui_e2e_045_048_offline_mobile.spec.ts` | `frontend/app/receipts/offline/page.tsx` + `frontend/components/offline/OfflineQueue.tsx` |
| SPEC-046 | BRIEF-046 | `app/quality_task_api.py` / `app/quality_task_models.py` (`QualityTask`) / `app/quality_task_service.py` (`QualityTaskService`) | `test_e2e_046.py:24,29,33,37,41,45,50,58` | `gui_e2e_046_047_quality_lock.spec.ts` | `frontend/app/quality-inbox/page.tsx` |
| SPEC-047 | BRIEF-047 | `app/period_close_api.py` / `app/period_close_models.py` (`AccountingPeriod`) / `app/period_close_service.py` (`AccountingPeriodService`) | `test_e2e_047.py:24,29,33,37,41,45,50,58` | ugyanaz | `frontend/app/accounting/period-close/page.tsx` + `frontend/components/accounting/PeriodCloseWizard.tsx` |
| SPEC-048 | BRIEF-048 | `app/mobile_receipt_api.py` / `app/mobile_receipt_models.py` (`MobileReceiptJourney`) / `app/mobile_receipt_service.py` (`MobileReceiptJourneyService`) | `test_e2e_048.py:24,29,33,37,41,45,50,58` | `gui_e2e_045_048_offline_mobile.spec.ts` | `frontend/app/receipts/capture/page.tsx` + `frontend/components/mobile/MobileCaptureFlow.tsx` + `frontend/components/mobile/ThumbActionBar.tsx` |

Közös bekötés: `app/api_v2.py:14-24` (importok), `app/api_v2.py:150-160` (`include_router`).
Közös route-minta minden modulban: `GET ""` (`:21`), `POST ""` (`:24`), `GET /{id}` (`:28`),
`PATCH /{id}` (`:32`), `POST /{id}/confirm` (`:36-38`); auth-kontextus (`:10-13`),
idempotencia-őrzés (`:15-17`), problem-helper (`:19`).

## 3. SPEC-001..037 (korábbi állomány, változatlan)

| SPEC | Státusz | Megjegyzés |
| :--- | :--- | :--- |
| SPEC-001..037 | `READY_FOR_DEV`, 14-fejezetes szerkezet | Nem része ennek a feladatnak; lásd `docs/specs/index.json` és `docs/specs/VALIDATION.md`. A VERITAS 1.1 §4.5 16-fejezetes sablonját a SPEC-038..048 vezeti be; a régebbi SPEC-ek 15. (rollback/megfigyelhetőség) és 16. (DoD) fejezetre hozása külön feladat lehet. |

## 4. GAP-lista (összesített, 45 tétel)

Minden GAP a saját SPEC 14. fejezetében részletezve; itt az áttekintés:

**Szerveroldali üzleti logika hiánya (kliens/`data`-szemantika helyettesíti):**

- GAP-038-01/02: pontszámító/magyarázó motor; borravaló/részfizetés/deviza/dátum-validáció.
- GAP-039-01/02: hiány-detektor; emlékeztető-motor (gyakoriság/csendes idő/csatorna/dedup).
- GAP-040-01/02: határidő-javaslat számítás; emlékeztető-motor.
- GAP-041-01/02: jelölt-képzés, egységár-normalizálás, trend-aggregálás, küszöbös riasztás; kizárás utáni újraszámolás.
- GAP-042-01/02: jóváírás-felismerő, rangsoroló, nettó-számító, többlépcsős maradvány; eltérő eszköz/pénznem konverzió.
- GAP-043-01/02: összeg-egyezés/kerekítés/kettős-számolás szervervalidációja; sablon-feloldás.
- GAP-044-01/02: korrigált haladás, eltérés-ok, ajánló-motor, kevés-adat korlát; kizárás/értékelés/megosztás kikényszerítése.
- GAP-045-01/02: eszköz-oldali perzisztencia/képbináris; automatikus folytatás és Wi-Fi-korlát kikényszerítése.
- GAP-046-01/02: detektor-motor és automatikus újraértékelő; tömeges művelet atomitása/visszavonása.
- GAP-047-01/02: hat-típusú előellenőrző, összesítés-előnézet, bizonyíték-generálás; zárás-blokkolás és módosításvédelem kikényszerítése.
- GAP-048-01: képtömörítés/adatforgalom-szabályozás és eszköz-oldali túlélés (kliens-felelősség).

**Állapotmodell-eltérések (séma gazdagabb, mint a generikus leképezés):**

- GAP-038-05: `confirm`→`REJECTED` leképezés a BRIEF "jóváhagyás" nyelvével szemben — felülvizsgálatra jelölve.
- GAP-039-03, GAP-040-03, GAP-041-03, GAP-042-03, GAP-043-03, GAP-044-03, GAP-045-03, GAP-046-03, GAP-047-03, GAP-048-02: a finom-állapotok (pl. `ASSIGNED`, `ON_TRACK`, `BLOCKED`, `NEEDS_REVIEW`) nem gépi átmenetek, csak `data`-szemantika.
- GAP-038-03, GAP-043-03: könyvelői visszakeresésnek / verziótörténetnek nincs audit-táblája (csak `reason` + revízió).

**Teszt-bizonyíték:**

- GAP-038-04, GAP-039-04, GAP-040-04, GAP-041-04, GAP-042-04, GAP-043-04, GAP-044-04, GAP-045-04, GAP-046-04, GAP-047-04, GAP-048-04 (11 db): az előd pipeline-spec unit-céljai (`tests/unit/test_*_service.py`) nem léteznek a repóban; elsődleges bizonyíték az E2E-suite (88/88 PASS).

**Infrastrukturális kockázat (mind a 11 modulban):**

- A service-ek folyamat-memóriában tárolnak (`threading.RLock` + dict); újraindítás adatvesztéssel jár. Különösen kritikus FEAT-047-nél (lezárási bizonyíték). Perzisztencia bevezetése termékdöntés.

## 5. REQ→teszt összesítés (SPEC-038..048)

| SPEC | REQ-ek | AC-k | E2E-fájl | E2E-eredmény | Unit-cél státusz |
| :--- | :--- | :--- | :--- | :--- | :--- |
| SPEC-038 | 8 | 8 | `test_e2e_038.py` | 8/8 PASS | hiányzik (GAP) |
| SPEC-039 | 8 | 8 | `test_e2e_039.py` | 8/8 PASS | hiányzik (GAP) |
| SPEC-040 | 8 | 8 | `test_e2e_040.py` | 8/8 PASS | hiányzik (GAP) |
| SPEC-041 | 8 | 8 | `test_e2e_041.py` | 8/8 PASS | hiányzik (GAP) |
| SPEC-042 | 8 | 8 | `test_e2e_042.py` | 8/8 PASS | hiányzik (GAP) |
| SPEC-043 | 8 | 8 | `test_e2e_043.py` | 8/8 PASS | hiányzik (GAP) |
| SPEC-044 | 8 | 8 | `test_e2e_044.py` | 8/8 PASS | hiányzik (GAP) |
| SPEC-045 | 8 | 8 | `test_e2e_045.py` | 8/8 PASS | hiányzik (GAP) |
| SPEC-046 | 8 | 8 | `test_e2e_046.py` | 8/8 PASS | hiányzik (GAP) |
| SPEC-047 | 8 | 8 | `test_e2e_047.py` | 8/8 PASS | hiányzik (GAP) |
| SPEC-048 | 8 | 8 | `test_e2e_048.py` | 8/8 PASS | hiányzik (GAP) |
| **Összesen** | **88** | **88** | 11 fájl | **88/88 PASS** | 0/88 létezik |

## 6. Karbantartás

- Új SPEC felvételekor: mátrix-bővítés + `docs/specs/index.json` + `docs/specs/VALIDATION.md` frissítése ugyanabban a commitban.
- GAP lezárásakor: a SPEC 14. fejezetéből törölni, itt a 4. fejezetből törölni, a REQ-sorhoz a megvalósító commitot bejegyezni.
- Az E2E-sor/def-számok (pl. `:24`) a `.agent-pipeline/03_e2e_suites/test_e2e_*.py` aktuális állapotára mutatnak; fájl-átrendezéskor frissítendők.

## 7. Előretekintő SPEC-ek (kutatás→spec, implementáció előtt)

| SPEC | Forrás | Kód | E2E | Státusz |
| :--- | :--- | :--- | :--- | :--- |
| SPEC-049 (`docs/specs/SPEC-049-ai-olvoso-chat.md`) | `docs/research/2026-09-11-ai-chat-deep-dive.md` 5. fej. (RL RESEARCH-1, t_e8a9057c) | még nincs (tervezett `POST /api/v2/chat/ask`) | tervezett `test_e2e_049_ac_*` | `READY_FOR_DEV`, R2 |
| SPEC-033B (`docs/specs/SPEC-033B-proaktiv-insight-kiterjesztes.md`) | `docs/research/2026-09-11-ai-chat-deep-dive.md` 2(c) fej. (RL RESEARCH-1, t_e8a9057c; t_71ad6116) | még nincs (ütemezett kiértékelő + kártya-kézbesítés FEAT-026-on) | tervezett `test_e2e_033B_ac_*` | `DRAFT`, R2 |

SPEC-049 REQ-lefedettség: REQ-049-01..08 → AC-049-01..AC-049-08 → tervezett
E2E `test_e2e_049_ac_01..08` (a megvalósító PR-ban szállítandó; eltérés
esetén SPEC-GAP-bejegyzés kötelező). Kapcsolódások: FEAT-008 (forrás-sorok),
FEAT-013 (aggregátumok), FEAT-025 (előzmény-megőrzés/törlés), FEAT-033
(nincs-adat minta); FEAT-050 (író-chat, R3) kizárva REQ-049-06-ban.

SPEC-033B REQ-lefedettség: REQ-033B-01..09 → AC-033B-01..AC-033B-09 →
tervezett E2E `test_e2e_033B_ac_01..09` (a megvalósító PR-ban szállítandó;
eltérés esetén SPEC-GAP-bejegyzés kötelező). Kiterjesztés, nem új FEAT:
FEAT-033 (jelek, REQ-033-02 magyarázhatóság, REQ-033-05 visszajelzés) +
FEAT-026 (kártya-kézbesítés, REQ-026-01..04) + FEAT-012 (keret-kontextus);
mélylink-cél SPEC-049 (`POST /api/v2/chat/ask`, OPEN-049-04 kétoldali
szerződés). REQ-számozás REQ-033B-01..09, nem ütközik SPEC-033-mal.
