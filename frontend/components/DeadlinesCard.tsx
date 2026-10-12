"use client";

import Link from "next/link";
import useSWR from "swr";
import { getWarranties } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { cx, formatDate } from "@/lib/utils";

/** The next return or warranty deadlines on the dashboard; absent until the household tracks something. */
export default function DeadlinesCard() {
  const { t } = useTranslation();
  const { data } = useSWR("/product/warranties", getWarranties);
  const active = (data?.items ?? []).filter((item) => item.due_soon);
  if (active.length === 0) return null;
  const shown = active.slice(0, 3);

  return (
    <section className="card p-5" aria-label={t("warrantyDashTitle")} data-testid="deadlines-card">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{t("warrantyDashTitle")}</h2>
        <Link href="/warranties" className="text-sm font-medium text-brand-700 hover:underline dark:text-brand-300">
          {t("warrantyDashAll")} →
        </Link>
      </div>
      <ul className="mt-3 divide-y divide-slate-100 dark:divide-slate-800">
        {shown.map((item) => {
          const days = item.days_to_next ?? 0;
          return (
            <li key={item.warranty_id} className="flex items-center justify-between gap-3 py-2.5">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-800 dark:text-slate-100">{item.item_name}</p>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  {item.next_deadline_kind === "return" ? t("warrantyKindReturn") : t("warrantyKindWarranty")} ·{" "}
                  {formatDate(item.next_deadline)}
                </p>
              </div>
              <span
                className={cx(
                  "shrink-0 text-sm font-semibold tabular-nums",
                  days <= 7 ? "text-rose-800 dark:text-rose-300"
                    : days <= 14 ? "text-amber-800 dark:text-amber-300"
                    : "text-emerald-800 dark:text-emerald-300",
                )}
              >
                {days === 0 ? t("warrantyEndsToday") : `${days} ${days === 1 ? t("warrantyDayLeft") : t("warrantyDaysLeft")}`}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
