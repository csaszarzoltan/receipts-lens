# ADR-006: QBO/Xero Direct Sync + Accountant Invite

- **Dátum:** 2026-08-27
- **Státusz:** accepted
- **Szerző:** analyst (research: `docs/research/2026-08-27-receipt-lens-revenue-features.md` — VOC #3, gap integrations, RICE 255)
- **Kanban:** [aaa bbb] B) bevétel — RICE #3 (Reach 600 × Impact 3.0 × Confidence 85% / Effort 6 hét = 255)

## Kontextus

A ReceiptLens ma CSV/PDF exportot ad — a felhasználó manuálisan importálja QBO/Xero-ba. A VOC 3. patternje: *"The Xero integration alone is worth every penny"* (receiptreader.ai), *"Rather than bringing them a pile of bills, I need only drop them on Dext"* (Trustpilot). Ez a legtisztább free→paid küszöb: Free = scan + local + CSV, Pro = direct sync + accountant invite. A 6 versenytársból 4-nél az accounting sync fizetős (Expensify Control $9, Dext $25, Zoho Standard $3, Klippa €5). ReceiptLens nem adja — 3. pillér a Pro csomagban (ADR-004 Tax + ADR-005 Vision).

JTBD: *"Amikor a könyvelőm kéri az anyagot, szeretném egy linkkel megosztani, ne emailben küldözgessek PDF-et."*

## Döntés

**QuickBooks Online + Xero direct sync (OAuth 2.0 + API push) + accountant invite link (read-only shared view).** MVP: QBO (Intuit OAuth — `app/intuit_oauth.py` + `app/connection_service.py` scaffold már van) + Xero (Xero OAuth). Nincs új Python csomag (httpx + cryptography + secrets — stdlib/dep már bent, `google_oidc.py` minta).

### 1) File-térkép (mit hozol létre / mit módosítasz)

| Művelet | File | Leírás | Sor-limit |
|---------|------|--------|-----------|
| Új | `app/qbo_service.py` | QBO OAuth: start URL, callback token exchange, refresh | ≤ 250 |
| Új | `app/xero_service.py` | Xero OAuth: u.a. Xero auth endpoints | ≤ 250 |
| Módosít | `app/credential_store.py` | `qbo_tokens`, `xero_tokens` dict — encrypted (Fernet, `CREDENTIAL_KEY`), tenant-scoped — bővítés | 40 sor |
| Új | `app/sync_service.py` | `push_to_qbo()`, `push_to_xero()` — batch 50/req, idempotent (`qbo_sync_id`) | ≤ 250 |
| Új | `app/accountant_invite.py` | `create_invite()`, `resolve_invite()` — token 30 nap, read-only | ≤ 180 |
| Új | `app/sync_api.py` | FastAPI router — 8 végpont (lásd API tábla) | ≤ 300 |
| Módosít | `app/api.py` | `from app.sync_api import router as sync_router` + `app.include_router(sync_router)` | 2 sor |
| Módosít | `app/reports.py` | `ConfidenceReceipt` bővítés: `qbo_sync_id`, `xero_sync_id` (default None) | 10 sor |
| Módosít | `app/subscriptions_api.py` | `is_pro(tenant_id) -> bool` stub (mint ADR-004/005 — `return False`) | 15 sor |
| Új | `frontend/app/(app)/integrations/page.tsx` | Connection list + CTA + status badge + Sync now | ≤ 350 |
| Új | `frontend/components/InviteAccountantModal.tsx` | Link másolás + expiry info | ≤ 120 |
| Új | `frontend/app/accountant/[token]/page.tsx` | SSR read-only view (no Topbar, no Sidebar) | ≤ 250 |
| Módosít | `frontend/lib/i18n.ts` | 4 kulcs ×10 nyelv: `integrationsTitle`, `connectQuickBooks`, `connectXero`, `syncNow`, `inviteCopied` | 30 sor |
| Módosít | `frontend/lib/featureFlags.ts` | `isPro` helper | 15 sor |

