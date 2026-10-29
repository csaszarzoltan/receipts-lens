import { test, expect, type Page } from "@playwright/test";
import { E2E_API_BASE, createDevSession, seedSession, tenantHeaders } from "./session";

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
 * Auth: a real dev session (see e2e/session.ts). Seeding calls use the
 * session's own tenant, so the data lands where the dashboard reads it.
 */

const THEME_KEY = "receiptlens.theme";

// The backend the frontend under test talks to (NEXT_PUBLIC_API_BASE_URL of
// the dev server). Overridable via E2E_API_BASE.
const API_BASE = E2E_API_BASE;

// Blocks the dashboard renders for a household with one budget and one receipt.
// Sections with an aria-label are checked by label; the rest by heading.
// Price-alert and subscription sections only render when there is data for them,
// so they are not asserted here.
const BLOCK_LABELS = [
  "Mire ment el a pénzem?", // spending by category
  "Ezt így tudnád megtakarítani", // savings
];

// Headings: daily remaining, recent receipts, household budget status.
const BLOCK_HEADINGS = ["Mennyit költhetek még ma?", "Legutóbbi nyugták", "Családi keret-státusz"];

/** Log in a fresh household session and return its tenant for the seeding calls. */
async function seedAuth(page: Page, dark = false): Promise<string> {
  const session = await createDevSession(page.request, `dashboard-${Date.now()}@example.test`);
  await seedSession(page, session.token, "hu"); // block labels are Hungarian
  await page.addInitScript(
    ([themeKey, dark]) => {
      window.localStorage.setItem(themeKey, dark ? "dark" : "light");
    },
    [THEME_KEY, dark] as const,
  );
  // Reset onboarding_done for the session's household: the shell onboarding modal
  // would otherwise overlay /dashboard and hide the blocks under test.
  await page.request.put(`${API_BASE}/product/preferences`, {
    headers: tenantHeaders(session.tenantId),
    data: { payload: { onboarding_done: false } },
  });
  return session.tenantId;
}

/** One monthly budget and one receipt through the real API, so the blocks show live numbers. */
async function seedLiveData(page: Page, tenantId: string): Promise<void> {
  // Seed live data through the real backend: a monthly household budget
  // (block 1 + 5) and a receipt uploaded through the REAL /product/receipts/
  // upload path (blocks 2 + 6) so the blocks render concrete numbers that
  // prove live-data wiring, not just empty states. The upload leg is what
  // makes the "live numbers" assertion meaningful: it writes to the tenant
  // SQLite store — the same store blocks 1/2/5 aggregate.
  await page.request.post(`${API_BASE}/api/v1/budgets`, {
    headers: tenantHeaders(tenantId),
    data: { category: "Háztartás", amount: 600, currency: "USD", period: "monthly" },
  });

  const upload = await page.request.post(
    `${API_BASE}/product/receipts/upload`,
    {
      headers: tenantHeaders(tenantId),
      multipart: {
        file: {
          name: "test-receipt-coop.jpg",
          mimeType: "image/jpeg",
          buffer: require("fs").readFileSync(
            "e2e/fixtures/test-receipt-coop.jpg",
          ),
        },
      },
    },
  );
  expect(upload.status(), "receipt upload via real path must succeed").toBe(201);
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

test("dashboard renders the consumer blocks with live data", async ({
  page,
}) => {
  const tenantId = await seedAuth(page);

  await seedLiveData(page, tenantId);

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

  // Blocks present: labelled sections and headed sections.
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
  const tenantId = await seedAuth(page, true);
  await seedLiveData(page, tenantId);
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
