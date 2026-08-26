"use client";

import { useMemo, useState } from "react";
import useSWR from "swr";
import {
  getCancelGuide,
  getPreferences,
  getSubscriptions,
  savePreferences,
} from "@/lib/api";
import type {
  CancelGuide,
  Preferences,
  Subscription,
} from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import { formatDate, formatMoney } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

const RENEWAL_SOON_DAYS = 14;

function daysUntil(iso: string): number {
  const target = new Date(`${iso}T00:00:00`);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.round((target.getTime() - today.getTime()) / 86_400_000);
}

function daysLabel(days: number): string {
  if (days === 0) return "renews today";
  if (days === 1) return "renews tomorrow";
  return `renews in ${days} days`;
}

export default function SubscriptionsPage() {
  const { t } = useTranslation();
  const [guideFor, setGuideFor] = useState<Subscription | null>(null);
  const { data: prefs } = useSWR<Preferences>("/product/preferences", getPreferences);
  const [emailAlerts, setEmailAlerts] = useState<boolean | null>(null);
  const [prefLoading, setPrefLoading] = useState(false);
  const { data, error, isLoading } = useSWR(
    "/api/v1/subscriptions",
    getSubscriptions,
  );
  const { data: guide, isLoading: guideLoading } = useSWR<CancelGuide | null>(
    guideFor ? `/api/v1/subscriptions/${guideFor.id}/cancel-guide` : null,
    () => getCancelGuide(guideFor!.id),
  );

  const items: Subscription[] = data?.subscriptions ?? [];
  const summary = data?.summary;

  const upcoming = useMemo(
    () =>
      items
        .filter((s) => daysUntil(s.renewal_date) <= RENEWAL_SOON_DAYS)
        .sort(
          (a, b) => daysUntil(a.renewal_date) - daysUntil(b.renewal_date),
        ),
    [items],
  );

  const priceChanges = useMemo(
    () => items.filter((s) => s.price_increase),
    [items],
  );

  async function toggleEmailAlerts(next: boolean) {
    setEmailAlerts(next);
    setPrefLoading(true);
    try {
      await savePreferences({ email_alerts: next });
    } catch {
      // Persistence is best-effort — the toggle stays local for this session.
      setEmailAlerts(!next);
    } finally {
      setPrefLoading(false);
    }
  }

  const emailAlertsOn = emailAlerts ?? prefs?.email_alerts ?? false;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {t("subscriptions")}
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Renewals, price changes and cancellation guides for your recurring
            expenses.
          </p>
        </div>
        <label className="flex cursor-pointer items-center gap-3">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Email alerts
          </span>
          <button
            type="button"
            role="switch"
            aria-checked={emailAlertsOn}
            aria-label="Email alerts"
            disabled={prefLoading}
            onClick={() => toggleEmailAlerts(!emailAlertsOn)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
              emailAlertsOn
                ? "bg-brand-600"
                : "bg-slate-300 dark:bg-slate-700"
            } ${prefLoading ? "opacity-60" : ""}`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                emailAlertsOn ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
        </label>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <SkeletonCard className="h-36" />
          <SkeletonCard className="h-36" />
          <SkeletonCard className="h-36" />
        </div>
      ) : error ? (
        <EmptyState
          icon="⚠️"
          title="Could not load subscriptions"
          description="Check that the backend is running."
        />
      ) : items.length === 0 ? (
        <EmptyState
          icon="🔄"
          title="No subscriptions detected"
          description="At least 2 matching transactions are needed to detect a subscription."
        />
      ) : (
        <>
          {summary ? (
            <section
              className="grid gap-4 sm:grid-cols-2"
              aria-label="Subscription summary"
            >
              <div className="card p-5">
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Active subscriptions
                </p>
                <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-slate-100">
                  {summary.total}
                </p>
              </div>
              <div className="card p-5">
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Monthly cost
                </p>
                <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-slate-100">
                  {formatMoney(summary.monthly_total, "USD")}
                </p>
              </div>
            </section>
          ) : null}

          {upcoming.length > 0 ? (
            <section aria-label="Upcoming renewals">
              <h2 className="mb-2 text-base font-semibold text-slate-900 dark:text-slate-100">
                Upcoming renewals
              </h2>
              <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {upcoming.map((s) => (
                  <li key={s.id} className="card p-4">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="font-medium text-slate-900 dark:text-slate-100">
                        {s.merchant}
                      </h3>
                      <span className="inline-flex rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700 dark:bg-brand-950 dark:text-brand-300">
                        {daysLabel(daysUntil(s.renewal_date))}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                      {formatDate(s.renewal_date)} ·{" "}
                      {formatMoney(s.monthly_cost, "USD")}/mo
                    </p>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {priceChanges.length > 0 ? (
            <section aria-label="Price changes">
              <h2 className="mb-2 text-base font-semibold text-slate-900 dark:text-slate-100">
                Price changes
              </h2>
              <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {priceChanges.map((s) => (
                  <li
                    key={s.id}
                    className="card border-rose-200 p-4 dark:border-rose-900"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="font-medium text-slate-900 dark:text-slate-100">
                        {s.merchant}
                      </h3>
                      <span className="inline-flex rounded-full bg-rose-50 px-2 py-0.5 text-xs font-medium text-rose-700 dark:bg-rose-950 dark:text-rose-300">
                        Price increased
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                      Now {formatMoney(s.amount, "USD")} ·{" "}
                      {formatMoney(s.monthly_cost, "USD")}/mo
                    </p>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section aria-label="All subscriptions">
            <h2 className="mb-2 text-base font-semibold text-slate-900 dark:text-slate-100">
              All subscriptions
            </h2>
            <div className="card overflow-x-auto">
              <table className="w-full min-w-[560px] text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-slate-800 dark:text-slate-400">
                    <th className="px-4 py-3">Merchant</th>
                    <th className="px-4 py-3">Frequency</th>
                    <th className="px-4 py-3">Renewal</th>
                    <th className="px-4 py-3 text-right">Monthly</th>
                    <th className="px-4 py-3 text-right">Annualized</th>
                    <th className="px-4 py-3">Trend</th>
                    <th className="px-4 py-3">Guide</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {items.map((s) => (
                    <tr
                      key={s.id}
                      className="hover:bg-slate-50 dark:hover:bg-slate-900"
                    >
                      <td className="px-4 py-3 font-medium text-slate-800 dark:text-slate-100">
                        {s.merchant}
                      </td>
                      <td className="px-4 py-3 capitalize text-slate-600 dark:text-slate-300">
                        {s.frequency}
                      </td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                        {formatDate(s.renewal_date)}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-600 dark:text-slate-300">
                        {formatMoney(s.monthly_cost, "USD")}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-600 dark:text-slate-300">
                        {formatMoney(s.annualized, "USD")}
                      </td>
                      <td className="px-4 py-3">
                        {s.trend === "up" ? (
                          <span className="text-rose-600 dark:text-rose-400">
                            ↑ up
                          </span>
                        ) : (
                          <span className="text-emerald-600 dark:text-emerald-400">
                            → stable
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          type="button"
                          onClick={() => setGuideFor(s)}
                          className="text-brand-600 hover:underline dark:text-brand-400"
                        >
                          Cancel guide
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      {guideFor ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
          role="dialog"
          aria-modal="true"
          aria-label={`Cancellation guide for ${guideFor.merchant}`}
          onClick={() => setGuideFor(null)}
        >
          <div
            className="card max-h-[80vh] w-full max-w-lg overflow-y-auto p-6"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  Cancel {guideFor.merchant}
                </h2>
                <p className="mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                  {guideFor.frequency} · {formatMoney(guideFor.amount, "USD")}{" "}
                  per charge
                </p>
              </div>
              <button
                type="button"
                onClick={() => setGuideFor(null)}
                className="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
                aria-label="Close"
              >
                ✕
              </button>
            </div>

            {guideLoading ? (
              <p className="mt-4 text-sm text-slate-400">Loading guide…</p>
            ) : guide ? (
              <ol className="mt-4 list-decimal space-y-2 pl-5">
                {guide.steps.map((step, index) => (
                  <li
                    key={index}
                    className="text-sm text-slate-700 dark:text-slate-300"
                  >
                    {step}
                  </li>
                ))}
              </ol>
            ) : (
              <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">
                No cancellation guide available for this merchant.
              </p>
            )}

            {guide?.url ? (
              <a
                href={guide.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-5 inline-flex min-h-11 items-center justify-center rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-700"
              >
                Open {guide.merchant} account
              </a>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
