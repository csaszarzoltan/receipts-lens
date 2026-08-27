# ADR-004: Tax Pro Pack — Auto-Categorization + Deduction Tracker + Audit PDF

- **Dátum:** 2026-08-27
- **Státusz:** accepted
- **Szerző:** analyst (research: `docs/research/2026-08-27-receipt-lens-revenue-features.md` — VOC 18, competitor 6, RICE 384)
- **Kanban:** [aaa bbb] B) bevétel — RICE #1 (Reach 800 × Impact 3.0 × Confidence 80% / Effort 5 hét = 384)

## Kontextus

A ReceiptLens ma Tesseract/ConfidenceReceipt + `Categorizer` + `BudgetStore` szintig jut: van kategória, de nincs adókategória. A VOC bányászat 1. patternje egyértelmű: *"The Schedule C categorization is the killer feature"* — $1,200–$3,200 visszanyert levonás az aha moment, nem a scan. Az accountant *"shocked I had everything organized"*. Minden 6 versenytárs adja (Dext, Expensify, Zoho min.), ReceiptLens nem — ez a legnagyobb bevételi gap. A csomag a free→paid híd első pillére: #1 + #2 + #3 együtt alkotja a **Pro $5–8/hó ($49/év)** ajánlatot.

Követelmény (JTBD): *"Amikor jön az adóbevallás, szeretném egy kattintással exportálni a kategorizált kiadásokat, hogy ne kelljen egy vasárnapot a könyvelővel tölteni."* — trigger április, alternatíva $150/óra könyvelő.

## Döntés

**Tax Pro Pack egy Pro-csomag részeként: auto-tag + deduction tracker + audit-ready PDF.** MVP US Schedule C + HU ÁFA (27/18/5/0), többi régió iterációban (DE USt, FR TVA, RO TVA…). A kód külön modul, nem a meglévő `Categorizer`/`BudgetStore` bővítése — tiszta határ, tesztelhető, feature-flag mögött.

### Architektúra

```
app/taxonomy.py        — szabálytár: (keyword → tax_category, schedule_c_line / áfa_kulcs, locale)
app/tax_service.py     — TaxService.categorize(line_items|vendor) → {tax_category, confidence, matched_rule}
app/tax_audit.py       — Audit PDF generálás (reportlab — már dep): kategóriánként összesítés
frontend/app/(app)/tax/page.tsx  — Tax dashboard (közös Reports/Dashboard alatt is widget)
frontend/components/TaxBadge.tsx  — kis badge a ReceiptCard mellé
```

- **Adatmodell:** a `ConfidenceReceipt` / `ReceiptStore` / `reports.py` `line_items` mellé új mező `tax_category: str | None`, `tax_confidence: "high"|"medium"|"low"|None`, `tax_locale: "US"|"HU"|None` — nem tör meglévő mezőt. Persist in-memory dict (mint `BudgetStore` — `threading.Lock` + `dict`, nincs migráció MVP-ben; Postgresre váltáskor Alembic migráció jön). Default `None` — régi nyugtákon backfill `POST /api/v1/tax/backfill`.
- **Kategória-szótár (MVP):** US 14 Schedule C line (C: Advertising, Car/Truck, Contract Labor, Rent, Supplies, Meals 50%, Utilities, Travel, stb.) + HU 4 ÁFA-kulcs (27% ÁFA, 18%, 5%, 0%/AAM). Mapping `_TAX_RULES: list[tuple[keyword, tax_category, locale, schedule_c_line]]` — pl. `("uber","Transportation — Car/Truck","US","Line 9")`, `("aldi","Groceries","HU","27%")`. Vendor + line_item.name együtt ellenőrizve (case-insensitive substring, mint `Categorizer._match_rules`). LLM fallback nincs MVP-ben.
- **API (FastAPI — `app/api.py` + `app/tax_api.py` router):**

| Metódus + útvonal | Auth | Leírás | Válasz |
|-------------------|------|--------|--------|
| `GET /api/v1/tax/categories?locale=US|HU` | `Authorization: Bearer` vagy `X-Tenant-ID/X-Role` (dev) | Adható tax kategóriák listája | `{categories: [{id, label, locale, line}]}` |
| `POST /api/v1/tax/categorize` `{vendor, line_items}` | tenant | Szinkron kategorizálás preview (nem ment) | `{results: [{name, tax_category, confidence, matched_rule}]}` |
| `PATCH /api/v1/receipts/{id}/tax` `{tax_category}` | tenant (Pro) | Felülírás / korrekció — provenance mentve | `{receipt_id, tax_category, updated}` |
| `GET /api/v1/tax/deduction?year=2026&locale=US` | tenant (Pro) | Éves deduction összesítés | `{year, locale, by_category: [{tax_category, total, count}], grand_total, estimated_saving}` |
| `GET /api/v1/tax/audit.pdf?year=2026&locale=US` | tenant (Pro) | Audit-ready PDF (reportlab) | `application/pdf` streaming |
| `POST /api/v1/tax/backfill` | tenant (Pro) | Régi nyugták utólagos tax-tagelése | `{updated: n}` |

