import type { Role } from "@/lib/auth";
import type { HouseholdRole } from "@/lib/types";

/**
 * F1.1 + F1.3 consumer-pivot role naming (§3.2 of
 * docs/plans/consumer-pivot-2026-08-13.md).
 *
 * The legacy wire roles (admin | reviewer | integrator) map to household
 * labels for the dev-mode header flow; the F1.3 household roles
 * (owner | adult | child | view_only) are the real auth vocabulary.
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
 * Household role labels (§3.2) — the F1.3 auth vocabulary. `viewer` was the
 * earlier draft name for the restricted member; F1.3 ships the final wire
 * values `child` and `view_only`.
 */
export const HOUSEHOLD_ROLE_LABELS: Record<HouseholdRole, string> = {
  owner: "Háztartás tulajdonosa",
  adult: "Felnőtt tag",
  child: "Gyermek / korlátozott tag",
  view_only: "Csak megtekintés",
};

export function householdRoleLabel(role: HouseholdRole | string): string {
  return HOUSEHOLD_ROLE_LABELS[role as HouseholdRole] ?? role;
}

/**
 * Target-state consumer roles (§3.2) — retained for compatibility with
 * existing copy that references the draft vocabulary.
 */
export const TARGET_ROLE_LABELS = {
  viewer: "Gyermek / korlátozott tag",
  viewOnly: "Csak megtekintés",
} as const;
