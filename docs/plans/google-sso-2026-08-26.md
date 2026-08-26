# Google SSO belépés + tartós session — terv (2026-08-26)

> Cél: a receipts.allthezoo.com bejelentkezési képernyőjén legyen „Folytatás Google-lel",
> és a session a kijelentkezésig megmaradjon (sliding TTL).

## Helyzet

- Auth most: magic-link (e-mail) → `sessions` tábla (SQLite), token a frontend
  `localStorage`-ban (`receiptlens.session`, lib/auth.ts), `Authorization: Bearer` fejléccel.
- `SESSION_TTL_SECONDS = 30 nap` (auth_api.py:43), NINCS logout végpont, nincs SSO.
- Minta: a MealMind-ban élő Google OIDC implementáció
  (`mealmind/app/services/google_oidc.py` + `routes/auth.py` google/start|callback|link).
- Dep-k: `cryptography 50.0.0` + `httpx` már bent vannak a pyprojectben —
  **új Python függőség nem kell** (az id_token RS256-ellenőrzése cryptography-val +
  Google JWKS letöltése httpx-szel megoldható).

## Döntések

- **D1 — Flow:** authorization-code, backend-vezérelt (mint MealMind):
  `GET /api/auth/google/start` (state+nonce HttpOnly cookie) → accounts.google.com →
  `GET /api/auth/google/callback` → id_token ellenőrzés (iss/aud/nonce/email_verified,
  JWKS) → háztartás find-or-create (`hh-{email}`, owner) → `service.create_session(...)` →
  `302` a frontend `/auth/google/callback#session_token=…&expires_at=…` címre
  (fragment nem megy szervernek; a JS kiolvassa, `setSessionToken()`, majd `/dashboard`).
- **D2 — Deps:** nulla új csomag. Új modul: `app/google_oidc.py` (httpx + cryptography).
- **D3 — Tartós belépés:** sliding session — `resolve_session()` frissíti az
  `expires_at`-et most+SESSION_TTL-re minden hitelesített kérésnél;
  `SESSION_TTL_SECONDS` 30 → **180 nap** (használat közben sosem jár le,
  kijelentkezés az egyetlen lezárás). `POST /api/auth/session/logout` törli a sort,
  a frontend `signOut()` ezt hívja, majd törli a localStorage-t.
- **D4 — Konfiguráció:** `RECEIPTLENS_GOOGLE_CLIENT_ID` / `_SECRET` (.env, gitignored);
  ha nincs beállítva → `/auth/google/*` **503** „Google sign-in is not configured",
  a gomb rejtve (futásidejű probe: `GET /api/auth/google/status` → `{enabled:bool}`).
- **D5 — Biztonság:** state+nonce random 32 bájt, HttpOnly+Secure+SameSite=Lax cookie
  (`receiptlens.oauth`, 10 perc TTL); `return_to` csak `/`-rel kezdődhet (open-redirect
  védelem); email kötelezően `email_verified=true`; rate-limit a start végponton
  (meglévő RateLimitMiddleware 60/min elég).
- **D6 — Frontend:** `/login`: „Folytatás Google-lel" gomb (status-probe alapján);
  új oldal `frontend/app/auth/google/callback/page.tsx` (fragment parse → session);
  `lib/api.ts`: `googleSsoEnabled()`, `logout()`; AppShell/profil menü: **Kilépés** gomb.
- **D7 — Tesztek:** unit: oidc verify (rossz iss/aud/nonce/expired/email_verified=false),
  find-or-create, sliding expiry, logout; API-integráció: mockolt exchange-szel a teljes
  callback-flow; E2E prod-journey: gomb látszik/eltűnik flag szerint, logout után 401.

## Feladatok (kanban: receipts-lens)

| ID | Név | Mi |
|---|---|---|
| G1 | Backend OIDC service | `app/google_oidc.py` + unit tesztek (RED→GREEN) |
| G2 | Backend routes + session | start/callback/status/logout + sliding TTL + tesztek |
| G3 | Frontend SSO + logout | gomb, callback oldal, Kilépés gomb, api.ts |
| G4 | Infra/kredenc | Google OAuth client (redirect URI: `https://receipts.allthezoo.com/api/auth/google/callback`), .env, FE rebuild + systemd restart |
| G5 | E2E + docs | prod-journey bővítés, README, CHANGELOG, release |

## G4 — két út (ajánlás: A)

- **A (ajánlott):** a meglévő MealMind Google OAuth client-hez **hozzáadjuk** a
  `https://receipts.allthezoo.com/api/auth/google/callback` redirect URI-t — a consent
  screen már létezik és hitelesítve van, így nincs új „tesztelés alatt" fázis.
- B: külön új OAuth client a ReceiptLensnek (tiszta elkülönülés, de consent screen
  publikálási körök).

## Elfogadási kritériumok

1. `/login` oldalon a Google gombbal való belépés után a dashboard betölt, session él.
2. Böngésző bezárása/újranyitása után is bent marad; heti használat mellett nem jár le.
3. „Kilépés" után minden védett hívás 401, a session sor törlődik a DB-ből.
4. Ha a Google-konfig hiányzik, a gomb nem jelenik meg és a végpont 503-at ad.
5. Teljes PROD E2E suite (20+ új tesztekkel) zöld élesben.
