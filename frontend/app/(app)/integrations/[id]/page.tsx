"use client";

import { useState } from "react";
import useSWR from "swr";
import Link from "next/link";
import {
  disconnectProviderConnection,
  getExportRuns,
  getProviderConnection,
  refreshProviderConnection,
} from "@/lib/api";
import type { ExportRun, ProviderConnection } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import WorkflowState from "@/components/WorkflowState";
import { SkeletonCard } from "@/components/Skeleton";
import { formatDateTime } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

export default function ConnectionDetailPage({ params }: { params: { id: string } }) {
  const { t } = useTranslation();
  const { data, error, isLoading, mutate } = useSWR(
    `/product/provider-connections/${params.id}`,
    () => getProviderConnection(params.id),
  );
  const { data: runsData, isLoading: runsLoading } = useSWR<{ items: ExportRun[] }>(
    "/product/export-runs",
    getExportRuns,
  );
  const [busy, setBusy] = useState<"refresh" | "disconnect" | null>(null);
  const [notice, setNotice] = useState("");

  const runs = runsData?.items ?? [];

  async function refresh() {
    setBusy("refresh");
    setNotice("");
    try {
      const result = await refreshProviderConnection(params.id);
      setNotice(
        result.status === "refreshed" ? t("tokenRefreshed") : t("tokenStillValid"),
      );
      mutate();
    } catch (e) {
      setNotice(e instanceof Error ? e.message : t("refreshFailed"));
    } finally {
      setBusy(null);
    }
  }

  async function disconnect() {
    if (!window.confirm(t("disconnectConfirm"))) return;
    setBusy("disconnect");
    setNotice("");
    try {
      await disconnectProviderConnection(params.id);
      setNotice(t("disconnectedNotice"));
      mutate();
    } catch (e) {
      setNotice(e instanceof Error ? e.message : t("disconnectFailed"));
    } finally {
      setBusy(null);
    }
  }

  if (isLoading) return <SkeletonCard className="h-40" />;
  if (error) {
    return (
      <WorkflowState
        kind="error"
        title="Connection unavailable"
        description="The connection could not be loaded."
      />
    );
  }
  if (!data) return null;

  const connection = data;
  const healthy = connection.health === "healthy" && !connection.reauthorization_required;

  return (
    <main className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            <Link href="/integrations" className="hover:underline">{t("integrations")}</Link> / {connection.provider}
          </p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">
            {connection.provider_company_name || connection.provider}
          </h1>
        </div>
        <span
          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
            healthy
              ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
              : "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
          }`}
        >
          {healthy ? t("healthyStatus") : connection.reauthorization_required ? t("reauthRequired") : connection.health}
        </span>
      </div>

      <dl className="card grid gap-4 p-5 sm:grid-cols-2">
        <div>
          <dt className="text-sm text-slate-500 dark:text-slate-400">{t("connectionIdLabel")}</dt>
          <dd className="break-all font-mono text-sm">{connection.connection_id}</dd>
        </div>
        <div>
          <dt className="text-sm text-slate-500 dark:text-slate-400">{t("quickBooksCompany")}</dt>
          <dd className="text-sm">{connection.provider_company_id}</dd>
        </div>
        <div>
          <dt className="text-sm text-slate-500 dark:text-slate-400">{t("connectedLabel")}</dt>
          <dd className="text-sm">{formatDateTime(connection.created_at)}</dd>
        </div>
        <div>
          <dt className="text-sm text-slate-500 dark:text-slate-400">{t("lastTestedLabel")}</dt>
          <dd className="text-sm">{connection.last_tested_at ? formatDateTime(connection.last_tested_at) : t("neverLabel")}</dd>
        </div>
      </dl>

      <div className="flex flex-wrap gap-3">
        <button type="button" onClick={refresh} disabled={busy !== null} className="btn-secondary text-sm">
          {busy === "refresh" ? t("refreshingLabel") : t("refreshToken")}
        </button>
        <button type="button" onClick={disconnect} disabled={busy !== null} className="btn-secondary text-sm text-rose-700 dark:text-rose-300">
          {busy === "disconnect" ? t("disconnectingLabel") : t("disconnectQB")}
        </button>
      </div>
      {notice ? <p role="status" className="text-sm text-slate-600 dark:text-slate-300">{notice}</p> : null}

      <section aria-label="Run history">
        <h2 className="mb-3 text-base font-semibold text-slate-900 dark:text-slate-100">{t("runHistory")}</h2>
        {runsLoading ? (
          <SkeletonCard className="h-24" />
        ) : runs.length === 0 ? (
          <EmptyState icon="📦" title={t("noExportsYet")} description={t("noExportsHint")} />
        ) : (
          <ul className="card divide-y divide-slate-100 dark:divide-slate-800">
            {runs
              .filter((run) => run.export_id)
              .map((run) => (
                <li key={run.export_id} className="flex items-center justify-between gap-3 px-5 py-3 text-sm">
                  <span className="font-medium text-slate-800 dark:text-slate-100">{run.format}</span>
                  <span className="text-slate-500 dark:text-slate-400">{run.status}</span>
                  <span className="text-slate-400">{formatDateTime(run.created_at)}</span>
                </li>
              ))}
          </ul>
        )}
      </section>
    </main>
  );
}
