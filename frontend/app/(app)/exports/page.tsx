"use client";

import { useState } from "react";
import useSWR from "swr";
import { createConnection, getConnections, getExportRuns, testConnection } from "@/lib/api";
import type { Connection, ExportRun } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import Modal from "@/components/Modal";
import { SkeletonCard } from "@/components/Skeleton";
import { formatDateTime } from "@/lib/utils";

export default function ExportsPage() {
  const { data: connectionsData, error: connectionsError, isLoading: connectionsLoading, mutate: mutateConnections } = useSWR<{ items: Connection[] }>(
    "/product/connections",
    getConnections,
  );
  const { data: runsData } = useSWR<{ items: ExportRun[] }>("/product/export-runs", getExportRuns);
  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState("");
  const [provider, setProvider] = useState("csv");
  const [testing, setTesting] = useState<string | null>(null);

  const connections = connectionsData?.items ?? [];
  const runs = runsData?.items ?? [];

  async function create() {
    await createConnection({ name: name || "My connection", provider, mapping: {} });
    setCreateOpen(false);
    setName("");
    mutateConnections();
  }

  async function test(connectionId: string) {
    setTesting(connectionId);
    try {
      await testConnection(connectionId);
    } finally {
      setTesting(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Export Center</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            CSV, QuickBooks and Xero connections plus export history.
          </p>
        </div>
        <button type="button" onClick={() => setCreateOpen(true)} className="btn-primary text-sm">
          + New connection
        </button>
      </div>

      <section aria-label="Connections">
        <h2 className="mb-3 text-base font-semibold text-slate-900 dark:text-slate-100">Connections</h2>
        {connectionsLoading ? (
          <SkeletonCard className="h-32" />
        ) : connectionsError ? (
          <EmptyState icon="⚠️" title="Could not load connections" description="Check that the backend is running." />
        ) : connections.length === 0 ? (
          <EmptyState icon="🔌" title="No connections yet" description="Create a CSV, QuickBooks or Xero connection to export receipts." />
        ) : (
          <ul className="grid gap-4 sm:grid-cols-2" aria-label="Connections">
            {connections.map((connection) => (
              <li key={connection.connection_id} className="card p-5">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <h3 className="font-semibold text-slate-900 dark:text-slate-100">{connection.name}</h3>
                    <p className="text-sm capitalize text-slate-500 dark:text-slate-400">{connection.provider}</p>
                  </div>
                  <span
                    className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                      connection.active
                        ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                        : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400"
                    }`}
                  >
                    {connection.active ? "Active" : "Inactive"}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => test(connection.connection_id)}
                  disabled={testing === connection.connection_id}
                  className="btn-secondary mt-4 text-sm"
                >
                  {testing === connection.connection_id ? "Testing…" : "🔍 Test connection"}
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-label="Export history">
        <h2 className="mb-3 text-base font-semibold text-slate-900 dark:text-slate-100">Export history</h2>
        {runs.length === 0 ? (
          <EmptyState icon="📦" title="No exports yet" description="Export runs will appear here." />
        ) : (
          <ul className="card divide-y divide-slate-100 dark:divide-slate-800">
            {runs.map((run) => (
              <li key={run.export_id} className="flex items-center justify-between gap-3 px-5 py-3 text-sm">
                <span className="font-medium text-slate-800 dark:text-slate-100">{run.format}</span>
                <span className="text-slate-500 dark:text-slate-400">{run.status}</span>
                <span className="text-slate-400">{formatDateTime(run.created_at)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <Modal
        open={createOpen}
        title="New connection"
        onClose={() => setCreateOpen(false)}
        footer={
          <>
            <button type="button" onClick={() => setCreateOpen(false)} className="btn-secondary text-sm">Cancel</button>
            <button type="button" onClick={create} className="btn-primary text-sm">Create connection</button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label htmlFor="conn-name" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">Name</label>
            <input id="conn-name" className="input" value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Accounting export" />
          </div>
          <div>
            <label htmlFor="conn-provider" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">Provider</label>
            <select id="conn-provider" className="input" value={provider} onChange={(event) => setProvider(event.target.value)}>
              <option value="csv">CSV</option>
              <option value="quickbooks">QuickBooks</option>
              <option value="xero">Xero</option>
            </select>
          </div>
        </div>
      </Modal>
    </div>
  );
}
