"use client";

import { useTranslation } from "@/lib/i18n";
import { cx } from "@/lib/utils";

interface QuotaBarProps {
  used: number;
  limit: number | null;
  isPro: boolean;
}

export default function QuotaBar({ used, limit, isPro }: QuotaBarProps) {
  const { t } = useTranslation();
  if (isPro || limit === null) {
    return (
      <div className="flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300" role="status" aria-label="quota">
        <span aria-hidden>✓</span> {t("quotaUsed")}: ∞ — Pro
      </div>
    );
  }
  const pct = Math.min(100, Math.round((used / limit) * 100));
  const tone = pct >= 100 ? "bg-rose-500" : pct >= 80 ? "bg-amber-400" : "bg-brand-500";
  const remaining = Math.max(0, limit - used);
  return (
    <div className="space-y-1.5" role="group" aria-label="quota">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-600 dark:text-slate-300">
          {t("quotaUsed")}: {used}/{limit}
        </span>
        <span className={cx("text-xs", remaining === 0 ? "font-semibold text-rose-600" : "text-slate-500")}>
          {remaining === 0 ? t("upgradeToPro") : `${remaining} left`}
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700" role="progressbar" aria-valuenow={used} aria-valuemax={limit} aria-label="quota">
        <div className={cx("h-full rounded-full transition-all", tone)} style={{ width: `${pct}%` }} />
      </div>
      {remaining === 0 ? (
        <p className="text-xs font-medium text-rose-600 dark:text-rose-400">{t("upgradeToPro")}</p>
      ) : null}
    </div>
  );
}
