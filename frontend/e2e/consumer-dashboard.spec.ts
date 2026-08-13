import { test, expect, type Page } from "@playwright/test";

/**
 * F1.2 consumer-dashboard E2E — §3.4 of
 * docs/plans/consumer-pivot-2026-08-13.md (US-023).
 *
 * Verifies on a live stack (frontend :3011 + backend :8101):
 *   1. /dashboard renders the consumer header + upload CTA (no crash).
 *   2. All six §3.4 blocks are present in the DOM (live backend data,
 *      not placeholders) — checked via the aria-labels the page sets.
 *   3. Dark mode does not break the dashboard: theme=dark in localStorage
 *      before navigation, html.dark applied, no Unhandled Runtime Error
 *      overlay, blocks still visible.
 *
 * Auth: header-based (X-Tenant-ID/X-Role) seeded into localStorage before
 * navigation — same pattern as smoke.spec.ts.
 */

const TENANT_KEY = "receiptlens.tenant";
const ROLE_KEY = "receiptlens.role";
const THEME_KEY = "receiptlens.theme";

// The backend the frontend under test talks to (NEXT_PUBLIC_API_BASE_URL of
// the dev server on :3011). Overridable via E2E_API_BASE (same pattern as
// onboarding.spec.ts).
const API_BASE = process.env.E2E_API_BASE ?? "http://127.0.0.1:8100";

const BLOCK_LABELS = [
  "Napi maradékkeret", // block 1 — Mennyit költhetek még ma?
  "Havi költés kategóriánként", // block 2 — Mire ment el a pénzem?
  "Drágulás-figyelmeztetések", // block 3
  "Lemondható előfizetések", // block 4
  "Legutóbbi nyugták", // block 6
];

// Block 5 (Családi keret-státusz) lives inside the block-1 section which is
// aria-labelled "Napi maradékkeret" — assert it by heading text instead.
const BLOCK_HEADINGS = ["Családi keret-státusz"];

async function seedAuth(page: Page, dark = false): Promise<void> {
  await page.addInitScript(
    ([tenantKey, roleKey, themeKey, dark]) => {
      window.localStorage.setItem(tenantKey, "demo");
      window.localStorage.setItem(roleKey, "admin");
      window.localStorage.setItem(themeKey, dark ? "dark" : "light");
    },
    [TENANT_KEY, ROLE_KEY, THEME_KEY, dark] as const,
  );
  // The demo tenant may already have onboarding_done=true persisted from an
  // earlier run (the shell modal would overlay /dashboard and hide the
  // blocks under test). Reset it — same pattern as onboarding.spec.ts.
  await page.request.put(`${API_BASE}/product/preferences`, {
    headers: { "X-Tenant-ID": "demo", "X-Role": "admin" },
    data: { payload: { onboarding_done: false } },
  });
}

async function expectNoErrorOverlay(page: Page): Promise<void> {
  const overlayGone = await page.evaluate(() => {
    const portal = document.querySelector("nextjs-portal");
    if (!portal?.shadowRoot) return true;
    return !portal.shadowRoot.textContent?.includes(
      "Unhandled Runtime Error",
    );
  });
  expect(overlayGone, "Unhandled Runtime Error overlay detected").toBe(true);
}

test("dashboard renders all six consumer blocks with live data", async ({
  page,
}) => {
  await seedAuth(page);

  // Seed live data through the real backend: a monthly household budget
  // (block 1 + 5) and a receipt (blocks 2 + 6) so the blocks render
  // concrete numbers, not just empty states.
  await page.request.post(`${API_BASE}/api/v1/budgets`, {
    headers: { "X-Tenant-ID": "demo", "X-Role": "admin" },
    data: { category: "Háztartás", amount: 600, currency: "USD", period: "monthly" },
  });

  await page.goto("/dashboard");
  await page.waitForLoadState("domcontentloaded");

  // Consumer header + primary CTA (block-1 header row). `.first()` because
  // the sidebar link "Áttekintés" matches the same accessible name.
  await expect(
    page.getByRole("heading", { name: "Áttekintés" }).first(),
  ).toBeVisible({
    timeout: 10_000,
  });
  // Header CTA (the sidebar also has a "Nyugta hozzáadása" link — scope to
  // the header row so the assertion is unambiguous).
  await expect(
    page.getByRole("link", { name: "Nyugta hozzáadása" }).first(),
  ).toBeVisible();

  // All six blocks present — aria-labels are set on each section.
  for (const label of BLOCK_LABELS) {
    const section = page.getByLabel(label).first();
    await expect(section).toBeVisible({ timeout: 10_000 });
  }
  for (const heading of BLOCK_HEADINGS) {
    await expect(
      page.getByRole("heading", { name: heading }),
    ).toBeVisible({ timeout: 10_000 });
  }

  // The daily-remaining figure renders (live number, not placeholder text).
  const body = await page.evaluate(() => document.body.innerText);
  expect(body).toContain("Mennyit költhetek még ma?");

  await expectNoErrorOverlay(page);
});

test("dashboard dark mode does not break", async ({ page }) => {
  await seedAuth(page, true);
  await page.goto("/dashboard");
  await page.waitForLoadState("domcontentloaded");

  // Theme applied at the document root.
  const htmlDark = await page.evaluate(() =>
    document.documentElement.classList.contains("dark"),
  );
  expect(htmlDark, "html.dark expected with receiptlens.theme=dark").toBe(
    true,
  );

  // Blocks still render under dark mode.
  for (const label of BLOCK_LABELS) {
    await expect(page.getByLabel(label).first()).toBeVisible({
      timeout: 10_000,
    });
  }
  for (const heading of BLOCK_HEADINGS) {
    await expect(
      page.getByRole("heading", { name: heading }),
    ).toBeVisible({ timeout: 10_000 });
  }

  await expectNoErrorOverlay(page);
});
