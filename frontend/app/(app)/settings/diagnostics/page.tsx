"use client";

import useSWR from "swr";
import { downloadDiagnostics, getDiagnostics } from "@/lib/api";
import type { Diagnostics } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import { useTranslation } from "@/lib/i18n";

export default function DiagnosticsSettingsPage() {
  const { t } = useTranslation();
  const { data, error, isLoading } = useSWR<Diagnostics>("/product/diagnostics", getDiagnostics);

  async function download() {
    const blob = await downloadDiagnostics();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "receiptlens-diagnostics.zip";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (isLoading) return <SkeletonCard className="h-48" />;

  if (error || !data) {
    return <EmptyState icon="⚠️" title={t("couldNotLoad")} description={t("error")} />;
  }

  const rows: Array<[string, string | number | boolean]> = [
    [t("versionLabel"), data.version],
    [t("databaseLabel"), data.database],
    [t("receiptCountLabel"), data.receipt_count],
    [t("failedJobsLabel"), data.failed_jobs],
    [t("pwaLabel"), data.pwa ? "enabled" : "disabled"],
    [t("ocrEngineLabel"), data.ocr],
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Diagnostics</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Backend health and version information.
        </p>
      </div>

      <section className="card max-w-lg" aria-label="Diagnostics">
        <dl className="divide-y divide-slate-100 dark:divide-slate-800">
          {rows.map(([label, value]) => (
            <div key={label} className="flex items-center justify-between px-5 py-3 text-sm">
              <dt className="text-slate-500 dark:text-slate-400">{label}</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">{String(value)}</dd>
            </div>
          ))}
        </dl>
      </section>

      <button type="button" onClick={download} className="btn-primary text-sm">
        ⬇ {t("downloadDiagnosticsBundle")}
      </button>
    </div>
  );
}