- **Feature flag / paywall:** `lib/featureFlags.ts` + BE `app/subscriptions_api.py` / `product_api.py` `Actor` role + `tenant` entitlement check. Free: `GET /categories` és preview `POST /categorize` megy (conversion teaser), `PATCH`, `deduction`, `audit.pdf`, `backfill` **Pro-only → 402 Payment Required** + FE paywall modal (`"Pro — $5/hó, $49/év"`, link `/settings/billing`). Entitlement hiányában a BE `HTTPException(402, "Pro required")`. Free 25 scan cap külön ADR-005-ben — itt nem keverjük.
- **Frontend:**
  - `/tax` (vagy `/reports` al-tab `Tax`) — `useSWR("/product/tax/deduction?year=…")`, lista `by_category` + `grand_total` + `estimated_saving` (zöld badge), `Download audit PDF` gomb → `GET audit.pdf` blob download. `t("taxDeduction")`, `t("auditPdf")` kulcsok 10 nyelvre `lib/i18n.ts`-ben.
  - `ReceiptCard` / `Receipts` táblázat — `TaxBadge` (`{tax_category ?? "—"}`), szerkesztés `PATCH` (inline select).
  - Dashboard widget (`consumer_dashboard.py` `build_consumer_dashboard` kibővítve + FE `DashboardPage`) — "Éves megtakarítás" kártya, `grand_total` gyorsnézet (Pro) / teaser (Free).
  - 400 sor/file limit: `tax/page.tsx` ≤ 300, `TaxBadge.tsx` ≤ 80.
- **Validáció / biztonság:** tenant-isolation (mint `BudgetStore.list(tenant_id)`), `vendor`/`tax_category` trim + enum check, PDF csak tenant saját nyugtáiból, `Content-Disposition: attachment`.

## Elvetve

| Opció | Miért nem |
|-------|-----------|
| LLM-only kategorizálás (GPT-4o minden tételre) | Költség + latency + hallucináció — VOC-ben a szabály-alapú 80%-ot fedi, elég |
| Külön Tax microservice / queue | Over-engineering MVP-re — 1 modul elég, később kiszervezhető |
| Adó-jog teljes lefedés (US+EU összes kulcs) nap 1 | Scope — MVP US+HU, DE/FR/RO iteráció; külön RICE |
| PDF helyett csak CSV | Audithoz PDF kell (accountant "shocked" — nyomtatható, aláírható) |

## Következmény

- **Fejlesztő:** `app/taxonomy.py` + `app/tax_service.py` + `app/tax_audit.py` + `app/tax_api.py` (router), `app/api.py` include, FE `tax/page.tsx` + `TaxBadge.tsx` + i18n 2 kulcs ×10 nyelv (+ `lib/featureFlags.ts` entitlement). Max 400 sor/file, type hints, docstring (`METH-COD-001…008`), `ruff` + `mypy`.
- **Teszt — BE:** `tests/test_tax_service.py` (categorize table-driven, backfill idempotens, tenant isolation), `tests/test_tax_api.py` (GET categories 200, POST categorize 200, PATCH 402 free / 200 pro, audit.pdf `content-type: application/pdf` + `Content-Disposition`).
- **Teszt — E2E (Browser Helper 1.35.0 — ezentúl BH az E2E, vö. user kérés):**
  - `frontend/e2e/us_TAX_001_tax_pro.spec.ts` — **BH** `browser_navigate` + `browser_inject_storage_state` (session seed, `storageState` locale-val) + `browser_interact` + `browser_get_console_logs` + `browser_get_network_activity`. Cases: (a) Free user `/tax` teaser + `PATCH` 402 paywall modal, (b) Pro user `POST /tax/categorize` badge látható, (c) `Download audit PDF` → `browser_get_network_activity` `audit.pdf` 200 + `content-type` pdf + `expect` polling, (d) 10 nyelv `t("taxDeduction")` nem angol. `TSC 0 BUILD 0`, `curl 200 /tax`, `npx playwright` helyett `fleet_run_batch` bulk a BH-n.
- **Migráció:** nincs — in-memory dict (`budget_store` minta). Postgresre váltáskor Alembic migráció `tax_category` oszloppal.
- **Következő ADR:** ADR-005 (Vision Pro OCR — ugyanazon Pro csomag 2. pillére).

## Kapcsolódó

- Research: `docs/research/2026-08-27-receipt-lens-revenue-features.md` (VOC #1, gap #6, RICE 384)
- Kód: `app/categorizer.py`, `app/budgets.py` (minta), `app/reports.py`, `frontend/lib/i18n.ts`, `frontend/app/(app)/reports/page.tsx`
- Következő: ADR-005, ADR-006
