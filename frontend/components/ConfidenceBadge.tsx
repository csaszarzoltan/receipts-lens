import Pill, { type PillTone } from "@/components/Pill";
import { formatPercent } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

interface ConfidenceBadgeProps {
  /** OCR confidence 0..1 (or 0..100, auto-detected). */
  value: number | null;
  label?: string;
  /** Hide the retake hint under a low value (used where space is tight, e.g. list cards). */
  compact?: boolean;
}

function tone(ratio: number): PillTone {
  if (ratio >= 0.85) return "ok";
  if (ratio >= 0.6) return "wait";
  return "bad";
}

/** OCR confidence indicator — green/amber/red by threshold. */
export default function ConfidenceBadge({ value, label, compact = false }: ConfidenceBadgeProps) {
  const { t } = useTranslation();
  if (value === null || !Number.isFinite(value)) return <span className="text-sm text-slate-600 dark:text-slate-400">{t("unknownConfidence")}</span>;
  const ratio = value > 1 ? value / 100 : value;
  const isLow = ratio < 0.6;
  return (
    <span className="inline-flex flex-col items-start gap-1">
      <Pill tone={tone(ratio)} title={label ? `${label}: ${formatPercent(ratio)}` : formatPercent(ratio)}>
        <span aria-hidden="true">◉</span>
        {formatPercent(ratio)}
      </Pill>
      {isLow && !compact && (
        <span className="text-xs text-rose-700 dark:text-rose-300">
          {t("lowConfidenceShort")}
          <span className="block text-[11px] opacity-80">{t("retryCaptureHint")}</span>
        </span>
      )}
    </span>
  );
}
