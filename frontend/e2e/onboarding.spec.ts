import { test, expect, type Page } from "@playwright/test";
import { createDevSession, seedSession, E2E_API_BASE, tenantHeaders } from "./session";

/**
 * First-run onboarding (current single-screen flow).
 *
 * /onboarding shows one screen: the start title, a hint, the currency selector,
 * a drop zone, Skip, and Finish (enabled after the first upload). The dashboard
 * shows the same flow as an inline card until onboarding is done.
 *
 * Copy is Hungarian (session locale "hu"). Auth is a fresh dev session per test,
 * so every test starts from a household with onboarding not done.
 */

const TITLE = "Kezdj egy nyugtával";
const HINT = "Fotózd le vagy válassz egy képet";
const SKIP = "Kihagyás";
const FINISH = "Befejezés";
const DROP_INPUT = 'input[data-testid="dropzone-input"]';

async function freshHousehold(page: Page): Promise<void> {
  const session = await createDevSession(page.request, `onboarding-${Date.now()}-${Math.random().toString(36).slice(2, 7)}@example.test`);
  await seedSession(page, session.token, "hu");
  await page.request.put(`${E2E_API_BASE}/product/preferences`, {
    headers: tenantHeaders(session.tenantId),
    data: { payload: { onboarding_done: false } },
  });
}

test("onboarding page shows the start screen and Skip lands on the dashboard", async ({ page }) => {
  await freshHousehold(page);
  await page.goto("/onboarding", { waitUntil: "load" });

  await expect(page.locator("main h1").first()).toHaveText(TITLE);
  await expect(page.getByText(HINT)).toBeVisible();
  await expect(page.locator(DROP_INPUT)).toHaveCount(1);
  await expect(page.getByRole("button", { name: SKIP })).toBeVisible();

  await page.getByRole("button", { name: SKIP }).click();
  await page.waitForURL("**/dashboard", { timeout: 15_000 });
  // Onboarding is now done, so the dashboard must not show the first-run card again.
  await expect(page.locator("section[aria-labelledby='onboarding-title']")).toHaveCount(0);
});

test("first receipt upload enables Finish and opens the saved receipt", async ({ page }) => {
  await freshHousehold(page);
  await page.goto("/onboarding", { waitUntil: "load" });
  await expect(page.locator("main h1").first()).toHaveText(TITLE);

  await page.locator(DROP_INPUT).setInputFiles("e2e/fixtures/test-receipt-coop.jpg");

  const finish = page.getByRole("button", { name: FINISH });
  await expect(finish).toBeEnabled({ timeout: 90_000 });
  await finish.click();
  await page.waitForURL(/\/receipts\/[^/]+$/, { timeout: 20_000 });
});

test("dashboard first-run card can be dismissed", async ({ page }) => {
  await freshHousehold(page);
  await page.goto("/dashboard", { waitUntil: "load" });

  const card = page.locator("section[aria-labelledby='onboarding-title']");
  await expect(card).toBeVisible();
  await expect(card.locator("#onboarding-title")).toHaveText(TITLE);
  // No blocking dialog may cover the header while the card is shown.
  await expect(page.locator("[role='dialog'][aria-modal='true']")).toHaveCount(0);

  await card.getByRole("button", { name: "Ablak bezárása" }).click();
  await expect(card).toHaveCount(0);
});
