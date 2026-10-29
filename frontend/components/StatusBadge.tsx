import Pill, { type PillTone } from "@/components/Pill";
import { getLocale, t } from "@/lib/i18n";

type Status = "needs_review" | "completed" | "pending" | "approved" | "rejected" | "failed" | string;

// Tone per receipt, household or budget state: amber = waiting, blue = check, green = done, red = refused or failed.
const TONES: Record<string, PillTone> = {
  needs_review: "check",
  completed: "ok",
  approved: "ok",
  pending: "wait",
  rejected: "bad",
  failed: "bad",
  exportable: "ok",
  warning: "wait",
  blocked: "bad",
  on_track: "ok",
  over_budget: "bad",
  active: "ok",
};

const STATUS_KEYS: Record<string, string> = {
  needs_review: "statusNeedsReview",
  completed: "statusCompleted",
  pending: "statusPending",
  approved: "statusApproved",
  rejected: "statusRejected",
  failed: "statusFailed",
  exportable: "statusExportable",
  warning: "statusWarning",
  blocked: "statusBlocked",
  on_track: "statusOnTrack",
  over_budget: "statusOverBudget",
  active: "statusActive",
};

function labelFor(status: string): string {
  const key = STATUS_KEYS[status];
  if (key) {
    try { return t(key as any, getLocale()); } catch { return status.replace(/_/g, " "); }
  }
  return status.replace(/_/g, " ");
}

/** Status/readiness badge — tone mapped per status value, label via i18n or an explicit label. */
export default function StatusBadge({ status, label }: { status: Status; label?: string }) {
  return <Pill tone={TONES[status] ?? "neutral"}>{label ?? labelFor(status)}</Pill>;
}
