import { test, expect, type Page } from "@playwright/test";

/**
 * F1.5 consumer onboarding E2E — full 3-step journey (plan §4 / F1.5).
 *
 * Acceptance coverage:
 *  1. Exactly 3 steps with sticky progress + forward/back, skippable.
 *  2. Step 1 shows the one-sentence positioning promise (§3.1):
 *     "Fotózd le a nyugtát. Mi megmutatjuk, hol folyik el a pénzed — és hol
 *     takaríthatsz meg."
 *  3. Finishing navigates to the consumer dashboard (/dashboard).
 *  4. State persistence: after completion, the flow does not reappear
 *     (onboarding_done persisted via /product/preferences).
 *
 * The receipt-upload leg of step 3 is exercised by the contract tests +
 * the browser-helper journey (real camera cannot be driven headless); here
 * we verify the full navigation flow, the promise copy and persistence.
 */

const ONBOARDING_DONE_KEY = "receiptlens.onboarding.seen"; // local echo only

// The backend the frontend talks to (NEXT_PUBLIC_API_BASE_URL of the dev
// server under test). Overridable so CI can point at any port.
const API_BASE = process.env.E2E_API_BASE ?? "http://127.0.0.1:8100";

async function seedAuth(page: Page): Promise<void> {
  await page.addInitScript(() => {
    window.localStorage.setItem("receiptlens.tenant", "demo");
    window.localStorage.setItem("receiptlens.role", "admin");
  });
  // The demo tenant may already have onboarding_done=true persisted from an
  // earlier run (which would redirect /onboarding straight to /dashboard).
  // Reset it so the flow under test genuinely starts from step 1.
  await page.request.put(`${API_BASE}/product/preferences`, {
    headers: { "X-Tenant-ID": "demo", "X-Role": "admin" },
    data: { payload: { onboarding_done: false } },
  });
}

test("onboarding: 3-step journey with promise, back/forward, dashboard finish and persistence", async ({ page }) => {
  await seedAuth(page);
  await page.goto("/onboarding");
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(1500);

  // --- Step 1: positioning promise (§3.1) ---
  const h1 = page.locator("h1").first();
  await expect(h1).toBeVisible({ timeout: 10_000 });
  await expect(h1).toContainText("Mi ez?");
  await expect(page.getByText(/Fotózd le a nyugtát/)).toBeVisible();
  await expect(page.getByText(/1\. lépés a 3 közül/)).toBeVisible();

  // --- Step 2: camera / upload access ---
  await page.getByRole("button", { name: "Tovább" }).click();
  await expect(h1).toContainText("Kamera hozzáférése");
  await expect(page.getByRole("button", { name: /Fénykép készítése/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Feltöltés az eszközről/ })).toBeVisible();
  await expect(page.getByText(/2\. lépés a 3 közül/)).toBeVisible();

  // --- Back navigation preserves state (sticky) ---
  await page.getByRole("button", { name: "Vissza" }).click();
  await expect(h1).toContainText("Mi ez?");
  await page.getByRole("button", { name: "Tovább" }).click();

  // --- Step 3: first receipt ---
  await page.getByRole("button", { name: "Tovább" }).click();
  await expect(h1).toContainText("Az első nyugtád");
  await expect(page.getByRole("button", { name: /Nyugta kiválasztása/ })).toBeVisible();
  await expect(page.getByText(/3\. lépés a 3 közül/)).toBeVisible();

  // --- Finish → consumer dashboard (F1.2 destination) ---
  await page.getByRole("button", { name: /Áttekintés megnyitása/ }).click();
  await page.waitForURL("**/dashboard", { timeout: 15_000 });
  await expect(page.locator("h1").first()).toBeVisible({ timeout: 10_000 });
  // The dashboard shell (AppShell) renders — dashboard heading or app shell
  // must be present; the Onboarding modal must NOT be shown anymore.
  await expect(page.locator('[role="dialog"][aria-modal="true"]')).toHaveCount(0);

  // --- State persistence: no replay on next visit ---
  await page.goto("/onboarding");
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(1500);
  await expect(page.locator('[role="dialog"][aria-modal="true"]')).toHaveCount(0);
});

test("onboarding: skip is available and lands on dashboard", async ({ page }) => {
  await seedAuth(page);
  await page.goto("/onboarding");
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(1500);

  await expect(page.locator("h1").first()).toContainText("Mi ez?");
  await page.getByRole("button", { name: "Kihagyás" }).click();
  await page.waitForURL("**/dashboard", { timeout: 15_000 });
  await expect(page.locator("h1").first()).toBeVisible({ timeout: 10_000 });
});

test("onboarding: first receipt upload shows the extracted result (step 3)", async ({ page }) => {
  await seedAuth(page);
  await page.goto("/onboarding");
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(1500);

  // Step 1 → 2
  await page.getByRole("button", { name: "Tovább" }).click();
  await expect(page.locator("h1").first()).toContainText("Kamera hozzáférése");
  // Step 2 → 3
  await page.getByRole("button", { name: "Tovább" }).click();
  await expect(page.locator("h1").first()).toContainText("Az első nyugtád");

  // Real file upload through the picker (the page uses uploadReceipt —
  // the classic OCR pipeline with the F1.4 confidence level — against the
  // live backend; the AI vision toggle stays on /upload).
  const fileInput = page.locator('input[data-testid="onboarding-file-input"]');
  await fileInput.setInputFiles("e2e/fixtures/test-receipt-coop.jpg");

  // Processing state appears, then the extracted result panel.
  await expect(page.getByText("Feldolgozás…")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText(/Kész — az első nyugtád feldolgozva/)).toBeVisible({
    timeout: 60_000,
  });

  // Finishing navigates to the consumer dashboard.
  await page.getByRole("button", { name: /Áttekintés megnyitása/ }).click();
  await page.waitForURL("**/dashboard", { timeout: 15_000 });
  await expect(page.locator("h1").first()).toBeVisible({ timeout: 10_000 });
});
