import type { PillTone } from "@/components/Pill";

/**
 * Colour tone per status. Labels come from lib/featureI18n.ts.
 * ok = done or active, check = needs a look, wait = in progress or waiting, bad = refused or failed.
 */
const TONE: Record<string, PillTone> = {
  RESOLVED: "ok", APPROVED: "ok", ACHIEVED: "ok", CLOSED: "ok", CONFIRMED: "ok", REVERSED: "ok",
  MATCHED: "ok", SYNCED: "ok", TRACKED: "ok", ON_TRACK: "ok", ACTIVE: "ok", READY_TO_CLOSE: "ok",
  REJECTED: "bad", FAILED: "bad", DISCARDED: "bad", CANCELLED: "bad", DISPUTED: "bad", CONFLICT: "bad",
  BLOCKED: "bad", AT_RISK: "bad",
  NEEDS_REVIEW: "check",
  OPEN: "wait", UNMATCHED: "wait", SUGGESTED: "wait", PENDING_APPROVAL: "wait", REOPENED: "wait",
  REOPEN_PENDING: "wait", SNOOZED: "wait", PAUSED: "wait", QUEUED: "wait", UPLOADING: "wait",
  PROCESSING: "wait", PARTIALLY_MATCHED: "wait", DETECTED: "wait", CANDIDATE: "wait", ASSIGNED: "wait",
  IN_PROGRESS: "wait", LOCAL_ONLY: "wait", CAPTURING: "wait", PREVIEW: "wait", DRAFT: "wait",
};

export function featureStatusTone(status: string): PillTone {
  return TONE[status] ?? "neutral";
}
