"use client";

import React from "react";
import Link from "next/link";
import { deleteWarranty, updateWarranty } from "@/lib/api";
import { useTranslation, type MessageKey } from "@/lib/i18n";
import type { Warranty, WarrantyStatus } from "@/lib/types";
import { cx, formatDate } from "@/lib/utils";

const DAY_MS = 86_400_000;

function daysBetween(from: string, to: string): number {
  return Math.round((Date.parse(`${to}T00:00:00Z`) - Date.parse(`${from}T00:00:00Z`)) / DAY_MS);
}

/** How urgent a deadline is: drives colour and wording together, never colour alone. */
function urgency(daysLeft: number | null): "past" | "soon" | "near" | "calm" {
  if (daysLeft === null || daysLeft < 0) return "past";
  if (daysLeft <= 7) return "soon";
  if (daysLeft <= 14) return "near";
  return "calm";
}

const TONE = {
  past: { text: "text-slate-600 dark:text-slate-400", bar: "bg-slate-400 dark:bg-slate-500" },
  soon: { text: "text-rose-800 dark:text-rose-300", bar: "bg-rose-600 dark:bg-rose-400" },
  near: { text: "text-amber-800 dark:text-amber-300", bar: "bg-amber-600 dark:bg-amber-400" },
  calm: { text: "text-emerald-800 dark:text-emerald-300", bar: "bg-emerald-600 dark:bg-emerald-400" },
} as const;

const STATUS_LABEL: Record<WarrantyStatus, MessageKey> = {
  active: "warrantyStatusActive",
  returned: "warrantyStatusReturned",
  claim: "warrantyStatusClaim",
  archived: "warrantyStatusArchived",
};

function Deadline({
  title, date, daysLeft, purchaseDate, muted,
}: { title: string; date: string | null; daysLeft: number | null; purchaseDate: string; muted: boolean }) {
  const { t } = useTranslation();
  if (!date || daysLeft === null) return null;
  const tone = TONE[muted ? "past" : urgency(daysLeft)];
  const total = Math.max(1, daysBetween(purchaseDate, date));
  const used = Math.min(total, Math.max(0, total - daysLeft));
  // A closed item no longer counts down: only its dates remain.
  const words = muted ? null
    : daysLeft < 0 ? t("warrantyExpired")
    : daysLeft === 0 ? t("warrantyEndsToday")
    : `${daysLeft} ${daysLeft === 1 ? t("warrantyDayLeft") : t("warrantyDaysLeft")}`;
  return (
    <div>
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 text-sm">
        <span className="font-medium text-slate-800 dark:text-slate-100">
          {title} <span className="font-normal text-slate-600 dark:text-slate-400">· {formatDate(date)}</span>
        </span>
        {words ? <span className={cx("font-semibold tabular-nums", tone.text)}>{words}</span> : null}
      </div>
      <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700" aria-hidden="true">
        <div className={cx("h-full rounded-full", tone.bar)} style={{ width: `${(used / total) * 100}%` }} />
      </div>
    </div>
  );
}

export default function WarrantyCard({ item, onChanged }: { item: Warranty; onChanged: () => void }) {
  const { t } = useTranslation();
  const [busy, setBusy] = React.useState(false);
  const [confirmingDelete, setConfirmingDelete] = React.useState(false);
  const [error, setError] = React.useState(false);
  const open = item.status === "active";

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    setError(false);
    try {
      await action();
      onChanged();
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }

  const setStatus = (status: WarrantyStatus) => run(() => updateWarranty(item.warranty_id, { status }));
  const accent = open ? TONE[urgency(item.days_to_next)].bar : "bg-slate-300 dark:bg-slate-600";

  return (
    <li className="card relative overflow-hidden" data-testid="warranty-card">
      <span className={cx("absolute inset-y-0 left-0 w-1", accent)} aria-hidden="true" />
      <div className="space-y-4 p-5 pl-6">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 className="truncate text-base font-semibold text-slate-900 dark:text-slate-100">{item.item_name}</h2>
            <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-400">
              {[item.merchant, formatDate(item.purchase_date)].filter(Boolean).join(" · ")}
              {item.receipt_id ? (
                <>
                  {" · "}
                  <Link href={`/receipts/${item.receipt_id}`} className="font-medium text-brand-700 underline dark:text-brand-300">
                    {t("warrantyLinkedReceipt")}
                  </Link>
                </>
              ) : null}
            </p>
          </div>
          {!open || item.due_soon ? (
            <span
              className={cx(
                "shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium",
                open
                  ? "bg-amber-50 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                  : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
              )}
            >
              {open ? t("warrantySummaryDue") : t(STATUS_LABEL[item.status])}
            </span>
          ) : null}
        </div>

        <div className="space-y-3">
          <Deadline title={t("warrantyReturnBy")} date={item.return_by} daysLeft={item.return_days_left}
                    purchaseDate={item.purchase_date} muted={!open} />
          <Deadline title={t("warrantyUntil")} date={item.warranty_ends} daysLeft={item.warranty_days_left}
                    purchaseDate={item.purchase_date} muted={!open} />
          {!item.return_by ? (
            <p className="text-sm text-slate-600 dark:text-slate-400">{t("warrantyNoReturn")}</p>
          ) : null}
        </div>

        {item.notes ? <p className="text-sm text-slate-700 dark:text-slate-300">{item.notes}</p> : null}

        <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3 dark:border-slate-800">
            {open ? (
              <>
                <button type="button" className="btn-secondary text-sm" disabled={busy} onClick={() => setStatus("returned")}>
                  {t("warrantyMarkReturned")}
                </button>
                <button type="button" className="btn-secondary text-sm" disabled={busy} onClick={() => setStatus("claim")}>
                  {t("warrantyMarkClaim")}
                </button>
              </>
            ) : (
              <button type="button" className="btn-secondary text-sm" disabled={busy} onClick={() => setStatus("active")}>
                {t("warrantyReopen")}
              </button>
            )}
            {item.status !== "archived" ? (
              <button type="button" className="btn-secondary text-sm" disabled={busy} onClick={() => setStatus("archived")}>
                {t("warrantyArchive")}
              </button>
            ) : null}
            {confirmingDelete ? (
              <span className="ml-auto flex flex-wrap items-center gap-2" role="group" aria-label={t("warrantyDeleteConfirm")}>
                <span className="text-sm text-slate-700 dark:text-slate-300">{t("warrantyDeleteConfirm")}</span>
                <button type="button" className="inline-flex min-h-11 items-center rounded-lg bg-rose-700 px-4 text-sm font-medium text-white hover:bg-rose-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-500 focus-visible:ring-offset-2 disabled:opacity-50"
                        disabled={busy} onClick={() => run(() => deleteWarranty(item.warranty_id))}>
                  {t("warrantyDelete")}
                </button>
                <button type="button" className="btn-secondary text-sm" onClick={() => setConfirmingDelete(false)}>
                  {t("warrantyKeep")}
                </button>
              </span>
            ) : (
              <button type="button" className="ml-auto inline-flex min-h-11 items-center px-2 text-sm font-medium text-rose-700 hover:underline dark:text-rose-300"
                      onClick={() => setConfirmingDelete(true)}>
                {t("warrantyDelete")}
              </button>
            )}
        </div>
        {error ? <p role="alert" className="text-sm text-rose-700 dark:text-rose-300">{t("warrantySaveError")}</p> : null}
      </div>
    </li>
  );
}
