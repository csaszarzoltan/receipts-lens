# ADR-005: Vision AI OCR Pro — 25 scan/hó Free cap, unlimited Pro

- **Dátum:** 2026-08-27
- **Státusz:** accepted
- **Szerző:** analyst (research: `docs/research/2026-08-27-receipt-lens-revenue-features.md` — gap Tesseract 85–92% vs Veryfi 99%, RICE 350)
- **Kanban:** [aaa bbb] B) bevétel — RICE #2 (Reach 1000 × Impact 2.0 × Confidence 70% / Effort 4 hét = 350)

## Kontextus

A Tesseract 85–92% receipt-accuracy-val ma ingyen, limit nélkül megy — nincs urgency, nincs free→paid trigger. A `frontend/app/(app)/upload` `aiScanDesc` már ígéri: *"Vision AI reads blurry photos, handwritten amounts... Pro plan"* — de nincs mögötte provider, quota, vagy cap. A versenytársak mind limitálják a free scan-t (Expensify 25 SmartScan/hó, Zoho Standard-tól AI OCR), a Veryfi $0.08/receipt díja meg mutatja a piaci értéket. A ReceiptLens egyetlen self-hosted + open-source + API + 10 nyelv + offline kombó — de a minőségi különbség (elmosódott fotó, kézírás) monetizálatlan. A csomag #2 pillére a Pro-nak: minőség = upsell, mennyiség = urgency. Ugyanaz a Pro $5–8/hó ($49/év) a #1-gyel együtt — nem külön termék.

## Döntés

**Vision AI OCR Pro: Free 25 scan/hó Tesseract-only cap, Pro unlimited Vision (GPT-4o / Gemini) — fallback Tesseract.** A provider absztrahált, a cap tenant-havi, a Vision csak Pro-ban hívódik — költség kontrollált. Nincs új Python csomag (httpx + cryptography + secrets — stdlib/már dep, `google_oidc.py` minta).

### 1) File-térkép (mit hozol létre / mit módosítasz)

| Művelet | File | Leírás | Sor-limit |
|---------|------|--------|-----------|
| Új | `app/quota.py` | `QuotaStore` — tenant×month counter (`Lock` + dict) | ≤ 200 |
| Új | `app/vision_providers/__init__.py` | `VisionProvider` Protocol + `VisionResult` dataclass | ≤ 80 |
| Új | `app/vision_providers/openai_vision.py` | OpenAI Vision adapter (gpt-4o) | ≤ 180 |
| Új | `app/vision_providers/gemini_vision.py` | Gemini Vision adapter (gemini-1.5-flash) | ≤ 180 |
| Új | `app/vision_ocr.py` | `get_vision_provider()` factory + `parse_receipt_with_vision()` (már van stub — bővíted) | ≤ 200 |
| Módosít | `app/api.py` | `POST /api/v1/receipts/scan` elé quota check + Pro ? Vision : Tesseract routing + `X-Quota-Remaining` header | 30 sor |
| Módosít | `app/subscriptions_api.py` | `is_pro(tenant_id) -> bool` stub (`return False` — mint ADR-004) | 15 sor |
| Módosít | `frontend/lib/i18n.ts` | 2 kulcs ×10 nyelv: `quotaUsed` ("{used}/{limit} scans"), `upgradeToPro` | 20 sor |
| Módosít | `frontend/lib/featureFlags.ts` | `isPro` helper | 15 sor |
| Új | `frontend/hooks/useQuota.ts` | `useSWR("/product/quota")` → `{used, limit, remaining, isPro}` | ≤ 60 |
| Új | `frontend/components/QuotaBar.tsx` | `used/25` progress bar (Free) / `∞` + zöld pipa (Pro) | ≤ 120 |
| Módosít | `frontend/app/(app)/upload/page.tsx` | Drag&drop mellé `QuotaBar` + 402 paywall modal | 40 sor |

