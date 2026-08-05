import { formatPercent } from "@/lib/utils";
import { cx } from "@/lib/utils";

interface ConfidenceBadgeProps {
  /** OCR confidence 0..1 (or 0..100, auto-detected). */
  value: number;
  label?: string;
}

function tone(ratio: number): string {
  if (ratio >= 0.85) return "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300";
  if (ratio >= 0.6) return "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300";
  return "bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300";
}

/** OCR confidence indicator — green/amber/red by threshold. */
export default function ConfidenceBadge({ value, label }: ConfidenceBadgeProps) {
  const ratio = value > 1 ? value / 100 : value;
  return (
    <span
      className={cx(
        "inline-flex min-h-6 items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        tone(ratio),
      )}
      title={label ? `${label}: ${formatPercent(ratio)}` : formatPercent(ratio)}
    >
      <span aria-hidden="true">◉</span>
      {formatPercent(ratio)}
    </span>
  );
}
