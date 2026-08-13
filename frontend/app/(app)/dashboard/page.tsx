"use client";

import Link from "next/link";
import useSWR from "swr";
import { getBudgetVariance, getDashboard, getWorkQueue, searchReceipts } from "@/lib/api";
import type { DashboardData, WorkQueueItem } from "@/lib/types";
import KpiCard from "@/components/KpiCard";
import { SpendingChart, type SpendPoint } from "@/components/Charts";
import { PageSkeleton } from "@/components/Skeleton";
import EmptyState from "@/components/EmptyState";
import { formatMoney } from "@/lib/utils";

/** Group receipts by month for the spending trend series. */
function monthlySpend(items: Array<{ receipt: { date: string | null; total: number | null } }>): SpendPoint[] {
  const byMonth = new Map<string, number>();
  for (const item of items) {
    const date = item.receipt.date;
    if (!date) continue;
    const month = date.slice(0, 7); // YYYY-MM
    const total = item.receipt.total ?? 0;
    byMonth.set(month, (byMonth.get(month) ?? 0) + total);
  }
  return Array.from(byMonth.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-6)
    .map(([month, amount]) => ({
      label: new Date(`${month}-01T00:00:00`).toLocaleDateString("en-US", { month: "short" }),
      amount: Math.round(amount * 100) / 100,
    }));
}

/**
 * Dashboard — KPI cards (total receipts, spending trend, budget status)
 * fed by the real backend APIs: /product/dashboard, /product/receipts,
 * /product/work-queue and /forecasts/budget-variance.
 */
export default function DashboardPage() {
  const { data: dashboard, error, isLoading } = useSWR<DashboardData>(
    "/product/dashboard",
    getDashboard,
  );
  const { data: receiptsPage } = useSWR("/product/receipts?limit=200", () =>
    searchReceipts({ limit: 200 }),
  );
  const { data: queueData } = useSWR<{ items: WorkQueueItem[] }>(
    "/product/work-queue",
    () => getWorkQueue(8),
  );
  const { data: budgetVariance } = useSWR("/forecasts/budget-variance?horizon=1", () =>
    getBudgetVariance({ horizon: 1 }),
  );

  if (isLoading) return <PageSkeleton />;

  if (error || !dashboard) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Áttekintés</h1>
        <EmptyState
          icon="⚠️"
          title="Could not load dashboard"
          description="The backend may be offline. Start the FastAPI server and try again."
          action={{ label: "Retry", href: "/dashboard" }}
        />
      </div>
    );
  }

  const jobsByStatus = dashboard.usage?.jobs_by_status ?? {};
  const totalReceipts = receiptsPage?.total ?? Object.values(jobsByStatus).reduce((sum, count) => sum + (count as number), 0);
  const needsReview = dashboard.quality?.needs_review ?? 0;
  const queue: WorkQueueItem[] = queueData?.items ?? [];

  const trend = monthlySpend(receiptsPage?.items ?? []);
  const totalSpent = trend.reduce((sum, point) => sum + point.amount, 0);
  const projections = budgetVariance?.projections ?? [];
  const overBudgetCount = projections.filter((p) => p.status === "over_budget").length;
  const budgetSummary =
    projections.length === 0
      ? "No budget set"
      : `${overBudgetCount} of ${projections.length} over budget`;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Áttekintés</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Service status:{" "}
            <span className="font-medium text-emerald-600 dark:text-emerald-400">
              {dashboard.service?.status ?? "unknown"}
            </span>
          </p>
        </div>
        <Link href="/upload" className="btn-primary">
          ⬆ Upload receipt
        </Link>
      </div>

      <section aria-label="Key performance indicators" className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard icon="🧾" title="Total receipts" value={String(totalReceipts)} sub="all time" />
        <KpiCard
          icon="💸"
          title="Spent (last 6 mo)"
          value={formatMoney(totalSpent, "USD")}
          sub={`${trend.length} months of history`}
        />
        <KpiCard
          icon="🔍"
          title="Needs review"
          value={String(needsReview)}
          sub="OCR confidence low"
          tone={needsReview > 0 ? "warning" : "default"}
        />
        <KpiCard
          icon="🎯"
          title="Budget status"
          value={budgetSummary}
          sub={overBudgetCount > 0 ? "action needed" : "looking good"}
          tone={overBudgetCount > 0 ? "danger" : projections.length > 0 ? "success" : "default"}
        />
      </section>

      <section className="card p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              Spending trend
            </h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Monthly totals from your receipts (last {trend.length} months).
            </p>
          </div>
          <Link href="/receipts" className="text-sm font-medium text-brand-600 hover:underline dark:text-brand-400">
            View all receipts →
          </Link>
        </div>
        {trend.length === 0 ? (
          <div className="mt-4">
            <EmptyState
              icon="📄"
              title="No receipts yet"
              description="Upload your first receipt to start tracking spending."
              action={{ label: "Upload a receipt", href: "/upload" }}
            />
          </div>
        ) : (
          <div className="mt-4">
            <SpendingChart data={trend} height={240} />
          </div>
        )}
      </section>

      <section className="card p-5">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Work queue</h2>
        {queue.length === 0 ? (
          <div className="mt-4">
            <EmptyState
              icon="🎉"
              title="All clear!"
              description="Nothing needs your attention right now."
            />
          </div>
        ) : (
          <ul className="mt-4 divide-y divide-slate-100 dark:divide-slate-800">
            {queue.map((item, index) => (
              <li key={`${item.title}-${index}`} className="flex items-center justify-between gap-3 py-3">
                <div>
                  <p className="font-medium text-slate-800 dark:text-slate-100">{item.title}</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{item.reason}</p>
                </div>
                <Link href={item.action_url} className="btn-secondary shrink-0 text-sm">
                  {item.action_label}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