### 2) Adatmodell

```python
# app/reports.py — ConfidenceReceipt bővítés (nem tör meglévőt)
@dataclass
class ConfidenceReceipt:
    merchant: str
    total: float | None
    # ... meglévő mezők ...
    qbo_sync_id: str | None = None    # QBO Purchase.Id — ha nem None, már synced
    xero_sync_id: str | None = None   # Xero PurchaseID

# app/credential_store.py — bővítés (Fernet encrypted, tenant-scoped)
# In-memory dict (BudgetStore minta: Lock + dict, nincs migráció MVP-ben)
_qbo_tokens: dict[str, dict] = {}    # tenant_id -> {realm_id, access_token (enc), refresh_token (enc), expires_at}
_xero_tokens: dict[str, dict] = {}   # tenant_id -> {tenant_id_xero, access_token (enc), refresh_token (enc), expires_at}

# app/accountant_invite.py — in-memory (BudgetStore minta)
_invites: dict[str, dict] = {}       # token -> {tenant_id, created_at, expires_at}
_lock = threading.Lock()

# Postgresre váltáskor Alembic:
# ALTER TABLE receipts ADD COLUMN qbo_sync_id TEXT, ADD COLUMN xero_sync_id TEXT;
# CREATE TABLE connections (tenant_id TEXT, provider TEXT, realm_id TEXT, access_enc TEXT, ...);
# CREATE TABLE invite_tokens (token TEXT PRIMARY KEY, tenant_id TEXT, expires_at TIMESTAMPTZ);
```

### 3) OAuth flow (QBO példa — Xero analóg)

```
GET /api/v1/integrations/qbo/start  (tenant, Pro-only → 402 ha Free)
  → state = secrets.token_urlsafe(32), set HttpOnly cookie "qbo_state"
  → redirect 302: https://appcenter.intuit.com/app/connect/oauth2
      ?client_id=${INTUIT_CLIENT_ID}
      &redirect_uri=${INTUIT_REDIRECT_URI}   # https://receipts.allthezoo.com/api/v1/integrations/qbo/callback
      &response_type=code
      &scope=com.intuit.quickbooks.accounting
      &state=${state}

GET /api/v1/integrations/qbo/callback?realmId=123&code=QBO_CODE&state=STATE
  → verify state cookie == query state (CSRF) → 400 ha nem egyezik
  → POST https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer
      Basic auth: base64(client_id:client_secret)
      body: {grant_type: "authorization_code", code: QBO_CODE, redirect_uri: ...}
  → {access_token, refresh_token, expires_in: 3600, x_refresh_token_expires_in: 8723800}
  → encrypt(access_token, refresh_token) via Fernet(CREDENTIAL_KEY)
  → store _qbo_tokens[tenant_id] = {realm_id, access_enc, refresh_enc, expires_at: now+3600}
  → redirect 302: /integrations  (FE success toast)
```

Xero:

```
GET /api/v1/integrations/xero/start
  → state cookie
  → redirect: https://login.xero.com/identity/connect/authorize
      ?response_type=code&client_id=${XERO_CLIENT_ID}&redirect_uri=...&scope=accounting.transactions&state=...

GET /api/v1/integrations/xero/callback?code=XERO_CODE&state=STATE
  → POST https://identity.xero.com/connect/token  (grant_type=authorization_code)
  → {access_token, refresh_token}
  → GET https://api.xero.com/connections  (access_token) → [{tenantId, tenantName}]
  → encrypt + store _xero_tokens[tenant_id]
  → redirect /integrations
```

Env (már van `.env` + `CREDENTIAL_KEY` — nincs új secret típus):

```
INTUIT_CLIENT_ID=...
INTUIT_CLIENT_SECRET=...
INTUIT_REDIRECT_URI=https://receipts.allthezoo.com/api/v1/integrations/qbo/callback
XERO_CLIENT_ID=...
XERO_CLIENT_SECRET=...
XERO_REDIRECT_URI=https://receipts.allthezoo.com/api/v1/integrations/xero/callback
CREDENTIAL_KEY=<Fernet key — már létezik>
```

