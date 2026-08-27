# ADR-002: Pre-login dark mód

- **Dátum:** 2026-08-27
- **Státusz:** accepted
- **Szerző:** analyst (research: `docs/research/2026-08-27-pre-login-dark-mode.md`)
- **Kanban:** [aaa bbb] — két feladat (1/2)

## Kontextus
Pre-login oldalakon (landing, login, register, magic-link, invite, google/callback, onboarding) a dark mód nem kapcsolható; `ThemeToggle` csak a Topbar-on (bejelentkezve) van. A `receiptlens.theme` + `THEME_INIT_SCRIPT` már adott — csak a kapcsoló hiányzik.

## Döntés
**Meglévő `components/ThemeToggle.tsx` újrahasználása** 6 pre-login oldalon (1 import/oldal, sarok/header). Nincs új logika, nincs duplikáció; `layout.tsx`init script már FOUC-guardolt.

- Érintett: `/`, `/(auth)/login`, `/(auth)/register`, `/auth/magic-link`, `/auth/invite`, `/auth/google/callback`, `/onboarding` (7 oldal, loginon felül is).
- Validálás: `TSC 0 BUILD 0`, E2E `us_007` bővítve / `us_008` `6×2` dark interakció (`html.dark` + `localStorage` + reload perzisztens).

## Elvetve

| Opció | Miért nem |
|---|---|
| Új PreLoginThemeToggle | Duplikáció, drift |
| prefers-color-scheme csak | Nem teljesíti a manuális kérést |

## Következmény
- Fejlesztő: 6 oldal patch (`import ThemeToggle` + JSX sarok), `ThemeToggle` `aria-label` már adott.
- Validálás: `curl 200` pre-login route-ok, E2E `ThemeToggle` látható + click `html.dark` flip.

## Kapcsolódó
- Research: `docs/research/2026-08-27-pre-login-dark-mode.md`
- Kód: `frontend/components/ThemeToggle.tsx`, `frontend/app/**/page.tsx` (6)
- Következő ADR: ADR-003 (fordítás)
