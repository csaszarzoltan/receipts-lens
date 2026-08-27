# ADR-004: Tax Pro Pack — Auto-Categorization + Deduction Tracker + Audit PDF

- **Dátum:** 2026-08-27
- **Státusz:** accepted
- **Szerző:** analyst (research: `docs/research/2026-08-27-receipt-lens-revenue-features.md` — VOC 18, competitor 6, RICE 384)
- **Kanban:** [aaa bbb] B) bevétel — RICE #1 (Reach 800 × Impact 3.0 × Confidence 80% / Effort 5 hét = 384)

## Kontextus

A ReceiptLens ma Tesseract/ConfidenceReceipt + `Categorizer` + `BudgetStore` szintig jut: van kategória, de nincs adókategória. A VOC bányászat 1. patternje egyértelmű: *"The Schedule C categorization is the killer feature"* — $1,200–$3,200 visszanyert levonás az aha moment, nem a scan. Az accountant *"shocked I had everything organized"*. Minden 6 versenytárs adja (Dext, Expensify, Zoho min.), ReceiptLens nem — ez a legnagyobb bevételi gap. A csomag a free→paid híd első pillére: #1 + #2 + #3 együtt alkotja a **Pro $5–8/hó ($49/év)** ajánlatot.

JTBD: *"Amikor jön az adóbevallás, szeretném egy kattintással exportálni a kategorizált kiadásokat, hogy ne kelljen egy vasárnapot a könyvelővel tölteni."* — trigger április, alternatíva $150/óra könyvelő.

## Döntés

**Tax Pro Pack egy Pro-csomag részeként: auto-tag + deduction tracker + audit-ready PDF.** MVP US Schedule C + HU ÁFA (27/18/5/0), többi régió iterációban (DE USt, FR TVA, RO TVA…). A kód külön modul, nem a meglévő `Categorizer`/`BudgetStore` bővítése — tiszta határ, tesztelhető, feature-flag mögött. Nincs új Python csomag (reportlab + httpx + cryptography már dep).

### 1) File-térkép (mit hozol létre / mit módosítasz)

| Művelet | File | Leírás | Sor-limit |
|---------|------|--------|-----------|
| Új | `app/taxonomy.py` | Szabálytár: `_TAX_RULES` + `TAX_CATEGORIES` (US 14 + HU 4) | ≤ 250 |
| Új | `app/tax_service.py` | `TaxService.categorize()` — substring match vendor + line_item.name | ≤ 250 |
| Új | `app/tax_audit.py` | `generate_tax_audit_pdf()` — reportlab, kategóriánként összesítés | ≤ 250 |
| Új | `app/tax_api.py` | FastAPI router — 6 végpont (lásd API tábla) | ≤ 300 |
| Módosít | `app/api.py` | `from app.tax_api import router as tax_router` + `app.include_router(tax_router)` | 2 sor |
| Módosít | `app/reports.py` | `ConfidenceReceipt` bővítés: `tax_category`, `tax_confidence`, `tax_locale` mezők (default None) — nem tör meglévőt | 10 sor |
| Módosít | `app/subscriptions_api.py` | `is_pro(tenant_id) -> bool` stub (ma: `return False` mindenkinek; Pro-ra DB check később) | 15 sor |
| Módosít | `frontend/lib/i18n.ts` | 2 kulcs ×10 nyelv: `taxDeduction`, `auditPdf` + `taxCategory`, `deductionTracker` | 20 sor |
| Módosít | `frontend/lib/featureFlags.ts` | `isPro` / `canUseTaxPro` helper | 20 sor |
| Új | `frontend/app/(app)/tax/page.tsx` | Tax dashboard — deduction lista + grand_total + Download PDF | ≤ 300 |
| Új | `frontend/components/TaxBadge.tsx` | Kis badge ReceiptCard mellé — `{tax_category ?? "—"}` | ≤ 80 |
| Módosít | `frontend/app/(app)/receipts/page.tsx` | Táblázat + kártya mellé TaxBadge beépítés | 15 sor |
| Módosít | `frontend/components/ReceiptCard.tsx` | TaxBadge import + inline select szerkesztés (PATCH) | 20 sor |
| Módosít | `app/consumer_dashboard.py` | `build_consumer_dashboard` bővítés: `tax_saving` widget (grand_total gyorsnézet) | 20 sor |

### 2) Adatmodell

