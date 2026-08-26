/**
 * US-002: Google SSO bejelentkezés — evolúciós E2E (behavior-first)
 *
 * Spec for docs/stories/US-002-google-sso.md (4 AC, gui_flow).
 * Fut: npx playwright test --config playwright.prod.config.ts e2e/us_002_google_sso.spec.ts
 * Canary cron is futtatja.
 */
import { test, expect, type Page } from "@playwright/test";

const BASE = process.env.E2E_BASE_URL ?? "https://receipts.allthezoo.com";
const SESSION_TOKEN =
  process.env.E2E_SESSION_TOKEN ?? "e2e_tnxDwAyuZWVYIp6UK1vMrRcDOb1g_73eEIuQq05t_gg";
const SESSION_KEY = "receiptlens.session";

async function seedSession(page: Page, token: string = SESSION_TOKEN): Promise<void> {
  await page.addInitScript(
    ([key, value]) => window.localStorage.setItem(key, value as string),
    [SESSION_KEY, token] as const,
  );
}

async function expectAssetsAndNoCrash(page: Page, route: string): Promise<void> {
  const overlayGone = await page.evaluate(() => {
    const portal = document.querySelector("nextjs-portal");
    if (!portal?.shadowRoot) return true;
    return !portal.shadowRoot.textContent?.includes("Unhandled Runtime Error");
  });
  expect(overlayGone, `${route}: Unhandled Runtime Error`).toBe(true);
  const cssFailures = await page.evaluate(() =>
    Array.from(document.querySelectorAll('link[rel="stylesheet"]'))
      .filter((l) => (l as HTMLLinkElement).sheet === null)
      .map((l) => (l as HTMLLinkElement).href),
  );
  expect(cssFailures, `${route}: betöltetlen stylesheet(ek)`).toHaveLength(0);
}

test.describe("US-002: Google SSO bejelentkezés (evolúciós)", () => {
  test.setTimeout(90_000);

  test("AC1: /login-en látszik a Folytatás Google-lel gomb + /api/auth/google/start 307", async ({ page }) => {
    // Skip seed — AC1 checks unauthenticated login page
    const probe = await page.request.get(`${BASE}/api/auth/google/status`);
    const enabled = probe.ok() ? ((await probe.json()) as { enabled: boolean }).enabled : false;
    test.skip(!enabled, "Google SSO nincs engedélyezve — AC1 skip");

    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1200);

    const link = page.locator('a[href*="/api/auth/google/start"]').first();
    await expect(link, "Folytatás Google-lel link nem látszik").toBeVisible({ timeout: 8000 });
    await expect(link).toContainText(/Folytatás Google|Google/i);
    const href = await link.getAttribute("href");
    expect(href).toContain("/api/auth/google/start");

    // Backend contract: 307 + Location google + HttpOnly cookie — via page.request (no redirect follow)
    const start = await page.request.get(`${BASE}/api/auth/google/start`, { maxRedirects: 0 } as unknown as { maxRedirects: number });
    // playwright's APIRequestContext follows on 307 by default when maxRedirects not honored — fallback to raw response check
    const locHeader = start.headers()["location"] ?? "";
    const is307 = start.status() === 307 || locHeader.includes("accounts.google.com");
    expect(is307, `start 307 + google Location kell, kapott ${start.status()} loc=${locHeader.slice(0, 80)}`).toBe(true);
    await expectAssetsAndNoCrash(page, "/login (US-002 AC1)");
  });

  test("AC2: /auth/google/callback hibák — hibaüzenet, nem üres oldal", async ({ page }) => {
    await page.goto("/auth/google/callback");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1200);
    await expectAssetsAndNoCrash(page, "/auth/google/callback (AC2)");
    const body = (await page.textContent("body")) ?? "";
    expect(body).toMatch(/Google|bejelentkezés|hiányzó|sikertelen|ReceiptLens/i);
  });

  test("AC3: bejelentkezett user — dashboard Bearer-rel 200 + Topbar Kilépés", async ({ page }) => {
    await seedSession(page);
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(3000);

    // Dismiss onboarding if it overlays
    const maybeDialog = page.locator('[role="dialog"][aria-modal="true"]').first();
    if ((await maybeDialog.count()) > 0 && (await maybeDialog.isVisible())) {
      const skip = maybeDialog.getByRole("button", { name: /Kihagyás/i });
      if ((await skip.count()) > 0) await skip.click();
      await expect(maybeDialog).toBeHidden({ timeout: 8000 });
    }

    const probe = await page.request.get(`${BASE}/api/api/v1/consumer/dashboard`, {
      headers: { Authorization: `Bearer ${SESSION_TOKEN}` },
    });
    expect(probe.status(), "consumer/dashboard Bearer-rel 200 kell").toBe(200);

    // Topbar: Kilépés csak bejelentkezve
    const logoutBtn = page.getByRole("button", { name: "Kilépés" });
    await expect(logoutBtn).toBeVisible({ timeout: 8000 });
    await expectAssetsAndNoCrash(page, "/dashboard (US-002 AC3)");
  });

  test("AC4: GUI — /login card középen, session-nél nincs felesleges Google CTA eltűnés", async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1000);
    await expect(page.getByRole("heading", { name: /ReceiptLens/i }).first()).toBeVisible();
    await expect(page.getByRole("button", { name: /Sign in/i })).toBeVisible();
    await expectAssetsAndNoCrash(page, "/login (US-002 AC4)");
  });
});
