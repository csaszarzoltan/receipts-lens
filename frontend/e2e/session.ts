import type { APIRequestContext, Page } from "@playwright/test";

/**
 * Session-based auth for the e2e specs.
 *
 * The (app) routes require a real session (`receiptlens.session`), not the
 * legacy X-Tenant-ID/X-Role headers. In development the magic-link flow
 * returns the link token in the response, so a spec can log in without mail.
 *
 * Overridable via E2E_API_BASE (the backend the dev server talks to).
 */
export const E2E_API_BASE = process.env.E2E_API_BASE ?? "http://127.0.0.1:8078";

const SESSION_KEY = "receiptlens.session";

export interface DevSession {
  token: string;
  /** Tenant of the household the session belongs to; use it in X-Tenant-ID seeding calls. */
  tenantId: string;
}

/** Create a fresh household session through the dev magic-link flow. */
export async function createDevSession(request: APIRequestContext, email: string): Promise<DevSession> {
  const requested = await request.post(`${E2E_API_BASE}/auth/magic-link-request`, { data: { email } });
  if (!requested.ok()) throw new Error(`magic-link-request failed: ${requested.status()}`);
  const { token: linkToken } = await requested.json();
  const verified = await request.post(`${E2E_API_BASE}/auth/magic-link-verify`, { data: { token: linkToken } });
  if (!verified.ok()) throw new Error(`magic-link-verify failed: ${verified.status()}`);
  const body = await verified.json();
  return { token: body.session_token, tenantId: body.household_id };
}

/**
 * Make every navigation of this page start with the given session. Pass a locale
 * when the spec asserts translated copy; otherwise the app's default applies.
 */
export async function seedSession(page: Page, token: string, locale?: string): Promise<void> {
  await page.addInitScript(
    ([sessionKey, sessionValue, localeKey, localeValue]) => {
      window.localStorage.setItem(sessionKey, sessionValue);
      if (localeValue) window.localStorage.setItem(localeKey, localeValue);
    },
    [SESSION_KEY, token, "receiptlens.locale", locale ?? ""] as const,
  );
}

/** Headers for direct API seeding calls against the session's tenant (dev mode accepts them). */
export function tenantHeaders(tenantId: string): Record<string, string> {
  return { "X-Tenant-ID": tenantId, "X-Role": "admin" };
}
