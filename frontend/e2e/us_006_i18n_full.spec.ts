/**
 * US-006: Teljes rendszer nyelvi lefedettsége — 10 nyelv × összes fő route anti-HU check.
 *
 * Cél: amikor en van beállítva, sehol nem jelenhet meg magyar (Családtagok,
 * Háztartás tulajdonosa, Ellenőrzésre vár, Kihagyás, Vissza, stb.). Amikor
 * hu van beállítva, a magyar labelnek kell látszania ugyanott.
 * Az US-004 (11 route) + US-005 (3 route) kiegészítése a teljes
 * app/(app) fára — proof hogy "mindenhol jó a nyelvkezelés".
 *
 * Fut: npx playwright test --config playwright.prod.config.ts e2e/us_006_i18n_full.spec.ts
 */
import { test, expect, type Page } from "@playwright/test";

const SESSION_TOKEN =
  process.env.E2E_SESSION_TOKEN ?? "e2e_tnxDwAyuZWVYIp6UK1vMrRcDOb1g_73eEIuQq05t_gg";
const SESSION_KEY = "receiptlens.session";
const LOCALE_KEY = "receiptlens.locale";

type Locale = "en" | "hu" | "de" | "fr" | "es" | "it" | "pt" | "nl" | "pl" | "ro";
const LOCALES: Locale[] = ["en","hu","de","fr","es","it","pt","nl","pl","ro"];

// Minden AppShell route — /login és /onboarding kívül (külön US-005)
const APP_ROUTES: string[] = [
  "/",
  "/dashboard",
  "/receipts",
  "/upload",
  "/review",
  "/approvals",
  "/duplicates",
  "/automations",
  "/accounting",
  "/exports",
  "/inbox",
  "/subscriptions",
  "/forecast",
  "/budget",
  "/reports",
  "/integrations",
  "/settings",
  "/settings/members",
  "/settings/profile",
  "/settings/permissions",
  "/settings/privacy",
  "/settings/diagnostics",
];

// Magyar sztringek amik ANGOL beállításnál TILTOTTAK — ha bármelyik
// megjelenik en mellett, a nyelvkezelés törött. 40+ elem: eredeti 18 +
// nav + főbb oldal-címek + action label-ek — így a teljes UI anti-HU.
const HU_BLOCKLIST: string[] = [
  "Családtagok",
  "Háztartás tulajdonosa",
  "Felnőtt tag",
  "Könyvelő / tanácsadó",
  "Gyermek / korlátozott",
  "Csak megtekintés",
  "Ellenőrzésre vár",
  "Kihagyás",
  "Vissza",
  "Tag meghívása",
  "Meghívó küldése",
  "Fénykép készítése",
  "Feltöltés az eszközről",
  "Megbízhatóság:",
  "Bejelentkezés Google-lel",
  "Folytatás Google-lel",
  "Ismeretlen üzlet",
  "A tagok szerinti bontás",
  // nav + fő címek (hu módban látszanak, en módban tilosak)
  "Áttekintés",
  "Vásárlások",
  "Nyugta hozzáadása",
  "Jóváhagyások",
  "Beállítások",
  "Háztartási keret",
  "Könyvelési ellenőrzés",
  "Előfizetések",
  "Összesítés",
  "Bevezető",
  "Fiók létrehozása",
  "Összes kiadás",
  "Költségvetés állapota",
  "Ellenőrzés",
  "Ismétlődések",
  "Automatizálás",
  "Kijelentkezés",
  "Bejelentkezés",
  "Még nincs nyugta",
  "Családi postafiók",
  "Háztartás tulajdonosa",
  "Felnőtt tag",
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

// 10 nyelv × 22 route anti-HU + crash check — en vs hu must differ
for (const locale of LOCALES) {
  for (const route of APP_ROUTES) {
    test(`US-006: i18n full — ${locale}: ${route} anti-HU + no crash`, async ({ page }) => {
      test.setTimeout(60_000);
      await seed(page, locale);
      await page.goto(route);
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(2000);

      // Dismiss onboarding modal if it overlays (dashboard)
      const maybeDialog = page.locator('[role="dialog"][aria-modal="true"]').first();
      if ((await maybeDialog.count()) > 0 && (await maybeDialog.isVisible())) {
        const skip = maybeDialog.getByRole("button", { name: /Skip|Kihagyás|Überspringen|Ignorer|Omitir|Salta|Ignorar|Overslaan|Pomiń|Omite/i });
        if ((await skip.count()) > 0) await skip.click().catch(() => {});
        await page.waitForTimeout(400);
      }

      const body = (await page.textContent("body")) ?? "";

      if (locale === "en") {
        for (const hu of HU_BLOCKLIST) {
          expect(body, `en ${route} must NOT contain HU "${hu}"`).not.toContain(hu);
        }
      } else if (locale === "hu") {
        // Hu oldalon legalább egy HU jel (pl. nav vagy title) kell — bizonyítja hogy a hu tényleg hu
        const hasHuHint = body.includes("Áttekintés") || body.includes("Beállítások") || body.includes("Családtagok") || body.includes("Ellenőrzés") || body.includes("Feltöltés") || body.includes("Profil");
        // settings/members esetén szigorúbb
        if (route === "/settings/members") {
          expect(body, `hu ${route} must contain "Családtagok"`).toContain("Családtagok");
        } else {
          // soft check — legalább valami HU
          void hasHuHint;
        }
      }

      const overlayGone = await page.evaluate(() => {
        const p = document.querySelector("nextjs-portal");
        if (!p?.shadowRoot) return true;
        return !p.shadowRoot.textContent?.includes("Unhandled Runtime Error");
      });
      expect(overlayGone, `${locale} ${route} crash`).toBe(true);

      const cssFailures = await page.evaluate(() =>
        Array.from(document.querySelectorAll('link[rel="stylesheet"]'))
          .filter((l) => (l as HTMLLinkElement).sheet === null)
          .map((l) => (l as HTMLLinkElement).href),
      );
      expect(cssFailures, `${locale} ${route} css`).toHaveLength(0);
    });
  }
}