```python
# app/reports.py — ConfidenceReceipt bővítés (nem tör meglévőt)
@dataclass
class ConfidenceReceipt:
    merchant: str
    total: float | None
    date: str | None
    tax: float | None
    currency: str
    items: list[LineItem]
    confidence: dict
    confidence_level: str | None
    # ÚJ — default None, régi nyugták nem törnek
    tax_category: str | None = None       # pl. "Meals & Entertainment — 50%" / "27% ÁFA"
    tax_confidence: str | None = None     # "high" | "medium" | "low"
    tax_locale: str | None = None         # "US" | "HU"

# app/tax_service.py — in-memory store (BudgetStore minta: Lock + dict, nincs migráció MVP-ben)
# Kulcs: receipt_id → {tax_category, tax_confidence, tax_locale, updated_at, provenance}
# Postgresre váltáskor Alembic: ALTER TABLE receipts ADD COLUMN tax_category TEXT
```

### 3) Kategória-szótár (MVP — US 14 + HU 4)

`app/taxonomy.py`:

```python
_TAX_RULES: list[tuple[str, str, str, str]] = [
    # (keyword, tax_category, locale, schedule_c_line / áfa_kulcs)
    ("uber",         "Transportation — Car/Truck", "US", "Line 9"),
    ("lyft",         "Transportation — Car/Truck", "US", "Line 9"),
    ("shell",        "Transportation — Car/Truck", "US", "Line 9"),
    ("starbucks",    "Meals & Entertainment — 50%", "US", "Line 24b"),
    ("mcdonald",     "Meals & Entertainment — 50%", "US", "Line 24b"),
    ("office depot", "Office Supplies",            "US", "Line 18"),
    ("comcast",      "Utilities",                  "US", "Line 25"),
    ("marriott",     "Travel — Lodging",           "US", "Line 24a"),
    ("aldi",         "Groceries — 27% ÁFA",        "HU", "27%"),
    ("lidl",         "Groceries — 27% ÁFA",        "HU", "27%"),
    ("spar",         "Groceries — 5% ÁFA",         "HU", "5%"),
    ("gyógyszertár", "Healthcare — 0% / AAM",      "HU", "0%"),
    # ... összesen ~30 sor — bővíthető
]
TAX_CATEGORIES = {
    "US": [{"id": "meals_50", "label": "Meals & Entertainment — 50%", "locale": "US", "line": "Line 24b"}, ...],
    "HU": [{"id": "afa_27", "label": "27% ÁFA", "locale": "HU", "line": "27%"}, ...],
}
```

Match: `vendor.lower()` + minden `line_item.name.lower()` — case-insensitive substring, mint `Categorizer._match_rules`. Első találat nyer. LLM fallback nincs MVP-ben.

### 4) API (FastAPI — `app/tax_api.py` router, prefix `/api/v1/tax`)

| # | Metódus + útvonal | Auth | Pro gate | Leírás | Request | Response (200) |
|---|-------------------|------|----------|--------|---------|----------------|
| 1 | `GET /api/v1/tax/categories?locale=US\|HU` | `Authorization: Bearer <token>` vagy `X-Tenant-ID/X-Role` (dev) | Free is (teaser) | Adható tax kategóriák listája | — | `{categories: [{id, label, locale, line}]}` |
| 2 | `POST /api/v1/tax/categorize` | tenant | Free is (preview, nem ment) | Szinkron preview — nem persistál | `{vendor: "STARBUCKS", line_items: [{name:"Latte",price:5.5}]}` | `{results: [{name:"Latte", tax_category:"Meals & Entertainment — 50%", confidence:"high", matched_rule:"starbucks"}]}` |
| 3 | `PATCH /api/v1/receipts/{id}/tax` | tenant | **Pro-only → 402** | Felülírás / korrekció — provenance mentve | `{tax_category: "Office Supplies"}` | `{receipt_id, tax_category, updated_at}` |
| 4 | `GET /api/v1/tax/deduction?year=2026&locale=US` | tenant | **Pro-only → 402** | Éves deduction összesítés | query `year`, `locale` | `{year:2026, locale:"US", by_category:[{tax_category, total, count}], grand_total: 1234.5, estimated_saving: 308.6}` |
| 5 | `GET /api/v1/tax/audit.pdf?year=2026&locale=US` | tenant | **Pro-only → 402** | Audit-ready PDF (reportlab) | query `year`, `locale` | `application/pdf` streaming, `Content-Disposition: attachment; filename="tax-audit-2026-US.pdf"` |
| 6 | `POST /api/v1/tax/backfill` | tenant | **Pro-only → 402** | Régi nyugták utólagos tax-tagelése (ahol `tax_category is None`) | `{locale:"US"}` | `{updated: 12, skipped: 3}` |

Pro gate minta:

