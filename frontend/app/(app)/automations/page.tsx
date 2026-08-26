"use client";

import { useState } from "react";
import useSWR from "swr";
import { createRule, getRules, previewRule } from "@/lib/api";
import type { AutomationRule } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import Modal from "@/components/Modal";
import { SkeletonCard } from "@/components/Skeleton";
import { useTranslation } from "@/lib/i18n";

export default function AutomationsPage() {
  const { t } = useTranslation();
  const { data, error, isLoading, mutate } = useSWR<{ items: AutomationRule[] }>(
    "/product/automation-rules",
    getRules,
  );
  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState("");
  const [conditionKey, setConditionKey] = useState("vendor");
  const [conditionValue, setConditionValue] = useState("");
  const [saving, setSaving] = useState(false);

  const rules = data?.items ?? [];

  async function create() {
    setSaving(true);
    try {
      await createRule({
        name: name || "New rule",
        conditions: { [conditionKey]: conditionValue },
        actions: { categorize_as: "auto" },
        priority: 0,
      });
      setCreateOpen(false);
      setName("");
      setConditionValue("");
      mutate();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("automations")}</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Rules that run automatically when a receipt is uploaded.
          </p>
        </div>
        <button type="button" onClick={() => setCreateOpen(true)} className="btn-primary text-sm">
          + New rule
        </button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          <SkeletonCard className="h-32" />
          <SkeletonCard className="h-32" />
        </div>
      ) : error ? (
        <EmptyState icon="⚠️" title="Could not load rules" description="Check that the backend is running." />
      ) : rules.length === 0 ? (
        <EmptyState
          icon="⚡"
          title="No rules yet"
          description="Create rules to automate categorization and tagging."
        />
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2" aria-label="Automation rules">
          {rules.map((rule) => (
            <li key={rule.rule_id} className="card p-5">
              <div className="flex items-center justify-between gap-3">
                <h2 className="font-semibold text-slate-900 dark:text-slate-100">{rule.name}</h2>
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                    rule.active
                      ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                      : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400"
                  }`}
                >
                  {rule.active ? "Active" : "Inactive"}
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Priority {rule.priority} · conditions:{" "}
                <code className="rounded bg-slate-100 px-1 py-0.5 text-xs dark:bg-slate-800">
                  {JSON.stringify(rule.conditions)}
                </code>
              </p>
            </li>
          ))}
        </ul>
      )}

      <Modal
        open={createOpen}
        title="Create automation rule"
        onClose={() => setCreateOpen(false)}
        footer={
          <>
            <button type="button" onClick={() => setCreateOpen(false)} className="btn-secondary text-sm">
              Cancel
            </button>
            <button type="button" onClick={create} disabled={saving} className="btn-primary text-sm">
              {saving ? "Creating…" : "Create rule"}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label htmlFor="rule-name" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
              Rule name
            </label>
            <input id="rule-name" className="input" value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Grocery stores → Groceries" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="rule-key" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
                Field
              </label>
              <select id="rule-key" className="input" value={conditionKey} onChange={(event) => setConditionKey(event.target.value)}>
                <option value="vendor">vendor</option>
                <option value="category">category</option>
                <option value="currency">currency</option>
              </select>
            </div>
            <div>
              <label htmlFor="rule-value" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
                Matches
              </label>
              <input id="rule-value" className="input" value={conditionValue} onChange={(event) => setConditionValue(event.target.value)} placeholder="e.g. Lidl" />
            </div>
          </div>
          <button
            type="button"
            className="text-sm font-medium text-brand-600 hover:underline dark:text-brand-400"
            onClick={async () => {
              const result = await previewRule({ [conditionKey]: conditionValue }).catch(() => null);
              if (result) alert(`Preview: ${JSON.stringify(result.matching_receipts)}`);
            }}
          >
            🔍 Preview matching receipts
          </button>
        </div>
      </Modal>
    </div>
  );
}
