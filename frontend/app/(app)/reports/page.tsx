"use client";

import useSWR from "swr";
import { getExportRuns, searchReceipts } from "@/lib/api";
import type { ExportRun, ReceiptItem } from "@/lib/types";
import { SpendingChart, type SpendPoint } from "@/components/Charts";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import { formatDateTime, formatMoney } from "@/lib/utils";

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
  const { data: receiptsData, error: receiptsError, isLoading: receiptsLoading } = useSWR(
    "/product/receipts?limit=200",
    () => searchReceipts({ limit: 200 }),
  );
  const { data: runsData } = useSWR<{ items: ExportRun[] }>("/product/export-runs", getExportRuns);

  const items: ReceiptItem[] = receiptsData?.items ?? [];
  const trend = monthlySpend(items);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Reports</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Spending analytics and export activity.
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

      <section className="card p-5" aria-label="Export activity">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Export activity</h2>
        {(runsData?.items ?? []).length === 0 ? (
          <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">No exports yet.</p>
        ) : (
          <ul className="mt-3 divide-y divide-slate-100 dark:divide-slate-800">
            {runsData?.items.map((run) => (
              <li key={run.export_id} className="flex items-center justify-between gap-3 py-2 text-sm">
                <span className="font-medium text-slate-800 dark:text-slate-100">{run.format}</span>
                <span className="text-slate-500 dark:text-slate-400">{run.status}</span>
                <span className="text-slate-400">{formatDateTime(run.created_at)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
