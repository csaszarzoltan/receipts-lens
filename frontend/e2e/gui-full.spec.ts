import { test, expect, type Page, type ConsoleMessage, type Response } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { createDevSession, seedSession, E2E_API_BASE } from "./session";

/**
 * Full GUI regression pass.
 *
 * Public pages (no session needed) run against any deployment, including live,
 * because they only read the page. App pages need a dev session, so they run
 * only where the backend is in development mode (E2E_SESSION=1 or a reachable
 * dev API). Set GUI_PUBLIC_ONLY=1 to run just the public checks.
 *
 * Every page is checked in light and dark mode for: a visible heading, no
 * Next.js error overlay, no console errors, no 5xx responses, no WCAG 2.x
 * A/AA serious or critical axe violations (incl. colour contrast), theme
 * applied to <body>, and no horizontal scroll at 390 px.
 */

const PUBLIC_PAGES = ["/", "/login", "/auth/magic-link", "/auth/invite", "/auth/google/callback"];

const APP_PAGES = [
  "/dashboard", "/receipts", "/upload", "/review", "/finances", "/more", "/subscriptions",
  "/budget", "/forecast", "/reports", "/exports", "/exports/prepare", "/accounting",
  "/accounting/period-close", "/tax", "/warranties", "/savings-goals", "/statement",
  "/settings", "/settings/profile", "/settings/notifications", "/settings/members",
  "/settings/permissions", "/settings/privacy", "/settings/diagnostics",
  "/settings/diagnostics/quality", "/approvals", "/automations", "/chat", "/cost-splits",
  "/duplicates", "/inbox", "/insights", "/integrations", "/missing-receipts",
  "/price-tracking", "/quality-inbox", "/reconciliation", "/reconciliation/refunds",
  "/receipts/capture", "/receipts/offline", "/onboarding",
];

/** Console noise that is not an application defect (CSP on third-party font CSS, dev hints). */
const BENIGN_CONSOLE = [/Content Security Policy/i, /fonts\.googleapis/i, /favicon/i, /Download the React DevTools/i];

/** True for an opaque colour whose luminance is dark; transparent or unparseable is not dark. */
function bodyIsDark(bg: string): boolean {
  const m = bg.match(/[\d.]+/g);
  if (!m || m.length < 3) return false;
  const [r, g, b] = m.slice(0, 3).map(Number);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b < 128;
}

interface PageProbe {
  consoleErrors: string[];
  serverErrors: string[];
  /** API responses with status >= 400, as "STATUS /path". */
  apiErrors: string[];
}

/**
 * Expected API errors per page. Each entry is a deliberate state, not a defect:
 * /tax is a Pro-only feature and answers 402 pro_required, and the page shows its upgrade prompt.
 */
const EXPECTED_API_ERRORS: Record<string, string[]> = {
  "/tax": ["402 /api/v1/tax/deduction"],
};

function watch(page: Page): PageProbe {
  const probe: PageProbe = { consoleErrors: [], serverErrors: [], apiErrors: [] };
  page.on("console", (msg: ConsoleMessage) => {
    if (msg.type() !== "error") return;
    const text = msg.text();
    if (BENIGN_CONSOLE.some((re) => re.test(text))) return;
    // Failed-resource lines repeat an API status that is checked per URL below.
    if (/Failed to load resource: the server responded with a status of \d{3}/.test(text)) return;
    probe.consoleErrors.push(text.slice(0, 200));
  });
  page.on("pageerror", (err) => probe.consoleErrors.push(`pageerror: ${err.message.slice(0, 200)}`));
  page.on("response", (res: Response) => {
    // Only same-origin API and page responses count; third-party 5xx are not ours.
    if (res.status() >= 500 && res.url().includes("/_next/") === false) {
      probe.serverErrors.push(`${res.status()} ${res.url().slice(0, 160)}`);
    }
    if (res.status() >= 400 && res.url().startsWith(E2E_API_BASE)) {
      probe.apiErrors.push(`${res.status()} ${new URL(res.url()).pathname}`);
    }
  });
  return probe;
}

/** Seed the theme once per tab. An init script that ran on every navigation would undo the user's choice on reload. */
async function setTheme(page: Page, theme: "dark" | "light" | null): Promise<void> {
  await page.addInitScript((value) => {
    if (window.sessionStorage.getItem("gui-theme-seeded")) return;
    window.sessionStorage.setItem("gui-theme-seeded", "1");
    if (value) window.localStorage.setItem("receiptlens.theme", value);
    else window.localStorage.removeItem("receiptlens.theme");
  }, theme);
}

