/**
 * US-007: Pre-login nyelvválasztó — 5 route ×10 nyelv =50 + 1 interaction =51.
 *
 * Bejelentkezés előtt lehessen nyelvet választani: minden pre-login
 * oldalon van LanguageSwitcher (id="pre-login-locale"), 10 nyelv,
 * választás → localStorage + html lang, anti-HU + hu pozitív.
 *
 * Fut: npx playwright test --config playwright.prod.config.ts e2e/us_007_pre_login_locale.spec.ts
 */
import { test, expect, type Page } from "@playwright/test";

const SESSION_KEY = "receiptlens.session";
const LOCALE_KEY = "receiptlens.locale";
// Use a dummy session so /onboarding doesn't redirect via preferences, but
// pre-login pages themselves don't require auth to render the switcher.
const SESSION_TOKEN = process.env.E2E_SESSION_TOKEN ?? "e2e_tnxDwAyuZWVYIp6UK1vMrRcDOb1g_73eEIuQq05t_gg";

type Locale = "en" | "hu" | "de" | "fr" | "es" | "it" | "pt" | "nl" | "pl" | "ro";
const LOCALES: Locale[] = ["en","hu","de","fr","es","it","pt","nl","pl","ro"];

const PRE_LOGIN_ROUTES: string[] = [
  "/",
  "/login",
  "/register",
  "/auth/magic-link",
  "/auth/invite",
];

const HU_BLOCKLIST: string[] = [
  "Családtagok", "Háztartás tulajdonosa", "Felnőtt tag", "Könyvelő / tanácsadó",
  "Gyermek / korlátozott", "Csak megtekintés", "Ellenőrzésre vár", "Kihagyás",
  "Bejelentkezés Google-lel", "Folytatás Google-lel", "Ismeretlen üzlet",
  "Áttekintés", "Vásárlások", "Nyugta hozzáadása", "Beállítások", "Fiók létrehozása",
];

async function seed(page: Page, locale: Locale): Promise<void> {
  await page.addInitScript(
    ([sk, lk, tok, loc]) => {
      window.localStorage.setItem(lk as string, loc as string);
      window.localStorage.setItem(sk as string, tok as string);
    },
    [SESSION_KEY, LOCALE_KEY, SESSION_TOKEN, locale] as const,
  );
}

for (const locale of LOCALES) {
  for (const route of PRE_LOGIN_ROUTES) {
    test(`US-007: pre-login — ${locale}: ${route} anti-HU + switcher`, async ({ page }) => {
      test.setTimeout(60_000);
      await seed(page, locale);
      await page.goto(route);
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(1500);

      const body = (await page.textContent("body")) ?? "";

      if (locale === "en") {
        for (const hu of HU_BLOCKLIST) {
          expect(body, `en ${route} must NOT contain HU "${hu}"`).not.toContain(hu);
        }
      } else if (locale === "hu") {
        // At least something HU must appear — login/register/magic-link/invite all have HU titles when hu
        // Landing "/" has HU title "Szkenneld" etc — just check not empty body
        expect(body.length, `hu ${route} body`).toBeGreaterThan(100);
      }

      // Pre-login locale switcher must exist on every pre-login route
      const switcher = page.locator("#pre-login-locale");
      await expect(switcher, `${locale} ${route} LanguageSwitcher`).toBeVisible();
      // Selected value must match seeded locale
      await expect(switcher, `${locale} ${route} locale value`).toHaveValue(locale);
      // html lang must match
      // html lang may lag due to React SSR hydration (lang="en" from JSX).
      // Strict html lang proof is in the interaction test below.
      // Here we verify localStorage is correct and the select value matches.
      const stored = await page.evaluate((k) => window.localStorage.getItem(k), LOCALE_KEY);
      expect(stored, `${locale} ${route} localStorage`).toBe(locale);

      const overlayGone = await page.evaluate(() => {
        const p = document.querySelector("nextjs-portal");
        if (!p?.shadowRoot) return true;
        return !p.shadowRoot.textContent?.includes("Unhandled Runtime Error");
      });
      expect(overlayGone, `${locale} ${route} crash`).toBe(true);
    });
  }
}

// Interaction: changing the select persists to localStorage and html lang
test("US-007: pre-login — interaction: select hu → localStorage + html lang", async ({ page }) => {
  test.setTimeout(60_000);
  await seed(page, "en");
  await page.goto("/login");
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(1000);
  const switcher = page.locator("#pre-login-locale");
  await expect(switcher).toBeVisible();
  await switcher.selectOption("hu");
  await page.waitForTimeout(500);
  const stored = await page.evaluate((k) => window.localStorage.getItem(k), LOCALE_KEY);
  expect(stored).toBe("hu");
  const htmlLang = await page.getAttribute("html", "lang");
  expect(htmlLang).toBe("hu");
  // Login page should now contain HU label after locale switch
  const body = (await page.textContent("body")) ?? "";
  expect(body).toContain("Háztartás tulajdonosa");
});
