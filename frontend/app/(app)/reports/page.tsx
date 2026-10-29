"use client";

import useSWR from "swr";
import { searchReceipts } from "@/lib/api";
import type { ReceiptItem } from "@/lib/types";
import { SpendingChart, type SpendPoint } from "@/components/Charts";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import { formatMoney } from "@/lib/utils";
import UnpricedNote from "@/components/UnpricedNote";
import { getLocale, useTranslation } from "@/lib/i18n";

type ReportReceipt = { date: string | null; total: number | null; currency?: string | null };

/** The currency most receipts are in; totals in other currencies are not added to it. */
function dominantCurrency(items: Array<{ receipt: ReportReceipt }>): string {
  const counts = new Map<string, number>();
  for (const { receipt } of items) {
    if (receipt.total === null || receipt.total === undefined || !receipt.currency) continue;
    counts.set(receipt.currency, (counts.get(receipt.currency) ?? 0) + 1);
  }
  return Array.from(counts.entries()).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "USD";
}

function monthlySpend(items: Array<{ receipt: ReportReceipt }>, currency: string): SpendPoint[] {
  const byMonth = new Map<string, number>();
  for (const item of items) {
    const date = item.receipt.date;
    // Receipts with an unknown total are left out (and counted separately), not summed as 0.
    if (!date || item.receipt.total === null || item.receipt.total === undefined) continue;
    if (item.receipt.currency && item.receipt.currency !== currency) continue;
    const month = date.slice(0, 7);
    byMonth.set(month, (byMonth.get(month) ?? 0) + item.receipt.total);
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
  const currency = dominantCurrency(items);
  const trend = monthlySpend(items, currency);
  const unpriced = items.filter((item) => item.receipt.total === null || item.receipt.total === undefined).length;

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
        <EmptyState title={t("couldNotLoad")} description={t("error")} />
      ) : trend.length === 0 ? (
        <div className="space-y-2">
          <EmptyState title={t("notEnoughData")} description={t("reportsEmptyDesc")} action={{ label: t("uploadReceiptsAction"), href: "/upload" }} />
          <UnpricedNote count={unpriced} />
        </div>
      ) : (
        <section className="card p-5" aria-label={t("spendingTrend")}>
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{t("spendingTrend")}</h2>
          <p className="mb-4 mt-1 text-sm text-slate-500 dark:text-slate-400">
            {items.length} {t("receiptsCountLabel")} · {formatMoney(trend.reduce((sum, p) => sum + p.amount, 0), currency)} {t("totalLabel")}
          </p>
          <UnpricedNote count={unpriced} />
          <SpendingChart data={trend} height={280} currency={currency} />
        </section>
      )}
    </div>
  );
}