### 2) Adatmodell / quota

```python
# app/quota.py — in-memory counter (BudgetStore minta: Lock + dict, nincs migráció MVP-ben)
# Kulcs: f"{tenant_id}:{YYYY-MM}" → {count: int, vision_used: int}
from threading import Lock

_quota: dict[str, int] = {}           # f"{tenant}:{YYYY-MM}" -> count
_vision_used: dict[str, int] = {}     # monitoring (nem limit)
_lock = Lock()

def _month_key(tenant_id: str) -> str:
    from datetime import UTC, datetime
    return f"{tenant_id}:{datetime.now(UTC).strftime('%Y-%m')}"

def incr_and_check(tenant_id: str, limit: int = 25) -> tuple[int, bool]:
    """Atomi increment. Returns (used, exceeded)."""
    key = _month_key(tenant_id)
    with _lock:
        _quota[key] = _quota.get(key, 0) + 1
        used = _quota[key]
    return used, used > limit

def get_quota(tenant_id: str, is_pro: bool) -> dict:
    key = _month_key(tenant_id)
    with _lock:
        used = _quota.get(key, 0)
    limit = None if is_pro else 25
    remaining = None if is_pro else max(0, 25 - used)
    return {"used": used, "limit": limit, "remaining": remaining, "is_pro": is_pro, "period": key.split(":")[1]}
```

- Kulcs `YYYY-MM` — havi rollover automatikus, nem kell cron. Tesztben `freezegun` vagy `_quota.clear()` mockolható.
- Számlálás: minden `POST /api/v1/receipts/scan` és `POST /v1/parse-receipt` (sync) + `POST /jobs` → async OCR job egyaránt `incr_and_check` — 25 felett `quota_exceeded` akkor is, ha Tesseract lenne.
- Pro: `limit=None` / `∞` — nincs 402. Vision-hívás csak akkor, ha `is_pro(tenant)` igaz — monitoring `vision_used` külön counter.

### 3) Provider absztrakció

```python
# app/vision_providers/__init__.py
from typing import Protocol

class VisionResult:
    vendor: str; total: float | None; date: str | None; tax: float | None
    currency: str; line_items: list[dict]; confidence: dict  # {source:"vision", model:"gpt-4o"}

class VisionProvider(Protocol):
    async def extract(self, image_bytes: bytes) -> VisionResult | None: ...

# app/vision_providers/openai_vision.py — közös prompt:
# "Extract vendor, total, date, tax, currency, line items from this receipt image.
#  Respond ONLY JSON {vendor, total, date, tax, currency, line_items:[{name,price}], confidence}"
# env: LLM_API_KEY, LLM_MODEL (default gpt-4o), LLM_BASE_URL (default https://api.openai.com/v1)
# httpx timeout: connect 5s, read 15s; exception → None → Tesseract fallback (app/ocr.py)
# gemini_vision.py ugyanez: GEMINI_API_KEY, gemini-1.5-flash, https://generativelanguage.googleapis.com
```

- `app/vision_ocr.py` factory: `def get_vision_provider() -> VisionProvider | None` — env alapján választ (LLM_API_KEY → OpenAI, GEMINI_API_KEY → Gemini, egyik sem → None → Tesseract-only).
- Timeout / 401 / 429 → `logger.warning` + `return None` → Tesseract fallback — a response `source:"tesseract"` marad, nem 500.

### 4) API (FastAPI — `app/api.py` + `app/quota.py` + `app/vision_ocr.py`)

