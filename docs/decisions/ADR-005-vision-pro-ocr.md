# ADR-005: Vision AI OCR Pro — 25 scan/hó Free cap, unlimited Pro

- **Dátum:** 2026-08-27
- **Státusz:** accepted
- **Szerző:** analyst (research: `docs/research/2026-08-27-receipt-lens-revenue-features.md` — gap Tesseract 85–92% vs Veryfi 99%, RICE 350)
- **Kanban:** [aaa bbb] B) bevétel — RICE #2 (Reach 1000 × Impact 2.0 × Confidence 70% / Effort 4 hét = 350)

## Kontextus

A Tesseract 85–92% receipt-accuracy-val ma ingyen, limit nélkül megy — nincs urgency, nincs free→paid trigger. A `frontend/app/(app)/upload` `aiScanDesc` már ígéri: *"Vision AI reads blurry photos, handwritten amounts... Pro plan"* — de nincs mögötte provider, quota, vagy cap. A versenytársak mind limitálják a free scan-t (Expensify 25 SmartScan/hó, Zoho Standard-tól AI OCR), a Veryfi $0.08/receipt díja meg mutatja a piaci értéket. A ReceiptLens egyetlen self-hosted + open-source + API + 10 nyelv + offline kombó — de a minőségi különbség (elmosódott fotó, kézírás) monetizálatlan. A csomag #2 pillére a Pro-nak: minőség = upsell, mennyiség = urgency.

## Döntés

**Vision AI OCR Pro: Free 25 scan/hó Tesseract-only cap, Pro unlimited Vision (GPT-4o / Gemini) — fallback Tesseract.** A provider absztrahált, a cap tenant-havi, a Vision csak Pro-ban hívódik — költség kontrollált. Ugyanaz a Pro $5–8/hó ($49/év) a #1-gyel együtt — nem külön termék.

### Architektúra

```
app/vision_ocr.py        — már létező stub / VisionProvider absztrakció
app/vision_providers/
  openai_vision.py       — OpenAI Vision (gpt-4o) — prompt + JSON parse
  gemini_vision.py       — Gemini Vision (gemini-1.5-flash) — u.a. adapter
app/quota.py             — tenant×month counter (in-memory dict + Lock, daily rollover check)
app/ocr_router.py        — _render_ai_mode / POST /api/v1/receipts/scan routing
frontend/hooks/useQuota.ts  — quota SWR + TanStack store
frontend/components/QuotaBar.tsx  — 25-ből x, upsell CTA
```

- **Adatmodell / quota:**
  - Kulcs: `f"{tenant_id}:{YYYY-MM}"` → `count: int`, `vision_used: int`. Counter `quota_store: dict[str,int]` in-memory (`BudgetStore` minta — `threading.Lock` + dict, nincs migráció MVP-ben). Atomi `incr_and_check` — 25 felett `quota_exceeded`.
  - Számlálás: minden `POST /api/v1/receipts/scan` és `POST /v1/parse-receipt` (sync) + `POST /jobs` → `async OCR job` egyaránt növeli a havi count-ot. Vision-hívás csak akkor, ha `is_pro(tenant)` igaz — külön `vision_used` counter a monitoringhoz (nem limit).
  - Havi rollover: `YYYY-MM` kulcs automatikusan új hónapot nyit, nem kell cron. Tesztben `freezegun`-nal vagy `quota_store.clear()`-rel mockolható.
  - Fair use: Tesseract Free-ben továbbra is megy, de 25 felett ugyanaz a kép is `402`.

- **Provider absztrakció (`app/vision_ocr.py`):**

  ```python
  class VisionProvider(Protocol):
      async def extract(self, image_bytes: bytes) -> VisionResult | None: ...
  # VisionResult = {vendor, total, date, tax, currency, line_items, confidence: {source:"vision", model}}
  # openai_vision.py, gemini_vision.py implementálják — közös prompt:
  # "Extract vendor, total, date, tax, currency, line items from this receipt image.
  #  Respond ONLY JSON {vendor, total, date, tax, currency, line_items:[{name,price}], confidence}"
  # env: LLM_API_KEY, LLM_MODEL, LLM_BASE_URL / GEMINI_API_KEY — nincs új dep (httpx már bent)
  # timeout: connect 5s, read 15s; exception → None → Tesseract fallback (app/ocr.py)
  ```

- **API (FastAPI — `app/api.py` + `app/vision_ocr.py` / `app/quota.py`):**

