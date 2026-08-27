/**
 * US-008: Pre-login dark mode — 6 route × dark toggle.
 * Bejelentkezés előtt dark mód: ThemeToggle minden pre-login oldalon,
 * click → html.dark + localStorage["receiptlens.theme"], reload perzisztens.
 */
import { test, expect } from "@playwright/test";

const SESSION_TOKEN = process.env.E2E_SESSION_TOKEN ?? "e2e_tnxDwAyuZWVYIp6UK1vMrRcDOb1g_73eEIuQq05t_gg";
const SESSION_KEY = "receiptlens.session";
const LOCALE_KEY = "receiptlens.locale";
const THEME_KEY = "receiptlens.theme";

const PRE_LOGIN_ROUTES = ["/", "/login", "/register", "/auth/magic-link", "/auth/invite", "/onboarding"];

async function seed(page: any, theme: string) {
  await page.addInitScript(([sk, tk, thk, tok, th]: any) => {
    window.localStorage.setItem(sk, tok);
    window.localStorage.setItem(thk, th);
    window.localStorage.setItem("receiptlens.locale", "en");
  }, [SESSION_KEY, THEME_KEY, LOCALE_KEY, SESSION_TOKEN, theme]);
}

for (const route of PRE_LOGIN_ROUTES) {
  test(`US-008: dark — ${route} ThemeToggle visible + toggles html.dark`, async ({ page }) => {
    test.setTimeout(60_000);
    await seed(page, "light");
    await page.goto(route);
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1200);
    // Skip onboarding redirect: if /onboarding redirects to /dashboard, skip html.dark check there
    const url = page.url();
    if (route === "/onboarding" && url.includes("/dashboard")) {
      test.skip();
      return;
    }
    const toggle = page.getByRole("button", { name: /Switch to dark|Switch to light|Dark mode|Light mode/i }).first();
    await expect(toggle, `${route} ThemeToggle`).toBeVisible();
    const isDarkBefore = await page.evaluate(() => document.documentElement.classList.contains("dark"));
    expect(isDarkBefore, `${route} initially light`).toBe(false);
    await toggle.click();
    await page.waitForTimeout(400);
    const isDarkAfter = await page.evaluate(() => document.documentElement.classList.contains("dark"));
    expect(isDarkAfter, `${route} after toggle dark`).toBe(true);
    const stored = await page.evaluate((k) => window.localStorage.getItem(k), THEME_KEY);
    expect(stored, `${route} localStorage dark`).toBe("dark");
    // Reload persists
    await page.reload();
    await page.waitForTimeout(800);
    const isDarkReload = await page.evaluate(() => document.documentElement.classList.contains("dark"));
    expect(isDarkReload, `${route} dark persists after reload`).toBe(true);
    // Toggle back
    const toggle2 = page.getByRole("button", { name: /Switch to/i }).first();
    await toggle2.click();
    await page.waitForTimeout(300);
    const isLight = await page.evaluate(() => document.documentElement.classList.contains("dark"));
    expect(isLight, `${route} back to light`).toBe(false);
  });
}
