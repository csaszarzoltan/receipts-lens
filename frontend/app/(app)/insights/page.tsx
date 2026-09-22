"use client";

import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";
import {
  evaluateInsights,
  getInsightCards,
  setInsightPreferences,
} from "@/lib/api";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import { useTranslation } from "@/lib/i18n";

/**
 * Insights page (FEAT-033B proactive insight delivery).
 *
 * Insight cards (title/explanation/confidence/deep_link → chat) plus an
 * evaluate button and an unsubscribe/resubscribe toggle. No mock data —
 * cards come from GET /api/v1/insights/cards, evaluation from
 * POST /api/v1/insights/evaluate, opt-out from
 * POST /api/v1/insights/preferences.
 */
export default function InsightsPage() {
  const { t } = useTranslation();
  const [evaluating, setEvaluating] = useState(false);
  const [unsubscribed, setUnsubscribed] = useState(false);
  const [prefBusy, setPrefBusy] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { data, error, isLoading, mutate } = useSWR(
    "/api/v1/insights/cards",
    getInsightCards,
  );

  async function runEvaluate() {
    setEvaluating(true);
    setErrorMsg(null);
    try {
      await evaluateInsights();
      await mutate();
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err));
    } finally {
      setEvaluating(false);
    }
  }

  async function toggleSubscription() {
    setPrefBusy(true);
    setErrorMsg(null);
    try {
      const res = await setInsightPreferences(!unsubscribed);
      setUnsubscribed(res.unsubscribed);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err));
    } finally {
      setPrefBusy(false);
    }
  }

  if (isLoading) return <SkeletonCard className="h-64" />;

  const cards = data?.cards ?? [];
  const failure = errorMsg ?? (error instanceof Error ? error.message : null);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {t("insights")}
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {t("insightsSubtitle")}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={runEvaluate}
            disabled={evaluating}
            className="btn-primary disabled:opacity-50"
          >
            {evaluating ? t("evaluating") : t("evaluateNow")}
          </button>
          <button
            type="button"
            onClick={toggleSubscription}
            disabled={prefBusy}
            className="btn-secondary disabled:opacity-50"
          >
            {unsubscribed ? t("resubscribe") : t("unsubscribe")}
          </button>
        </div>
      </div>

      {unsubscribed ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">
          {t("unsubscribedNote")}
        </p>
      ) : null}

      {failure ? (
        <EmptyState icon="⚠️" title={t("error")} description={failure} />
      ) : null}

      {!failure && cards.length === 0 ? (
        <EmptyState
          icon="💡"
          title={t("noInsightsTitle")}
          description={t("noInsightsHint")}
        />
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        {cards.map((card) => (
          <article key={card.insight_id} className="card space-y-2 p-5">
            <div className="flex items-start justify-between gap-3">
              <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                {card.title}
              </h2>
              <span
                className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300"
                title={t("confidence")}
              >
                {Math.round(card.confidence * 100)}%
              </span>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              {card.explanation}
            </p>
            <Link
              href={`/chat?insight=${encodeURIComponent(card.insight_id)}`}
              className="btn-secondary inline-flex text-xs"
            >
              {t("openInChat")}
            </Link>
          </article>
        ))}
      </div>
    </div>
  );
}
