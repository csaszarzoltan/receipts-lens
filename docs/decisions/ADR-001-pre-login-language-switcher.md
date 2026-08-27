# ADR-001: Pre-login nyelvválasztó (közös komponens)

- **Dátum:** 2026-08-27
- **Státusz:** accepted
- **Szerző:** analyst (research: `docs/research/2026-08-27-pre-login-language-switcher.md`)
- **Kanban:** standing goal — nyelvi lefedettség

## Kontextus
Bejelentkezés előtt a nyelv csak a `/login`-on volt választható; `/`, `/register`, `/auth/magic-link`, `/auth/invite`, `/auth/google/callback`, `/onboarding` oldalakon nem. Új/inkognitó látogatónál így az első képernyő nyelve nem kontrollálható. A rendszer 10 nyelvet támogat, `localStorage["receiptlens.locale"]` + `useTranslation()` alapon.

## Döntés
**Közös `LanguageSwitcher` komponens** (`frontend/components/LanguageSwitcher.tsx`, `"use client"`, `useTranslation` + `SUPPORTED_LOCALES/LOCALE_LABELS`, `id="pre-login-locale"`, `aria-label={t("language")}`), beépítve 6 pre-login oldalra (landing, register, magic-link, invite, google/callback, onboarding). A választás `setLocale()`-ön keresztül `localStorage`-ba íródik és `html lang`-ot állít; bejelentkezés után a `settings/profile` BE szinkronja megmarad.

- 6 oldal: `/`, `/(auth)/register`, `/auth/magic-link`, `/auth/invite`, `/auth/google/callback`, `/onboarding`
- 2 hardcoded fix: `magic-link` `placeholder` + `Vagy`, `invite` `Vagy/sign in with household` → `t()`
- E2E: új `us_007_pre_login_locale.spec.ts` 6×10=60 (anti-HU + hu pozitív + select interakció)

## Elvetve

| Opció | Miért nem |
|---|---|
| Inline `<select>` másolás 5× | Duplikáció, 5 helyen kell karbantartani |
| `navigator.language` auto-detect | Nem determinisztikus, felülírhatja a tudatos választást, plusz heurisztika |

## Következmény
- Fejlesztő: 1 komponens + 6 oldal patch, `register` client-re vált (metadata törlés), `t()` hiányok pótlása.
- Validálás: `TSC 0 BUILD 0`, `E2E us_007 60 passed` + `us_006 30×10` továbbra is zöld, `curl 200` pre-login route-ok.

## Kapcsolódó
- Research: `docs/research/2026-08-27-pre-login-language-switcher.md`
- Kód: `frontend/components/LanguageSwitcher.tsx`, `frontend/app/**/page.tsx` (6), `frontend/lib/i18n.ts` (504 kulcs)
- Következő ADR: —