| # | Metódus + útvonal | Auth | Pro gate | Leírás | Request | Response (200 / 402) |
|---|-------------------|------|----------|--------|---------|----------------------|
| 1 | `POST /api/v1/receipts/scan` (multipart `image`) | tenant | quota check mindenkin, Vision csak Pro | Scan — quota check → Pro ? Vision : Tesseract → count++ | `multipart/form-data: image: bytes` | 200: `{source:"tesseract"\|"vision", receipt:{vendor,total,...}, quota:{used, limit:25\|null, remaining}}` + header `X-Quota-Remaining: 3` / 402: `{"detail":{"code":"quota_exceeded","limit":25,"used":26,"message":"Free limit reached — upgrade to Pro"}}` + `Retry-After: <seconds to next month>` |
| 2 | `GET /api/v1/quota` | tenant | — | Havi quota státusz | — | `{used: 12, limit: 25, remaining: 13, is_pro: false, period:"2026-08"}` / Pro: `{used: 30, limit: null, remaining: null, is_pro: true}` |
| 3 | `POST /api/v1/quota/reset` | admin (teszt seed) | **csak non-production** (`RECEIPTLENS_ENV != "production"`) | Tenant havi counter reset / set — teszthez | `{tenant_id, used:0}` | `{used:0, limit:25}` — productionban 404 |

Pro gate minta (mint ADR-004):

```python
from app.subscriptions_api import is_pro
from app.quota import incr_and_check, get_quota

used, exceeded = incr_and_check(tenant_id, limit=25 if not is_pro(tenant_id) else 10_000_000)
if exceeded and not is_pro(tenant_id):
    raise HTTPException(status_code=402, detail={"code":"quota_exceeded","limit":25,"used":used,"message":"Free limit reached — upgrade to Pro for unlimited Vision OCR"})
# Vision csak Pro-ban:
if is_pro(tenant_id):
    vision_result = await get_vision_provider().extract(image_bytes)  # None → Tesseract fallback
```

### 5) Frontend

- **`useQuota.ts`** (≤ 60 sor): `export function useQuota(){ return useSWR("/product/quota", fetcher) }` → `{used, limit, remaining, isPro, period}`.
- **`QuotaBar.tsx`** (≤ 120 sor):
  - Free: `<div role="progressbar" aria-valuenow={used} aria-valuemax={25} aria-label="quota">` — `used/25` szám + progress bar (0–24 szürke, 24 sárga warning `bg-yellow-400`, 25 piros `bg-red-500` + `t("upgradeToPro")` link).
  - Pro: `∞` + zöld pipa + `t("unlimitedScans")`.
  - 10 nyelven: `t("quotaUsed")` = `"{used}/{limit} scans"` / `t("upgradeToPro")` = `"Upgrade to Pro — $5/mo"`.
- **`/upload`** (`app/(app)/upload/page.tsx` +40 sor):
  - Drag&drop fölé `<QuotaBar />` + `aiScanComingSoon` badge Pro-ban eltűnik (már él — itt feltételes).
  - `POST /scan` 402-kor `catch (e) { if (e.status===402) setShowPaywall(true) }` — paywall modal (`"Pro — $5/hó, $49/év"`, CTA `/settings/billing`), nincs unhandled rejection.
  - `app/api.py` `_render_ai_mode` már Vision+Tesseract összehasonlítást ad (`ai_result` + `tesseract_result`) — itt a quota check a Vision előtt fut.

### 6) Biztonság / költség-kontroll

- Tenant-isolation a counter kulcsban (`f"{tenant}:{YYYY-MM}"` — nincs cross-tenant leak, mint `BudgetStore.list(tenant_id)`).
- Vision API key rotálható env-ben (`LLM_API_KEY` / `GEMINI_API_KEY`), nincs logban (`logger.warning` csak "vision failed" — nem az image).
- No-per-doc charge — hosting költség fedezi ($5–20/hó). Vision költség Pro bevételből.

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

1. **Quota store (BE counter, DB nélkül):**
   - Hozd létre `app/quota.py` — másold a fenti `_quota` + `incr_and_check` + `get_quota` struktúrát (≤ 200 sor).
   - Írd meg `tests/test_quota.py` table-driven: `test_under_limit_200` (12 → not exceeded), `test_26th_402` (26 → exceeded), `test_pro_unlimited` (is_pro=True → 100 scan nem exceeded), `test_month_rollover_new_key` (mock `datetime.now` → új `YYYY-MM` 0-ról indul), `test_tenant_isolation` (hh-1 25 nem érinti hh-2-t).

