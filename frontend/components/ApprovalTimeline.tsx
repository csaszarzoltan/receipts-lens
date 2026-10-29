"use client";

import type { Approval } from "@/lib/types";
import StatusBadge from "@/components/StatusBadge";
import { cx, formatDate } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

/** Approval state as one pill: amber while waiting, green approved, red rejected. */
export function ApprovalPill({ approval }: { approval: Approval }) {
  const { t } = useTranslation();
  const label =
    approval.status === "pending"
      ? t("approvalAwaiting")
      : approval.status === "approved"
        ? t("statusApproved")
        : t("statusRejected");
  return <StatusBadge status={approval.status} label={label} />;
}

type StepState = "done" | "current" | "failed" | "upcoming";

const DOT: Record<StepState, string> = {
  done: "border-emerald-600 bg-emerald-600",
  current: "border-amber-600 bg-white dark:bg-slate-900",
  failed: "border-rose-600 bg-rose-600",
  upcoming: "border-slate-300 bg-white dark:border-slate-600 dark:bg-slate-900",
};

/**
 * Approval as a visible, asynchronous sequence: submitted, then waiting or decided,
 * then done. The waiting step stays visible until someone decides.
 */
export default function ApprovalTimeline({ approval }: { approval: Approval }) {
  const { t, locale } = useTranslation();
  const decided = approval.status !== "pending";
  const approved = approval.status === "approved";
  const waitingDays = Math.floor((Date.now() - Date.parse(approval.created_at)) / 86_400_000);
  const waitingText =
    waitingDays < 1 ? t("approvalWaitingToday") : t("approvalWaitingDays").replace("{n}", String(waitingDays));

  const steps: Array<{ key: string; label: string; detail: string; state: StepState }> = [
    {
      key: "submitted",
      label: t("approvalSubmitted"),
      detail: formatDate(approval.created_at, locale),
      state: "done",
    },
    {
      key: "decision",
      label: approval.status === "pending" ? t("approvalAwaiting") : approved ? t("statusApproved") : t("statusRejected"),
      detail: decided
        ? formatDate(approval.decided_at ?? approval.created_at, locale)
        : `${t("approvalPolicyLabel")}: ${approval.policy_name ?? "—"} · ${waitingText}`,
      state: decided ? (approved ? "done" : "failed") : "current",
    },
    {
      key: "done",
      label: t("statusCompleted"),
      detail: "",
      state: approved ? "done" : "upcoming",
    },
  ];

  return (
    <section aria-label={t("approvalTitle")} className="space-y-3">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {t("approvalTitle")}
      </h2>
      <ol className="space-y-3">
        {steps.map((step) => (
          <li key={step.key} className="flex items-start gap-3">
            <span
              aria-hidden="true"
              className={cx("mt-1 h-3 w-3 shrink-0 rounded-full border-2", DOT[step.state])}
            />
            <div className="min-w-0">
              <p
                className={cx(
                  "text-sm font-semibold",
                  step.state === "upcoming" ? "text-slate-500 dark:text-slate-400" : "text-slate-900 dark:text-slate-100",
                )}
              >
                {step.label}
              </p>
              {step.detail ? <p className="text-xs text-slate-500 dark:text-slate-400">{step.detail}</p> : null}
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
