"use client";

import useSWR from "swr";
import { getRecurringExpenses, submitRecurringFeedback } from "@/lib/api";
import type { RecurringExpense } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import { formatMoney } from "@/lib/utils";

export default function SubscriptionsPage() {
  const { data, error, isLoading, mutate } = useSWR<{ items: RecurringExpense[] }>(
    "/product/recurring-expenses",
    getRecurringExpenses,
  );

  const items = data?.items ?? [];

  async function feedback(merchant: string, isSubscription: boolean) {
    await submitRecurringFeedback({ merchant, is_subscription: isSubscription });
    mutate();
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Subscriptions</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Recurring expenses detected from your receipt history.
        </p>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          <SkeletonCard className="h-36" />
          <SkeletonCard className="h-36" />
        </div>
      ) : error ? (
        <EmptyState icon="⚠️" title="Could not load recurring expenses" description="Check that the backend is running." />
      ) : items.length === 0 ? (
        <EmptyState
          icon="🔄"
          title="No recurring expenses"
          description="At least 2 matching transactions are needed to detect a subscription."
        />
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2" aria-label="Recurring expenses">
          {items.map((item) => (
            <li key={item.merchant} className="card p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="font-semibold text-slate-900 dark:text-slate-100">{item.merchant}</h2>
                  <p className="mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                    {item.occurrences} occurrences · {item.price_change >= 0 ? "+" : ""}
                    {(item.price_change * 100).toFixed(0)}% price change
                  </p>
                </div>
                {item.likely_subscription ? (
                  <span className="inline-flex rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700 dark:bg-brand-950 dark:text-brand-300">
                    Likely subscription
                  </span>
                ) : null}
              </div>
              <p className="mt-3 text-xl font-semibold text-slate-900 dark:text-slate-100">
                {formatMoney(item.annualized, "USD")}
                <span className="ml-1 text-sm font-normal text-slate-400">annualized</span>
              </p>
              <div className="mt-4 flex gap-2">
                <button type="button" onClick={() => feedback(item.merchant, true)} className="btn-primary flex-1 text-sm">
                  It's a subscription
                </button>
                <button type="button" onClick={() => feedback(item.merchant, false)} className="btn-secondary flex-1 text-sm">
                  Not a subscription
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
