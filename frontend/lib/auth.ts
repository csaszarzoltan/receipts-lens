/**
 * Header-based tenant/role auth + F1.3 household session support.
 *
 * The ReceiptLens backend authenticates via two mechanisms:
 *   - Legacy dev identity: X-Tenant-ID / X-Role headers (default demo/admin),
 *     still valid whenever RECEIPTLENS_ENV != production (F1.3 AC6).
 *   - Real household sessions: Authorization: Bearer <session_token>,
 *     created by magic-link login or family-invite acceptance (F1.3).
 *
 * The selected identity is persisted to localStorage. When a session token
 * is present it wins and is attached as the Bearer header; the legacy
 * tenant/role headers remain as the dev-mode fallback.
 */

export type Role = "admin" | "reviewer" | "integrator";

export const TENANT_KEY = "receiptlens.tenant";
export const ROLE_KEY = "receiptlens.role";
export const SESSION_KEY = "receiptlens.session";

export const DEFAULT_TENANT = "demo";
export const DEFAULT_ROLE: Role = "admin";

export const ROLES: Role[] = ["admin", "reviewer", "integrator"];

function readStorage(key: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key: string, value: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // private mode / quota — non-fatal
  }
}

function removeStorage(key: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(key);
  } catch {
    // non-fatal
  }
}

export function getTenant(): string {
  return readStorage(TENANT_KEY) ?? DEFAULT_TENANT;
}

export function getRole(): Role {
  const stored = readStorage(ROLE_KEY);
  return stored === "admin" || stored === "reviewer" || stored === "integrator"
    ? stored
    : DEFAULT_ROLE;
}

export function setTenant(tenant: string): void {
  writeStorage(TENANT_KEY, tenant.trim() || DEFAULT_TENANT);
}

export function setRole(role: Role): void {
  writeStorage(ROLE_KEY, role);
}

/** The stored household session token, or null. */
export function getSessionToken(): string | null {
  return readStorage(SESSION_KEY);
}

/** Persist a household session after magic-link login / invite accept. */
export function setSessionToken(token: string): void {
  writeStorage(SESSION_KEY, token);
}

/** Clear the session (sign out) — the legacy dev identity stays intact. */
export function clearSessionToken(): void {
  removeStorage(SESSION_KEY);
}

/** Headers attached to every authenticated request by tenantRequest(). */
export function authHeaders(): Record<string, string> {
  const session = getSessionToken();
  if (session) {
    return { Authorization: `Bearer ${session}` };
  }
  return {
    "X-Tenant-ID": getTenant(),
    "X-Role": getRole(),
  };
}

export interface AuthState {
  tenant: string;
  role: Role;
}

export function getAuthState(): AuthState {
  return { tenant: getTenant(), role: getRole() };
}

export function setAuthState(tenant: string, role: Role): void {
  setTenant(tenant);
  setRole(role);
}

/** Sign out: drop the session; fall back to the dev header identity. */
export function signOut(): void {
  clearSessionToken();
}
