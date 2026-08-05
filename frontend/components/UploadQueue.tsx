"use client";

import Link from "next/link";
import type { UploadQueueEntry } from "@/lib/hooks/useUpload";
import { cx } from "@/lib/utils";

interface UploadQueueProps {
  entries: UploadQueueEntry[];
  onRemove: (id: string) => void;
}

/** Upload queue — per-file progress bars and results with links to the receipt. */
export default function UploadQueue({ entries, onRemove }: UploadQueueProps) {
  if (entries.length === 0) return null;

  return (
    <ul className="space-y-3" aria-label="Upload queue">
      {entries.map((entry) => (
        <li
          key={entry.id}
          className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-slate-800 dark:text-slate-100">
                {entry.fileName}
              </p>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                {entry.status === "queued" && "Queued…"}
                {entry.status === "uploading" && `Uploading ${entry.progress}%`}
                {entry.status === "done" && "✓ OCR complete"}
                {entry.status === "error" && (
                  <span className="text-rose-600 dark:text-rose-400">{entry.error}</span>
                )}
              </p>
            </div>
            <button
              type="button"
              onClick={() => onRemove(entry.id)}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
              aria-label={`Remove ${entry.fileName}`}
            >
              ✕
            </button>
          </div>

          <div
            className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800"
            role="progressbar"
            aria-valuenow={entry.progress}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${entry.fileName} upload progress`}
          >
            <div
              className={cx(
                "h-full rounded-full transition-all duration-300",
                entry.status === "error" ? "bg-rose-500" : "bg-brand-600",
              )}
              style={{ width: `${entry.progress}%` }}
            />
          </div>

          {entry.status === "done" && entry.result ? (
            <div className="mt-3 flex flex-wrap items-center gap-3 text-sm">
              <span className="font-medium text-slate-800 dark:text-slate-100">
                {entry.result.receipt?.vendor || "Unknown vendor"}
              </span>
              <span className="text-slate-500 dark:text-slate-400">
                {entry.result.receipt?.total != null
                  ? `${entry.result.receipt.currency ?? "USD"} ${Number(entry.result.receipt.total).toFixed(2)}`
                  : "—"}
              </span>
              <Link
                href={`/receipts/${entry.result.receipt_id}`}
                className="ml-auto inline-flex min-h-9 items-center rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-700"
              >
                View receipt →
              </Link>
            </div>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