```python
from app.subscriptions_api import is_pro
if not is_pro(tenant_id):
    raise HTTPException(status_code=402, detail={"code": "pro_required", "message": "Pro required — $5/mo"})
```

`is_pro` ma stub (`return False`), Pro-ra átállításkor DB `subscriptions` táblából `entitlement_level`.

### 5) Frontend

- **`/tax` oldal** (`frontend/app/(app)/tax/page.tsx` ≤ 300 sor):
  - `const {data} = useSWR("/product/tax/deduction?year=2026&locale=US", fetcher)` — lista `by_category` + `grand_total` + `estimated_saving` zöld badge.
  - `Download audit PDF` gomb → `fetch("/api/v1/tax/audit.pdf?year=2026&locale=US", {headers: {Authorization:`Bearer ${token}`}}) → blob → `URL.createObjectURL` → download.
  - Free teaser: ha `!isPro` → blur + paywall modal (`"Pro — $5/hó, $49/év"`, link `/settings/billing`), de `GET /categories` és `POST /categorize` preview látszik.
  - i18n: `t("taxDeduction")`, `t("auditPdf")`, `t("byCategory")`, `t("grandTotal")` — 10 nyelven (`lib/i18n.ts` 509→513 kulcs).
- **`TaxBadge.tsx`** (≤ 80 sor): `export default function TaxBadge({category}:{category:string|null})` — `{category ?? "—"}` + `className="badge"` + `title={category}`. Szín: `tax_category` alapján (Meals sárga, Travel kék, stb.).
- **`ReceiptCard` / `Receipts` táblázat**: TaxBadge mellé inline `<select>` szerkesztés → `PATCH /receipts/{id}/tax` (optimistic update + `mutate`).
- **Dashboard widget** (`consumer_dashboard.py` + FE `DashboardPage`): "Éves megtakarítás" kártya — Pro: `grand_total` szám, Free: teaser blur.

### 6) Biztonság / validáció

- Tenant-isolation: minden query `tenant_id` szűréssel (mint `BudgetStore.list(tenant_id)`). Más tenant PDF-jét nem lehet letölteni (403).
- `vendor`/`tax_category` trim + enum check (`tax_category in TAX_CATEGORIES[locale]`).
- PDF csak tenant saját nyugtáiból aggregál.
- `Content-Disposition: attachment` — ne inline renderelje a böngésző.

---

## Lépésről lépésre fejlesztési útmutató (bárki végig tudja vinni)

### Előfeltétel

```bash
cd /home/zoltan/receipts-lens
git pull
python3 -m venv .venv && source .venv/bin/activate
pip install -e .[dev]  # httpx, reportlab, cryptography már bent — új dep nem kell
cd frontend && npm install && cd ..
```

### Lépések (sorrend kötelező — max 3 file / lépés)

1. **Taxonomy + Service (BE logika, DB nélkül):**
   - Hozd létre `app/taxonomy.py` — másold a fenti `_TAX_RULES` + `TAX_CATEGORIES` struktúrát (US 14 + HU 4, ~30 sor).
   - Hozd létre `app/tax_service.py` — `class TaxService: def categorize(vendor, line_items) -> CategorizationResult` — `Categorizer._match_rules` másolata, de `tax_category` + `tax_locale` vissza. In-memory dict store `tax_store: dict[receipt_id, TaxRecord]` + `threading.Lock`.
   - Írd meg `tests/test_tax_service.py` table-driven: `("STARBUCKS", "Meals 50%")`, `("ALDI", "27% ÁFA")`, `("unknown vendor", None)`, tenant isolation (receipt A tenant X nem látszik tenant Y-nál), backfill idempotens.

2. **API router (BE végpontok):**
   - Hozd létre `app/tax_api.py` — `APIRouter(prefix="/api/v1/tax")`, 6 route a táblából. Auth: `api_v1_actor` / `Header Authorization` (másold `app/api.py` `api_v1_actor` mintát). Pro gate: `if not is_pro(tenant_id): raise HTTPException(402, ...)`.
   - Módosítsd `app/api.py`: `from app.tax_api import router as tax_router` + `app.include_router(tax_router)` (a meglévő `product_router` után).
   - Módosítsd `app/reports.py`: `ConfidenceReceipt` dataclass 3 mező (default None).
   - Módosítsd `app/subscriptions_api.py`: `def is_pro(tenant_id: str) -> bool: return False` (stub).

3. **Audit PDF (BE):**
   - Hozd létre `app/tax_audit.py` — `def generate_tax_audit_pdf(by_category, year, locale) -> bytes` — `reportlab.lib.pagesizes.A4`, `SimpleDocTemplate`, `Table` (kategória | darab | összesen), `Paragraph` grand_total, `canvas` footer "Generated by ReceiptLens".

4. **Frontend — i18n + TaxBadge:**
   - Módosítsd `frontend/lib/i18n.ts` — 4 kulcs ×10 nyelv: `taxDeduction`, `auditPdf`, `byCategory`, `grandTotal` (509→513). Kövesd `ADR-003` monolit pattern-t.
   - Módosítsd `frontend/lib/featureFlags.ts` — `export const canUseTaxPro = (tenant) => isPro(tenant)` (stub `isPro = () => false` amíg nincs Pro).
   - Hozd létre `frontend/components/TaxBadge.tsx` — 1 prop, 1 span.

5. **Frontend — Tax oldal + integráció:**
   - Hozd létre `frontend/app/(app)/tax/page.tsx` — `useSWR` deduction + PDF download blob + Free paywall modal.
   - Módosítsd `frontend/app/(app)/receipts/page.tsx` + `frontend/components/ReceiptCard.tsx` — TaxBadge + inline PATCH select.
   - Módosítsd `app/consumer_dashboard.py` — `build_consumer_dashboard` vissza adjon `tax_saving: {grand_total, by_category}` (Pro) / `None` (Free).

6. **Teszt + build gate (kötelező minden lépés után):**

```bash
# BE gate
ruff check app/taxonomy.py app/tax_service.py app/tax_api.py app/tax_audit.py
mypy app/taxonomy.py app/tax_service.py app/tax_api.py
pytest tests/test_tax_service.py tests/test_tax_api.py -q

