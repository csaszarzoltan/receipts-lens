import { defineConfig } from "@playwright/test";

/**
 * ReceiptLens UI E2E smoke config.
 *
 * Target stack: Next.js dev server (port 3010) + FastAPI backend
 * (port 8078) — both already running on the Hermes host for this board's
 * validation run. Auth is header-based (X-Tenant-ID / X-Role) persisted in
 * localStorage by lib/auth.ts; the smoke specs seed it via addInitScript so
 * the (app) routes render without a manual login.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 45_000,
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
  use: {
    baseURL: "http://127.0.0.1:3010",
    trace: "retain-on-failure",
  },
  reporter: [["list"]],
});
