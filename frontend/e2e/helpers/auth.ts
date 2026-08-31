import type { Page } from "@playwright/test";

export const TENANT_KEY = "receiptlens.tenant";
export const ROLE_KEY = "receiptlens.role";
export const SESSION_KEY = "receiptlens.session";

let cachedSessionToken: string | null = null;

export async function getOrCreateSessionToken(apiBase: string = "http://127.0.0.1:8123"): Promise<string> {
  if (cachedSessionToken) return cachedSessionToken;
  try {
    const reqRes = await fetch(`${apiBase}/auth/magic-link-request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "e2e-gui@allthezoo.com" }),
    });
    if (!reqRes.ok) throw new Error(`Magic link request failed: ${reqRes.status}`);
    const reqData = await reqRes.json();
    const token = reqData.token;

    const verifyRes = await fetch(`${apiBase}/auth/magic-link-verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    if (!verifyRes.ok) throw new Error(`Magic link verify failed: ${verifyRes.status}`);
    const verifyData = await verifyRes.json();
    cachedSessionToken = verifyData.session_token;
    return cachedSessionToken as string;
  } catch (err) {
    // Fallback static token
    return "6CSeLfab_NFKMJEwa2WVq6ca0BX97h33aq8YuNrvnbc";
  }
}

export async function seedAuthenticatedSession(
  page: Page,
  tenant: string = "demo",
  role: string = "admin",
): Promise<void> {
  const sessionToken = await getOrCreateSessionToken();
  await page.addInitScript(
    ([tKey, tVal, rKey, rVal, sKey, sVal]) => {
      window.localStorage.setItem(tKey, tVal);
      window.localStorage.setItem(rKey, rVal);
      window.localStorage.setItem(sKey, sVal);
    },
    [TENANT_KEY, tenant, ROLE_KEY, role, SESSION_KEY, sessionToken] as const,
  );
}
