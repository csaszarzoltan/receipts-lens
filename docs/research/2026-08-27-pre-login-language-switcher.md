# Pre-login nyelvválasztó — kutatás (2026-08-27)

## Probléma
Bejelentkezés előtt a nyelv nem választható, csak bejelentkezés után a `/settings/profile`-on. A rendszer 10 nyelvet támogat (`en, hu, de, fr, es, it, pt, nl, pl, ro`), a választás `localStorage["receiptlens.locale"]` + `document.documentElement.lang`, és `useTranslation()`-ön keresztül él. A `/login`-on már van választó (`id="login-locale"`), de a többi pre-login belépési ponton nincs: landing `/`, `/register`, `/auth/magic-link`, `/auth/invite`, `/auth/google/callback` (és részben `/onboarding`). Emiatt angol böngésző/új inkognitó ablakban is magyar maradhat az első képernyő, vagy fordítva.

## Cél
Bármely pre-login oldal `en` módban ne mutasson magyar szöveget, `hu` módban magyarul jelenjen meg, és a választás `localStorage`-ban megmaradjon bejelentkezés után is. E2E-vel bizonyított `10 nyelv × pre-login route` lefedettség.

## Megvizsgált opciók

| Szempont | A) Inline `<select>` másolás (login minta) | B) Közös `LanguageSwitcher` komponens | C) `navigator.language` auto-detect + fallback |
|---|---|---|---|
| Leírás | Minden pre-login oldalra bemásoljuk a loginon lévő 10 soros `<select>` blokkot (`SUPPORTED_LOCALES` + `LOCALE_LABELS` + `useTranslation`). | Új `frontend/components/LanguageSwitcher.tsx` (`"use client"`, `useTranslation` + `getLocale/setLocale`), minden pre-login oldal importálja. | Első látogatáskor `navigator.language` alapján állít be `receiptlens.locale`-t, mellé opcionális manuális választó. |
| Előny | Nulla új absztrakció, 1:1 a meglévő login megoldással, azonnal érthető, nincs új függőség. | DRY — 5 oldal × duplikáció helyett 1 komponens, egységes `id="pre-login-locale"`, tesztelhető izoláltan. | Automatikus, kevesebb kattintás új látogatónak. |
| Hátrány | Duplikáció (5× azonos JSX), jövőbeli label-változás 5 helyen. | +1 komponens karbantartása, minimális plusz import. | Nem determinisztikus E2E-ben, inkognitó/Accept-Language eltér, felülírhatja a tudatos választást; plusz logika a `getLocale()`-ba. |
| E2E tesztelhetőség | Jó — minden oldal `select` DOM-ja közvetlenül tesztelhető. | Kiváló — komponens + integrációs teszt egy helyen. | Gyenge — auto-detect miatt flaky, mock kell. |
| Illeszkedés lean elvhez | Lean — nincs új file, de duplikál. | Lean + DRY — 1 kis file (<60 sor), indokolt 5 felhasználásnál. | Túlzott — plusz heurisztika, nem kért igény. |
| Kockázat | Elfelejtett oldal = hiányos lefedettség. | Elfelejtett import = ugyanaz, de grep könnyebb. | Nyelvi override meglepetés. |

## Döntés
**B) Közös `LanguageSwitcher` komponens** — a mealmind-ben már bizonyított minta (`setLocale` → `localStorage["receiptlens.locale"]` + `html lang`), de ReceiptLens-en egyszerűsítve: nincs `i18next`, csak a meglévő `lib/i18n.ts` (`getLocale/setLocale/useTranslation`). A komponens `id="pre-login-locale"` és `aria-label={t("language")}` attribútummal, `SUPPORTED_LOCALES` listával. Opció A-hoz képest a duplikációt szünteti, opció C-t elvetjük (kérés explicit választás, nem auto-detect).

## Érintett felületek
- `/` (landing) — jelenleg `useTranslation` van, de nincs választó
- `/(auth)/register` — jelenleg nincs i18n, nincs választó
- `/auth/magic-link` — van i18n, nincs választó + `placeholder="te@pelda.hu"` hardcoded, `Vagy` hardcoded
- `/auth/invite` — van i18n, nincs választó + `Vagy` / `sign in with household` hardcoded
- `/auth/google/callback` — van i18n, nincs választó
- `/onboarding` — van i18n, nincs választó (első belépéskor pre-dashboard, hasznos)

`/login` már kész — nem érintjük (referencia).

## Perzisztencia
`setLocale(next)` → `localStorage.setItem("receiptlens.locale", next)` + `document.documentElement.lang = next`. Bejelentkezés után `settings/profile` ugyanezt hívja `savePreferences({language})`-szel is — a pre-login választás így automatikusan megmarad, nincs külön BE szinkron előtte.

## E2E lefedettség bővítése
`us_006` eddig 30 route `10 nyelv × anti-HU 38` — pre-login kimaradt. Új `us_007_pre_login_locale.spec.ts`: 6 route ×10 nyelv =60 teszt: `anti-HU` (en módban nincs magyar) + `hu pozitív` (hu módban `Bejelentkezés/Sign in` megfelelő) + `select` interakció (értékváltás → localStorage + html lang).

## Kockázatok
- Landing `"use client"` már megtörtént (504 kulcs) — nem okoz regressziót.
- `register` eddig server component — `"use client"` kell a választóhoz, de a `metadata` exporttal ütközik (client nem exportálhat metadata-t) → metadata-t törölni vagy layoutba tenni.

## Következő lépés
ADR → implementáció (komponens + 6 oldal patch + E2E `us_007`) → `TSC 0 BUILD 0` → `E2E 60 passed` → `curl 200`.
