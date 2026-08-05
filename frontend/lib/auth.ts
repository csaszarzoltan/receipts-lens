/**
 * Header-based tenant/role auth.
 *
 * The ReceiptLens backend authenticates via two HTTP headers:
 *   X-Tenant-ID  (default "demo")
 *   X-Role       (default "admin", one of admin | reviewer | integrator)
 *
 * The selected tenant/role is persisted to localStorage so the login
 * selector can change it without any server-side session machinery.
 */

export type Role = "admin" | "reviewer" | "integrator";

const TENANT_KEY = "receiptlens.tenant";
const ROLE_KEY = "receiptlens.role";

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

/** Headers attached to every authenticated request by tenantRequest(). */
export function authHeaders(): Record<string, string> {
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