Refresh: `get_valid_token(tenant_id)` → ha `expires_at - now < 300s` → `POST .../tokens/bearer {grant_type: refresh_token}` → update store (sliding, mint `google_oidc.py`).

### 4) API (FastAPI — `app/sync_api.py` router, prefix `/api/v1`)

| # | Metódus + útvonal | Auth | Pro gate | Leírás | Request | Response (200 / 402) |
|---|-------------------|------|----------|--------|---------|----------------------|
| 1 | `GET /api/v1/integrations/qbo/start` | tenant | **Pro-only → 402** | OAuth init → Intuit URL redirect | — | `302 redirect` / 402 `{"detail":{"code":"pro_required"}}` |
| 2 | `GET /api/v1/integrations/qbo/callback?realmId=&code=&state=` | — (Intuit) | state CSRF | Token exchange + store | query | `302 /integrations` / 400 bad state |
| 3 | `GET /api/v1/integrations/xero/start` | tenant | **Pro-only → 402** | OAuth init → Xero URL redirect | — | `302` / 402 |
| 4 | `GET /api/v1/integrations/xero/callback?code=&state=` | — (Xero) | state CSRF | Token exchange + store | query | `302 /integrations` / 400 |
| 5 | `POST /api/v1/integrations/{provider}/sync` | tenant | **Pro-only → 402** | Push receipts → QBO/Xero (batch 50) | `{date_from:"2026-07-01", date_to:"2026-08-27"}` | `{pushed:5, failed:1, errors:[{receipt_id, error:"Invalid account"}]}` |
| 6 | `GET /api/v1/integrations` | tenant | — (list látszik Free-ben is) | List connections | — | `{connections:[{provider:"qbo", status:"connected", org_name:"Acme LLC", realm_id:"123", connected_at:"..."}, {provider:"xero", ...}]}` |
| 7 | `GET /api/v1/accountant/invite` | tenant | **Pro-only → 402** | Generate invite link | — | `{url:"https://receipts.allthezoo.com/accountant/abc123...", expires_at:"2026-09-26T..."}` |
| 8 | `POST /api/v1/accountant/invite/revoke` | tenant | Pro | Revoke invite | `{token:"abc..."}` | `{revoked:true}` |
| 9 | `GET /accountant/{token}` | — (token URL-ben) | public de token-gated | Read-only receipt view | path `token` | HTML SSR (200) / 404 expired |

Pro gate minta (mint ADR-004):

```python
from app.subscriptions_api import is_pro
if not is_pro(tenant_id):
    raise HTTPException(status_code=402, detail={"code":"pro_required","message":"Pro required — $5/mo"})
```

### 5) Sync orchestrator (`app/sync_service.py`)

```python
@dataclass
class SyncResult:
    pushed: int
    failed: int
    errors: list[dict]  # [{receipt_id, error}]
    provider: str

def push_to_qbo(tenant_id: str, date_from: str, date_to: str) -> SyncResult:
    # 1. Receipts
    receipts = receipt_store.list(date_from=date_from, date_to=date_to, tenant_id=tenant_id)
    # 2. Filter: skip if qbo_sync_id is not None (idempotencia)
    to_push = [r for r in receipts if r.qbo_sync_id is None]
    # 3. Batch 50/request — QBO rate limit
    pushed, failed, errors = 0, 0, []
    token = get_valid_token(tenant_id, provider="qbo")  # decrypt + refresh ha kell
    for batch in chunked(to_push, 50):
        for receipt in batch:
            try:
                # QBO POST /v3/company/{realmId}/purchase
                # Body: {TotalAmt: receipt.total, PaymentType:"Cash",
                #        Line:[{DetailType:"AccountBasedExpenseLineDetail",
                #               Amount: receipt.total,
                #               AccountRef:{value:"7"},  # default expense account
                #               Description: receipt.merchant}]}
                resp = httpx.post(f"https://quickbooks.api.intuit.com/v3/company/{realm_id}/purchase",
                                  headers={"Authorization": f"Bearer {token}", "Accept":"application/json"},
                                  json={...}, timeout=15)
                resp.raise_for_status()
                purchase_id = resp.json()["Purchase"]["Id"]
                receipt.qbo_sync_id = purchase_id  # in-memory update
                pushed += 1
            except Exception as e:
                failed += 1
                errors.append({"receipt_id": receipt.receipt_id, "error": str(e)[:200]})
    return SyncResult(pushed=pushed, failed=failed, errors=errors, provider="qbo")

def push_to_xero(tenant_id, date_from, date_to) -> SyncResult:
    # U.a.: POST https://api.xero.com/api.xro/2.0/Purchases
    # Body: {Type:"SPEND", Contact:{Name: receipt.merchant}, LineItems:[{Description, Quantity:1, UnitAmount: total, AccountCode:"400"}]}
    ...
```

