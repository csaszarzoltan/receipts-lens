"use client";

import { useState } from "react";
import useSWR from "swr";
import { decideDuplicate, getDuplicates } from "@/lib/api";
import type { DuplicateCandidate } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import { formatMoney } from "@/lib/utils";

export default function DuplicatesPage() {
  const { data, error, isLoading, mutate } = useSWR<{ items: DuplicateCandidate[] }>(
    "/product/duplicates",
    getDuplicates,
  );
  const [busy, setBusy] = useState<string | null>(null);

  async function decide(candidate: DuplicateCandidate, decision: string) {
    setBusy(`${candidate.left_id}:${candidate.right_id}`);
    try {
      await decideDuplicate(candidate.left_id, candidate.right_id, decision);
      mutate();
    } finally {
      setBusy(null);
    }
  }

  const items = data?.items ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Ismétlődések</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Potential duplicate receipts detected by the matching engine.
        </p>
      </div>

      {isLoading ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <SkeletonCard className="h-44" />
          <SkeletonCard className="h-44" />
        </div>
      ) : error ? (
        <EmptyState icon="⚠️" title="Could not load duplicates" description="Check that the backend is running." />
      ) : items.length === 0 ? (
        <EmptyState
          icon="🔄"
          title="No duplicates found"
          description="Your receipt data looks clean."
        />
      ) : (
        <ul className="space-y-4" aria-label="Duplicate candidates">
          {items.map((candidate) => {
            const key = `${candidate.left_id}:${candidate.right_id}`;
            return (
              <li key={key} className="card p-5">
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Match confidence:{" "}
                  <span className="font-medium text-slate-700 dark:text-slate-200">
                    {Math.round(candidate.confidence * 100)}%
                  </span>
                </p>
                <div className="mt-3 grid gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-700">
                    <p className="font-medium text-slate-900 dark:text-slate-100">
                      {candidate.left.vendor || "Unknown"}
                    </p>
                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                      {candidate.left.date ?? "No date"} ·{" "}
                      {formatMoney(candidate.left.total, candidate.left.currency)}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">{candidate.left_id}</p>
                  </div>
                  <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-700">
                    <p className="font-medium text-slate-900 dark:text-slate-100">
                      {candidate.right.vendor || "Unknown"}
                    </p>
                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                      {candidate.right.date ?? "No date"} ·{" "}
                      {formatMoney(candidate.right.total, candidate.right.currency)}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">{candidate.right_id}</p>
                  </div>
                </div>
                <div className="mt-4 flex gap-2">
                  <button
                    type="button"
                    onClick={() => decide(candidate, "keep_left")}
                    disabled={busy === key}
                    className="btn-primary flex-1 text-sm"
                  >
                    Keep left, remove right
                  </button>
                  <button
                    type="button"
                    onClick={() => decide(candidate, "keep_right")}
                    disabled={busy === key}
                    className="btn-secondary flex-1 text-sm"
                  >
                    Keep right, remove left
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
