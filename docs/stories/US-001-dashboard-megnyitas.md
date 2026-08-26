# US-001: Dashboard megnyitás — háztartás pénzügyei egy helyen

- Epic: Core / Consumer Dashboard
- Priority: P0
- Source: docs/plans/consumer-pivot-2026-08-13.md §3.4, docs/plans/google-sso-2026-08-26.md
- Prototípus: élő https://receipts.allthezoo.com/dashboard — státusz: production

## Story (As a … I want … So that …)

**Happy:** As a háztartás tagja I want that miután beléptem (Google SSO / magic-link), a /dashboard oldal azonnal megjelenik a háztartásom adataival So that azonnal átlátom a pénzügyeinket.

**Error:** As a háztartás tagja I want that ha a backend nem elérhető, egyérthető hibaüzenetet látok és van „Újrapróbálkozás" gomb So that nem ragadok egy üres oldalon.

**Edge:** As a háztartás tagja I want that ha üres a háztartás (még nincs nyugta), az onboarding/bemutató modal jelenik meg So that tudom mit kell csinálni.

**Gui:** As a háztartás tagja I want that a /dashboard oldalon a sidebar, a topbar és a fő tartalom blokkok egymás mellett/mellett jelennek meg és nem takarják egymást So that a teljes felület használható.

## Acceptance Criteria (Gherkin — given/when/then)

### AC1: Happy path — session-nel a dashboard adatot mutat
- **given** a felhasználó be van jelentkezve (valid session Bearer token)
- **when** navigál a /dashboard oldalra
- **then** az oldal 200-as, a „Áttekintés" heading látható, és a consumer/dashboard API adatot ad vissza (nem 401)
- **then** a „Nyugta hozzáadása" gomb kattintható és /upload-ra visz
- **then** a háztartási keret blokk „Keret beállítása" gombot tartalmaz
- **then** a havi költés blokk számértéket jelenít meg (nem skeleton)

### AC2: Error state — session nélkül vagy backend down
- **given** a felhasználó NINCS bejelentkezve (nincs session token localStorage-ben)
- **when** navigál a /dashboard oldalra
- **then** a /api/v1/consumer/dashboard hívás 401-et ad
- **then** az oldal NEM jelenít meg skeleton loading-t örökké
- **then** legalább egy hibaüzenet vagy login redirect megjelenik

### AC3: Onboarding overlay — új háztartás, első belépés
- **given** a felhasználó frissen regisztrált (üres háztartás, 0 nyugta)
- **when** a /dashboard oldal betölt
- **then** egy 3-lépéses onboarding modal jelenik meg (role=dialog, aria-modal=true)
- **then** a „Kihagyás" gomb kattintható és bezárja a modalt
- **then** a „Tovább" gomb a következő lépésre visz

### AC4: GUI layout — sidebar + topbar + main blokk nem takarja egymást
- **given** a felhasználó desktop méretű ablakban nézi (1280px széles)
- **when** a /dashboard oldal betölt
- **then** a sidebar (aria-label="Sidebar navigation") bal oldalt jelenik meg, nem takarja a fő tartalmat
- **then** a topbar sticky a tetején, nem takarja a main contentet
- **then** a fő tartalom (id="main-content") látható és scrollható
- **then** overlay-ek (z≥40) NEM takarnak interactive elemeket a main contentben

## gui_flow (UI kontraktus)

### Happy flow:
1. Open `/dashboard` → látom: sidebar (11 navigációs pont), topbar (search + role + 🔔 + Google + theme toggle)
2. Látom: h1 „Áttekintés" + alcím „A háztartásod pénzügyei egy helyen"
3. Látom: „📤 Nyugta hozzáadása" gomb (jobb felső sarok)
4. Látom: Budget blokk — vagy „Még nincs havi kereted" + „Keret beállítása" CTA, VAGY $Maradék érték
5. Látom: Havi költés blokk — $Összeg + kategória szöveg (nem skeleton!)
6. Látom: Drágulás-figyelmeztetések blokk — zöld pipa VAGY figyelmeztetés
7. Látom: „Összesítés megnyitása" link → /reports

### Error flow:
1. Open `/dashboard` session nélkül → API 401 → error state megjelenik
2. Látom: „⚠️ Nem sikerült betölteni az áttekintést" + „Újrapróbálkozás" CTA
3. NEM látom: örökké spinning skeleton-t

### Onboarding flow:
1. Open `/dashboard` üres háztartással → modal overlay (z-50)
2. Látom: „💡 1. lépés a 3 közül" + „Mi ez?" + szöveg
3. Click „Kihagyás" → modal bezárul → dashboard látható
4. Click „Tovább" → 2. lépés → 3. lépés → dashboard

## Megjegyzés
- Max 400 sor/file, type hints + docstring (METH-COD-001…008 ahol releváns).
- gui_flow lépést csak US-frissítéssel szabad változtatni.
- E2E skeleton: `frontend/e2e/us_001_dashboard.spec.ts`
- API teszt: `tests/test_us_001_dashboard.py`