- Hiba per item — nem az egész batch bukik. `errors` itemized vissza a FE-nek.
- Idempotencia: `qbo_sync_id` / `xero_sync_id` check — ha már van, skip (második `Sync now` nem duplikál).
- Timeout 15s, `raise_for_status` → error dict.

### 6) Accountant invite (`app/accountant_invite.py`)

```python
import secrets, threading
from datetime import UTC, datetime, timedelta

_invites: dict[str, dict] = {}
_lock = threading.Lock()

def create_invite(tenant_id: str, days_valid: int = 30) -> dict:
    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    expires_at = now + timedelta(days=days_valid)
    with _lock:
        _invites[token] = {"tenant_id": tenant_id, "created_at": now.isoformat(), "expires_at": expires_at.isoformat()}
    return {"token": token, "url": f"https://receipts.allthezoo.com/accountant/{token}", "expires_at": expires_at.isoformat()}

def resolve_invite(token: str) -> dict | None:
    with _lock:
        data = _invites.get(token)
    if not data:
        return None
    if datetime.fromisoformat(data["expires_at"]) < datetime.now(UTC):
        with _lock:
            _invites.pop(token, None)
        return None  # expired
    return data  # {tenant_id, created_at, expires_at}

def revoke_invite(token: str, tenant_id: str) -> bool:
    with _lock:
        data = _invites.get(token)
        if not data or data["tenant_id"] != tenant_id:
            return False
        _invites.pop(token)
        return True
```

- `GET /accountant/{token}` SSR: `resolve_invite(token)` → `None` → 404 page (`"Invite expired or invalid"`), `Some` → `receipt_store.list(tenant_id=...)` → HTML table (no `fetch` a klienton, SSR embedded).
- `noindex` meta: `<meta name="robots" content="noindex, nofollow">` — ne indexelje Google.

### 7) Frontend

- **`/integrations`** (`frontend/app/(app)/integrations/page.tsx` ≤ 350 sor):
  - `const {data} = useSWR("/product/integrations", fetcher)` → `connections` lista.
  - QBO kártya: `org_name`, `status` (`connected` zöld, `disconnected` szürke, `reauth_required` sárga), `Connect QuickBooks` CTA → `window.location.href = "/api/v1/integrations/qbo/start"` (redirect). Xero kártya u.a.
  - `Sync now` gomb + date range picker (`<input type="date">` from/to, default 30 nap) → `POST /api/v1/integrations/{provider}/sync` → toast `t("pushedCount", {n: result.pushed})` + error lista ha `failed>0`.
  - Free teaser: ha `!isPro` → gombok disabled + overlay paywall modal (`"Pro — $5/hó, $49/év"`, CTA `/settings/billing`), `GET /integrations` list de `start` → 402 → modal.
  - i18n: `t("integrationsTitle")`, `t("connectQuickBooks")`, `t("connectXero")`, `t("syncNow")`, `t("inviteAccountant")` — 10 nyelv.

