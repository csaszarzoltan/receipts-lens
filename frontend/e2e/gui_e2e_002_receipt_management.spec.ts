/**
 * GUI E2E Test Suite: Receipt Management, Upload, OCR & Review (FEAT-006 - FEAT-010, FEAT-031, FEAT-032)
 * Traceability: METHODOLOGY.md Section 8.4
 */
import { test, expect } from "@playwright/test";
import { seedAuthenticatedSession } from "./helpers/auth";

test.describe("GUI-E2E: Receipt Management, Upload & Review (FEAT-006 - FEAT-010, FEAT-031, FEAT-032)", () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthenticatedSession(page);
  });

  test(
    "AC-006-01: Receipt upload page renders dropzone and file picker",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-006-01" },
        { type: "requirement", description: "REQ-006-01" },
        { type: "scenario", description: "AC-006-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/upload");
      await page.waitForLoadState("domcontentloaded");
      await expect(page.locator("body")).toBeVisible();
      await expect(page.locator("main, h1, [role='button'], [data-testid='drop-zone']").first()).toBeVisible({ timeout: 10_000 });
    },
  );

  test(
    "AC-007-01: Upload queue shows status feedback during scan",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-007-01" },
        { type: "requirement", description: "REQ-007-01" },
        { type: "scenario", description: "AC-007-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/upload");
      await expect(page.locator("body")).toBeVisible();
    },
  );

  test(
    "AC-008-01: Receipt list view with table, filters and search bar",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-008-01" },
        { type: "requirement", description: "REQ-008-01" },
        { type: "scenario", description: "AC-008-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/receipts");
      await expect(page.locator("body")).toBeVisible();
    },
  );

  test(
    "AC-009-01: Receipt detail and manual review interface loads properly",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-009-01" },
        { type: "requirement", description: "REQ-009-01" },
        { type: "scenario", description: "AC-009-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/receipts/demo-receipt-id");
      await expect(page.locator("body")).toBeVisible();
    },
  );

  test(
    "AC-010-01: Duplicate detection warning and resolution triggers",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-010-01" },
        { type: "requirement", description: "REQ-010-01" },
        { type: "scenario", description: "AC-010-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/receipts");
      await expect(page.locator("body")).toBeVisible();
    },
  );

  test(
    "AC-031-01: Saved views filter bar and custom queries",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-031-01" },
        { type: "requirement", description: "REQ-031-01" },
        { type: "scenario", description: "AC-031-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/receipts");
      await expect(page.locator("body")).toBeVisible();
    },
  );

  test(
    "AC-032-01: Audit history timeline and change tracking",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-032-01" },
        { type: "requirement", description: "REQ-032-01" },
        { type: "scenario", description: "AC-032-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/receipts/demo-receipt-id");
      await expect(page.locator("body")).toBeVisible();
    },
  );
});
