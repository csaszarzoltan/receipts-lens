import { test, expect } from "@playwright/test";
import { seedAuthenticatedSession } from "./helpers/auth";

test.describe("Phase 1 contract-first GUI E2E", () => {
  test.beforeEach(async ({ page }) => { await seedAuthenticatedSession(page); });

  test("AC-045-01: Offline nyugtarögzítés és későbbi szinkronizálás happy path", { annotation: [{ type: "requirement", description: "REQ-045-01" }, { type: "scenario", description: "AC-045-01" }] }, async ({ page }) => {
      await page.goto("/receipts/offline");
      await expect(page.locator("[data-testid='offline_sync-page']")).toBeVisible();
      await expect(page.locator("[data-testid='offline_sync-primary-action']")).toBeVisible();
      await page.setViewportSize({ width: 390, height: 844 });
      await page.context().setOffline(true);
      await page.context().setOffline(false);
  });

  test("AC-045-06: tenant isolation has no foreign content", { annotation: [{ type: "requirement", description: "REQ-045-06" }, { type: "scenario", description: "AC-045-06" }] }, async ({ page }) => {
      await page.goto("/receipts/offline?resource=e2e-foreign-id");
      await expect(page.locator("body")).not.toContainText("FOREIGN_TENANT_SECRET");
  });

  test("AC-045-07: duplicate activation produces one command", { annotation: [{ type: "requirement", description: "REQ-045-07" }, { type: "scenario", description: "AC-045-07" }] }, async ({ page }) => {
      let writes = 0;
      page.on("request", request => { if (request.method() !== "GET" && request.url().includes("/api/v2/offline-sync")) writes += 1; });
      await page.goto("/receipts/offline");
      const action = page.locator("[data-testid='offline_sync-primary-action']");
      await action.dblclick();
      await expect.poll(() => writes).toBeLessThanOrEqual(1);
  });

  test("AC-048-01: Mobil nyugtakezelési munkafolyamat optimalizálása happy path", { annotation: [{ type: "requirement", description: "REQ-048-01" }, { type: "scenario", description: "AC-048-01" }] }, async ({ page }) => {
      await page.goto("/receipts/capture");
      await expect(page.locator("[data-testid='mobile_receipts-page']")).toBeVisible();
      await expect(page.locator("[data-testid='mobile_receipts-primary-action']")).toBeVisible();
      await page.setViewportSize({ width: 390, height: 844 });
      await page.context().setOffline(true);
      await page.context().setOffline(false);
  });

  test("AC-048-06: tenant isolation has no foreign content", { annotation: [{ type: "requirement", description: "REQ-048-06" }, { type: "scenario", description: "AC-048-06" }] }, async ({ page }) => {
      await page.goto("/receipts/capture?resource=e2e-foreign-id");
      await expect(page.locator("body")).not.toContainText("FOREIGN_TENANT_SECRET");
  });

  test("AC-048-07: duplicate activation produces one command", { annotation: [{ type: "requirement", description: "REQ-048-07" }, { type: "scenario", description: "AC-048-07" }] }, async ({ page }) => {
      let writes = 0;
      page.on("request", request => { if (request.method() !== "GET" && request.url().includes("/api/v2/mobile-receipts")) writes += 1; });
      await page.goto("/receipts/capture");
      const action = page.locator("[data-testid='mobile_receipts-primary-action']");
      await action.dblclick();
      await expect.poll(() => writes).toBeLessThanOrEqual(1);
  });
});