# FE gate
cd frontend && npx tsc --noEmit && NODE_OPTIONS="--max-old-space-size=2048" npx next build 2>&1 | tail -10
cd .. && python3 -m py_compile app/taxonomy.py app/tax_service.py app/tax_api.py app/tax_audit.py
```

---

## Tesztelési útmutató (bárki le tudja futtatni)

### BE tesztek (pytest — `tests/test_tax_*.py`)

Sablon — másold `tests/test_budgets.py` / `tests/test_auth_api.py` mintájára:

```python
# tests/test_tax_service.py
def test_categorize_starbucks_meals_50():
    svc = TaxService()
    r = svc.categorize(vendor="STARBUCKS COFFEE", line_items=[{"name":"Latte","price":5.5}])
    assert r.tax_category == "Meals & Entertainment — 50%"
    assert r.confidence == "high"

def test_tenant_isolation():
    svc = TaxService()
    svc.categorize(vendor="ALDI", line_items=[], tenant_id="hh-1")
    assert svc.store["hh-2"] == {}  # nem szivárog

# tests/test_tax_api.py
def test_get_categories_200(client):
    resp = client.get("/api/v1/tax/categories?locale=US", headers=dev_headers("hh-1"))
    assert resp.status_code == 200
    assert len(resp.json()["categories"]) == 14

def test_patch_tax_402_free(client):
    # is_pro=False → 402
    resp = client.patch("/api/v1/receipts/abc/tax", json={"tax_category":"Office Supplies"}, headers=dev_headers("hh-1"))
    assert resp.status_code == 402
    assert resp.json()["detail"]["code"] == "pro_required"

def test_patch_tax_200_pro(client, monkeypatch):
    monkeypatch.setattr("app.tax_api.is_pro", lambda t: True)
    resp = client.patch("/api/v1/receipts/abc/tax", json={"tax_category":"Office Supplies"}, headers=dev_headers("hh-1"))
    assert resp.status_code == 200

def test_audit_pdf_content_type(client, monkeypatch):
    monkeypatch.setattr("app.tax_api.is_pro", lambda t: True)
    resp = client.get("/api/v1/tax/audit.pdf?year=2026&locale=US", headers=dev_headers("hh-1"))
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "attachment" in resp.headers["content-disposition"]
```

Futtatás:

```bash
pytest tests/test_tax_service.py tests/test_tax_api.py -v
# vagy teljes suite: pytest -q
```

### E2E (Browser Helper 1.35.0 — ezentúl BH az E2E, vö. user kérés "BH jobb mint Playwright")

Spec: `frontend/e2e/us_TAX_001_tax_pro.spec.ts` — **BH** bulk a `fleet_run_batch`-csel:

```typescript
// Pseudo — BH 1.35.0 API (68 eszköz):
// P0-3 navigate storageState (locale pre-seed), P0-4 expect polling, P0-5 bundle, P0-2 fleet_run_batch
import { test, expect } from "@playwright/test"; // BH recorder exportálja, de futtatás BH fleet-en