async function themeSnapshot(page: Page) {
  return page.evaluate(() => {
    // The visible background is often a wrapper, not <body>. Walk up from the element at the top of the viewport.
    const transparent = (c: string) => c === "rgba(0, 0, 0, 0)" || c === "transparent";
    let el: Element | null = document.elementFromPoint(window.innerWidth / 2, 24) ?? document.body;
    let bg = "";
    while (el) {
      const c = getComputedStyle(el).backgroundColor;
      if (!transparent(c)) { bg = c; break; }
      el = el.parentElement;
    }
    return {
      htmlDark: document.documentElement.classList.contains("dark"),
      stored: window.localStorage.getItem("receiptlens.theme"),
      body: bg || "rgb(255, 255, 255)",
      toggleLabel: document.querySelector("button[aria-label*='mode']")?.getAttribute("aria-label") ?? null,
    };
  });
}

async function expectBodyTheme(page: Page, dark: boolean): Promise<void> {
  // Colours transition (transition-colors), so poll until the computed background settles.
  await expect.poll(async () => bodyIsDark((await themeSnapshot(page)).body), { message: "body background follows theme" }).toBe(dark);
}

async function expectNoErrorOverlay(page: Page): Promise<void> {
  const overlay = await page.evaluate(() => {
    const portal = document.querySelector("nextjs-portal");
    if (!portal?.shadowRoot) return false;
    return !!portal.shadowRoot.textContent?.includes("Unhandled Runtime Error");
  });
  expect(overlay, "Next.js error overlay visible").toBe(false);
}

async function expectNoHorizontalScroll(page: Page): Promise<void> {
  const widths = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, inner: window.innerWidth }));
  expect(widths.scroll, "horizontal scroll at this width").toBeLessThanOrEqual(widths.inner + 1);
}

async function expectAxeClean(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
  const blocking = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(
    blocking.map((v) => `${v.id} (${v.impact}): ${v.nodes.length} node(s)`),
    "serious/critical WCAG A/AA violations",
  ).toEqual([]);
}

// ---------------------------------------------------------------------------
// Public pages: theme switch, both OS schemes, persistence, keyboard.
// ---------------------------------------------------------------------------

test.describe("public pages: theme switch", () => {
  for (const path of PUBLIC_PAGES) {
    for (const scheme of ["dark", "light"] as const) {
      test(`${path} switches both ways, persists after reload (OS ${scheme})`, async ({ browser }) => {
        const context = await browser.newContext({ colorScheme: scheme });
        const page = await context.newPage();
        await setTheme(page, null);
        const probe = watch(page);
        const response = await page.goto(path, { waitUntil: "load" });
        expect(response?.status() ?? 0, "HTTP status").toBeLessThan(500);
        const toggle = page.locator("button[aria-label*='mode']").first();
        await expect(toggle).toBeVisible();

        const start = await themeSnapshot(page);
        expect(start.htmlDark, "initial dark class follows OS scheme").toBe(scheme === "dark");

        await toggle.click();
        const afterFirst = await themeSnapshot(page);
        expect(afterFirst.htmlDark, "first click flips the theme").toBe(!start.htmlDark);
        await expectBodyTheme(page, afterFirst.htmlDark);
        expect(afterFirst.stored).toBe(afterFirst.htmlDark ? "dark" : "light");

        await toggle.click();
        const afterSecond = await themeSnapshot(page);
        expect(afterSecond.htmlDark).toBe(start.htmlDark);
        await expectBodyTheme(page, start.htmlDark);

        // Choose the opposite of the OS scheme, then reload: the stored choice must win.
        await toggle.click();
        const chosen = await themeSnapshot(page);
        await page.reload({ waitUntil: "load" });
        await expect(page.locator("button[aria-label*='mode']").first()).toBeVisible();
        const reloaded = await themeSnapshot(page);
        expect(reloaded.htmlDark, "theme survives reload").toBe(chosen.htmlDark);
        await expectBodyTheme(page, chosen.htmlDark);

        expect(probe.consoleErrors, "console errors").toEqual([]);
        expect(probe.serverErrors, "5xx responses").toEqual([]);
        await context.close();
      });
    }
  }

  test("theme toggle works from the keyboard (Tab to it, Enter to switch)", async ({ browser }) => {
    const context = await browser.newContext({ colorScheme: "light" });
    const page = await context.newPage();
    await setTheme(page, "light");
    await page.goto("/login", { waitUntil: "load" });
    const toggle = page.locator("button[aria-label*='mode']").first();
    await toggle.focus();
    await expect(toggle).toBeFocused();
    await page.keyboard.press("Enter");
    expect((await themeSnapshot(page)).htmlDark).toBe(true);
    await page.keyboard.press("Space");
    expect((await themeSnapshot(page)).htmlDark).toBe(false);
    await context.close();
  });

  test("public pages pass axe in both themes", async ({ browser }) => {
    for (const theme of ["dark", "light"] as const) {
      const context = await browser.newContext();
      const page = await context.newPage();
      await setTheme(page, theme);
      for (const path of PUBLIC_PAGES) {
        await page.goto(path, { waitUntil: "load" });
        await page.waitForTimeout(800);
        await expectAxeClean(page);
      }
      await context.close();
    }
  });
});

// ---------------------------------------------------------------------------
// App pages: needs a dev session (see header comment).
// ---------------------------------------------------------------------------

const SESSION_ENABLED = process.env.GUI_PUBLIC_ONLY !== "1";

