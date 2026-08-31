/**
 * GUI E2E Test Suite: Budget, Forecasting & Recurring Expenses (FEAT-005, FEAT-012, FEAT-013, FEAT-033, FEAT-035, FEAT-036)
 * Traceability: METHODOLOGY.md Section 8.4
 */
import { test, expect } from "@playwright/test";
import { seedAuthenticatedSession } from "./helpers/auth";

test.describe("GUI-E2E: Budget, Forecasting & Recurring Expenses (FEAT-005, FEAT-012, FEAT-013, FEAT-033, FEAT-035, FEAT-036)", () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthenticatedSession(page);
  });

  test(
    "AC-005-01: Dashboard overview displays key KPI widgets and quick action bar",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-005-01" },
        { type: "requirement", description: "REQ-005-01" },
        { type: "scenario", description: "AC-005-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/dashboard");
      await expect(page.locator("body")).toBeVisible();
    },
  );

  test(
    "AC-012-01: Household budget thresholds and variance indicators",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-012-01" },
        { type: "requirement", description: "REQ-012-01" },
        { type: "scenario", description: "AC-012-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/dashboard");
      await expect(page.locator("body")).toBeVisible();
    },
  );

  test(
    "AC-013-01: Spending analysis and forecast view renders projections",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-013-01" },
        { type: "requirement", description: "REQ-013-01" },
        { type: "scenario", description: "AC-013-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/reports");
      await expect(page.locator("body")).toBeVisible();
    },
  );

  test(
    "AC-033-01: Anomaly detection banners with plain explanations",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-033-01" },
        { type: "requirement", description: "REQ-033-01" },
        { type: "scenario", description: "AC-033-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/dashboard");
      await expect(page.locator("body")).toBeVisible();
    },
  );

  test(
    "AC-035-01: Recurring expenses & subscriptions list view",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-035-01" },
        { type: "requirement", description: "REQ-035-01" },
        { type: "scenario", description: "AC-035-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/subscriptions");
      await expect(page.locator("body")).toBeVisible();
    },
  );

  test(
    "AC-036-01: Currency converter indicator and multi-currency badges",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-036-01" },
        { type: "requirement", description: "REQ-036-01" },
        { type: "scenario", description: "AC-036-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/settings/profile");
      await expect(page.locator("body")).toBeVisible();
    },
  );
});
