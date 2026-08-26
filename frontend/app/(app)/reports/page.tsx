"use client";

import useSWR from "swr";
import { searchReceipts } from "@/lib/api";
import type { ReceiptItem } from "@/lib/types";
import { SpendingChart, type SpendPoint } from "@/components/Charts";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import { formatMoney } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

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
      label: new Date(`${month}-01T00:00:00`).toLocaleDateString("en-US", { month: "short" }),
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
          Spending analytics for your household.
        </p>
      </div>

      {receiptsLoading ? (
        <SkeletonCard className="h-72" />
      ) : receiptsError ? (
        <EmptyState icon="⚠️" title="Could not load reports" description="Check that the backend is running." />
      ) : trend.length === 0 ? (
        <EmptyState icon="📊" title="Not enough data" description="Upload receipts to unlock spending reports." action={{ label: "Upload receipts", href: "/upload" }} />
      ) : (
        <section className="card p-5" aria-label="Spending by month">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Spending by month</h2>
          <p className="mb-4 mt-1 text-sm text-slate-500 dark:text-slate-400">
            {items.length} receipts · {formatMoney(trend.reduce((sum, p) => sum + p.amount, 0), "USD")} total
          </p>
          <SpendingChart data={trend} height={280} />
        </section>
      )}
    </div>
  );
}
