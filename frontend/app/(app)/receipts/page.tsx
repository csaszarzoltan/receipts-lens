"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import useSWR from "swr";
import { searchReceipts } from "@/lib/api";
import type { ReceiptItem } from "@/lib/types";
import ReceiptCard from "@/components/ReceiptCard";
import FilterBar from "@/components/FilterBar";
import Pagination from "@/components/Pagination";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import StatusBadge from "@/components/StatusBadge";
import { formatDate, formatMoney } from "@/lib/utils";

const STATUS_OPTIONS = [
  { value: "needs_review", label: "Needs review" },
  { value: "completed", label: "Completed" },
  { value: "pending", label: "Pending" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "failed", label: "Failed" },
];

function ReceiptsContent() {
  const searchParams = useSearchParams();
  const [query, setQuery] = useState(searchParams.get("q") ?? "");
  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [offset, setOffset] = useState(0);
  const [limit] = useState(50);

  // Debounce the search box so typing doesn't hammer the API.
  const [debouncedQuery, setDebouncedQuery] = useState(query);
  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query), 300);
    return () => window.clearTimeout(timer);
  }, [query]);

  const { data, error, isLoading } = useSWR(
    `/product/receipts?q=${debouncedQuery}&status=${status}&offset=${offset}`,
    () => searchReceipts({ query: debouncedQuery || undefined, status: status || undefined, limit, offset }),
  );

  const items: ReceiptItem[] = data?.items ?? [];

  // Category/date filters are applied client-side on top of the API search
  // (the backend exposes query/status/tag/total filters natively).
  const filtered = useMemo(() => {
    return items.filter((item) => {
      if (category && item.receipt.category !== category) return false;
      if (dateFrom && (item.receipt.date ?? "") < dateFrom) return false;
      if (dateTo && (item.receipt.date ?? "") > dateTo) return false;
      return true;
    });
  }, [items, category, dateFrom, dateTo]);

  const categories = useMemo(() => {
    const set = new Set<string>();
    items.forEach((item) => {
      if (item.receipt.category) set.add(item.receipt.category);
    });
    return Array.from(set).sort();
  }, [items]);

  const resetFilters = () => {
    setQuery("");
    setStatus("");
    setCategory("");
    setDateFrom("");
    setDateTo("");
    setOffset(0);
  };

  const hasFilters = Boolean(query || status || category || dateFrom || dateTo);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Receipts</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {data?.total != null ? `${data.total} receipts` : "Search your receipts"}
          </p>
        </div>
        <a href="/upload" className="btn-primary">
          ⬆ Upload
        </a>
      </div>

      <FilterBar
        query={query}
        onQueryChange={(value) => {
          setQuery(value);
          setOffset(0);
        }}
        searchPlaceholder="Search by merchant…"
        filters={[
          {
            name: "status",
            label: "Status",
            value: status,
            onChange: (value) => {
              setStatus(value);
              setOffset(0);
            },
            options: STATUS_OPTIONS,
            allLabel: "All statuses",
          },
          {
            name: "category",
            label: "Category",
            value: category,
            onChange: (value) => {
              setCategory(value);
              setOffset(0);
            },
            options: categories.map((value) => ({ value, label: value })),
            allLabel: "All categories",
          },
        ]}
      />

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3">
        <div className="md:col-span-1">
          <label htmlFor="filter-date-from" className="sr-only">Date from</label>
          <input
            id="filter-date-from"
            type="date"
            value={dateFrom}
            onChange={(event) => {
              setDateFrom(event.target.value);
              setOffset(0);
            }}
            className="input"
          />
        </div>
        <div className="md:col-span-1">
          <label htmlFor="filter-date-to" className="sr-only">Date to</label>
          <input
            id="filter-date-to"
            type="date"
            value={dateTo}
            onChange={(event) => {
              setDateTo(event.target.value);
              setOffset(0);
            }}
            className="input"
          />
        </div>
        {hasFilters ? (
          <div className="flex items-center">
            <button type="button" onClick={resetFilters} className="text-sm font-medium text-brand-600 hover:underline dark:text-brand-400">
              ✕ Clear filters
            </button>
          </div>
        ) : null}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <SkeletonCard key={index} />
          ))}
        </div>
      ) : error ? (
        <EmptyState
          icon="⚠️"
          title="Could not load receipts"
          description="The backend may be offline. Check the server and retry."
        />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon="📄"
          title={hasFilters ? "No matching receipts" : "No receipts yet"}
          description={
            hasFilters
              ? "Try adjusting your search or filters."
              : "Upload your first receipt to get started."
          }
          action={hasFilters ? undefined : { label: "Upload a receipt", href: "/upload" }}
        />
      ) : (
        <>
          <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-label="Receipt list">
            {filtered.map((item) => (
              <li key={item.receipt_id}>
                <ReceiptCard item={item} />
              </li>
            ))}
          </ul>
          {data && data.total > limit ? (
            <Pagination
              total={data.total}
              offset={offset}
              limit={limit}
              onPageChange={setOffset}
            />
          ) : null}
        </>
      )}

      {/* Table view for desktop power users */}
      {filtered.length > 0 ? (
        <section className="card overflow-x-auto" aria-label="Receipt table">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-slate-800 dark:text-slate-400">
                <th className="px-4 py-3">Merchant</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3 text-right">Total</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {filtered.slice(0, 10).map((item) => (
                <tr key={item.receipt_id} className="hover:bg-slate-50 dark:hover:bg-slate-900">
                  <td className="px-4 py-3">
                    <a href={`/receipts/${item.receipt_id}`} className="font-medium text-brand-600 hover:underline dark:text-brand-400">
                      {item.receipt.vendor || "Unknown vendor"}
                    </a>
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{formatDate(item.receipt.date)}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.receipt.category ?? "—"}</td>
                  <td className="px-4 py-3 text-right font-medium text-slate-900 dark:text-slate-100">
                    {formatMoney(item.receipt.total, item.receipt.currency)}
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={item.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}
    </div>
  );
}

export default function ReceiptsPage() {
  return (
    <Suspense fallback={<SkeletonCard className="h-64" />}>
      <ReceiptsContent />
    </Suspense>
  );
}
