"use client";

import { averageConfidence } from "@/lib/confidence";
import Link from "next/link";
import { categoryLabel } from "@/lib/categories";
import type { ReceiptItem } from "@/lib/types";
import ConvertedMoney from "@/components/ConvertedMoney";
import StatusBadge from "@/components/StatusBadge";
import ConfidenceBadge from "@/components/ConfidenceBadge";
import { formatDate } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

interface ReceiptCardProps {
  item: ReceiptItem;
}

/** Receipt list/grid card — vendor, date, total, status and confidence. */
export default function ReceiptCard({ item }: ReceiptCardProps) {
  const { t } = useTranslation();
  const { receipt, receipt_id } = item;
  return (
    <Link
      href={`/receipts/${receipt_id}`}
      className="block rounded-xl border border-slate-200 bg-white p-4 shadow-card transition-shadow hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="truncate font-semibold text-slate-900 dark:text-slate-100">
            {receipt.vendor || t("unknownVendorLabel")}
          </h2>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            {formatDate(receipt.date)}
          </p>
        </div>
        <StatusBadge status={item.status} />
      </div>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        {receipt.total == null ? (
          <span className="text-sm font-medium text-amber-800 dark:text-amber-300">{t("amountNotConfirmed")}</span>
        ) : (
          <span className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            <ConvertedMoney amount={receipt.total} currency={receipt.currency} />
          </span>
        )}
        {receipt.confidence && Object.keys(receipt.confidence).length > 0 ? (
          <ConfidenceBadge
            compact
            value={averageConfidence(receipt.confidence)}
          />
        ) : null}
      </div>
      {receipt.category ? (
        <p className="mt-2 inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          {categoryLabel(t, receipt.category)}
        </p>
      ) : null}
    </Link>
  );
}
