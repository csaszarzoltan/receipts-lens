"use client";

import { cx } from "@/lib/utils";

interface PaginationProps {
  total: number;
  offset: number;
  limit: number;
  onPageChange: (offset: number) => void;
}

function pageCount(total: number, limit: number): number {
  return Math.max(1, Math.ceil(total / Math.max(1, limit)));
}

/** Reusable pagination controls for list views. */
export default function Pagination({ total, offset, limit, onPageChange }: PaginationProps) {
  const pages = pageCount(total, limit);
  const current = Math.floor(offset / limit) + 1;
  if (pages <= 1) return null;

  const go = (page: number) => onPageChange((page - 1) * limit);
  const button =
    "inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-white dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800 dark:disabled:hover:bg-slate-900";

  return (
    <nav
      className="flex flex-wrap items-center justify-between gap-3"
      aria-label="Pagination"
    >
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Showing {Math.min(offset + 1, total)}–{Math.min(offset + limit, total)} of {total}
      </p>
      <div className="flex items-center gap-2">
        <button
          type="button"
          className={button}
          onClick={() => go(current - 1)}
          disabled={current <= 1}
          aria-label="Previous page"
        >
          ←
        </button>
        <span className="px-2 text-sm text-slate-600 dark:text-slate-300" aria-live="polite">
          Page {current} of {pages}
        </span>
        <button
          type="button"
          className={button}
          onClick={() => go(current + 1)}
          disabled={current >= pages}
          aria-label="Next page"
        >
          →
        </button>
      </div>
    </nav>
  );
}
