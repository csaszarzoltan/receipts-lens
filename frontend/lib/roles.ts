import type { Role } from "@/lib/auth";
import type { HouseholdRole } from "@/lib/types";
import { getLocale, t as translate } from "@/lib/i18n";

/**
 * F1.1 + F1.3 consumer-pivot role naming (§3.2 of
 * docs/plans/consumer-pivot-2026-08-13.md).
 *
 * Labels are resolved via i18n so English users never see Hungarian.
 * Keep the wire values (admin/reviewer/integrator, owner/adult/…) — only
 * the displayed label changes.
 */
export const ROLE_LABELS: Record<Role, string> = {
  admin: "roleAdmin",
  reviewer: "roleReviewer",
  integrator: "roleIntegrator",
} as const;

export function roleLabel(role: Role | string, locale?: string): string {
  const key = ROLE_LABELS[role as Role];
  if (key) {
    try { return translate(key as any, (locale as any) ?? getLocale()); } catch { return key; }
  }
  return role;
}

export const HOUSEHOLD_ROLE_LABELS: Record<HouseholdRole, string> = {
  owner: "roleOwner",
  adult: "roleAdult",
  child: "roleChild",
  view_only: "roleViewOnly",
} as const;

export function householdRoleLabel(role: HouseholdRole | string, locale?: string): string {
  const key = HOUSEHOLD_ROLE_LABELS[role as HouseholdRole];
  if (key) {
    try { return translate(key as any, (locale as any) ?? getLocale()); } catch { return key; }
  }
  return role;
}

export const TARGET_ROLE_LABELS = {
  viewer: "roleChild",
  viewOnly: "roleViewOnly",
} as const;
