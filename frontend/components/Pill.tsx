import type { HTMLAttributes } from "react";
import { cx } from "@/lib/utils";

/**
 * The six tones. Meaning, not colour, decides which one to use:
 * neutral = plain label, accent = brand highlight, ok = done or active,
 * wait = waiting or needs attention, check = needs a look, bad = refused or failed.
 */
export type PillTone = "neutral" | "accent" | "ok" | "wait" | "check" | "bad";

const BASE = "inline-flex min-h-6 items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold";

const TONE: Record<PillTone, string> = {
  neutral: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  accent: "bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300",
  ok: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300",
  wait: "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300",
  check: "bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300",
  bad: "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300",
};

/** The one badge shape used across the app: same size, weight, radius and tone set. */
export default function Pill({
  tone = "neutral",
  className,
  ...rest
}: HTMLAttributes<HTMLSpanElement> & { tone?: PillTone }) {
  return <span {...rest} className={cx(BASE, TONE[tone], className)} />;
}
