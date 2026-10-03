"use client";

import EmptyState from "@/components/EmptyState";
import { useTranslation } from "@/lib/i18n";
import type { SavingsBlock, SavingsCandidate } from "@/lib/types";
import { formatMoney } from "@/lib/utils";

/**
 * Dashboard savings block — how much the household could keep by moving to
 * the cheapest candidates for the given period.
 *
 * Purely presentational: the payload already arrives on the consumer
 * dashboard response (`ConsumerDashboard.savings`), so this card adds no
 * fetch and no auth handling of its own. The backend may report an empty
 * block (`top_candidates: []`, `potential_saving: 0`) when the window holds
 * too few receipts to rank anything — that renders as an empty state rather
 * than a bare "0.00".
 */
export default function SavingsBlockCard({ savings }: { savings: SavingsBlock }) {
  const { t } = useTranslation();
  const { currency } = savings;
  // An empty block is signalled either by no candidates or by a non-positive
  // headroom — both would otherwise render a meaningless "0.00".
  const hasSavings =
    savings.top_candidates.length > 0 && savings.potential_saving > 0;

  return (
    <section className="card p-5" aria-label={t("savingsOpportunities")}>
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
          {t("savingsOpportunities")}
        </h2>
        <span className="text-xl" aria-hidden="true">
          🐖
        </span>
      </div>
      {hasSavings ? (
        <>
          <p className="mt-3 text-3xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400">
            {formatMoney(savings.potential_saving, currency)}
          </p>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {savings.period} — {t("totalSpentLabel")}{" "}
            {formatMoney(savings.total_spent, currency)}
          </p>
          <ul className="mt-4 space-y-3">
            {savings.top_candidates.map((candidate) => (
              <SavingsCandidateRow
                key={candidate.merchant}
                candidate={candidate}
                currency={currency}
              />
            ))}
          </ul>
        </>
      ) : (
        <div className="mt-4">
          <EmptyState
            icon="✅"
            title={t("noSavingsFound")}
            description={t("noSavingsFoundHint")}
          />
        </div>
      )}
    </section>
  );
}

/**
 * One ranked candidate: merchant, its own headroom, and the price delta that
 * makes it a candidate. `delta_pct` is signed and the backend may leave it
 * unset, so it is only rendered when it is a real finite number — never as
 * `NaN`, and never as a bare value without its unit.
 */
function SavingsCandidateRow({
  candidate,
  currency,
}: {
  candidate: SavingsCandidate;
  currency: string;
}) {
  const { t } = useTranslation();
  const delta = Number.isFinite(candidate.delta_pct) ? candidate.delta_pct : null;
  const rising = delta !== null && delta > 0;

  return (
    <li className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900 dark:bg-emerald-950/40">
      <div className="flex items-center justify-between gap-2">
        <p className="font-medium text-slate-900 dark:text-slate-100">
          {candidate.merchant}
        </p>
        {delta === null ? null : (
          <span className="inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            {t("deltaVsAverage")} {delta > 0 ? "+" : ""}
            {delta.toFixed(1)}%
          </span>
        )}
      </div>
      <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
        {t("potentialSaving")} {formatMoney(candidate.potential_saving, currency)}
        {rising ? ` · ${t("priceRising")}` : ""}
      </p>
    </li>
  );
}