- **`InviteAccountantModal.tsx`** (≤ 120 sor):
  - `POST /api/v1/accountant/invite` → `{url, expires_at}` → `<input readonly value={url}>` + Copy gomb (`navigator.clipboard.writeText(url)` + toast `t("inviteCopied")` 2s) + expiry info `t("expiresAt", {date: formatDate(expires_at)})` + Revoke gomb.

- **`/accountant/[token]/page.tsx`** (SSR, ≤ 250 sor, App Router):
  - `export default async function AccountantPage({params}:{params:{token:string}})` — server component, `resolve_invite(params.token)` (BE `GET /api/v1/accountant/resolve/{token}` proxy vagy direct DB) → ha None → `notFound()`.
  - Layout nélkül: `return (<html><body className="p-8"><h1>Receipts — read only</h1><table>...</table></body></html>)` — nincs `Topbar`, nincs `Sidebar` (a könyvelő nem fog bejelentkezni).
  - ReceiptCard lista helyett minimal `<table>` (vendor | date | category | total | status) — `useSWR` nélkül, SSR + `noindex`.

### 8) Biztonság / validáció

- Token titkosítás: Fernet(`CREDENTIAL_KEY`) — `credential_store.py` `encrypt`/`decrypt` helper, nem plain.
- OAuth state CSRF: `state` HttpOnly cookie + query compare → 400 ha mismatch.
- Accountant read-only: nincs delete/upload/modify a `/accountant/{token}` oldalon — csak GET list.
- Tenant-isolation: minden `receipt_store.list(tenant_id)` + `credential_store.get(tenant_id)` + `invite.resolve` tenant check.
- Rate limit: `RateLimitMiddleware` alatt (mint minden `/api/v1/*`).
- Invite expiry: 30 nap, `resolve` törli expired-et.

---

## Lépésről lépésre fejlesztési útmutató (bárki végig tudja vinni)

### Előfeltétel

```bash
cd /home/zoltan/receipts-lens
git pull
python3 -m venv .venv && source .venv/bin/activate
pip install -e .[dev]  # httpx, cryptography, reportlab már bent — új dep nem kell
cd frontend && npm install && cd ..

# Env — Intuit/Xero developer console-ból (sandbox credentials elég MVP-hez):
cat >> .env <<'EOF'
INTUIT_CLIENT_ID=...
INTUIT_CLIENT_SECRET=...
INTUIT_REDIRECT_URI=https://receipts.allthezoo.com/api/v1/integrations/qbo/callback
XERO_CLIENT_ID=...
XERO_CLIENT_SECRET=...
XERO_REDIRECT_URI=https://receipts.allthezoo.com/api/v1/integrations/xero/callback
# CREDENTIAL_KEY már létezik — ne írd felül
EOF
```

### Lépések (sorrend kötelező — max 3 file / lépés)

1. **Credential store bővítés + Invite store (BE alap):**
   - Módosítsd `app/credential_store.py` — add `_qbo_tokens`, `_xero_tokens` dict + `save_qbo(tenant, data)`, `get_qbo(tenant)`, `save_xero`, `get_xero` (Fernet encrypt/decrypt, tenant key).
   - Hozd létre `app/accountant_invite.py` — másold a fenti `create_invite` + `resolve_invite` + `revoke_invite` struktúrát (≤ 180 sor).
   - Írd meg `tests/test_accountant_invite.py`: `test_create_resolve_200`, `test_expired_None` (mock `datetime.now` +31 nap), `test_tenant_isolation` (token A nem látja tenant B adatait), `test_revoke` (revoke → None).

2. **QBO + Xero OAuth (BE):**
   - Hozd létre `app/qbo_service.py` — `def build_authorize_url(state) -> str`, `async def exchange_code(code, realm_id) -> dict`, `async def refresh_token(tenant)` (httpx, Basic auth, timeout 15s). Mint `google_oidc.py`.
   - Hozd létre `app/xero_service.py` — u.a. Xero endpoints (`https://identity.xero.com/connect/token`, `https://api.xero.com/connections`).
   - Írd meg `tests/test_qbo_oauth.py` + `tests/test_xero_oauth.py` — httpx mock (`respx` vagy `monkeypatch` httpx.Client.post) → 200 callback, invalid code 400, state mismatch 400.

