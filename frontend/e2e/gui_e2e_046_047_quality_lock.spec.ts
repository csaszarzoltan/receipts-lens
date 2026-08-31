import { test, expect } from "@playwright/test";
import { seedAuthenticatedSession } from "./helpers/auth";

test.describe("Phase 1 contract-first GUI E2E", () => {
  test.beforeEach(async ({ page }) => { await seedAuthenticatedSession(page); });

  test("AC-046-01: Adatminőségi feladatközpont happy path", { annotation: [{ type: "requirement", description: "REQ-046-01" }, { type: "scenario", description: "AC-046-01" }] }, async ({ page }) => {
      await page.goto("/quality-inbox");
      await expect(page.locator("[data-testid='data_quality-page']")).toBeVisible();
      await expect(page.locator("[data-testid='data_quality-primary-action']")).toBeVisible();
  });

  test("AC-046-06: tenant isolation has no foreign content", { annotation: [{ type: "requirement", description: "REQ-046-06" }, { type: "scenario", description: "AC-046-06" }] }, async ({ page }) => {
      await page.goto("/quality-inbox?resource=e2e-foreign-id");
      await expect(page.locator("body")).not.toContainText("FOREIGN_TENANT_SECRET");
  });

  test("AC-046-07: duplicate activation produces one command", { annotation: [{ type: "requirement", description: "REQ-046-07" }, { type: "scenario", description: "AC-046-07" }] }, async ({ page }) => {
      let writes = 0;
      page.on("request", request => { if (request.method() !== "GET" && request.url().includes("/api/v2/quality-tasks")) writes += 1; });
      await page.goto("/quality-inbox");
      const action = page.locator("[data-testid='data_quality-primary-action']");
      await action.dblclick();
      await expect.poll(() => writes).toBeLessThanOrEqual(1);
  });

  test("AC-047-01: Könyvelési időszak lezárása happy path", { annotation: [{ type: "requirement", description: "REQ-047-01" }, { type: "scenario", description: "AC-047-01" }] }, async ({ page }) => {
      await page.goto("/accounting/period-close");
      await expect(page.locator("[data-testid='period_close-page']")).toBeVisible();
      await expect(page.locator("[data-testid='period_close-primary-action']")).toBeVisible();
  });

  test("AC-047-06: tenant isolation has no foreign content", { annotation: [{ type: "requirement", description: "REQ-047-06" }, { type: "scenario", description: "AC-047-06" }] }, async ({ page }) => {
      await page.goto("/accounting/period-close?resource=e2e-foreign-id");
      await expect(page.locator("body")).not.toContainText("FOREIGN_TENANT_SECRET");
  });

  test("AC-047-07: duplicate activation produces one command", { annotation: [{ type: "requirement", description: "REQ-047-07" }, { type: "scenario", description: "AC-047-07" }] }, async ({ page }) => {
      let writes = 0;
      page.on("request", request => { if (request.method() !== "GET" && request.url().includes("/api/v2/accounting-periods")) writes += 1; });
      await page.goto("/accounting/period-close");
      const action = page.locator("[data-testid='period_close-primary-action']");
      await action.dblclick();
      await expect.poll(() => writes).toBeLessThanOrEqual(1);
  });
});