2. **Provider absztrakció (BE Vision):**
   - Hozd létre `app/vision_providers/__init__.py` + `app/vision_providers/openai_vision.py` + `app/vision_providers/gemini_vision.py` — Protocol + 2 adapter (prompt + JSON parse + exception→None).
   - Hozd létre / bővítsd `app/vision_ocr.py` — `get_vision_provider()` factory + `parse_receipt_with_vision()` wrapper (már van stub — bővíted, nem duplikálod).
   - Írd meg `tests/test_vision_ocr.py` mock Vision: success → `source:"vision"`, timeout → `None` → fallback `tesseract`, 401 → None.

3. **API wiring (BE végpontok + quota gate):**
   - Módosítsd `app/api.py` — `POST /api/v1/receipts/scan` elejére quota check (`incr_and_check` → 402 ha Free + exceeded), Vision csak `is_pro` → factory → `extract` → fallback. Add header `X-Quota-Remaining`.
   - Hozd létre `app/quota_api.py` vagy told `app/api.py`-ba: `GET /api/v1/quota` + `POST /api/v1/quota/reset` (non-production guard: `if os.getenv("RECEIPTLENS_ENV")=="production": raise HTTPException(404)`).
   - Módosítsd `app/subscriptions_api.py`: `def is_pro(tenant_id: str) -> bool: return False` (stub — mint ADR-004).

4. **Frontend — i18n + QuotaBar:**
   - Módosítsd `frontend/lib/i18n.ts` — 2 kulcs ×10 nyelv: `quotaUsed` (`"{used}/{limit} scans"` 10 nyelven), `upgradeToPro` (`"Upgrade to Pro — $5/mo"` 10 nyelven). Kövesd ADR-003 monolit pattern-t (509→511 kulcs).
   - Módosítsd `frontend/lib/featureFlags.ts` — `export const isPro = (tenant) => false` stub.
   - Hozd létre `frontend/hooks/useQuota.ts` (≤ 60 sor) + `frontend/components/QuotaBar.tsx` (≤ 120 sor) — lásd 5) Frontend szakasz.

5. **Frontend — Upload integráció:**
   - Módosítsd `frontend/app/(app)/upload/page.tsx` — `<QuotaBar />` a drag&drop fölé + 402 paywall modal (`showPaywall` state + `t("upgradeToPro")` CTA).
   - Manuális teszt: Free tenant 24 scan → sárga bar, 25 → piros + paywall, Pro → ∞.

6. **Teszt + build gate (kötelező minden lépés után):**

```bash
# BE gate
ruff check app/quota.py app/vision_providers/ app/vision_ocr.py app/api.py
mypy app/quota.py app/vision_providers/ app/vision_ocr.py
pytest tests/test_quota.py tests/test_vision_ocr.py tests/test_api_quota.py -q

# FE gate
cd frontend && npx tsc --noEmit && NODE_OPTIONS="--max-old-space-size=2048" npx next build 2>&1 | tail -10
cd .. && python3 -m py_compile app/quota.py app/vision_ocr.py
```

---

## Tesztelési útmutató (bárki le tudja futtatni)

### BE tesztek (pytest — `tests/test_quota.py`, `tests/test_vision_ocr.py`, `tests/test_api_quota.py`)

Sablon — másold `tests/test_budgets.py` / `tests/test_auth_api.py` mintájára:

