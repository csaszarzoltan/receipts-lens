"use client";

import { averageConfidence } from "@/lib/confidence";
import Link from "next/link";
import { categoryLabel } from "@/lib/categories";
import type { Approval, ReceiptItem } from "@/lib/types";
import ConvertedMoney from "@/components/ConvertedMoney";
import StatusBadge from "@/components/StatusBadge";
import ConfidenceBadge from "@/components/ConfidenceBadge";
import ReceiptThumb from "@/components/ReceiptThumb";
import { ApprovalPill } from "@/components/ApprovalTimeline";
import { formatDate } from "@/lib/utils";
import { photoForCategory } from "@/lib/photos";
import { useTranslation } from "@/lib/i18n";

interface ReceiptCardProps {
  item: ReceiptItem;
  /** Latest approval for this receipt, if one was requested. */
  approval?: Approval | null;
}

/**
 * Receipt tile: photo first, then the amount (the largest figure), merchant and date,
 * and one state pill. The approval pill replaces the receipt status once an approval exists.
 * Low OCR confidence is the only confidence signal shown here.
 */
export default function ReceiptCard({ item, approval }: ReceiptCardProps) {
  const { t } = useTranslation();
  const { receipt, receipt_id } = item;
  const confidence = averageConfidence(receipt.confidence);
  const showLowConfidence = confidence !== null && confidence < 0.6;
  return (
    <Link
      href={`/receipts/${receipt_id}`}
      className="card flex h-full flex-col overflow-hidden transition-colors hover:border-slate-300 dark:hover:border-slate-700"
    >
      <ReceiptThumb receiptId={receipt_id} fallback={photoForCategory(receipt.category)} />
      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="min-w-0">
          <h2 className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
            {receipt.vendor || t("unknownVendorLabel")}
          </h2>
          <p className="mt-0.5 truncate text-xs text-slate-500 dark:text-slate-400">
            {formatDate(receipt.date)}
            {receipt.category ? ` · ${categoryLabel(t, receipt.category)}` : null}
          </p>
        </div>
        <div className="mt-auto flex flex-wrap items-center justify-between gap-2">
          {receipt.total == null ? (
            <span className="text-sm font-semibold text-amber-800 dark:text-amber-300">{t("amountNotConfirmed")}</span>
          ) : (
            <span className="text-xl font-bold text-slate-900 dark:text-slate-100">
              <ConvertedMoney amount={receipt.total} currency={receipt.currency} />
            </span>
          )}
          {approval ? <ApprovalPill approval={approval} /> : <StatusBadge status={item.status} />}
        </div>
        {showLowConfidence ? <ConfidenceBadge compact value={confidence} /> : null}
      </div>
    </Link>
  );
}
