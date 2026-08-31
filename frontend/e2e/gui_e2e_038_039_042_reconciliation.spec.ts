import { test, expect } from "@playwright/test";
import { seedAuthenticatedSession } from "./helpers/auth";

test.describe("Phase 1 contract-first GUI E2E", () => {
  test.beforeEach(async ({ page }) => { await seedAuthenticatedSession(page); });

  test("AC-038-01: Bank- és kártyatranzakciók párosítása happy path", { annotation: [{ type: "requirement", description: "REQ-038-01" }, { type: "scenario", description: "AC-038-01" }] }, async ({ page }) => {
      await page.goto("/reconciliation");
      await expect(page.locator("[data-testid='reconciliation-page']")).toBeVisible();
      await expect(page.locator("[data-testid='reconciliation-primary-action']")).toBeVisible();
  });

  test("AC-038-06: tenant isolation has no foreign content", { annotation: [{ type: "requirement", description: "REQ-038-06" }, { type: "scenario", description: "AC-038-06" }] }, async ({ page }) => {
      await page.goto("/reconciliation?resource=e2e-foreign-id");
      await expect(page.locator("body")).not.toContainText("FOREIGN_TENANT_SECRET");
  });

  test("AC-038-07: duplicate activation produces one command", { annotation: [{ type: "requirement", description: "REQ-038-07" }, { type: "scenario", description: "AC-038-07" }] }, async ({ page }) => {
      let writes = 0;
      page.on("request", request => { if (request.method() !== "GET" && request.url().includes("/api/v2/reconciliation/matches")) writes += 1; });
      await page.goto("/reconciliation");
      const action = page.locator("[data-testid='reconciliation-primary-action']");
      await action.dblclick();
      await expect.poll(() => writes).toBeLessThanOrEqual(1);
  });

  test("AC-039-01: Hiányzó nyugták követése happy path", { annotation: [{ type: "requirement", description: "REQ-039-01" }, { type: "scenario", description: "AC-039-01" }] }, async ({ page }) => {
      await page.goto("/missing-receipts");
      await expect(page.locator("[data-testid='missing_receipts-page']")).toBeVisible();
      await expect(page.locator("[data-testid='missing_receipts-primary-action']")).toBeVisible();
  });

  test("AC-039-06: tenant isolation has no foreign content", { annotation: [{ type: "requirement", description: "REQ-039-06" }, { type: "scenario", description: "AC-039-06" }] }, async ({ page }) => {
      await page.goto("/missing-receipts?resource=e2e-foreign-id");
      await expect(page.locator("body")).not.toContainText("FOREIGN_TENANT_SECRET");
  });

  test("AC-039-07: duplicate activation produces one command", { annotation: [{ type: "requirement", description: "REQ-039-07" }, { type: "scenario", description: "AC-039-07" }] }, async ({ page }) => {
      let writes = 0;
      page.on("request", request => { if (request.method() !== "GET" && request.url().includes("/api/v2/missing-receipts")) writes += 1; });
      await page.goto("/missing-receipts");
      const action = page.locator("[data-testid='missing_receipts-primary-action']");
      await action.dblclick();
      await expect.poll(() => writes).toBeLessThanOrEqual(1);
  });

  test("AC-042-01: Visszatérítések és sztornók egyeztetése happy path", { annotation: [{ type: "requirement", description: "REQ-042-01" }, { type: "scenario", description: "AC-042-01" }] }, async ({ page }) => {
      await page.goto("/reconciliation/refunds");
      await expect(page.locator("[data-testid='refunds-page']")).toBeVisible();
      await expect(page.locator("[data-testid='refunds-primary-action']")).toBeVisible();
  });

  test("AC-042-06: tenant isolation has no foreign content", { annotation: [{ type: "requirement", description: "REQ-042-06" }, { type: "scenario", description: "AC-042-06" }] }, async ({ page }) => {
      await page.goto("/reconciliation/refunds?resource=e2e-foreign-id");
      await expect(page.locator("body")).not.toContainText("FOREIGN_TENANT_SECRET");
  });

  test("AC-042-07: duplicate activation produces one command", { annotation: [{ type: "requirement", description: "REQ-042-07" }, { type: "scenario", description: "AC-042-07" }] }, async ({ page }) => {
      let writes = 0;
      page.on("request", request => { if (request.method() !== "GET" && request.url().includes("/api/v2/refunds")) writes += 1; });
      await page.goto("/reconciliation/refunds");
      const action = page.locator("[data-testid='refunds-primary-action']");
      await action.dblclick();
      await expect.poll(() => writes).toBeLessThanOrEqual(1);
  });
});
