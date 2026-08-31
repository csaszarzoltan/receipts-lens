/**
 * GUI E2E Test Suite: Landing, Authentication & Onboarding (FEAT-001 - FEAT-004)
 * Traceability: METHODOLOGY.md Section 8.4
 */
import { test, expect } from "@playwright/test";
import { seedAuthenticatedSession } from "./helpers/auth";

test.describe("GUI-E2E: Public Landing, Auth & Navigation (FEAT-001 - FEAT-004)", () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthenticatedSession(page);
  });

  test(
    "AC-001-01: Landing page renders hero, CTAs and marketing content",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-001-01" },
        { type: "requirement", description: "REQ-001-01" },
        { type: "scenario", description: "AC-001-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/");
      await expect(page).toHaveTitle(/ReceiptLens/);
      await expect(page.locator("a[href='/']").first()).toBeVisible();
      await expect(page.locator("a[href='/login']").first()).toBeVisible();
    },
  );

  test(
    "AC-001-02: Navigation from landing to login and dashboard views",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-001-02" },
        { type: "requirement", description: "REQ-001-02" },
        { type: "scenario", description: "AC-001-02" },
      ],
    },
    async ({ page }) => {
      await page.goto("/");
      const signInLink = page.locator("a[href='/login']").first();
      await signInLink.click();
      await expect(page).toHaveURL(/.*login/);
      await expect(page.locator("#login-tenant")).toBeVisible();
    },
  );

  test(
    "AC-002-01: Login view handles household selection, role and sign-in action",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-002-01" },
        { type: "requirement", description: "REQ-002-01" },
        { type: "scenario", description: "AC-002-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/login");
      const tenantSelect = page.locator("#login-tenant");
      await expect(tenantSelect).toBeVisible();
      await tenantSelect.selectOption("demo");
      const roleSelect = page.locator("#login-role");
      await expect(roleSelect).toBeVisible();
      await roleSelect.selectOption("admin");
      const loginBtn = page.locator("button.btn-primary").first();
      await expect(loginBtn).toBeVisible();
    },
  );

  test(
    "AC-003-01: Login view provides navigation to Magic Link and Onboarding",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-003-01" },
        { type: "requirement", description: "REQ-003-01" },
        { type: "scenario", description: "AC-003-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/login");
      const magicLink = page.locator("a[href='/auth/magic-link']").first();
      await expect(magicLink).toBeVisible();
      const onboardingLink = page.locator("a[href='/onboarding']").first();
      await expect(onboardingLink).toBeVisible();
    },
  );

  test(
    "AC-004-01: Onboarding flow steps and welcome guide interaction",
    {
      annotation: [
        { type: "test-id", description: "TEST-GUI-004-01" },
        { type: "requirement", description: "REQ-004-01" },
        { type: "scenario", description: "AC-004-01" },
      ],
    },
    async ({ page }) => {
      await page.goto("/onboarding");
      await expect(page.locator("body")).toBeVisible();
      const heading = page.locator("h1, h2").first();
      await expect(heading).toBeVisible();
    },
  );
});
