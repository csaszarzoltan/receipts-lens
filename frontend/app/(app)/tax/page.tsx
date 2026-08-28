"use client";

import { useState } from "react";
import useSWR from "swr";
import { useTranslation } from "@/lib/i18n";
import { tenantRequest } from "@/lib/api";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";

interface DeductionRow {
  tax_category: string;
  total: number;
  count: number;
}
interface DeductionSummary {
  year: number;
  locale: string;
  by_category: DeductionRow[];
  grand_total: number;
  estimated_saving: number;
}

export default function TaxPage() {
  const { t } = useTranslation();
  const [year] = useState(2026);
  const [locale, setLocale] = useState("US");
  const { data, error, isLoading } = useSWR<DeductionSummary>(
    `/api/v1/tax/deduction?year=${year}&locale=${locale}`,
    (path: string) => tenantRequest<DeductionSummary>(path),
  );
  const [downloading, setDownloading] = useState(false);
  const [proRequired, setProRequired] = useState(false);

  async function downloadPdf() {
    setDownloading(true);
    try {
      const res = await fetch(`/api/v1/tax/audit.pdf?year=${year}&locale=${locale}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("receiptlens.session") ?? ""}` },
      });
      if (res.status === 402) {
        setProRequired(true);
        return;
      }
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `tax-audit-${year}-${locale}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(false);
    }
  }

  if (isLoading) return <SkeletonCard className="h-64" />;
  if (error) {
    const msg = String((error as Error).message ?? "");
    if (msg.includes("402") || msg.toLowerCase().includes("pro required")) {
      return (
        <div className="space-y-6">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("taxTitle")}</h1>
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 dark:border-amber-800 dark:bg-amber-950">
            <p className="font-medium text-amber-800 dark:text-amber-200">{t("upgradeToPro")}</p>
            <p className="mt-1 text-sm text-amber-700 dark:text-amber-300">{t("taxDeduction")}</p>
          </div>
        </div>
      );
    }
    return <EmptyState icon="⚠️" title="Error" description={msg} />;
  }

  const summary = data;
  if (!summary || summary.by_category.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("taxTitle")}</h1>
        <p className="text-sm text-slate-500">{t("taxDeduction")}</p>
        <div className="flex gap-2">
          <select value={locale} onChange={(e) => setLocale(e.target.value)} className="input w-32" aria-label="locale">
            <option value="US">US</option>
            <option value="HU">HU</option>
          </select>
          <button type="button" onClick={downloadPdf} disabled={downloading} className="btn-primary disabled:opacity-50">
            {t("auditPdf")}
          </button>
        </div>
        {proRequired ? <p className="text-sm font-medium text-amber-700">{t("upgradeToPro")}</p> : null}
        <EmptyState icon="📄" title={t("taxDeduction")} description="No categorized receipts yet." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("taxTitle")}</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{t("taxDeduction")} — {year} ({locale})</p>
        </div>
        <div className="flex items-center gap-2">
          <select value={locale} onChange={(e) => setLocale(e.target.value)} className="input w-28" aria-label="locale">
            <option value="US">US</option>
            <option value="HU">HU</option>
          </select>
          <button type="button" onClick={downloadPdf} disabled={downloading} className="btn-primary disabled:opacity-50">
            {downloading ? "…" : t("auditPdf")}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="card p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">{t("taxDeduction")}</p>
          <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">${summary.grand_total.toFixed(2)}</p>
        </div>
        <div className="card p-4 bg-emerald-50 dark:bg-emerald-950">
          <p className="text-xs uppercase tracking-wide text-emerald-700 dark:text-emerald-300">Est. saving (25%)</p>
          <p className="mt-1 text-2xl font-bold text-emerald-700 dark:text-emerald-300">${summary.estimated_saving.toFixed(2)}</p>
        </div>
      </div>

      <section className="card overflow-hidden" aria-label={t("taxDeduction")}>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-slate-800">
              <th className="px-4 py-3">{t("taxCategory")}</th>
              <th className="px-4 py-3 text-right">Count</th>
              <th className="px-4 py-3 text-right">Total</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {summary.by_category.map((row) => (
              <tr key={row.tax_category}>
                <td className="px-4 py-3 font-medium">{row.tax_category}</td>
                <td className="px-4 py-3 text-right">{row.count}</td>
                <td className="px-4 py-3 text-right font-medium">${row.total.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      {proRequired ? <p className="text-sm font-medium text-amber-700">{t("upgradeToPro")}</p> : null}
    </div>
  );
}
