"use client";

import Link from "next/link";
import useSWR from "swr";
import { getConsumerDashboard } from "@/lib/api";
import type {
  ConsumerDashboard,
  HouseholdStatus,
  RecentReceipt,
} from "@/lib/types";
import { PageSkeleton } from "@/components/Skeleton";
import EmptyState from "@/components/EmptyState";
import { formatDate, formatMoney } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

/**
 * Lakossági dashboard (F1.2 — docs/plans/consumer-pivot-2026-08-13.md §3.4).
 *
 * Hat blokk, mindegyik élő backend adatot mutat (GET /api/v1/consumer/dashboard):
 *   1. „{t("dailyRemaining")}" — napi maradékkeret (budget visszaszámolás)
 *   2. Havi költés kategóriánként — „mire ment el a pénzem"
 *   3. {t("priceAlerts")} (meglévő előfizetés-motor)
 *   4. {t("cancellableSubscriptions")}
 *   5. {t("householdStatus")} (közös háztartási keret + tagok)
 *   6. {t("recentReceipts")}
 *
 * Lakossági nyelvezet: nincs üzleti szakkifejezés. Üres állapotnál a blokk
 * onboarding/első lépés CTA-ra mutat.
 */
export default function ConsumerDashboardPage() {
  const { t } = useTranslation();
  const { data, error, isLoading } = useSWR<ConsumerDashboard>(
    "/api/v1/consumer/dashboard",
    getConsumerDashboard,
  );

  if (isLoading) return <PageSkeleton />;

  if (error || !data) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          {t("overviewTitle")}
        </h1>
        <EmptyState
          icon="⚠️"
          title={t("error")}
          description={t("retry")}
          action={{ label: t("retry"), href: "/dashboard" }}
        />
      </div>
    );
  }

  const { daily_remaining, monthly_by_category, price_alerts, cancellable_subscriptions, household, recent_receipts } = data;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {t("overviewTitle")}
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {t("overviewSubtitle")}
          </p>
        </div>
        <Link href="/upload" className="btn-primary">
          {t("addReceipt")}
        </Link>
      </div>

      {/* 1. {t("dailyRemaining")} */}
      <section aria-label="Napi maradékkeret" className="grid gap-4 lg:grid-cols-2">
        {daily_remaining ? (
          <div className="card p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                {t("dailyRemaining")}
              </h2>
              <span className="text-xl" aria-hidden="true">
                💶
              </span>
            </div>
            <p className="mt-3 text-3xl font-bold tracking-tight text-brand-600 dark:text-brand-400">
              {formatMoney(daily_remaining.daily_remaining, daily_remaining.currency)}
            </p>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {daily_remaining.days_left} {t("dailyRemainingHint")}
              keretből {formatMoney(daily_remaining.remaining_this_month, daily_remaining.currency)}{" "}
              
            </p>
            <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
              <div
                className="h-full rounded-full bg-brand-500 transition-all"
                style={{ width: `${Math.min(100, daily_remaining.pct_used)}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
               {daily_remaining.pct_used}
            </p>
          </div>
        ) : (
          <EmptyState
            icon="🎯"
            title={t("noBudgetSet")}
            description={t("noBudgetSetHint")}
            action={{ label: t("noBudgetSet"), href: "/budget" }}
          />
        )}

        {/* 5. {t("householdStatus")} */}
        <HouseholdBlock household={household} />
      </section>

      {/* 2. Havi költés kategóriánként */}
      <section className="card p-5" aria-label={t("monthlySpending")}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              {t("monthlySpending")}
            </h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {monthly_by_category.month} {t("monthlySpending")} — {t("totalSpentLabel")}{" "}
              {formatMoney(monthly_by_category.total_spent, monthly_by_category.currency)}.
            </p>
          </div>
          <Link
            href="/reports"
            className="text-sm font-medium text-brand-600 hover:underline dark:text-brand-400"
          >
            {t("openReports")}
          </Link>
        </div>
        {monthly_by_category.categories.length === 0 ? (
          <div className="mt-4">
            <EmptyState
              icon="🧾"
              title={t("noReceipts")}
              description="Az első nyugta feltöltése után itt látod, mire ment el a pénzed."
              action={{ label: t("uploadFirst"), href: "/upload" }}
            />
          </div>
        ) : (
          <ul className="mt-4 divide-y divide-slate-100 dark:divide-slate-800">
            {monthly_by_category.categories.map((category) => (
              <li
                key={category.key}
                className="flex items-center justify-between gap-3 py-3"
              >
                <div className="flex items-center gap-3">
                  <span
                    className="h-3 w-3 rounded-full bg-brand-500"
                    aria-hidden="true"
                  />
                  <span className="font-medium text-slate-800 dark:text-slate-100">
                    {category.label}
                  </span>
                  <span className="text-xs text-slate-400 dark:text-slate-500">
                    {category.count} db
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-slate-500 dark:text-slate-400">
                    {category.pct}%
                  </span>
                  <span className="font-semibold text-slate-900 dark:text-slate-100">
                    {formatMoney(category.total, monthly_by_category.currency)}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* 3. {t("priceAlerts")} */}
      <section className="card p-5" aria-label={t("priceAlerts")}>
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
            {t("priceAlerts")}
          </h2>
          <span className="text-xl" aria-hidden="true">
            📈
          </span>
        </div>
        {price_alerts.length === 0 ? (
          <div className="mt-4">
            <EmptyState
              icon="✅"
              title={t("allClear")}
              description={t("noPriceAlerts")}
            />
          </div>
        ) : (
          <ul className="mt-4 space-y-3">
            {price_alerts.map((alert) => (
              <li
                key={alert.merchant}
                className="rounded-lg border border-rose-200 bg-rose-50 p-4 dark:border-rose-900 dark:bg-rose-950/40"
              >
                <p className="font-medium text-slate-900 dark:text-slate-100">
                  {alert.message}
                </p>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                   {formatMoney(alert.monthly_cost, alert.currency)} — érdemes
                  átnézni a díjat.
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* 4. {t("cancellableSubscriptions")} */}
      <section className="card p-5" aria-label={t("cancellableSubscriptions")}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              {t("cancellableSubscriptions")}
            </h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Ezeket bármikor lemondhatod — a lemondási útmutató az Előfizetések
              oldalon van.
            </p>
          </div>
          <Link
            href="/subscriptions"
            className="text-sm font-medium text-brand-600 hover:underline dark:text-brand-400"
          >
            Összes előfizetés →
          </Link>
        </div>
        {cancellable_subscriptions.length === 0 ? (
          <div className="mt-4">
            <EmptyState
              icon="🔁"
              title={t("noSubscriptionsFound")}
              description="Ha egy szolgáltatásért rendszeresen fizetsz, itt fog megjelenni."
            />
          </div>
        ) : (
          <ul className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {cancellable_subscriptions.map((subscription) => (
              <li key={subscription.id} className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="font-medium text-slate-900 dark:text-slate-100">
                    {subscription.merchant}
                  </h3>
                  {subscription.price_increase ? (
                    <span className="inline-flex rounded-full bg-rose-50 px-2 py-0.5 text-xs font-medium text-rose-700 dark:bg-rose-950 dark:text-rose-300">
                      {t("warning")}
                    </span>
                  ) : null}
                </div>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                  {formatMoney(subscription.monthly_cost, "USD")}/hó · lejárat:{" "}
                  {formatDate(subscription.renewal_date)}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* 6. {t("recentReceipts")} */}
      <RecentReceiptsBlock receipts={recent_receipts} />
    </div>
  );
}

function HouseholdBlock({ household }: { household: HouseholdStatus }) {
  const { t } = useTranslation();
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
          {t("householdStatus")}
        </h2>
        <span className="text-xl" aria-hidden="true">
          👨‍👩‍👧‍👦
        </span>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-3 text-center">
        <div>
          <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            {formatMoney(household.shared_budget, household.currency)}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{t("familyBudget")}</p>
        </div>
        <div>
          <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            {formatMoney(household.spent, household.currency)}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{t("spent")}</p>
        </div>
        <div>
          <p className="text-lg font-semibold text-emerald-600 dark:text-emerald-400">
            {formatMoney(household.remaining, household.currency)}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{t("remaining")}</p>
        </div>
      </div>
      {household.members.length > 0 ? (
        <ul className="mt-4 space-y-2">
          {household.members.map((member) => (
            <li
              key={member.member_id}
              className="flex items-center justify-between text-sm"
            >
              <span className="truncate text-slate-700 dark:text-slate-300">
                {member.email}
              </span>
              <span className="ml-3 shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                {member.role_label}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">
          {household.member_breakdown_note ?? t("overviewSubtitle")}
        </p>
      )}
    </div>
  );
}

function RecentReceiptsBlock({ receipts }: { receipts: RecentReceipt[] }) {
  const { t } = useTranslation();
  return (
    <section className="card p-5" aria-label={t("recentReceipts")}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
          {t("recentReceipts")}
        </h2>
        <Link
          href="/receipts"
          className="text-sm font-medium text-brand-600 hover:underline dark:text-brand-400"
        >
          {t("allPurchases")}
        </Link>
      </div>
      {receipts.length === 0 ? (
        <div className="mt-4">
          <EmptyState
            icon="🧾"
            title={t("noReceipts")}
            description={t("noReceiptsHint")}
            action={{ label: t("addReceipt"), href: "/upload" }}
          />
        </div>
      ) : (
        <ul className="mt-4 divide-y divide-slate-100 dark:divide-slate-800">
          {receipts.map((receipt) => (
            <li key={receipt.receipt_id}>
              <Link
                href={`/receipts/${receipt.receipt_id}`}
                className="flex items-center justify-between gap-3 py-3 hover:bg-slate-50 dark:hover:bg-slate-900"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium text-slate-800 dark:text-slate-100">
                    {receipt.merchant}
                  </p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {formatDate(receipt.date)}
                  </p>
                </div>
                <span className="shrink-0 font-semibold text-slate-900 dark:text-slate-100">
                  {formatMoney(receipt.total, receipt.currency)}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
