# ADR-006: QBO/Xero Direct Sync + Accountant Invite

- **Dátum:** 2026-08-27
- **Státusz:** accepted
- **Szerző:** analyst (research: `docs/research/2026-08-27-receipt-lens-revenue-features.md` — VOC #3, gap integrations, RICE 255)
- **Kanban:** [aaa bbb] B) bevétel — RICE #3 (Reach 600 × Impact 3.0 × Confidence 85% / Effort 6 hét = 255)

## Kontextus

A ReceiptLens ma CSV/PDF exportot ad — a felhasználó manuálisan importálja QBO/Xero-ba. A VOC 3. patternje: *"The Xero integration alone is worth every penny"* (receiptreader.ai), *"Rather than bringing them a pile of bills, I need only drop them on Dext"* (Trustpilot). Ez a legtisztább free→paid küszöb: Free = scan + local + CSV, Pro = direct sync + accountant invite. A 6 versenytársból 4-nél az accounting sync fizetős (Expensify Control $9, Dext $25, Zoho Standard $3, Klippa €5). ReceiptLens nem adja — 3. pillér a Pro csomagban (ADR-004 Tax + ADR-005 Vision).

JTBD: *"Amikor a könyvelőm kéri az anyagot, szeretném egy linkkel megosztani, ne emailben küldözgessek PDF-et."*

## Döntés

**QuickBooks Online + Xero direct sync (OAuth 2.0 + API push) + accountant invite link (read-only shared view).** MVP: QBO (Intuit OAuth — `app/intuit_oauth.py` + `app/connection_service.py` scaffold már van) + Xero (Xero OAuth). Nincs új Python csomag (httpx + cryptography + secrets — stdlib/dep már bent).

### Komponensek

| Komponens | File | Leírás |
|-----------|------|--------|
| QBO OAuth | `app/qbo_service.py` | Authorization-code flow, token exchange, refresh, realm_id. `httpx + cryptography` (mint `google_oidc.py`) |
| Xero OAuth | `app/xero_service.py` | U.a. Xero auth endpoints, tenant_id, scopes |
| Credential store | `app/credential_store.py` (meglévő bővítés) | `qbo_tokens`, `xero_tokens` — encrypted (Fernet, `CREDENTIAL_KEY`), tenant-scoped |
| Sync orchestrator | `app/sync_service.py` | `push_to_qbo(tenant, date_from, date_to)`, `push_to_xero(...)` — batch 50/req, idempotent (`ext_ref_id`) |
| Accountant invite | `app/accountant_invite.py` | `create_invite(tenant) → token`, `resolve_invite(token) → tenant_id` — 30 nap expiry, read-only |
| API router | `app/api.py` (bővítés) | 6 végpont (lásd alább) |
| FE: integrations | `frontend/app/(app)/integrations/page.tsx` | Connection list + CTA + status badge |
| FE: invite modal | `frontend/components/InviteAccountantModal.tsx` | Link másolás + expiry info |

### API végpontok (FastAPI — Pro-only, 402 ha Free)

| Metódus + útvonal | Auth | Leírás | Válasz |
|-------------------|------|--------|--------|
| `GET /api/v1/integrations/qbo/start` | tenant (Pro) | OAuth init → Intuit authorization URL redirect | `302 redirect` |
| `GET /api/v1/integrations/qbo/callback` | — (Intuit vissza) | Token exchange + store | redirect `/integrations` |
| `GET /api/v1/integrations/xero/start` | tenant (Pro) | OAuth init → Xero authorization URL redirect | `302 redirect` |
| `GET /api/v1/integrations/xero/callback` | — (Xero vissza) | Token exchange + store | redirect `/integrations` |
| `POST /api/v1/integrations/{provider}/sync` `{date_from, date_to}` | tenant (Pro) | Push receipts → QBO/Xero (batch 50) | `{pushed, failed, errors: [{receipt_id, error}]}` |
| `GET /api/v1/integrations` | tenant | List connections | `[{provider, status, org_name, connected_at}]` |
| `GET /api/v1/accountant/invite` | tenant (Pro) | Generate invite link | `{url, expires_at}` |
| `GET /accountant/{token}` | — (token a URL-ben) | Read-only receipt view (no sidebar, no Topbar) | HTML response |

### OAuth flow (QBO példa)

```
GET /api/v1/integrations/qbo/start
  → state=csrf_nonce HttpOnly cookie
  → redirect: https://appcenter.intuit.com/app/connect/oauth2
      ?client_id=...&redirect_uri=...&response_type=code&scope=com.intuit.quickbooks.accounting&state=...

GET /api/v1/integrations/qbo/callback?realmId=...&code=...
  → POST https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer
      {grant_type=authorization_code, code=...}
  → {access_token, refresh_token, expires_in}
  → encrypt → credential_store.save(qbo_tokens, {realm_id, access, refresh, expires})
  → redirect /integrations
```

### Sync (sync_service.py)

- `push_to_qbo(connection_id, tenant_id, date_from, date_to) → SyncResult`:
  1. Receipts from `receipt_store.list(date_from, date_to, tenant_id)`
  2. Filter: skip if `qbo_sync_id` not None (idempotencia)
  3. QBO POST `/v3/company/{realmId}/purchase` — `{TotalAmt, PaymentType:"Cash", Line:[{DetailType:"AccountBasedExpenseLineDetail", Amount, AccountRef:{value:"7"}, Description: vendor}]}` — batch 50/request
  4. Response `Purchase.Id` → write `qbo_sync_id` vissza a receiptbe (in-memory update)
  5. Error per item → `{receipt_id, error: provider.message}`, nem az egész batch bukik

