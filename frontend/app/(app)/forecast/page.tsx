"use client";

import useSWR from "swr";
import { getAnomalies, getBudgetVariance, getForecast } from "@/lib/api";
import type { AnomalyResult, BudgetVarianceResult, ForecastResult } from "@/lib/types";
import { ForecastChart, VarianceChart, type ForecastPoint, type VariancePoint } from "@/components/Charts";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import StatusBadge from "@/components/StatusBadge";
import { formatMoney } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

/**
 * Forecast page — spending predictions from the ForecastEngine, anomaly
 * table and budget variance projections. All data comes from the real
 * /forecasts* endpoints.
 */
export default function ForecastPage() {
  const { t } = useTranslation();
  const { data: forecast, error: forecastError, isLoading: forecastLoading } = useSWR<ForecastResult>(
    "/forecasts",
    () => getForecast({ period: "monthly", horizon: 1 }),
  );
  const { data: anomalies, error: anomaliesError, isLoading: anomaliesLoading } = useSWR<AnomalyResult>(
    "/forecasts/anomalies",
    () => getAnomalies({ period: "monthly", method: "zscore", threshold: 2.0 }),
  );
  const { data: variance, error: varianceError, isLoading: varianceLoading } = useSWR<BudgetVarianceResult>(
    "/forecasts/budget-variance",
    () => getBudgetVariance({ horizon: 1 }),
  );

  if (forecastLoading || anomaliesLoading || varianceLoading) {
    return (
      <div className="space-y-6">
        <SkeletonCard className="h-10 w-64" />
        <div className="grid gap-6 lg:grid-cols-2">
          <SkeletonCard className="h-80" />
          <SkeletonCard className="h-80" />
        </div>
      </div>
    );
  }

  const hasData = forecast && forecast.forecasts && forecast.forecasts.length > 0;

  if (forecastError && anomaliesError && varianceError) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("forecast")}</h1>
        <EmptyState icon="⚠️" title={t("couldNotLoad")} description={t("error")} />
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("forecast")}</h1>
        <EmptyState
          icon="📊"
          title={t("notEnoughData")}
          description={t("notEnoughDataHint")}
          action={{ label: t("uploadFirst"), href: "/upload" }}
        />
      </div>
    );
  }

  const forecastPoints: ForecastPoint[] = (forecast.forecasts ?? []).map((entry) => ({
    label: entry.category === "overall" ? t("overallLabel") : entry.category,
    projected: entry.next_period_total,
    low: entry.confidence_low,
    high: entry.confidence_high,
  }));

  const variancePoints: VariancePoint[] = (variance?.projections ?? []).map((projection) => ({
    label: projection.category,
    budgeted: projection.budgeted,
    projected: projection.projected_spend,
    overage: projection.expected_overage,
  }));

  const anomalyEntries = anomalies?.anomalies ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("forecast")}</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {forecast.period} · {forecast.currency} · {t("horizonLabel")} {1} {t("periodSuffix")}
          {forecast.narrative ? ` — ${forecast.narrative}` : ""}
        </p>
      </div>

      <section className="card p-5" aria-label={t("forecastTitle")}>
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
          {t("nextPeriodProjections")}
        </h2>
        <ForecastChart data={forecastPoints} height={280} />
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="card p-5" aria-label={t("budgetVariance")}>
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
            Budget variance
          </h2>
          {variancePoints.length === 0 ? (
            <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">
              {t("noBudgetsConfigured")}
            </p>
          ) : (
            <>
              <VarianceChart data={variancePoints} height={240} />
              <ul className="mt-4 space-y-2">
                {variance?.projections.map((projection) => (
                  <li key={projection.budget_id} className="flex items-center justify-between gap-3 text-sm">
                    <span className="font-medium text-slate-700 dark:text-slate-200">{projection.category}</span>
                    <span className="text-slate-500 dark:text-slate-400">
                      {formatMoney(projection.budgeted, variance.currency)} →{" "}
                      {formatMoney(projection.projected_spend, variance.currency)}
                    </span>
                    <StatusBadge status={projection.status} />
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>

        <section className="card p-5" aria-label={t("anomalies")}>
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
            Anomalies
            {anomalies ? (
              <span className="ml-2 text-xs font-normal text-slate-400">
                ({anomalies.method}, threshold {anomalies.threshold})
              </span>
            ) : null}
          </h2>
          {anomalyEntries.length === 0 ? (
            <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">
              {t("noUnusualSpending")}
            </p>
          ) : (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[420px] text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-slate-800 dark:text-slate-400">
                    <th className="py-2 pr-3">{t("periodHeader")}</th>
                    <th className="py-2 pr-3">{t("category")}</th>
                    <th className="py-2 pr-3 text-right">{t("expectedHeader")}</th>
                    <th className="py-2 pr-3 text-right">{t("actualHeader")}</th>
                    <th className="py-2 text-right">{t("scoreHeader")}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {anomalyEntries.map((entry, index) => (
                    <tr key={`${entry.period}-${entry.category}-${index}`}>
                      <td className="py-2 pr-3 text-slate-600 dark:text-slate-300">{entry.period}</td>
                      <td className="py-2 pr-3 font-medium text-slate-800 dark:text-slate-100">{entry.category}</td>
                      <td className="py-2 pr-3 text-right text-slate-600 dark:text-slate-300">
                        {formatMoney(entry.expected, forecast.currency)}
                      </td>
                      <td className="py-2 pr-3 text-right font-medium text-rose-600 dark:text-rose-400">
                        {formatMoney(entry.actual, forecast.currency)}
                      </td>
                      <td className="py-2 text-right text-slate-600 dark:text-slate-300">
                        {entry.score.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