3. **Sync orchestrator (BE):**
   - Hozd létre `app/sync_service.py` — `push_to_qbo` + `push_to_xero` (batch 50, idempotent `qbo_sync_id` skip, per-item try/except).
   - Módosítsd `app/reports.py` — `ConfidenceReceipt` 2 mező (`qbo_sync_id`, `xero_sync_id` default None).
   - Írd meg `tests/test_sync_service.py` table-driven: `test_push_5_pushed` (5 receipts → `{pushed:5, failed:0}`), `test_skip_already_synced` (3 synced → skip), `test_one_error` (QBO 400 egy itemre → `{pushed:4, failed:1, errors:[{receipt_id}]}`), `test_free_402` (is_pro=False → 402).

4. **API router (BE végpontok):**
   - Hozd létre `app/sync_api.py` — `APIRouter(prefix="/api/v1")`, 8 route a táblából. Auth: `api_v1_actor` / `Header Authorization` (másold `app/api.py` mintát). Pro gate: `if not is_pro(tenant_id): raise HTTPException(402, ...)`.
   - Módosítsd `app/api.py`: `from app.sync_api import router as sync_router` + `app.include_router(sync_router)`.
   - Módosítsd `app/subscriptions_api.py`: `def is_pro(tenant_id: str) -> bool: return False` (stub).

5. **Frontend — i18n + Integrations oldal + Invite modal:**
   - Módosítsd `frontend/lib/i18n.ts` — 5 kulcs ×10 nyelv: `integrationsTitle`, `connectQuickBooks`, `connectXero`, `syncNow`, `inviteCopied` (kövesd ADR-003 monolit pattern-t).
   - Módosítsd `frontend/lib/featureFlags.ts` — `export const isPro = (tenant) => false` stub.
   - Hozd létre `frontend/app/(app)/integrations/page.tsx` (≤ 350) + `frontend/components/InviteAccountantModal.tsx` (≤ 120) — lásd 7) Frontend.

6. **Frontend — Accountant read-only view:**
   - Hozd létre `frontend/app/accountant/[token]/page.tsx` — SSR server component, `resolve_invite` + receipt table (≤ 250 sor, no Topbar/Sidebar, `noindex`).

7. **Teszt + build gate (kötelező minden lépés után):**

```bash
# BE gate
ruff check app/qbo_service.py app/xero_service.py app/sync_service.py app/accountant_invite.py app/sync_api.py
mypy app/qbo_service.py app/xero_service.py app/sync_service.py app/accountant_invite.py
pytest tests/test_qbo_oauth.py tests/test_xero_oauth.py tests/test_sync_service.py tests/test_accountant_invite.py tests/test_sync_api.py -q

# FE gate
cd frontend && npx tsc --noEmit && NODE_OPTIONS="--max-old-space-size=2048" npx next build 2>&1 | tail -10
cd .. && python3 -m py_compile app/qbo_service.py app/xero_service.py app/sync_service.py app/accountant_invite.py app/sync_api.py
```

---

## Tesztelési útmutató (bárki le tudja futtatni)

### BE tesztek (pytest — `tests/test_qbo_oauth.py`, `tests/test_sync_service.py`, `tests/test_accountant_invite.py`)

Sablon — másold `tests/test_budgets.py` / `tests/test_auth_api.py` mintájára:

