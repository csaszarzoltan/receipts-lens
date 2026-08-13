import type { Role } from "@/lib/auth";

/**
 * F1.1 consumer-pivot role naming (§3.2 of
 * docs/plans/consumer-pivot-2026-08-13.md).
 *
 * The backend wire format still speaks `admin | reviewer | integrator`
 * (X-Role header — backend schema change is explicitly out of scope for
 * F1.1, real household auth lands in F1.3). This module maps those wire
 * roles to the household-facing labels the UI must display, and carries the
 * target-state role vocabulary (§3.2) ready for F1.3 to activate.
 */
export const ROLE_LABELS: Record<Role, string> = {
  admin: "Háztartás tulajdonosa",
  reviewer: "Felnőtt tag",
  integrator: "Könyvelő / tanácsadó (Business mód)",
};

/** Human-readable label for a wire role. Falls back to the raw value. */
export function roleLabel(role: Role | string): string {
  return ROLE_LABELS[role as Role] ?? role;
}

/**
 * Target-state consumer roles (§3.2) — NOT wired to any backend value yet.
 * F1.3 (auth) introduces the real household roles; until then these labels
 * exist as vocabulary so the UI copy can reference them.
 */
export const TARGET_ROLE_LABELS = {
  viewer: "Gyermek / korlátozott tag",
  viewOnly: "Csak megtekintés",
} as const;