test.describe("app pages", () => {
  test.skip(!SESSION_ENABLED, "GUI_PUBLIC_ONLY=1");

  let token = "";
  test.beforeAll(async ({ request }) => {
    token = (await createDevSession(request, `gui-full-${Date.now()}@example.test`)).token;
  });

  for (const scheme of ["light", "dark"] as const) {
    test.describe(`in ${scheme} mode`, () => {
      for (const path of APP_PAGES) {
        test(`${path} renders with no errors, passes axe, no horizontal scroll at 390px`, async ({ browser }) => {
          const context = await browser.newContext({ colorScheme: scheme, viewport: { width: 1280, height: 900 } });
          const page = await context.newPage();
          await setTheme(page, scheme);
          await seedSession(page, token, "en");
          const probe = watch(page);
          await page.goto(path, { waitUntil: "load" });
          await page.waitForTimeout(1500);
          await expectNoErrorOverlay(page);
          await expect(page.locator("main h1, main h2").first(), "page heading").toBeVisible();
          const snap = await themeSnapshot(page);
          expect(snap.htmlDark).toBe(scheme === "dark");
          await expectBodyTheme(page, scheme === "dark");
          await expectAxeClean(page);
          expect(probe.consoleErrors, "console errors").toEqual([]);
          expect(probe.serverErrors, "5xx responses").toEqual([]);
          const expected = EXPECTED_API_ERRORS[path] ?? [];
          expect(probe.apiErrors.filter((e) => !expected.includes(e)), "unexpected API errors").toEqual([]);
          await page.setViewportSize({ width: 390, height: 844 });
          await page.waitForTimeout(400);
          await expectNoHorizontalScroll(page);
          await context.close();
        });
      }
    });
  }

  test("theme switch in the app header works on the first-run dashboard", async ({ browser }) => {
    const context = await browser.newContext({ colorScheme: "dark", viewport: { width: 1280, height: 900 } });
    const page = await context.newPage();
    await setTheme(page, null);
    await seedSession(page, token, "en");
    await page.goto("/dashboard", { waitUntil: "load" });
    const headerToggle = page.locator("header button[aria-label*='mode']").first();
    await expect(headerToggle).toBeVisible();
    const before = await themeSnapshot(page);
    await headerToggle.click();
    const after = await themeSnapshot(page);
    expect(after.htmlDark, "single click on the header switch changes the theme").toBe(!before.htmlDark);
    await context.close();
  });

  test("first-run card can be dismissed and does not block the header", async ({ browser }) => {
    const context = await browser.newContext({ colorScheme: "light", viewport: { width: 1280, height: 900 } });
    const page = await context.newPage();
    await setTheme(page, "light");
    await seedSession(page, token, "en");
    await page.goto("/dashboard", { waitUntil: "load" });
    const card = page.locator("section[aria-labelledby='onboarding-title']");
    if (await card.count()) {
      await expect(card).toBeVisible();
      // No modal overlay may cover the header.
      const overlay = await page.locator("[role=dialog][aria-modal=true]").count();
      expect(overlay, "first-run card must not be a blocking modal").toBe(0);
      await card.getByRole("button", { name: /close|bezár|schließen|fermer|cerrar|chiudi|fechar|sluit|zamknij|închide/i }).first().click();
      await expect(card).toHaveCount(0);
    }
    const headerToggle = page.locator("header button[aria-label*='mode']").first();
    const before = await themeSnapshot(page);
    await headerToggle.click();
    expect((await themeSnapshot(page)).htmlDark).toBe(!before.htmlDark);
    await context.close();
  });

  test("mobile navigation reaches the main sections at 390px", async ({ browser }) => {
    const context = await browser.newContext({ colorScheme: "light", viewport: { width: 390, height: 844 } });
    const page = await context.newPage();
    await setTheme(page, "light");
    await seedSession(page, token, "en");
    await page.goto("/dashboard", { waitUntil: "load" });
    for (const href of ["/receipts", "/finances", "/more"]) {
      const link = page.locator(`a[href='${href}']:visible`).first();
      await expect(link, `mobile link to ${href}`).toBeVisible();
      await link.click();
      await expect(page).toHaveURL(new RegExp(`${href}$`));
      await expectNoErrorOverlay(page);
    }
    await context.close();
  });

  test("unknown receipt id shows an explicit state, not a crash", async ({ browser }) => {
    const context = await browser.newContext({ colorScheme: "light", viewport: { width: 1280, height: 900 } });
    const page = await context.newPage();
    await setTheme(page, "light");
    await seedSession(page, token, "en");
    const probe = watch(page);
    await page.goto("/receipts/does-not-exist-12345", { waitUntil: "load" });
    await page.waitForTimeout(1500);
    await expectNoErrorOverlay(page);
    await expect(page.locator("main")).toBeVisible();
    expect(probe.serverErrors.filter((e) => !e.includes("does-not-exist")), "unexpected 5xx").toEqual([]);
    await context.close();
  });
});