- `push_to_xero(...)` ugyanígy: POST `/api.xro/2.0/Purchases` — `{Type:"SPEND", LineItems:[...]}`

### Accountant invite

- `create_invite(tenant_id, days_valid=30) → str`:
  - `token = secrets.token_urlsafe(32)`, store `{token → {tenant_id, expires_at}}`
  - URL: `https://receipts.allthezoo.com/accountant/{token}`
  - Pro-only → 402 Free

- `GET /accountant/{token}` → resolve_invite → receipt list (read-only view):
  - **Layout nélkül** (nincs Topbar, nincs sidebar — a könyvelő nem fog bejelentkezni)
  - ReceiptCard lista: vendor, date, category, total, status — `useSWR` nélkül, SSR + embedded data
  - `noindex` meta robots (ne indexelje Google)

### Feature flag / paywall

- `is_pro(tenant)` — `app/subscriptions_api.py` / `app/product_api.py` check. Ma stub: mindenki Free. Pro-ra átállításkor entitlement check DB-ből (`Actor` + `subscriptions` tábla, `entitlement_level`).
- Free-ben: `/integrations` oldal látja a gombokat de `connect` → 402 paywall modal: *"Pro — $5/hó"*.
- `lib/featureFlags.ts` → `isPro` prop → `InviteAccountantModal` és sync gomb disabled/402 handling.

### Frontend

- `/integrations` (`app/(app)/integrations/page.tsx` ≤ 350 sor):
  - `useSWR("/product/integrations")` → connection list
  - QBO card: company name, status (Connected/Disconnected), `Sync now` gomb + date range picker
  - Xero card: u.a.
  - 402 paywall modal ha nincs Pro.
  - `t("integrationsTitle")`, `t("connectQuickBooks")`, `t("connectXero")`, `t("syncNow")` — 10 nyelv `lib/i18n.ts`.

- `InviteAccountantModal.tsx` (≤ 120 sor):
  - `POST /api/v1/accountant/invite` → copy link gomb + expiry info
  - `navigator.clipboard.writeText(url)` + toast: `t("inviteCopied")`

- `AccountantView` (SSR route `/accountant/[token]`):
  - `resolve_invite(token)` server-side → receipt list SSR render (Next.js App Router, `page.tsx`)
  - No Topbar, no Sidebar — minimal receipt table

### Elvetve

| Opció | Miért nem |
|-------|-----------|
| Full sync engine (real-time webhook + delta) | Over-engineering MVP — batch push elég, webhook később |
| NetSuite/Sage integráció nap 1 | B2B market, nem háztartás — később |
| Token alapú invite helyett auth kérés a könyvelőnek | UX gát — könyvelők nem fognak regisztrálni |
| Külön microservice sync-be | Nem lean — 1 router + 1 service elég MVP-ben |

## Következmény

- **Fejlesztő:** `app/qbo_service.py` + `app/xero_service.py` + `app/sync_service.py` + `app/accountant_invite.py` + `app/api.py` bővítés (6 route), FE `integrations/page.tsx` + `InviteAccountantModal.tsx` + i18n 4 kulcs ×10 nyelv. Max 400 sor/file, `ruff` + `mypy`.
- **Teszt — BE:**
  - `tests/test_qbo_oauth.py` — mock Intuit token exchange (httpx mock), 200 callback, invalid code 400
  - `tests/test_xero_oauth.py` — u.a. Xero mock
  - `tests/test_sync_service.py` — push_to_qbo table-driven: 5 receipts → `{pushed:5, failed:0}`, 3 already synced → skip, 1 error → `{pushed:4, failed:1, errors:[{receipt_id, error}]}`, Free tenant → 402
  - `tests/test_accountant_invite.py` — create → resolve 200, expired → None, tenant isolation (token A nem látja tenant B adatait)
- **Teszt — E2E (Browser Helper 1.35.0 — BH):**
  - `frontend/e2e/us_SYNC_001_qbo.spec.ts` — BH `browser_navigate("/integrations")` + `browser_inject_storage_state` (Pro session seed) + `browser_interact` (Connect QuickBooks click → mock OAuth redirect → callback → status "Connected") + `browser_interact` (Sync now → `browser_get_network_activity` `/api/v1/integrations/qbo/sync` 200 + `{pushed: N}`) + `browser_interact` (Invite accountant → modal link visible + copy). 402 case: Free user → paywall modal. 10 nyelv `t("connectQuickBooks")`.
  - `TSC 0 BUILD 0`, `fleet_run_batch` bulk a BH-n.
- **Migráció:** nincs — in-memory `connections` + `invite_tokens` dicts (Postgresre váltáskor `connections` + `invite_tokens` táblák, Alembic).
- **Előző:** ADR-005 (Vision Pro OCR) — ugyanaz a Pro csomag.

## Kapcsolódó

- Research: `docs/research/2026-08-27-receipt-lens-revenue-features.md` (VOC #3, RICE 255, Dext/Expensify pricing)
- Kód: `app/intuit_oauth.py` (meglévő scaffold), `app/connection_service.py` (meglévő), `app/api.py`, `frontend/app/(app)/integrations/page.tsx`
- Előző: ADR-004 (Tax), ADR-005 (Vision) — egy Pro csomag (5-8/hó, $49/év)
