"use client";

import { useState } from "react";
import useSWR from "swr";
import { searchReceipts, validateReceipt } from "@/lib/api";
import type { ReceiptItem, ValidationResult } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { SkeletonCard } from "@/components/Skeleton";
import { formatMoney } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

export default function AccountingPage() {
  const { t } = useTranslation();
  const { data, error, isLoading } = useSWR("/product/receipts?limit=100", () =>
    searchReceipts({ limit: 100 }),
  );
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data: validation, isLoading: validationLoading } = useSWR<ValidationResult | null>(
    selectedId ? `/validation/${selectedId}` : null,
    () => validateReceipt(selectedId as string),
  );

  const items: ReceiptItem[] = data?.items ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("accounting")}</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {t("exportReadinessDesc")}
        </p>
      </div>

      {isLoading ? (
        <SkeletonCard className="h-64" />
      ) : error ? (
        <EmptyState icon="⚠️" title={t("couldNotLoad")} description={t("error")} />
      ) : items.length === 0 ? (
        <EmptyState icon="📄" title={t("noReceipts")} description={t("noReceiptsHint")} action={{ label: t("uploadFirst"), href: "/upload" }} />
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="card overflow-x-auto" aria-label={t("receipts")}>
            <table className="w-full min-w-[420px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-slate-800 dark:text-slate-400">
                  <th className="px-4 py-3">{t("merchant")}</th>
                  <th className="px-4 py-3 text-right">{t("total")}</th>
                  <th className="px-4 py-3">{t("status")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {items.map((item) => (
                  <tr
                    key={item.receipt_id}
                    onClick={() => setSelectedId(item.receipt_id)}
                    className={`cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-900 ${
                      selectedId === item.receipt_id ? "bg-brand-50 dark:bg-brand-950" : ""
                    }`}
                  >
                    <td className="px-4 py-3 font-medium text-slate-800 dark:text-slate-100">
                      {item.receipt.vendor || t("unknownVendor")}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-600 dark:text-slate-300">
                      {formatMoney(item.receipt.total, item.receipt.currency)}
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={item.readiness?.state ?? item.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="card p-5" aria-label="Validation result">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              {t("validationTitle")}
            </h2>
            {!selectedId ? (
              <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">
                {t("selectReceiptHint")}
              </p>
            ) : validationLoading ? (
              <p className="mt-4 text-sm text-slate-400">{t("loadingValidation")}</p>
            ) : validation ? (
              <div className="mt-4 space-y-4">
                <StatusBadge status={validation.readiness} />
                {validation.errors.length > 0 ? (
                  <div>
                    <h3 className="text-sm font-semibold text-rose-600 dark:text-rose-400">{t("errorsHeader")}</h3>
                    <ul className="mt-1 space-y-1">
                      {validation.errors.map((err, index) => (
                        <li key={index} className="text-sm text-rose-600 dark:text-rose-400">• {err.message}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {validation.warnings.length > 0 ? (
                  <div>
                    <h3 className="text-sm font-semibold text-amber-600 dark:text-amber-400">{t("warningsHeader")}</h3>
                    <ul className="mt-1 space-y-1">
                      {validation.warnings.map((warn, index) => (
                        <li key={index} className="text-sm text-amber-600 dark:text-amber-400">• {warn.message}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {validation.errors.length === 0 && validation.warnings.length === 0 ? (
                  <p className="text-sm text-emerald-600 dark:text-emerald-400">
                    ✓ {t("readyForExport")}
                  </p>
                ) : null}
              </div>
            ) : (
              <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">{t("noValidationResult")}</p>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
