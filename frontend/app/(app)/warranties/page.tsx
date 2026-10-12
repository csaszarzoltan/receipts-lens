"use client";

import React, { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import useSWR from "swr";
import { getWarranties } from "@/lib/api";
import type { WarrantyList } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import WarrantyCard from "@/components/WarrantyCard";
import WarrantyForm from "@/components/WarrantyForm";
import { useTranslation } from "@/lib/i18n";

function WarrantiesWorkspace() {
  const { t } = useTranslation();
  const params = useSearchParams();
  const { data, error, isLoading, mutate } = useSWR<WarrantyList>("/product/warranties", getWarranties);
  // Arriving from a receipt opens the form with what that receipt already says.
  const fromReceipt = params.get("receipt");
  const [adding, setAdding] = React.useState(Boolean(fromReceipt));

  const items = data?.items ?? [];
  const active = items.filter((i) => i.status === "active");
  const closed = items.filter((i) => i.status !== "active");

  return (
    <div className="space-y-6" data-testid="warranties-page">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("warrantiesTitle")}</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{t("warrantiesDesc")}</p>
        </div>
        <button type="button" className="btn-primary text-sm" data-testid="warranties-primary-action"
                aria-expanded={adding} onClick={() => setAdding((v) => !v)}>
          {t("warrantyAdd")}
        </button>
      </div>

      {adding ? (
        <WarrantyForm
          prefill={fromReceipt ? {
            receipt_id: fromReceipt,
            merchant: params.get("merchant") ?? undefined,
            purchase_date: params.get("date") ?? undefined,
          } : undefined}
          onCancel={() => setAdding(false)}
          onSaved={() => { setAdding(false); mutate(); }}
        />
      ) : null}

      {isLoading ? (
        <SkeletonCard className="h-48" />
      ) : error ? (
        <EmptyState icon="⚠️" title={t("couldNotLoad")} description={t("error")} />
      ) : items.length === 0 && !adding ? (
        <EmptyState icon="🛡️" title={t("warrantyEmptyTitle")} description={t("warrantyEmptyDesc")} />
      ) : (
        <>
          {items.length > 0 ? (
            <p className="text-sm text-slate-700 dark:text-slate-300" role="status">
              {data && data.summary.due_soon > 0
                ? <><strong>{data.summary.due_soon}</strong> {t("warrantyItemsDue")}</>
                : t("warrantySummaryNone")}
            </p>
          ) : null}
          {active.length > 0 ? (
            <section aria-label={t("warrantySectionActive")} className="space-y-3">
              <ul className="space-y-3">
                {active.map((item) => (
                  <WarrantyCard key={item.warranty_id} item={item} onChanged={() => mutate()} />
                ))}
              </ul>
            </section>
          ) : null}
          {closed.length > 0 ? (
            <section aria-label={t("warrantySectionClosed")} className="space-y-3">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-400">
                {t("warrantySectionClosed")}
              </h2>
              <ul className="space-y-3">
                {closed.map((item) => (
                  <WarrantyCard key={item.warranty_id} item={item} onChanged={() => mutate()} />
                ))}
              </ul>
            </section>
          ) : null}
        </>
      )}
    </div>
  );
}

export default function WarrantiesPage() {
  return (
    <Suspense fallback={<SkeletonCard className="h-48" />}>
      <WarrantiesWorkspace />
    </Suspense>
  );
}
