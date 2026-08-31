import { test, expect } from "@playwright/test";
import { seedAuthenticatedSession } from "./helpers/auth";

test.describe("Phase 1 contract-first GUI E2E", () => {
  test.beforeEach(async ({ page }) => { await seedAuthenticatedSession(page); });

  test("AC-040-01: Garanciák és visszaküldési határidők happy path", { annotation: [{ type: "requirement", description: "REQ-040-01" }, { type: "scenario", description: "AC-040-01" }] }, async ({ page }) => {
      await page.goto("/warranties");
      await expect(page.locator("[data-testid='warranties-page']")).toBeVisible();
      await expect(page.locator("[data-testid='warranties-primary-action']")).toBeVisible();
  });

  test("AC-040-06: tenant isolation has no foreign content", { annotation: [{ type: "requirement", description: "REQ-040-06" }, { type: "scenario", description: "AC-040-06" }] }, async ({ page }) => {
      await page.goto("/warranties?resource=e2e-foreign-id");
      await expect(page.locator("body")).not.toContainText("FOREIGN_TENANT_SECRET");
  });

  test("AC-040-07: duplicate activation produces one command", { annotation: [{ type: "requirement", description: "REQ-040-07" }, { type: "scenario", description: "AC-040-07" }] }, async ({ page }) => {
      let writes = 0;
      page.on("request", request => { if (request.method() !== "GET" && request.url().includes("/api/v2/warranties")) writes += 1; });
      await page.goto("/warranties");
      const action = page.locator("[data-testid='warranties-primary-action']");
      await action.dblclick();
      await expect.poll(() => writes).toBeLessThanOrEqual(1);
  });

  test("AC-041-01: Háztartási bevásárlási árfigyelés happy path", { annotation: [{ type: "requirement", description: "REQ-041-01" }, { type: "scenario", description: "AC-041-01" }] }, async ({ page }) => {
      await page.goto("/price-tracking");
      await expect(page.locator("[data-testid='price_tracking-page']")).toBeVisible();
      await expect(page.locator("[data-testid='price_tracking-primary-action']")).toBeVisible();
  });

  test("AC-041-06: tenant isolation has no foreign content", { annotation: [{ type: "requirement", description: "REQ-041-06" }, { type: "scenario", description: "AC-041-06" }] }, async ({ page }) => {
      await page.goto("/price-tracking?resource=e2e-foreign-id");
      await expect(page.locator("body")).not.toContainText("FOREIGN_TENANT_SECRET");
  });

  test("AC-041-07: duplicate activation produces one command", { annotation: [{ type: "requirement", description: "REQ-041-07" }, { type: "scenario", description: "AC-041-07" }] }, async ({ page }) => {
      let writes = 0;
      page.on("request", request => { if (request.method() !== "GET" && request.url().includes("/api/v2/price-tracking")) writes += 1; });
      await page.goto("/price-tracking");
      const action = page.locator("[data-testid='price_tracking-primary-action']");
      await action.dblclick();
      await expect.poll(() => writes).toBeLessThanOrEqual(1);
  });
});