```python
# tests/test_quota.py
from app.quota import _quota, incr_and_check, get_quota

def test_under_limit():
    _quota.clear()
    used, exceeded = incr_and_check("hh-test", limit=25)
    assert used == 1 and not exceeded

def test_26th_exceeded():
    _quota.clear()
    for _ in range(25):
        incr_and_check("hh-test", limit=25)
    used, exceeded = incr_and_check("hh-test", limit=25)
    assert used == 26 and exceeded

def test_pro_unlimited():
    _quota.clear()
    for _ in range(100):
        used, exceeded = incr_and_check("hh-pro", limit=10_000_000)
        assert not exceeded

def test_tenant_isolation():
    _quota.clear()
    for _ in range(25):
        incr_and_check("hh-1", limit=25)
    used, exceeded = incr_and_check("hh-2", limit=25)
    assert used == 1 and not exceeded  # hh-2 nem érinti hh-1

# tests/test_api_quota.py — FastAPI TestClient + dev headers
def test_get_quota_200(client):
    resp = client.get("/api/v1/quota", headers=dev_headers("hh-1"))
    assert resp.status_code == 200
    assert resp.json()["limit"] == 25

def test_scan_26th_402(client):
    _quota.clear()
    for _ in range(25):
        client.post("/api/v1/receipts/scan", files={"image": (b"fake", b"fake")}, headers=dev_headers("hh-free"))
    resp = client.post("/api/v1/receipts/scan", files={"image": (b"fake", b"fake")}, headers=dev_headers("hh-free"))
    assert resp.status_code == 402
    assert resp.json()["detail"]["code"] == "quota_exceeded"

def test_scan_pro_unlimited(client, monkeypatch):
    monkeypatch.setattr("app.api.is_pro", lambda t: True)
    for _ in range(26):
        resp = client.post("/api/v1/receipts/scan", files={"image": (b"fake", b"fake")}, headers=dev_headers("hh-pro"))
        assert resp.status_code in (200, 201)

def test_vision_fallback_on_timeout(client, monkeypatch):
    monkeypatch.setattr("app.vision_providers.openai_vision.OpenAIVision.extract", side_effect=TimeoutError)
    monkeypatch.setattr("app.api.is_pro", lambda t: True)
    resp = client.post("/api/v1/receipts/scan", files={"image": (b"fake", b"fake")}, headers=dev_headers("hh-pro"))
    assert resp.json()["source"] == "tesseract"  # fallback
```

Futtatás:

```bash
pytest tests/test_quota.py tests/test_vision_ocr.py tests/test_api_quota.py -v
# vagy teljes suite: pytest -q
```

### E2E (Browser Helper 1.35.0 — ezentúl BH az E2E)

Spec: `frontend/e2e/us_VISION_001_quota.spec.ts` — **BH** bulk a `fleet_run_batch`-csel:

```typescript
// BH 1.35.0 API (68 eszköz):
// P0-3 navigate storageState (quota seed), P0-4 expect polling, P0-2 fleet_run_batch bulk

test("US-VISION-01 — 24 sárga → 25 piros → 26 402 paywall; Pro 26 vision", async ({ page }) => {
  // Free: seed 24 scan via quota/reset + storageState
  await page.goto("/upload", { waitUntil: "domcontentloaded" });
  // BH: browser_inject_storage_state({origins:[{origin:"https://receipts.allthezoo.com", localStorage:[{name:"receiptlens.session", value: freeToken}]}]})
  // BH: browser_navigate({url:"/upload", storageState:{origins:[{origin:"https://receipts.allthezoo.com", localStorage:[{name:"receiptlens.locale", value:"hu"}]}]}})
  await expect(page.getByRole("progressbar", {name:"quota"})).toContainText("24/25"); // sárga
  await page.setInputFiles('input[type="file"]', "/tmp/bh-upload-sandbox/receipt.jpg"); // BH: browser_upload_file sandboxed
  await expect(page.getByRole("progressbar", {name:"quota"})).toContainText("25/25"); // piros
  await page.setInputFiles('input[type="file"]', "/tmp/bh-upload-sandbox/receipt.jpg");
  await expect(page.getByText("Pro — $5/hó")).toBeVisible(); // paywall modal
  // BH: browser_get_network_activity({path:"/api/v1/receipts/scan", status_min:402}) → 402 + quota_exceeded
  // Pro tenant ugyanott 26. → 200 vision:
  // BH: browser_inject_storage_state proToken → /upload → 26 scan → 200 + source vision
});
// 10 nyelv: t("quotaUsed") check — /upload h1 nem angol ha locale=fr
```

