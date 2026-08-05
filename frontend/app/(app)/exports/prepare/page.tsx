"use client";

import { useState } from "react";
import useSWR from "swr";
import { searchReceipts } from "@/lib/api";
import type { ExportPreparation, ReceiptItem } from "@/lib/types";
import { prepareExport } from "@/lib/api";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import { formatMoney } from "@/lib/utils";

export default function ExportPreparePage() {
  const { data, error, isLoading } = useSWR("/product/receipts?limit=200", () =>
    searchReceipts({ limit: 200 }),
  );
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [preparation, setPreparation] = useState<ExportPreparation | null>(null);
  const [busy, setBusy] = useState(false);

  const items: ReceiptItem[] = data?.items ?? [];

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function run() {
    setBusy(true);
    try {
      const result = await prepareExport({ receipt_ids: Array.from(selected) });
      setPreparation(result);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Prepare export</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Select receipts and validate them before exporting.
        </p>
      </div>

      {isLoading ? (
        <SkeletonCard className="h-64" />
      ) : error ? (
        <EmptyState icon="⚠️" title="Could not load receipts" description="Check that the backend is running." />
      ) : items.length === 0 ? (
        <EmptyState icon="📄" title="No receipts yet" description="Upload receipts to prepare an export." action={{ label: "Upload a receipt", href: "/upload" }} />
      ) : (
        <>
          <ul className="card divide-y divide-slate-100 dark:divide-slate-800" aria-label="Receipt selection">
            {items.map((item) => (
              <li key={item.receipt_id}>
                <label className="flex cursor-pointer items-center gap-3 px-5 py-3 hover:bg-slate-50 dark:hover:bg-slate-900">
                  <input
                    type="checkbox"
                    checked={selected.has(item.receipt_id)}
                    onChange={() => toggle(item.receipt_id)}
                    className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                  />
                  <span className="flex-1 text-sm font-medium text-slate-800 dark:text-slate-100">
                    {item.receipt.vendor || "Unknown vendor"}
                  </span>
                  <span className="text-sm text-slate-500 dark:text-slate-400">
                    {formatMoney(item.receipt.total, item.receipt.currency)}
                  </span>
                </label>
              </li>
            ))}
          </ul>

          <div className="flex items-center gap-3">
            <button type="button" onClick={run} disabled={selected.size === 0 || busy} className="btn-primary">
              {busy ? "Validating…" : `Validate ${selected.size} receipt${selected.size === 1 ? "" : "s"}`}
            </button>
            {selected.size === 0 ? (
              <span className="text-sm text-slate-400">Select at least one receipt.</span>
            ) : null}
          </div>

          {preparation ? (
            <section className="card p-5" aria-label="Preparation result">
              <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                Result: <span className="capitalize">{preparation.status}</span>
              </h2>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                {preparation.valid_ids.length} ready · {preparation.blocked.length} blocked ·{" "}
                {preparation.warnings.length} warnings
              </p>
              {preparation.blocked.length > 0 ? (
                <ul className="mt-3 space-y-1">
                  {preparation.blocked.map((blocked) => (
                    <li key={blocked.receipt_id} className="text-sm text-rose-600 dark:text-rose-400">
                      • {blocked.receipt_id}: {blocked.reason}
                    </li>
                  ))}
                </ul>
              ) : null}
              {preparation.warnings.length > 0 ? (
                <ul className="mt-2 space-y-1">
                  {preparation.warnings.map((warning) => (
                    <li key={warning.receipt_id} className="text-sm text-amber-600 dark:text-amber-400">
                      • {warning.receipt_id}: {warning.reason}
                    </li>
                  ))}
                </ul>
              ) : null}
            </section>
          ) : null}
        </>
      )}
    </div>
  );
}
