"use client";

import useSWR from "swr";
import { getBudgetVariance } from "@/lib/api";
import type { BudgetVarianceResult } from "@/lib/types";
import { VarianceChart, type VariancePoint } from "@/components/Charts";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import StatusBadge from "@/components/StatusBadge";
import { formatMoney } from "@/lib/utils";

/**
 * Budget — variance view with per-category breakdown from the real
 * /forecasts/budget-variance endpoint.
 */
export default function BudgetPage() {
  const { data, error, isLoading } = useSWR<BudgetVarianceResult>(
    "/forecasts/budget-variance?horizon=1",
    () => getBudgetVariance({ horizon: 1 }),
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <SkeletonCard className="h-10 w-56" />
        <SkeletonCard className="h-80" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Háztartási keret</h1>
        <EmptyState icon="⚠️" title="Could not load budget data" description="Check that the backend is running." />
      </div>
    );
  }

  if (!data) return null;

  const projections = data.projections ?? [];
  const points: VariancePoint[] = projections.map((projection) => ({
    label: projection.category,
    budgeted: projection.budgeted,
    projected: projection.projected_spend,
    overage: projection.expected_overage,
  }));

  if (projections.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Háztartási keret</h1>
        <EmptyState
          icon="🎯"
          title="No budget set"
          description="Create a budget to track category spending and projected overruns."
        />
      </div>
    );
  }

  const totalBudgeted = projections.reduce((sum, p) => sum + p.budgeted, 0);
  const totalProjected = projections.reduce((sum, p) => sum + p.projected_spend, 0);
  const overBudget = projections.filter((p) => p.status === "over_budget");
  const warning = projections.filter((p) => p.status === "warning");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Háztartási keret</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {data.currency} · {projections.length} categories · projected end-of-period spend vs budget
        </p>
      </div>

      <section aria-label="Budget summary" className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="card p-5">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Total budgeted</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">
            {formatMoney(totalBudgeted, data.currency)}
          </p>
        </div>
        <div className="card p-5">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Projected spend</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">
            {formatMoney(totalProjected, data.currency)}
          </p>
        </div>
        <div className="card p-5">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">At risk</p>
          <p className="mt-2 text-2xl font-semibold text-amber-600 dark:text-amber-400">
            {warning.length} warning · {overBudget.length} over
          </p>
        </div>
      </section>

      <section className="card p-5" aria-label="Budget variance chart">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
          Budget vs projected spend by category
        </h2>
        <VarianceChart data={points} height={300} />
      </section>

      <section className="card overflow-x-auto" aria-label="Category breakdown">
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-slate-800 dark:text-slate-400">
              <th className="px-5 py-3">Category</th>
              <th className="px-5 py-3 text-right">Budgeted</th>
              <th className="px-5 py-3 text-right">Projected</th>
              <th className="px-5 py-3 text-right">Overage</th>
              <th className="px-5 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {projections.map((projection) => (
              <tr key={projection.budget_id} className="hover:bg-slate-50 dark:hover:bg-slate-900">
                <td className="px-5 py-3 font-medium text-slate-800 dark:text-slate-100">{projection.category}</td>
                <td className="px-5 py-3 text-right text-slate-600 dark:text-slate-300">
                  {formatMoney(projection.budgeted, data.currency)}
                </td>
                <td className="px-5 py-3 text-right text-slate-600 dark:text-slate-300">
                  {formatMoney(projection.projected_spend, data.currency)}
                </td>
                <td className="px-5 py-3 text-right font-medium text-rose-600 dark:text-rose-400">
                  {projection.expected_overage > 0
                    ? formatMoney(projection.expected_overage, data.currency)
                    : "—"}
                </td>
                <td className="px-5 py-3">
                  <StatusBadge status={projection.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
