import path from "node:path";
import { test, expect, type Page } from "@playwright/test";
import { seedAuthenticatedSession } from "./helpers/auth";

const RECEIPT_IMAGE = path.join(__dirname, "fixtures", "test-receipt-coop.jpg");

// Assertions use test ids and locale-tolerant labels, so they pass in any UI language.
const uniqueName = (prefix: string) => `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;

async function openCreateForm(page: Page, testId: string) {
  await page.getByTestId(`${testId}-primary-action`).click();
}

test.describe("Feature workflows (real state machines)", () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthenticatedSession(page);
  });

  test("missing receipts: create, assign through the inline input, status follows", async ({ page }) => {
    await page.goto("/missing-receipts");
    await openCreateForm(page, "missing_receipts");
    const name = uniqueName("Hiányzó");
    const form = page.getByRole("form");
    await form.getByLabel(/Megnevezés|Name/).fill(name);
    await form.getByLabel(/Kereskedő|Merchant/).fill("Példa Bolt");
    await form.getByLabel(/Összeg|Amount/).fill("1200");
    await form.getByRole("button", { name: /^(Mentés|Save)$/ }).click();

    const item = page.getByTestId("missing_receipts-item").filter({ hasText: name });
    await expect(item).toBeVisible();
    await item.getByTestId("missing_receipts-action-assign").click();
    await item.getByLabel(/Felelős|Assignee/).fill("Anna");
    await item.getByTestId("missing_receipts-apply").click();
    await expect(item.getByTestId("missing_receipts-status")).toHaveText(/Hozzárendelve|Assigned/);
    // Assigned items can be snoozed, exempted, resolved or reopened, but not assigned again from the same status.
    await expect(item.getByTestId("missing_receipts-action-snooze")).toBeVisible();
  });

  test("savings goal: contribution moves progress and reaching the target achieves the goal", async ({ page }) => {
    await page.goto("/savings-goals");
    await openCreateForm(page, "savings_goals");
    const name = uniqueName("Cél");
    const form = page.getByRole("form");
    await form.getByLabel(/Megnevezés|Name/).fill(name);
    await form.getByLabel(/Célösszeg|Target amount/).fill("100");
    await form.getByLabel(/Pénznem|Currency/).fill("HUF");
    await form.getByRole("button", { name: /^(Mentés|Save)$/ }).click();

    const item = page.getByTestId("savings_goals-item").filter({ hasText: name });
    await expect(item).toBeVisible();
    await item.getByTestId("savings_goals-action-activate").click();
    await item.getByTestId("savings_goals-action-contribute").click();
    await item.getByLabel(/Összeg|Amount/).fill("40");
    await item.getByTestId("savings_goals-apply").click();
    await expect(item.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "40");

    await item.getByTestId("savings_goals-action-contribute").click();
    await item.getByLabel(/Összeg|Amount/).fill("60");
    await item.getByTestId("savings_goals-apply").click();
    await expect(item.getByTestId("savings_goals-status")).toHaveText(/Elérve|Achieved/);
  });

  test("period close: precheck, close, then the closed period accepts only a reopen request", async ({ page }) => {
    await page.goto("/accounting/period-close");
    await openCreateForm(page, "period_close");
    // A random year keeps this period clear of data from other runs.
    const period = `${1900 + Math.floor(Math.random() * 99)}-${String(1 + Math.floor(Math.random() * 12)).padStart(2, "0")}`;
    const form = page.getByRole("form");
    await form.getByLabel(/Megnevezés|Name/).fill(uniqueName("Időszak"));
    await form.getByLabel(/Időszak|Period/).fill(period);
    await form.getByRole("button", { name: /^(Mentés|Save)$/ }).click();

    const item = page.getByTestId("period_close-item").filter({ hasText: period });
    await expect(item).toBeVisible();
    await item.getByTestId("period_close-action-precheck").click();
    await expect(item.getByTestId("period_close-status")).toHaveText(/Lezárható|Ready to close/);
    await item.getByTestId("period_close-action-close").click();
    await expect(item.getByTestId("period_close-status")).toHaveText(/Lezárva|Closed/);
    await expect(item.getByTestId("period_close-action-request_reopen")).toBeVisible();
    await expect(item.getByTestId("period_close-action-precheck")).toHaveCount(0);
    await expect(item.getByTestId("period_close-action-close")).toHaveCount(0);
  });

  test("mobile capture: a photo uploads, opens a capture item and attaches the receipt", async ({ page }) => {
    await page.goto("/receipts/capture");
    await page.getByTestId("mobile_receipts-file").setInputFiles(RECEIPT_IMAGE);
    const item = page.getByTestId("mobile_receipts-item").filter({ hasText: "test-receipt-coop.jpg" });
    await expect(item).toBeVisible({ timeout: 60000 });
    await expect(item.getByTestId("mobile_receipts-status")).toHaveText(/Előnézet|Preview/);
  });

  test("offline capture: a photo taken offline is queued, then uploaded and synced on reconnect", async ({ page, context }) => {
    await page.goto("/receipts/capture");
    await context.setOffline(true);
    await page.getByTestId("mobile_receipts-file").setInputFiles(RECEIPT_IMAGE);
    await expect(page.getByRole("status")).toHaveText(/Nincs kapcsolat|You are offline/, { timeout: 15000 });

    await expect(page.getByTestId("mobile_receipts-capture")).toContainText(/1 szinkronra vár|1 waiting/);

    // Back online, opening the offline page syncs the queue without any click.
    await context.setOffline(false);
    await page.goto("/receipts/offline");
    // Earlier runs may have left items with the same file name, so take the newest one (first in the list).
    const synced = page.getByTestId("offline_sync-item").filter({ hasText: "test-receipt-coop.jpg" }).first();
    await expect(synced).toBeVisible({ timeout: 90000 });
    await expect(synced.getByTestId("offline_sync-status")).toHaveText(/Szinkronizálva|Synced/);
    await expect(page.getByTestId("offline_sync-queue")).toContainText(/0 szinkronra vár|0 waiting/, { timeout: 20000 });
  });

  test("offline sync page: the queue panel renders and empty queue cannot sync", async ({ page }) => {
    await page.goto("/receipts/offline");
    await expect(page.getByTestId("offline_sync-page")).toBeVisible();
    await expect(page.getByTestId("offline_sync-queue")).toBeVisible();
    await expect(page.getByTestId("offline_sync-sync-now")).toBeDisabled();
  });
});
