# US-002: Google SSO bejelentkezés — „Folytatás Google-lel”

- Epic: Auth / Google SSO
- Priority: P0
- Source: docs/plans/google-sso-2026-08-26.md (G1-G5), docs/methodology/EVOLUTIONARY-SYSTEM.md §6
- Prototípus: élő https://receipts.allthezoo.com/login + /auth/google/callback — státusz: production

## Story (As a ... I want ... So that ...)

**Happy:** As a háztartás tagja I want that a /login oldalon lássam a „Folytatás Google-lel" gombot, rákattintva a Google OAuth képernyőre jutok, és sikeres engedélyzés után visszaérkezve bejelentkezve érkezzek a /dashboard-ra So that jelszó nélkül, egy kattintással be tudjak lépni.

**Error:** As a háztartás tagja I want that ha elutasítom a Google jogosultságot vagy lejár a code/state, a callback egyérthető hibaüzenetet mutasson („A Google bejelentkezés sikertelen — próbáld újra") So that tudjam mi történt és ne ragadjak üres oldalon.

**Edge:** As a háztartás tagja I want that ha már be vagyok jelentkezve (session él), a login oldal ne mutassa a Google gombot feleslegesen vagy azonnal továbbirányítson a /dashboard-ra So that ne kelljen újra belépnem.

**Gui:** As a háztartás tagja I want that a Google gomb vizuálisan felismerhető (Google színek/logó), a Topbaron a „Kilépés" csak bejelentkezve látszik, és a callback oldal loading/hiba állapotai nem fedik egymást So that konzisztens és nem zavaró a felület.

## Acceptance Criteria (Gherkin — given/when/then)

### AC1: Happy path — /login Google gomb → /auth/google/start → 307 → callback
- **given** a felhasználó NINCS bejelentkezve, és `GET /api/auth/google/status` `{"enabled": true}`
- **when** navigál a /login oldalra
- **then** a „Folytatás Google-lel" link látható, href-je tartalmazza `/api/auth/google/start`-ot
- **when** a user rákattint (vagy közvetlenül hívja `GET /api/auth/google/start`-ot)
- **then** a válasz `307` + `Location: https://accounts.google.com/o/oauth2/v2/auth?...` + `Set-Cookie: receiptlens.oauth="STATE:...; HttpOnly; SameSite=lax; Secure"`
- **then** a `state` 64 hex karakter, `nonce` 64 hex karakter az url-ben

### AC2: Error states — Google callback hibák
- **given** `state` hiányzik VAGY `state` != cookie (CSRF mismatch) VAGY `error=access_denied`
- **when** `GET /auth/google/callback?code=...&state=...` érkezik (vagy a frontend `/auth/google/callback#` fragment hibás)
- **then** a backend `302 /login?error=oauth_*`-ra redirectel (`oauth_missing_params|oauth_invalid_state|oauth_cancelled|oauth_exchange_failed`)
- **then** a frontend `/auth/google/callback` oldalon a hibaüzenet tartalmazza: „sikertelen" / „hiányzó" / oauth param-ot, nem „Betöltés..."-on ragad

### AC3: Edge — bejelentkezett user + session persistence
- **given** `GET /auth/google/callback#session_token=TOKEN` fragment megérkezik a frontendhez
- **when** a callback oldal betölt
- **then** `localStorage["receiptlens.session"] = TOKEN` beíródik (Bearer nyer a továbbiakban)
- **then** a user a `return_to` (alapból `/dashboard`) útvonalra navigál és a dashboard `200`-at ad Bearer-rel
- **when** a user a Topbar „Kilépés“ gombjára kattint
- **then** `POST /auth/session/logout` `204` és `localStorage["receiptlens.session"]` törlődik, újra `GET /api/v1/consumer/dashboard` 401

### AC4: GUI — login + topbar + callback layout
- **given** desktop 1280px, no onboarding overlay
- **when** /login betölt
- **then** a sidebar rejtett (hidden lg:block), a login card középen, Google gomb + „Sign in" + magic-link linkek látszanak
- **when** /auth/google/callback betölt (fragment nélkül)
- **then** a callback card látszik: „Bejelentkezés Google-lel..." VAGY hibaüzenet (nem crash/blank), és nincs `nextjs-portal` Unhandled Runtime Error

## gui_flow (UI kontraktus)

### Happy flow:
1. Open `/login` → látom: ReceiptLens card, „Sign in to your household" + tenant/role select + „Sign in" gomb
2. Látom: „Folytatás Google-lel" gomb (Google 4-szín logó, href `/api/auth/google/start`)
3. Click „Folytatás Google-lel" → böngésző navigál `https://accounts.google.com/o/oauth2/v2/auth?...` (request `redirect_uri=https://receipts.allthezoo.com/api/auth/google/callback`)
4. Google consent → allow → backend `302 /auth/google/callback#session_token=TOKEN&expires_at=...`
5. Frontend callback betölt → `localStorage.setItem(SESSION_KEY, TOKEN)` → `router.push(return_to || "/dashboard")`
6. `/dashboard` betölt → `X-Tenant-ID` helyett `Authorization: Bearer TOKEN` → consumer/dashboard `200` + heading „Áttekintés" + „Nyugta hozzáadása" CTA

### Error flow:
1. Open `/auth/google/callback` (no fragment) → látom: „A Google bejelentkezés sikertelen (hiányzó token/session)."
2. `GET /auth/google/callback?error=access_denied&state=x` → `302 /login?error=oauth_cancelled`
3. `GET /auth/google/callback?code=abc` (no state) → `302 /login?error=oauth_missing_params`

### Logout flow:
1. Topbar → „Kilépés" csak session-nel látszik → Click → `POST /auth/session/logout` `204` → `localStorage["receiptlens.session"]` törölve → redirect `/login`

## Megjegyzés
- E2E skeleton: `frontend/e2e/us_002_google_sso.spec.ts`
- API tesztek: `tests/test_us_002_google_sso.py` (Google OIDC offline, HMAC state kiterjesztés)