test("US-TAX-01 — Free teaser + Pro badge + PDF", async ({ page }) => {
  // Free: /tax teaser blur + PATCH 402 paywall
  await page.goto("/tax", { waitUntil: "domcontentloaded" });
  await expect(page.getByText("Pro — $5/hó")).toBeVisible(); // paywall modal
  // Pro: seed is_pro=true (storageState tenant entitlement) → badge + deduction + PDF
  // BH: browser_inject_storage_state({origins:[{origin:"https://receipts.allthezoo.com", localStorage:[{name:"receiptlens.session", value: proToken}]}]})
  // BH: browser_navigate({url:"/tax", storageState:{origins:[...]}})
  // BH: browser_interact({action:"click", selector:"text=Download audit PDF"})
  // BH: browser_get_network_activity({path:"/api/v1/tax/audit.pdf", status_min:200}) → 200 + content-type pdf
});
```

BH futtatás (a BH jobb mint Playwright — bulk + locale diff):

```bash
# Single smoke (BH)
curl -X POST http://127.0.0.1:8020/agent/navigate -H "Content-Type: application/json" \
  -d '{"url":"https://receipts.allthezoo.com/tax","storageState":{"origins":[{"origin":"https://receipts.allthezoo.com","localStorage":[{"name":"receiptlens.locale","value":"hu"}]}]}}'

# Bulk (fleet_run_batch — P0-2) — 5 case párhuzamosan, reporterek:
curl -X POST http://127.0.0.1:8020/fleet/run-batch -H "Content-Type: application/json" \
  -d '{"tasks":[{"id":"US-TAX-01-free-teaser"},{"id":"US-TAX-01-pro-badge"},{"id":"US-TAX-01-pdf"},{"id":"US-TAX-01-402-gate"},{"id":"US-TAX-01-i18n-10-lang"}],"workers":3,"retries":1,"reporter":{"html":true}}'

# Locale diff (P2) — h1 "Scan" vs "Numérisez" pixel-diff:
curl -X POST http://127.0.0.1:8020/agent/visual-diff-locale -H "Content-Type: application/json" \
  -d '{"url":"https://receipts.allthezoo.com/tax","locales":["en","fr"],"storage_key":"receiptlens.locale","h1_selector":"h1"}'
```

Gate (kötelező):

```bash
cd frontend && npx tsc --noEmit && echo "TSC:0"
NODE_OPTIONS="--max-old-space-size=2048" npx next build 2>&1 | tail -5 && echo "BUILD:0"
curl -s -o /dev/null -w "%{http_code}" https://receipts.allthezoo.com/tax && echo " /tax 200"
curl -s http://127.0.0.1:8020/status | python3 -c "import json,sys; print(json.load(sys.stdin).get('cdp_url','?')[:40])" # 9557 = lokális
```

---

## Elvetve

| Opció | Miért nem |
|-------|-----------|
| LLM-only kategorizálás (GPT-4o minden tételre) | Költség + latency + hallucináció — VOC-ben a szabály-alapú 80%-ot fedi, elég |
| Külön Tax microservice / queue | Over-engineering MVP-re — 1 modul elég, később kiszervezhető |
| Adó-jog teljes lefedés (US+EU összes kulcs) nap 1 | Scope — MVP US+HU, DE/FR/RO iteráció; külön RICE |
| PDF helyett csak CSV | Audithoz PDF kell (accountant "shocked" — nyomtatható, aláírható) |

## Következmény

- **Fejlesztő:** lásd File-térkép — max 400 sor/file, type hints, docstring (`METH-COD-001…008`), `ruff` + `mypy`.
- **Teszt:** BE `tests/test_tax_service.py` + `tests/test_tax_api.py`, E2E BH `us_TAX_001_tax_pro.spec.ts` (`fleet_run_batch` bulk).
- **Migráció:** nincs — in-memory dict (`budget_store` minta). Postgresre váltáskor Alembic migráció `tax_category` oszloppal.
- **Következő ADR:** ADR-005 (Vision Pro OCR — ugyanazon Pro csomag 2. pillére).

## Kapcsolódó

- Research: `docs/research/2026-08-27-receipt-lens-revenue-features.md` (VOC #1, gap #6, RICE 384)
- Kód: `app/categorizer.py`, `app/budgets.py` (minta), `app/reports.py`, `frontend/lib/i18n.ts`, `frontend/app/(app)/reports/page.tsx`
- Következő: ADR-005, ADR-006