BH futtatás:

```bash
# Single smoke
curl -X POST http://127.0.0.1:8020/agent/navigate -H "Content-Type: application/json" \
  -d '{"url":"https://receipts.allthezoo.com/upload","storageState":{"origins":[{"origin":"https://receipts.allthezoo.com","localStorage":[{"name":"receiptlens.locale","value":"hu"}]}]}}'

# Bulk (fleet_run_batch — P0-2) — 5 case párhuzamosan:
curl -X POST http://127.0.0.1:8020/fleet/run-batch -H "Content-Type: application/json" \
  -d '{"tasks":[{"id":"US-VISION-01-free-24-yellow"},{"id":"US-VISION-01-free-25-red"},{"id":"US-VISION-01-free-26-402"},{"id":"US-VISION-01-pro-26-vision"},{"id":"US-VISION-01-i18n-10-lang"}],"workers":3,"retries":1,"reporter":{"html":true}}'

# Locale diff (P2) — QuotaBar nem angol:
curl -X POST http://127.0.0.1:8020/agent/visual-diff-locale -H "Content-Type: application/json" \
  -d '{"url":"https://receipts.allthezoo.com/upload","locales":["en","fr"],"storage_key":"receiptlens.locale","h1_selector":"h1"}'
```

Gate (kötelező):

```bash
cd frontend && npx tsc --noEmit && echo "TSC:0"
NODE_OPTIONS="--max-old-space-size=2048" npx next build 2>&1 | tail -5 && echo "BUILD:0"
curl -s http://127.0.0.1:8020/status | python3 -c "import json,sys; print(json.load(sys.stdin).get('cdp_url','?')[:40])" # 9557 = lokális
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8130/api/v1/quota | python3 -m json.tool
curl -s -X POST -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8130/api/v1/receipts/scan -F image=@/tmp/receipt.jpg -i | head -20
```

---

## Elvetve

| Opció | Miért nem |
|-------|-----------|
| Csak Vision, Tesseract kikapcsol Free-ben is | Költség + hallucináció — Tesseract 85–92% jó alap, Vision csak upsell |
| Token / credit rendszer (10 kredit/hó) | Bonyolult UX, Expensify 25 scan minta egyszerűbb |
| Külön Vision szolgáltatás / queue | Over-engineering MVP-re — sync scan elég, async már van `JobStore` |
| Unlimited free marad | Nincs urgency — VOC-ben a cap a konverzió motorja |

## Következmény

- **Fejlesztő:** lásd File-térkép — max 400 sor/file, `ruff` + `mypy`.
- **Teszt:** BE `tests/test_quota.py` + `tests/test_vision_ocr.py` + `tests/test_api_quota.py`, E2E BH `us_VISION_001_quota.spec.ts` (`fleet_run_batch` bulk).
- **Migráció:** nincs — in-memory counter (Postgresre váltáskor `quotas` tábla + havi partíció, Alembic).
- **Következő ADR:** ADR-006 (QBO/Xero sync — Pro 3. pillére).

## Kapcsolódó

- Research: `docs/research/2026-08-27-receipt-lens-revenue-features.md` (RICE 350, aiScanDesc, 25 cap)
- Kód: `app/vision_ocr.py`, `app/api.py` `_render_ai_mode`, `app/reports.py`, `frontend/lib/i18n.ts`, `frontend/app/(app)/upload/page.tsx`
- Előző: ADR-004 (Tax Pro Pack) — ugyanaz a Pro csomag