```python
# tests/test_qbo_oauth.py — httpx mock
import respx  # vagy monkeypatch httpx.Client

@respx.mock
def test_qbo_callback_200(client):
    respx.post("https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer").mock(
        return_value=httpx.Response(200, json={"access_token":"at","refresh_token":"rt","expires_in":3600}))
    resp = client.get("/api/v1/integrations/qbo/callback?realmId=123&code=CODE&state=STATE",
                      cookies={"qbo_state": "STATE"}, headers=dev_headers("hh-1"))
    assert resp.status_code in (302, 200)

def test_qbo_state_mismatch_400(client):
    resp = client.get("/api/v1/integrations/qbo/callback?realmId=123&code=CODE&state=BAD",
                      cookies={"qbo_state": "GOOD"}, headers=dev_headers("hh-1"))
    assert resp.status_code == 400

# tests/test_sync_service.py
def test_push_5_pushed(monkeypatch):
    monkeypatch.setattr("app.sync_service.httpx.post", lambda *a, **kw: MockResponse(200, {"Purchase":{"Id":"p1"}}))
    result = push_to_qbo(tenant_id="hh-1", date_from="2026-07-01", date_to="2026-08-27")
    assert result.pushed == 5 and result.failed == 0

def test_free_402(client):
    resp = client.post("/api/v1/integrations/qbo/sync", json={"date_from":"2026-07-01","date_to":"2026-08-27"}, headers=dev_headers("hh-free"))
    assert resp.status_code == 402
    assert resp.json()["detail"]["code"] == "pro_required"

# tests/test_accountant_invite.py
def test_create_resolve():
    inv = create_invite("hh-1", days_valid=30)
    assert resolve_invite(inv["token"])["tenant_id"] == "hh-1"

def test_expired_None(monkeypatch):
    inv = create_invite("hh-1", days_valid=0)
    # mock now +1 nap
    assert resolve_invite(inv["token"]) is None

def test_tenant_isolation():
    inv = create_invite("hh-1")
    tok = inv["token"]
    # hh-2 nem látja hh-1 invite-ját read-only view-ban — resolve tenant check
    assert resolve_invite(tok)["tenant_id"] == "hh-1"  # nem hh-2
```

Futtatás:

```bash
pytest tests/test_qbo_oauth.py tests/test_xero_oauth.py tests/test_sync_service.py tests/test_accountant_invite.py tests/test_sync_api.py -v
# vagy teljes suite: pytest -q
```

### E2E (Browser Helper 1.35.0 — ezentúl BH az E2E)

Spec: `frontend/e2e/us_SYNC_001_qbo.spec.ts` — **BH** bulk a `fleet_run_batch`-csel:

```typescript
// BH 1.35.0 API (68 eszköz):
// P0-3 navigate storageState (locale pre-seed), P0-4 expect polling, P0-5 bundle, P0-2 fleet_run_batch
import { test, expect } from "@playwright/test"; // BH recorder exportálja, futtatás BH fleet-en

test("US-SYNC-01 — integrations + sync + invite", async ({ page }) => {
  // Pro: seed is_pro=true
  // BH: browser_inject_storage_state({origins:[{origin:"https://receipts.allthezoo.com", localStorage:[{name:"receiptlens.session", value: proToken}]}]})
  // BH: browser_navigate({url:"/integrations", storageState:{origins:[{origin:"https://receipts.allthezoo.com", localStorage:[{name:"receiptlens.locale", value:"hu"}]}]}})
  await page.goto("/integrations", { waitUntil: "domcontentloaded" });
  await expect(page.getByText("QuickBooks")).toBeVisible();
  // Connect → mock OAuth redirect → callback → Connected
  await page.getByRole("button", {name: "Connect QuickBooks"}).click();
  // BH: browser_interact({action:"click", selector:"text=Connect QuickBooks"}) → 302 Intuit → mock callback → 302 /integrations
  await expect(page.getByText("Connected")).toBeVisible();
  // Sync now
  await page.getByRole("button", {name: "Sync now"}).click();
  // BH: browser_get_network_activity({path:"/api/v1/integrations/qbo/sync", status_min:200}) → 200 {pushed: N}
  await expect(page.getByText(/pushed.*5/)).toBeVisible();
  // Invite accountant
  await page.getByRole("button", {name: "Invite accountant"}).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.getByDisplayValue(/https:\/\/receipts\.allthezoo\.com\/accountant\//)).toBeVisible();
  // 402 case: Free user → paywall modal
  // BH fleet második task: Free tenant → /integrations → Connect click → paywall modal "Pro — $5/hó"
});
// 10 nyelv: t("connectQuickBooks") check — /integrations h1 nem angol ha locale=fr
```

