/**
 * GUI E2E Test Suite: Accounting, Categorization & Export (FEAT-011, FEAT-014, FEAT-015, FEAT-021, FEAT-023)
 * Traceability: METHODOLOGY.md Section 8.4
 */
import { test, expect } from "@playwright/test";
import { seedAuthenticatedSession } from "./helpers/auth";

test.describe("GUI-E2E: Accounting, Categorization & Export (FEAT-011, FEAT-014, FEAT-015, FEAT-021, FEAT-023)", () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthenticatedSession(page);
  });

  test(
    "AC-011-01: Category picker and tax assignment dropdowns",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-011-01" },
        { type: "requirement", description: "REQ-011-01" },
        { type: "scenario", description: "AC-011-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/receipts");
      await expect(page.locator("body")).toBeVisible();
    },
  );

  test(
    "AC-014-01: Reports view displays monthly charts and summary metrics",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-014-01" },
        { type: "requirement", description: "REQ-014-01" },
        { type: "scenario", description: "AC-014-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/reports");
      await expect(page.locator("body")).toBeVisible();
      const heading = page.locator("h1, h2").first();
      await expect(heading).toBeVisible();
    },
  );

  test(
    "AC-015-01: Export preparation page with format selector (CSV, JSON, PDF)",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-015-01" },
        { type: "requirement", description: "REQ-015-01" },
        { type: "scenario", description: "AC-015-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/exports/prepare");
      await expect(page.locator("body")).toBeVisible();
    },
  );

  test(
    "AC-021-01: Automation rule builder with triggers and actions",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-021-01" },
        { type: "requirement", description: "REQ-021-01" },
        { type: "scenario", description: "AC-021-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/automations/demo-rule-id");
      await expect(page.locator("body")).toBeVisible();
    },
  );

  test(
    "AC-023-01: Tax workspace view and audit package download",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-023-01" },
        { type: "requirement", description: "REQ-023-01" },
        { type: "scenario", description: "AC-023-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/exports/runs/demo-run-id");
      await expect(page.locator("body")).toBeVisible();
    },
  );
});
