"use client";

import React, { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import useSWR from "swr";
import { correctReceipt, getReceiptImage, getReviewItems, rereadReviewTotals } from "@/lib/api";
import type { ReviewItem } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import ConfidenceBadge from "@/components/ConfidenceBadge";
import { SkeletonCard } from "@/components/Skeleton";
import { cx, formatDate, formatMoney, parseAmount } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

/** Receipts with an uncertain OCR extraction land in review. */
const LOW_CONFIDENCE_LEVELS = new Set(["low", "medium"]);

function isWeakMatch(item: ReviewItem): boolean {
  const level = item.receipt.confidence_level;
  if (level && LOW_CONFIDENCE_LEVELS.has(level)) return true;
  const conf = item.receipt.confidence ?? {};
  const values = Object.values(conf).filter(
    (v): v is number => typeof v === "number",
  );
  if (values.length === 0) return false;
  return values.reduce((a, b) => a + b, 0) / values.length < 0.6;
}

/** The amount the user is asked to confirm: the saved total, else what OCR read. */
function proposedAmount(item: ReviewItem): number | null {
  return item.receipt.total ?? item.receipt.total_candidate ?? null;
}

/** True while the stored image has not yet been read for an amount. */
function needsReread(item: ReviewItem): boolean {
  const r = item.receipt;
  return r.total == null && r.total_candidate == null && !r.total_candidate_checked;
}

function Icon({ kind }: { kind: "ok" | "warn" | "info" }) {
  const common = { width: 16, height: 16, viewBox: "0 0 16 16", fill: "none", "aria-hidden": true } as const;
  if (kind === "ok") {
    return (
      <svg {...common}>
        <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
        <path d="M4.8 8.2l2.2 2.2 4.2-4.6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  if (kind === "warn") {
    return (
      <svg {...common}>
        <path d="M8 1.8l6.6 11.6H1.4L8 1.8z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
        <path d="M8 6.4v3.2M8 11.4v.1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
      <path d="M8 7.2v4M8 4.8v.1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function ReviewWorkspace() {
  const { t } = useTranslation();
  const receiptId = useSearchParams().get("receipt") ?? undefined;
  const { data, error, isLoading, mutate } = useSWR<{ items: ReviewItem[] }>(
    ["/product/review-items", receiptId],
    () => getReviewItems(receiptId),
  );
  const items = React.useMemo(() => data?.items ?? [], [data]);
  const pendingReads = items.filter(needsReread).length;
  const [reading, setReading] = React.useState(false);
  const readingRef = React.useRef(false);
  const [bulk, setBulk] = React.useState<{ done: number; total: number } | null>(null);
  const [bulkDone, setBulkDone] = React.useState<number | null>(null);

  // Receipts saved before the total candidate existed have nothing to confirm yet:
  // read their stored images a few at a time until none are left.
  React.useEffect(() => {
    if (pendingReads === 0 || readingRef.current) return;
    readingRef.current = true;
    setReading(true);
    (async () => {
      try {
        for (;;) {
          const result = await rereadReviewTotals(2);
          await mutate();
          if (result.remaining === 0 || result.updated === 0) break;
        }
      } catch {
        // The cards below still work; the user can type the amount by hand.
      } finally {
        readingRef.current = false;
        setReading(false);
      }
    })();
  }, [pendingReads, mutate]);

  if (isLoading) {
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <SkeletonCard className="h-96" />
        <SkeletonCard className="h-96" />
      </div>
    );
  }

  if (error) {
    return (
      <EmptyState
        icon="⚠️"
        title={t("couldNotLoad")}
        description={t("error")}
      />
    );
  }

  if (items.length === 0) {
    return (
      <EmptyState
        icon="✅"
        title={bulkDone ? `${bulkDone} ${t("reviewConfirmedSuffix")}` : t("allClearTitle")}
        description={t("allClearDesc")}
      />
    );
  }

  const confirmable = items.filter((item) => item.checks?.lines_match === true && proposedAmount(item) != null);

  async function confirmAll() {
    const batch = confirmable;
    setBulk({ done: 0, total: batch.length });
    let done = 0;
    for (const item of batch) {
      try {
        const candidate = item.receipt.total == null ? proposedAmount(item) : null;
        await correctReceipt(
          item.receipt_id,
          { changes: candidate != null ? { total: candidate } : {}, action: "complete" },
          item.version,
        );
        done += 1;
      } catch {
        // A stale or failed receipt stays in the queue for a manual look.
      }
      setBulk({ done, total: batch.length });
    }
    setBulkDone(done);
    setBulk(null);
    await mutate();
  }

  return (
    <div className="space-y-4">
      <div className="card flex flex-wrap items-center justify-between gap-3 px-5 py-4">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100" data-testid="review-summary">
            {items.length} {t("reviewToCheckSuffix")}
          </p>
          <p
            className="mt-0.5 flex items-center gap-1.5 text-sm text-slate-600 dark:text-slate-400"
            role="status"
            aria-live="polite"
          >
            {reading ? (
              <>
                <span
                  className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600 motion-reduce:animate-none dark:border-slate-600"
                  aria-hidden
                />
                {t("reviewReading")} {pendingReads} {t("reviewLeftSuffix")}
              </>
            ) : (
              confirmable.length > 0
                ? `${confirmable.length} ${t("reviewAddUpSuffix")}`
                : t("reviewNoneAddUp")
            )}
          </p>
        </div>
        {confirmable.length > 0 ? (
          <button type="button" className="btn-secondary text-sm" onClick={confirmAll} disabled={bulk !== null}>
            {bulk
              ? `${t("reviewConfirming")} ${bulk.done}/${bulk.total}`
              : `${t("reviewConfirmAddUp")} (${confirmable.length})`}
          </button>
        ) : null}
      </div>
      <ul className="space-y-4" aria-label={t("review")}>
        {items.map((item) => (
          <ReviewCard key={item.receipt_id} item={item} reading={reading && needsReread(item)} onDone={() => mutate()} />
        ))}
      </ul>
    </div>
  );
}

function CheckLine({ item }: { item: ReviewItem }) {
  const { t } = useTranslation();
  const checks = item.checks;
  const currency = item.receipt.currency;
  if (!checks || checks.lines_match === null || checks.line_sum === null) {
    return (
      <p className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-400">
        <span className="mt-0.5 shrink-0"><Icon kind="info" /></span>
        <span>{t("reviewLinesNone")}</span>
      </p>
    );
  }
  if (checks.lines_match) {
    return (
      <p className="flex items-start gap-2 text-sm text-emerald-800 dark:text-emerald-300">
        <span className="mt-0.5 shrink-0"><Icon kind="ok" /></span>
        <span>
          {t("reviewLinesAddUp")} <strong className="tabular-nums">{formatMoney(checks.line_sum, currency)}</strong>
        </span>
      </p>
    );
  }
  return (
    <p className="flex items-start gap-2 text-sm text-amber-800 dark:text-amber-300">
      <span className="mt-0.5 shrink-0"><Icon kind="warn" /></span>
      <span>
        {t("reviewLinesDiffer")} <strong className="tabular-nums">{formatMoney(checks.line_sum, currency)}</strong>,{" "}
        {t("reviewLinesDifferHint")}
      </span>
    </p>
  );
}

function ReviewCard({ item, reading, onDone }: { item: ReviewItem; reading: boolean; onDone: () => void }) {
  const { t } = useTranslation();
  const [saving, setSaving] = React.useState(false);
  const [message, setMessage] = React.useState<string | null>(null);
  const [saveFailed, setSaveFailed] = React.useState(false);
  const [imageUrl, setImageUrl] = React.useState<string | null>(null);
  const weak = isWeakMatch(item);
  const proposed = proposedAmount(item);
  const fromOcr = item.receipt.total == null && proposed != null;
  const [typed, setTyped] = React.useState<string | null>(null);
  const [invalid, setInvalid] = React.useState(false);

  React.useEffect(() => {
    let cancelled = false;
    let objectUrl: string | undefined;
    getReceiptImage(item.receipt_id)
      .then((blob) => {
        if (!cancelled) { objectUrl = URL.createObjectURL(blob); setImageUrl(objectUrl); }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [item.receipt_id]);

  // What the box shows until the user types: the amount on file or the one OCR read.
  const shown = typed ?? (proposed != null ? String(proposed) : "");

  async function complete() {
    const amount = parseAmount(shown);
    const edited = typed !== null && typed !== (proposed != null ? String(proposed) : "");
    const needsAmount = item.receipt.total == null || edited;
    if (needsAmount && !(amount > 0)) {
      setInvalid(true);
      return;
    }
    setInvalid(false);
    setSaving(true);
    setMessage(null);
    setSaveFailed(false);
    try {
      await correctReceipt(
        item.receipt_id,
        { changes: needsAmount ? { total: amount } : {}, action: "complete" },
        item.version,
      );
      setMessage(t("markedComplete"));
      onDone();
    } catch (err) {
      setSaveFailed(true);
      setMessage(t("failedComplete"));
    } finally {
      setSaving(false);
    }
  }

  const inputId = `amount-${item.receipt_id}`;
  const stateTone = fromOcr
    ? "text-amber-800 dark:text-amber-300"
    : proposed != null
      ? "text-emerald-800 dark:text-emerald-300"
      : "text-slate-600 dark:text-slate-400";
  const stateLabel = fromOcr
    ? t("totalCandidateLabel")
    : proposed != null
      ? t("reviewAmountOnFile")
      : reading
        ? t("reviewReading")
        : t("reviewAmountNotRead");

  return (
    <li className="card overflow-hidden">
      <div className="grid gap-0 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
        <div className="bg-slate-100 dark:bg-slate-950">
          {imageUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={imageUrl}
              alt={`${t("reviewDesc")} ${item.receipt.vendor || t("unknownVendorLabel")}`}
              className="h-64 w-full object-contain lg:h-full lg:min-h-[22rem]"
              loading="lazy"
            />
          ) : (
            <div className="flex h-24 items-center justify-center text-sm text-slate-600 lg:h-full lg:min-h-[10rem] dark:text-slate-400">
              {t("imageUnavailable")}
            </div>
          )}
        </div>
        <div className="flex flex-col gap-4 p-5">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h2 className="truncate text-lg font-semibold text-slate-900 dark:text-slate-100">
                {item.receipt.vendor || t("unknownVendorLabel")}
              </h2>
              <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-400">
                {item.receipt.date ? formatDate(item.receipt.date) : t("noDateLabel")}
              </p>
            </div>
            <StatusBadge status="needs_review" />
          </div>

          <div
            className={cx(
              "rounded-lg border p-4",
              fromOcr
                ? "border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/40"
                : "border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/50",
            )}
          >
            <label htmlFor={inputId} className="text-xs font-medium uppercase tracking-wide text-slate-600 dark:text-slate-400">
              {t("reviewAmountInput")}
            </label>
            <div className="mt-1.5 flex items-center gap-2">
              <span className="text-sm font-medium text-slate-600 dark:text-slate-400" aria-hidden>
                {item.receipt.currency ?? ""}
              </span>
              <input
                id={inputId}
                className="input min-h-11 text-xl font-semibold tabular-nums"
                inputMode="decimal"
                autoComplete="off"
                value={shown}
                placeholder={reading ? "…" : "0"}
                aria-invalid={invalid}
                aria-describedby={`${inputId}-hint`}
                onChange={(e) => {
                  setTyped(e.target.value);
                  setInvalid(false);
                }}
              />
            </div>
            <p id={`${inputId}-hint`} className={cx("mt-2 text-xs font-medium", invalid ? "text-rose-700 dark:text-rose-300" : stateTone)}>
              {invalid ? t("reviewInvalidAmount") : stateLabel}
            </p>
          </div>

          <CheckLine item={item} />

          <div className="flex flex-wrap items-start gap-x-3 gap-y-2 text-sm text-slate-600 dark:text-slate-400">
            <ConfidenceBadge
              value={
                Object.values(item.receipt.confidence ?? {}).length
                  ? Object.values(item.receipt.confidence ?? {}).reduce((a, b) => a + b, 0) /
                    Object.values(item.receipt.confidence ?? {}).length
                  : 0
              }
            />
            <span>
              {item.receipt.line_items?.length ?? 0}{" "}
              {item.receipt.line_items?.length === 1 ? t("lineItemSingular") : t("lineItemsSuffix")}
            </span>
          </div>

          {weak && proposed != null && !fromOcr ? (
            <div
              role="note"
              className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200"
            >
              {t("uncertainAmountWarning")}
            </div>
          ) : null}

          <div className="mt-auto flex flex-wrap items-center gap-2">
            <button type="button" onClick={complete} disabled={saving} className="btn-primary text-sm">
              {saving ? t("savingLabel") : fromOcr || weak ? t("confirmAmount") : t("looksGood")}
            </button>
            <Link href={`/receipts/${item.receipt_id}`} className="btn-secondary text-sm">
              {t("openFullDetail")}
            </Link>
            {message ? (
              <span className={saveFailed ? "text-sm text-rose-700 dark:text-rose-300" : "text-sm text-emerald-700 dark:text-emerald-300"} role={saveFailed ? "alert" : "status"}>
                {message}
              </span>
            ) : null}
          </div>
        </div>
      </div>
    </li>
  );
}

export default function ReviewPage() {
  const { t } = useTranslation();
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("review")}</h1>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          {t("reviewDesc")}
        </p>
      </div>
      <Suspense fallback={<SkeletonCard className="h-64" />}><ReviewWorkspace /></Suspense>
    </div>
  );
}
