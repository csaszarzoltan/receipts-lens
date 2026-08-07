import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/**
 * ReceiptLens UI E2E smoke — fast subset.
 *
 * Checks: route load without Next.js "Unhandled Runtime Error" overlay,
 * at least one visible h1 per route, and an axe a11y audit (serious/critical
 * violations blocking). Uses domcontentloaded + 2s settle for SWR fetches
 * instead of networkidle (which times out on SPAs with polling SWR hooks).
 *
 * Auth: header-based (X-Tenant-ID/X-Role) seeded into localStorage before
 * navigation so (app) routes render without manual login.
 */

const TENANT_KEY = "receiptlens.tenant";
const ROLE_KEY = "receiptlens.role";

async function seedAuth(page: Page): Promise<void> {
  await page.addInitScript(
    ([tenantKey, roleKey]) => {
      window.localStorage.setItem(tenantKey, "demo");
      window.localStorage.setItem(roleKey, "admin");
    },
    [TENANT_KEY, ROLE_KEY] as const,
  );
}

async function expectNoErrorOverlay(page: Page): Promise<void> {
  const overlayGone = await page.evaluate(() => {
    const portal = document.querySelector("nextjs-portal");
    if (!portal?.shadowRoot) return true;
    return !portal.shadowRoot.textContent?.includes(
      "Unhandled Runtime Error",
    );
  });
  expect(overlayGone, "Unhandled Runtime Error overlay detected").toBe(true);
}

/** Key routes — the critical consumer-facing pages. */
const KEY_ROUTES = [
  "/",
  "/login",
  "/onboarding",
  "/dashboard",
  "/subscriptions",
  "/receipts",
  "/upload",
  "/reports",
  "/settings",
];

for (const route of KEY_ROUTES) {
  test(`page loads without crash: ${route}`, async ({ page }) => {
    await seedAuth(page);
    await page.goto(route);
    // domcontentloaded + settle avoids SWR long-poll timeout
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(2000);

    await expectNoErrorOverlay(page);

    const h1 = page.locator("h1").first();
    await expect(h1).toBeVisible({ timeout: 10_000 });
  });

  test(`accessibility: ${route}`, async ({ page }) => {
    await seedAuth(page);
    await page.goto(route);
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(2000);

    const results = await new AxeBuilder({ page })
      .disableRules(["color-contrast"]) // design tokens make this noisy
      .analyze();

    const blocking = results.violations.filter(
      (v) => v.impact === "serious" || v.impact === "critical",
    );

    expect(
      blocking,
      `Accessibility serious/critical violations on ${route}:\n${blocking
        .map((v) => `  - ${v.id}: ${v.description}`)
        .join("\n")}`,
    ).toHaveLength(0);
  });
}
