import { defineConfig } from "@playwright/test";

/**
 * ReceiptLens PROD E2E config — a VALÓDI éles buildet teszteli.
 *
 * Használat:
 *   cd frontend && npx playwright test --config playwright.prod.config.ts
 *
 * Követelmény: a .env.e2e-ből jön az E2E_SESSION_TOKEN (a prod SQLite
 * `sessions` táblájában seedelt e2e-gui@allthezoo.com session).
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  retries: 1,
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "https://receipts.allthezoo.com",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  reporter: [["list"]],
});
