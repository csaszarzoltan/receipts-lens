"use client";

import useSWR from "swr";
import { searchReceipts } from "@/lib/api";
import type { ReceiptItem } from "@/lib/types";
import { SpendingChart, type SpendPoint } from "@/components/Charts";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import { formatMoney } from "@/lib/utils";
import { getLocale, useTranslation } from "@/lib/i18n";

function monthlySpend(items: Array<{ receipt: { date: string | null; total: number | null } }>): SpendPoint[] {
  const byMonth = new Map<string, number>();
  for (const item of items) {
    const date = item.receipt.date;
    if (!date) continue;
    const month = date.slice(0, 7);
    const total = item.receipt.total ?? 0;
    byMonth.set(month, (byMonth.get(month) ?? 0) + total);
  }
  return Array.from(byMonth.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-12)
    .map(([month, amount]) => ({
      label: new Date(`${month}-01T00:00:00`).toLocaleDateString(({ en: "en-US", hu: "hu-HU", de: "de-DE", fr: "fr-FR", es: "es-ES", it: "it-IT", pt: "pt-PT", nl: "nl-NL", pl: "pl-PL", ro: "ro-RO" } as Record<string,string>)[getLocale()] ?? "en-US", { month: "short" }),
      amount: Math.round(amount * 100) / 100,
    }));
}

export default function ReportsPage() {
  const { t } = useTranslation();
  const { data: receiptsData, error: receiptsError, isLoading: receiptsLoading } = useSWR(
    "/product/receipts?limit=200",
    () => searchReceipts({ limit: 200 }),
  );

  const items: ReceiptItem[] = receiptsData?.items ?? [];
  const trend = monthlySpend(items);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("reports")}</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {t("reportsDesc")}
        </p>
      </div>

      {receiptsLoading ? (
        <SkeletonCard className="h-72" />
      ) : receiptsError ? (
        <EmptyState icon="⚠️" title={t("couldNotLoad")} description={t("error")} />
      ) : trend.length === 0 ? (
        <EmptyState icon="📊" title={t("notEnoughData")} description={t("reportsEmptyDesc")} action={{ label: t("uploadReceiptsAction"), href: "/upload" }} />
      ) : (
        <section className="card p-5" aria-label={t("spendingTrend")}>
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{t("spendingTrend")}</h2>
          <p className="mb-4 mt-1 text-sm text-slate-500 dark:text-slate-400">
            {items.length} {t("receiptsCountLabel")} · {formatMoney(trend.reduce((sum, p) => sum + p.amount, 0), "USD")} {t("totalLabel")}
          </p>
          <SpendingChart data={trend} height={280} />
        </section>
      )}
    </div>
  );
}
