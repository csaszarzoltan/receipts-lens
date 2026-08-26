"use client";

import React from "react";
import Link from "next/link";
import useSWR from "swr";
import { correctReceipt, getReceiptImage, getReviewItems } from "@/lib/api";
import type { ReviewItem } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import ConfidenceBadge from "@/components/ConfidenceBadge";
import { SkeletonCard } from "@/components/Skeleton";
import { formatMoney } from "@/lib/utils";
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

function ReviewWorkspace() {
  const { t } = useTranslation();
  const { data, error, isLoading, mutate } = useSWR<{ items: ReviewItem[] }>(
    "/product/review-items",
    getReviewItems,
  );

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

  const items = data?.items ?? [];

  if (items.length === 0) {
    return (
      <EmptyState
        icon="✅"
        title="All clear!"
        description="No receipts need review right now."
      />
    );
  }

  return (
    <ul className="space-y-4" aria-label="Review queue">
      {items.map((item) => (
        <ReviewCard key={item.receipt_id} item={item} onDone={() => mutate()} />
      ))}
    </ul>
  );
}

function ReviewCard({ item, onDone }: { item: ReviewItem; onDone: () => void }) {
  const [saving, setSaving] = React.useState(false);
  const [message, setMessage] = React.useState<string | null>(null);
  const [imageUrl, setImageUrl] = React.useState<string | null>(null);
  const weak = isWeakMatch(item);

  React.useEffect(() => {
    let cancelled = false;
    getReceiptImage(item.receipt_id)
      .then((blob) => {
        if (!cancelled) setImageUrl(URL.createObjectURL(blob));
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [item.receipt_id]);

  async function complete() {
    setSaving(true);
    setMessage(null);
    try {
      await correctReceipt(
        item.receipt_id,
        { changes: {}, action: "complete" },
        item.version,
      );
      setMessage("Marked as complete.");
      onDone();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Failed to complete.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <li className="card overflow-hidden">
      <div className="grid gap-0 lg:grid-cols-2">
        <div className="bg-slate-100 dark:bg-slate-950">
          {imageUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={imageUrl}
              alt={`Receipt under review from ${item.receipt.vendor || "unknown vendor"}`}
              className="h-64 w-full object-contain lg:h-full"
              loading="lazy"
            />
          ) : (
            <div className="flex h-64 items-center justify-center text-sm text-slate-400">
              Image unavailable
            </div>
          )}
        </div>
        <div className="p-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                {item.receipt.vendor || "Unknown vendor"}
              </h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                {item.receipt.date ?? "No date"} · v{item.version}
              </p>
            </div>
            <StatusBadge status="needs_review" />
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <ConfidenceBadge
              value={
                Object.values(item.receipt.confidence ?? {}).length
                  ? Object.values(item.receipt.confidence ?? {}).reduce((a, b) => a + b, 0) /
                    Object.values(item.receipt.confidence ?? {}).length
                  : 0
              }
            />
            <span className="text-sm text-slate-500 dark:text-slate-400">
              {item.receipt.line_items?.length ?? 0} line items
            </span>
            {item.receipt.confidence_level ? (
              <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
                {item.receipt.confidence_level} confidence
              </span>
            ) : null}
          </div>
          {weak ? (
            <div
              role="alert"
              className="mt-3 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200"
            >
              ⚠️ Uncertain amount — please verify the total against the receipt
              image before confirming. A misread total would corrupt your
              spending history.
            </div>
          ) : null}
          <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-400">Total</dt>
              <dd className="mt-0.5 text-lg font-semibold text-slate-900 dark:text-slate-100">
                {formatMoney(item.receipt.total, item.receipt.currency)}
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-400">Tax</dt>
              <dd className="mt-0.5 text-slate-700 dark:text-slate-200">
                {formatMoney(item.receipt.tax, item.receipt.currency)}
              </dd>
            </div>
          </dl>
          <div className="mt-5 flex flex-wrap items-center gap-2">
            <Link href={`/receipts/${item.receipt_id}`} className="btn-secondary text-sm">
              Open full detail
            </Link>
            <button
              type="button"
              onClick={complete}
              disabled={saving}
              className="btn-primary text-sm"
            >
              {saving ? "Saving…" : weak ? "✓ Confirm amount — complete" : "✓ Looks good — complete"}
            </button>
            {message ? (
              <span className="text-xs text-emerald-600 dark:text-emerald-400" role="status">
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
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Receipts where OCR confidence was low — verify and confirm.
        </p>
      </div>
      <ReviewWorkspace />
    </div>
  );
}
