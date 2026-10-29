import { API_BASE_URL } from "@/lib/api";
import { getRole, getSessionToken, getTenant } from "@/lib/auth";

export type FeatureAction = {
  action: string;
  /** Payload key the action asks for, if any (for example "reason" or "amount"). */
  input: string | null;
  input_type: "text" | "number" | "date";
  input_required: boolean;
  /** Fields the action still needs and that are blank on the item (empty when the action can run). */
  missing: string[];
};

export type FeatureItem = {
  id: string;
  tenant_id: string;
  status: string;
  revision: number;
  client_reference: string;
  data: Record<string, unknown>;
  /** Actions the server allows for this item, for the caller's role and current status. */
  actions: FeatureAction[];
  created_at: string;
  updated_at: string;
};

export class FeatureApiError extends Error {
  status: number;
  /** Machine-readable code from the server, e.g. INVALID_TRANSITION or VALIDATION_FAILED. */
  code: string;
  fields: string[];
  constructor(message: string, status: number, code = "HTTP_ERROR", fields: string[] = []) {
    super(message);
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

function authHeaders(): Record<string, string> {
  const session = getSessionToken();
  const headers: Record<string, string> = { "X-Tenant-ID": getTenant(), "X-Role": getRole() };
  if (session) headers.Authorization = `Bearer ${session}`;
  return headers;
}

async function parse<T>(res: Response): Promise<T> {
  if (res.ok) return (await res.json()) as T;
  let message = `HTTP ${res.status}`;
  let code = "HTTP_ERROR";
  let fields: string[] = [];
  try {
    const body = await res.json();
    if (typeof body?.message === "string") message = body.message;
    if (typeof body?.code === "string") code = body.code;
    if (Array.isArray(body?.fields)) fields = body.fields.map(String);
  } catch {
    // Non-JSON error body: keep the HTTP status message.
  }
  throw new FeatureApiError(message, res.status, code, fields);
}

/**
 * Idempotency keys must be at least 16 characters. randomUUID needs a secure context,
 * so a plain random fallback covers http:// on a LAN address.
 */
export function newIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") return crypto.randomUUID();
  return Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16)).join("");
}

/** Lists items from a v2 feature API. */
export async function listFeatureItems(path: string): Promise<FeatureItem[]> {
  const res = await fetch(`${API_BASE_URL}${path}`, { headers: authHeaders() });
  return (await parse<{ items: FeatureItem[] }>(res)).items;
}

/** Creates an item. Pass the same key again to retry without creating a second item. */
export async function createFeatureItem(
  path: string,
  body: { client_reference: string; payload: Record<string, unknown> },
  idempotencyKey: string,
): Promise<FeatureItem> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
    body: JSON.stringify({ expected_revision: 0, ...body }),
  });
  return parse<FeatureItem>(res);
}

/** Runs a state transition. expected_revision guards against acting on a stale item. */
export async function commandFeatureItem(
  path: string,
  itemId: string,
  body: { action: string; expected_revision: number; reason?: string; payload?: Record<string, unknown> },
  idempotencyKey: string,
): Promise<FeatureItem> {
  const res = await fetch(`${API_BASE_URL}${path}/${encodeURIComponent(itemId)}`, {
    method: "PATCH",
    headers: { ...authHeaders(), "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
    body: JSON.stringify(body),
  });
  return parse<FeatureItem>(res);
}
