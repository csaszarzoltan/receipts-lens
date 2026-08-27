# Pre-login dark mód — kutatás (2026-08-27)

## Probléma
Bejelentkezés előtt (landing `/`, `/login`, `/register`, `/auth/magic-link`, `/auth/invite`, `/auth/google/callback`, `/onboarding`) a dark mód nem kapcsolható. A `ThemeToggle` csak a bejelentkezett `/dashboard` Topbar-on van. Sötét környezetben a világos kezdőoldal vakít; a `receiptlens.theme` viszont már támogatott (layout `THEME_INIT_SCRIPT` + `ThemeToggle`).

## Cél
Bármely pre-login oldalon 1 kattintással sötét/világos mód, perzisztens (`localStorage["receiptlens.theme"]` + `html.dark`), újratöltés után is megmarad.

## Megvizsgált opciók

| Szempont | A) ThemeToggle újrahasználás (meglévő komponens) | B) Új PreLoginThemeToggle duplikált logikával | C) CSS `prefers-color-scheme` csak (nincs manuális) |
|---|---|---|---|
| Leírás | Meglévő `components/ThemeToggle.tsx` import 6 pre-login oldalra (header/sarok). Logika: `getInitialDark` → `useState` → `useEffect` `html.dark` + `localStorage["receiptlens.theme"]`. | Új komponens másolt `localStorage` + `matchMedia` logikával. | Csak OS beállítás követése, nincs gomb. |
| Előny | DRY — 1 komponens, már FOUC-guardolt (`layout.tsx` `THEME_INIT_SCRIPT`), bizonyított, 0 új logika. | Független evolúció (pre-login design eltérhet). | Nulla kód. |
| Hátrány | Pre-login designban gomb pozícionálás kell. | Duplikáció, drift kockázat. | Nem teljesíti a kérést (manuális kapcsolás kell). |
| E2E | Kiváló — ugyanaz a `html.dark` contract. | Ugyanaz, de két contract. | Nem tesztelhető manuálisan. |
| Illeszkedés leanhez | Lean — 6×1 import. | Túlzott. | Nem elég. |
| Kockázat | Alacsony. | Közepes (drift). | Magas (követelmény nem teljesül). |

## Döntés
**A) Meglévő ThemeToggle újrahasználás.** A pre-login oldalak header/sarkába kerül (landing: header jobb oldal, form-oldalak: card sarkába), `ThemeToggle` importtal. Nincs új logika, a `layout.tsx` init script már jól időzített. Pre-login `LanguageSwitcher` mintáját követi (1 komponens → N oldal).

## Érintett felületek
- `/` (landing) — header jobb oldal
- `/(auth)/login`, `/(auth)/register` — card header sarok
- `/auth/magic-link`, `/auth/invite`, `/auth/google/callback` — card sark
- `/onboarding` — step card header

## E2E lefedettség
`us_007` bővítve vagy `us_008_dark_mode.spec.ts`: 6 route ×2 állapot = dark toggle interakció (click → `html.dark` + `localStorage["receiptlens.theme"]` flip, reload után perzisztens) + anti-regresszió: `ThemeToggle` látható minden pre-login útvonalon.

## Kockázatok
- `ThemeToggle` `cx` + `getInitialDark` már SSR-safe (`typeof window` guard) — pre-login SSR-ben is OK.
- `suppressHydrationWarning` a `html`-en már van — `dark` class flash nincs.
