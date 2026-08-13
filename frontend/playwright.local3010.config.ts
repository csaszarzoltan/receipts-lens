import { defineConfig } from "@playwright/test";

/**
 * Local override: point E2E at the dev server actually running on :3010
 * (the board's canonical frontend port — see playwright.config.ts).
 * Backend base is 127.0.0.1:8100, overridable via E2E_API_BASE.
 */
export default defineConfig({
  use: { baseURL: "http://127.0.0.1:3010" },
});
