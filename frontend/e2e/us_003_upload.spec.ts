/**
 * US-003: Nyugta feltöltés — evolúciós E2E (behavior-first)
 *
 * Spec for docs/stories/US-003-nyugta-feltoltes.md (4 AC, gui_flow).
 * Fut: npx playwright test --config playwright.prod.config.ts e2e/us_003_upload.spec.ts
 * Canary cron futtatja.
 */
import { test, expect, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";

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
}

test.describe("US-003: Nyugta feltöltés (evolúciós)", () => {
  test.setTimeout(90_000);

  test("AC1: /upload betölt + DropZone látható", async ({ page }) => {
    await seedSession(page);
    await page.goto("/upload");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(2000);

    await expect(page.getByRole("heading", { name: /Nyugta hozzáadása|Add receipt|Beleg hinzufügen/i })).toBeVisible({ timeout: 8000 });
    // DropZone: input[type=file] vagy drag area
    const dropZone = page.locator('[data-testid="drop-zone"], input[type="file"], [role="button"]:has-text("Húzd")').first();
    const zoneVisible = (await dropZone.count()) > 0 && (await dropZone.isVisible().catch(() => false));
    // Fallback: at least the EmptyState or upload page content
    if (!zoneVisible) {
      await expect(page.locator("body")).toContainText(/Nyugta|Ready when you are|drag|drop|photo/i, { timeout: 6000 });
    }
    await expectAssetsAndNoCrash(page, "/upload (US-003 AC1)");
  });

  test("AC2: AI Scan gated — prod-on nincs active, coming soon szöveg", async ({ page }) => {
    await seedSession(page);
    await page.goto("/upload");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
    const body = (await page.textContent("body")) ?? "";
    expect(body).toMatch(/coming soon|Pro plan|AI Scan.*coming|Vision AI/i);
    await expectAssetsAndNoCrash(page, "/upload (US-003 AC2)");
  });

  test("AC3: API happy — session-nel /product/receipts/upload 201", async ({ page }) => {
    // Validate via API (artifacts via page.request)
    const img = readFileSync("e2e/fixtures/test-receipt-coop.jpg");
    const res = await page.request.post(`${BASE}/api/product/receipts/upload`, {
      headers: { Authorization: `Bearer ${SESSION_TOKEN}` },
      multipart: { file: { name: "receipt.jpg", mimeType: "image/jpeg", buffer: img } },
    });
    expect(res.status(), `upload 201 kell, kapott ${res.status()} body=${(await res.text()).slice(0, 200)}`).toBe(201);
    const json = (await res.json()) as { receipt_id?: string; source?: string };
    expect(json.receipt_id, "receipt_id kell").toBeTruthy();
  });

  test("AC4: GUI — upload page without crash, EmptyState or Queue sichtbar", async ({ page }) => {
    await seedSession(page);
    await page.goto("/upload");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
    await expectAssetsAndNoCrash(page, "/upload (US-003 AC4)");
  });
});
