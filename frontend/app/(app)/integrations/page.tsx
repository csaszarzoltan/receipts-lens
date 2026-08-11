"use client";

import { useState } from "react";
import useSWR from "swr";
import { createConnection, getConnections, testConnection } from "@/lib/api";
import type { Connection } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import Modal from "@/components/Modal";
import { SkeletonCard } from "@/components/Skeleton";

const PROVIDERS = [
  { value: "csv", label: "CSV", icon: "📄" },
  { value: "quickbooks", label: "QuickBooks", icon: "🏦" },
  { value: "xero", label: "Xero", icon: "🧾" },
];

export default function IntegrationsPage() {
  const { data, error, isLoading, mutate } = useSWR<{ items: Connection[] }>(
    "/product/connections",
    getConnections,
  );
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [provider, setProvider] = useState("csv");
  const [testing, setTesting] = useState<string | null>(null);

  const connections = data?.items ?? [];

  async function create() {
    await createConnection({ name: name || "New connection", provider, mapping: {} });
    setOpen(false);
    setName("");
    mutate();
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
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Integrations</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Connect ReceiptLens to your accounting tools.
          </p>
        </div>
        <button type="button" onClick={() => setOpen(true)} className="btn-primary text-sm">+ Add integration</button>
      </div>

      <section className="card overflow-hidden" aria-labelledby="qbo-heading">
        <div className="border-b border-slate-200 bg-gradient-to-r from-emerald-50 to-cyan-50 p-5 dark:border-slate-800 dark:from-emerald-950/40 dark:to-cyan-950/30">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div><p className="text-xs font-semibold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">Recommended next step</p><h2 id="qbo-heading" className="mt-1 text-xl font-bold text-slate-900 dark:text-white">QuickBooks Online sandbox</h2><p className="mt-1 max-w-2xl text-sm text-slate-600 dark:text-slate-300">Connect a sandbox company, validate account and tax mappings, then export with replay protection and reconciliation evidence.</p></div>
            <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700 shadow-sm dark:bg-slate-900 dark:text-slate-200">Not connected</span>
          </div>
        </div>
        <div className="grid gap-4 p-5 md:grid-cols-3">
          {[['1','Connect company','OAuth state is tenant-bound and credentials are encrypted.'],['2','Validate mapping','Choose expense accounts and tax treatment before posting.'],['3','Export and verify','Retry only failed items and compare the remote purchase.']].map(([n,title,body])=><div key={n} className="rounded-xl border border-slate-200 p-4 dark:border-slate-700"><span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-sm font-bold text-brand-700 dark:bg-brand-950 dark:text-brand-300">{n}</span><h3 className="mt-3 font-semibold">{title}</h3><p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{body}</p></div>)}
        </div>
        <div className="flex flex-wrap items-center gap-3 border-t border-slate-200 px-5 py-4 dark:border-slate-800"><button type="button" className="btn-primary text-sm" aria-describedby="qbo-disclosure">Connect QuickBooks</button><p id="qbo-disclosure" className="text-xs text-slate-500">Sandbox only. You will review requested accounting scopes before leaving ReceiptLens.</p></div>
      </section>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <SkeletonCard className="h-32" />
          <SkeletonCard className="h-32" />
        </div>
      ) : error ? (
        <EmptyState icon="⚠️" title="Could not load integrations" description="Check that the backend is running." />
      ) : connections.length === 0 ? (
        <EmptyState icon="🔌" title="No integrations yet" description="Add a CSV, QuickBooks or Xero connection to get started." />
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-label="Integrations">
          {connections.map((connection) => (
            <li key={connection.connection_id} className="card p-5">
              <div className="flex items-center gap-3">
                <span className="text-2xl" aria-hidden="true">
                  {PROVIDERS.find((p) => p.value === connection.provider)?.icon ?? "🔌"}
                </span>
                <div>
                  <h2 className="font-semibold text-slate-900 dark:text-slate-100">{connection.name}</h2>
                  <p className="text-sm capitalize text-slate-500 dark:text-slate-400">{connection.provider}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => test(connection.connection_id)}
                disabled={testing === connection.connection_id}
                className="btn-secondary mt-4 w-full text-sm"
              >
                {testing === connection.connection_id ? "Testing…" : "Test connection"}
              </button>
            </li>
          ))}
        </ul>
      )}

      <Modal
        open={open}
        title="Add integration"
        onClose={() => setOpen(false)}
        footer={
          <>
            <button type="button" onClick={() => setOpen(false)} className="btn-secondary text-sm">Cancel</button>
            <button type="button" onClick={create} className="btn-primary text-sm">Add</button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label htmlFor="int-name" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">Name</label>
            <input id="int-name" className="input" value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. My accountant" />
          </div>
          <div role="radiogroup" aria-label="Provider">
            <p className="mb-2 text-sm font-medium text-slate-700 dark:text-slate-200">Provider</p>
            <div className="grid grid-cols-3 gap-2">
              {PROVIDERS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  role="radio"
                  aria-checked={provider === option.value}
                  onClick={() => setProvider(option.value)}
                  className={`flex min-h-20 flex-col items-center justify-center gap-1 rounded-lg border text-sm font-medium transition-colors ${
                    provider === option.value
                      ? "border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300"
                      : "border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                  }`}
                >
                  <span aria-hidden="true" className="text-xl">{option.icon}</span>
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
}