BH futtatás:

```bash
# Single smoke
curl -X POST http://127.0.0.1:8020/agent/navigate -H "Content-Type: application/json" \
  -d '{"url":"https://receipts.allthezoo.com/integrations","storageState":{"origins":[{"origin":"https://receipts.allthezoo.com","localStorage":[{"name":"receiptlens.locale","value":"hu"}]}]}}'

# Bulk (fleet_run_batch — P0-2) — 5 case párhuzamosan:
curl -X POST http://127.0.0.1:8020/fleet/run-batch -H "Content-Type: application/json" \
  -d '{"tasks":[{"id":"US-SYNC-01-qbo-connect"},{"id":"US-SYNC-01-xero-connect"},{"id":"US-SYNC-01-sync-push"},{"id":"US-SYNC-01-invite-link"},{"id":"US-SYNC-01-402-gate"}],"workers":3,"retries":1,"reporter":{"html":true}}'

# Locale diff (P2) — integrations title nem angol:
curl -X POST http://127.0.0.1:8020/agent/visual-diff-locale -H "Content-Type: application/json" \
  -d '{"url":"https://receipts.allthezoo.com/integrations","locales":["en","fr"],"storage_key":"receiptlens.locale","h1_selector":"h1"}'
```

Gate (kötelező):

```bash
cd frontend && npx tsc --noEmit && echo "TSC:0"
NODE_OPTIONS="--max-old-space-size=2048" npx next build 2>&1 | tail -5 && echo "BUILD:0"
curl -s -o /dev/null -w "%{http_code}" https://receipts.allthezoo.com/integrations && echo " /integrations 200"
curl -s http://127.0.0.1:8020/status | python3 -c "import json,sys; print(json.load(sys.stdin).get('cdp_url','?')[:40])" # 9557 = lokális
# BE
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8130/api/v1/integrations | python3 -m json.tool
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8130/api/v1/accountant/invite | python3 -m json.tool
```

---

## Elvetve

| Opció | Miért nem |
|-------|-----------|
| Full sync engine (real-time webhook + delta) | Over-engineering MVP — batch push elég, webhook később |
| NetSuite/Sage integráció nap 1 | B2B market, nem háztartás — később |
| Token alapú invite helyett auth kérés a könyvelőnek | UX gát — könyvelők nem fognak regisztrálni |
| Külön microservice sync-be | Nem lean — 1 router + 1 service elég MVP-ben |

## Következmény

- **Fejlesztő:** lásd File-térkép — max 400 sor/file, `ruff` + `mypy`.
- **Teszt:** BE `tests/test_qbo_oauth.py` + `tests/test_xero_oauth.py` + `tests/test_sync_service.py` + `tests/test_accountant_invite.py` + `tests/test_sync_api.py`, E2E BH `us_SYNC_001_qbo.spec.ts` (`fleet_run_batch` bulk).
- **Migráció:** nincs — in-memory dict (`budget_store` minta). Postgresre váltáskor `connections` + `invite_tokens` táblák, Alembic.
- **Előző:** ADR-005 (Vision Pro OCR) — ugyanaz a Pro csomag.

## Kapcsolódó

- Research: `docs/research/2026-08-27-receipt-lens-revenue-features.md` (VOC #3, RICE 255, Dext/Expensify pricing)
- Kód: `app/intuit_oauth.py` (meglévő scaffold), `app/connection_service.py` (meglévő), `app/api.py`, `frontend/app/(app)/integrations/page.tsx`
- Előző: ADR-004 (Tax), ADR-005 (Vision) — egy Pro csomag (5-8/hó, $49/év)