| Metódus + útvonal | Auth | Leírás | Válasz |
|-------------------|------|--------|--------|
| `POST /api/v1/receipts/scan` (multipart `image`) | tenant | Scan — quota check → Pro ? Vision : Tesseract → count++ | `{source:"tesseract" | "vision", receipt, quota: {used, limit:25|∞ , remaining}}` + `X-Quota-Remaining` header |
| `GET /api/v1/quota` | tenant | Havi quota státusz | `{used, limit, remaining, is_pro, period:"2026-08"}` |
| `POST /api/v1/quota/reset` | admin (teszt seed) | Tenant havi counter reset / set | `{used, limit}` — **csak non-production** (`RECEIPTLENS_ENV != production`) |

  - 25 felett Free: `HTTPException(402, detail={"code":"quota_exceeded","limit":25,"used":26,"message":"Free limit reached — upgrade to Pro for unlimited Vision OCR"})` + `Retry-After: <next month>` + FE paywall. Pro: `limit = None` / `∞` — nincs 402.
  - Vision hiba (timeout, 401, 429) → `logger.warning` + Tesseract fallback — a response `source:"tesseract"` + `quota` normál.

- **Feature flag / paywall:** `app/subscriptions_api.py` `is_pro(tenant)` (ma stub — mindenki free; Pro-ra átállításkor `Actor` role vagy DB `subscriptions` táblából olvas). `lib/featureFlags.ts` `isPro` → `QuotaBar` és `Upload` paywall modal. Free-ben a 24. scannél sárga `QuotaBar` warning, 25-nél piros + upsell.

- **Frontend:**
  - `useQuota.ts` — `useSWR("/product/quota")` → `{used, limit, remaining, isPro}`.
  - `QuotaBar.tsx` — `used/25` progress bar (Free) / `∞` + zöld pipa (Pro), `aria-label="quota"`, 10 nyelven `t("quotaUsed")`, `t("upgradeToPro")`.
  - `/upload` — drag&drop mellé `QuotaBar` + `aiScanComingSoon` badge Pro-ban eltűnik (már él). `POST /scan` 402-kor catch → paywall modal (nincs unhandled rejection).
  - `app/api.py` `_render_ai_mode` már Vision+Tesseract összehasonlítást ad (`ai_result` + `tesseract_result`) — itt a quota előtte fut, a Vision csak Pro-ban.
  - 400 sor/file limit: `quota.py` ≤ 200, `openai_vision.py` ≤ 180.

- **Biztonság / költség-kontroll:** tenant-isolation a counter kulcsban, nincs cross-tenant leak. Vision provider API key rotálható env-ben, nincs logban. No-per-doc charge — hosting költség fedezi ($5–20/hó).

## Elvetve

| Opció | Miért nem |
|-------|-----------|
| Csak Vision, Tesseract kikapcsol Free-ben is | Költség + hallucináció — Tesseract 85–92% jó alap, Vision csak upsell |
| Token / credit rendszer (10 kredit/hó) | Bonyolult UX, Expensify 25 scan minta egyszerűbb |
| Külön Vision szolgáltatás / queue | Over-engineering MVP-re — sync scan elég, async már van `JobStore` |
| Unlimited free marad | Nincs urgency — VOC-ben a cap a konverzió motorja |

## Következmény

- **Fejlesztő:** `app/quota.py` + `app/vision_providers/` (2 adapter) + `app/api.py` wiring (`POST /scan` előtti check), FE `useQuota.ts` + `QuotaBar.tsx` + `/upload` integráció + i18n `quotaUsed`, `upgradeToPro` 10 nyelven. Max 400 sor/file, `ruff` + `mypy`.
- **Teszt — BE:** `tests/test_quota.py` (25 alatt 200, 26. 402, Pro ∞, hónapváltás új kulcs), `tests/test_vision_ocr.py` (mock Vision success → source vision, timeout → tesseract fallback, 402 quota, tenant isolation).
- **Teszt — E2E (Browser Helper 1.35.0 — BH az E2E):**
  - `frontend/e2e/us_VISION_001_quota.spec.ts` — BH `browser_navigate` + `browser_inject_storage_state` (seed 24 scan) + `browser_interact` (Upload → `browser_upload_file` sandboxed `/tmp/bh-upload-sandbox/receipt.jpg`) + `browser_wait_for_condition` (quota bar `24/25` → sárga) → 26. upload `browser_get_network_activity` `402 quota_exceeded` + paywall modal `expect` polling. Pro tenant ugyanott 26. `200 vision`. 10 nyelv `t("quotaUsed")` check.
  - `TSC 0 BUILD 0`, `curl GET /api/v1/quota` + `POST /scan` 402 proof, `fleet_run_batch` bulk a BH-n.
- **Migráció:** nincs — in-memory counter (Postgresre váltáskor `quotas` tábla + havi partíció, Alembic).
- **Következő ADR:** ADR-006 (QBO/Xero sync — Pro 3. pillére).

## Kapcsolódó

- Research: `docs/research/2026-08-27-receipt-lens-revenue-features.md` (RICE 350, aiScanDesc, 25 cap)
- Kód: `app/vision_ocr.py`, `app/api.py` `_render_ai_mode`, `app/reports.py`, `frontend/lib/i18n.ts`, `frontend/app/(app)/upload/page.tsx`
- Előző: ADR-004 (Tax Pro Pack) — ugyanaz a Pro csomag
