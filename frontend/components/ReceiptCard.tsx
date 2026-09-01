import Link from "next/link";
import type { ReceiptItem } from "@/lib/types";
import ConvertedMoney from "@/components/ConvertedMoney";
import StatusBadge from "@/components/StatusBadge";
import ConfidenceBadge from "@/components/ConfidenceBadge";
import { formatDate } from "@/lib/utils";

interface ReceiptCardProps {
  item: ReceiptItem;
}

/** Receipt list/grid card — vendor, date, total, status and confidence. */
export default function ReceiptCard({ item }: ReceiptCardProps) {
  const { receipt, receipt_id } = item;
  return (
    <Link
      href={`/receipts/${receipt_id}`}
      className="block rounded-xl border border-slate-200 bg-white p-4 shadow-card transition-shadow hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate font-semibold text-slate-900 dark:text-slate-100">
            {receipt.vendor || "Unknown vendor"}
          </h3>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            {formatDate(receipt.date)} · {item.status.replace(/_/g, " ")}
          </p>
        </div>
        <StatusBadge status={item.status} />
      </div>
      <div className="mt-3 flex items-center justify-between">
        <span className="text-lg font-semibold text-slate-900 dark:text-slate-100"><ConvertedMoney amount={receipt.total} currency={receipt.currency} /></span>
        {receipt.confidence && Object.keys(receipt.confidence).length > 0 ? (
          <ConfidenceBadge
            value={Math.min(...Object.values(receipt.confidence).filter((v) => v > 0), 1)}
          />
        ) : null}
      </div>
      {receipt.category ? (
        <p className="mt-2 inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          {receipt.category}
        </p>
      ) : null}
    </Link>
  );
}
