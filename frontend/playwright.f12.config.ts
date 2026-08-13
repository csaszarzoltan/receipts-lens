import { defineConfig } from "@playwright/test";

/**
 * E2E override for the F1.2 verification run: point at the isolated
 * frontend (:3011) + backend (:8101) serving the new consumer dashboard.
 */
export default defineConfig({
  use: { baseURL: "http://127.0.0.1:3011" },
});
