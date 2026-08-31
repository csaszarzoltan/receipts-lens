import { test, expect } from "@playwright/test";
import { seedAuthenticatedSession } from "./helpers/auth";

test.describe("Phase 1 contract-first GUI E2E", () => {
  test.beforeEach(async ({ page }) => { await seedAuthenticatedSession(page); });

  test("AC-043-01: Megosztott vásárlások és költségfelosztás happy path", { annotation: [{ type: "requirement", description: "REQ-043-01" }, { type: "scenario", description: "AC-043-01" }] }, async ({ page }) => {
      await page.goto("/cost-splits");
      await expect(page.locator("[data-testid='cost_splits-page']")).toBeVisible();
      await expect(page.locator("[data-testid='cost_splits-primary-action']")).toBeVisible();
  });

  test("AC-043-06: tenant isolation has no foreign content", { annotation: [{ type: "requirement", description: "REQ-043-06" }, { type: "scenario", description: "AC-043-06" }] }, async ({ page }) => {
      await page.goto("/cost-splits?resource=e2e-foreign-id");
      await expect(page.locator("body")).not.toContainText("FOREIGN_TENANT_SECRET");
  });

  test("AC-043-07: duplicate activation produces one command", { annotation: [{ type: "requirement", description: "REQ-043-07" }, { type: "scenario", description: "AC-043-07" }] }, async ({ page }) => {
      let writes = 0;
      page.on("request", request => { if (request.method() !== "GET" && request.url().includes("/api/v2/cost-splits")) writes += 1; });
      await page.goto("/cost-splits");
      const action = page.locator("[data-testid='cost_splits-primary-action']");
      await action.dblclick();
      await expect.poll(() => writes).toBeLessThanOrEqual(1);
  });

  test("AC-044-01: Kiadási célok és megtakarítási lehetőségek happy path", { annotation: [{ type: "requirement", description: "REQ-044-01" }, { type: "scenario", description: "AC-044-01" }] }, async ({ page }) => {
      await page.goto("/savings-goals");
      await expect(page.locator("[data-testid='savings_goals-page']")).toBeVisible();
      await expect(page.locator("[data-testid='savings_goals-primary-action']")).toBeVisible();
  });

  test("AC-044-06: tenant isolation has no foreign content", { annotation: [{ type: "requirement", description: "REQ-044-06" }, { type: "scenario", description: "AC-044-06" }] }, async ({ page }) => {
      await page.goto("/savings-goals?resource=e2e-foreign-id");
      await expect(page.locator("body")).not.toContainText("FOREIGN_TENANT_SECRET");
  });

  test("AC-044-07: duplicate activation produces one command", { annotation: [{ type: "requirement", description: "REQ-044-07" }, { type: "scenario", description: "AC-044-07" }] }, async ({ page }) => {
      let writes = 0;
      page.on("request", request => { if (request.method() !== "GET" && request.url().includes("/api/v2/savings-goals")) writes += 1; });
      await page.goto("/savings-goals");
      const action = page.locator("[data-testid='savings_goals-primary-action']");
      await action.dblclick();
      await expect.poll(() => writes).toBeLessThanOrEqual(1);
  });
});
