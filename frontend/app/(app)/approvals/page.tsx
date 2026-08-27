"use client";

import { useState } from "react";
import useSWR from "swr";
import { createApprovalPolicy, decideApproval, getApprovals } from "@/lib/api";
import type { Approval } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import Modal from "@/components/Modal";
import StatusBadge from "@/components/StatusBadge";
import { SkeletonCard } from "@/components/Skeleton";
import { formatDateTime, formatMoney } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

export default function ApprovalsPage() {
  const { t } = useTranslation();
  const { data, error, isLoading, mutate } = useSWR<{ items: Approval[] }>(
    "/product/approvals",
    () => getApprovals(),
  );
  const [policyOpen, setPolicyOpen] = useState(false);
  const [deciding, setDeciding] = useState<string | null>(null);
  const [policyName, setPolicyName] = useState("");
  const [policyThreshold, setPolicyThreshold] = useState("500");
  const [policySaving, setPolicySaving] = useState(false);

  async function decide(approval: Approval, decision: "approved" | "rejected") {
    setDeciding(approval.approval_id);
    try {
      await decideApproval(approval.approval_id, decision);
      mutate();
    } finally {
      setDeciding(null);
    }
  }

  async function createPolicy() {
    setPolicySaving(true);
    try {
      await createApprovalPolicy({
        name: policyName || t("defaultPolicy"),
        threshold: Number(policyThreshold) || 500,
        currency: "USD",
      });
      setPolicyOpen(false);
      setPolicyName("");
    } finally {
      setPolicySaving(false);
    }
  }

  const items = data?.items ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("approvals")}</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {t("approvalsDesc")}
          </p>
        </div>
        <button type="button" onClick={() => setPolicyOpen(true)} className="btn-secondary text-sm">
          {t("approvals")}
        </button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          <SkeletonCard className="h-40" />
          <SkeletonCard className="h-40" />
        </div>
      ) : error ? (
        <EmptyState icon="⚠️" title={t("couldNotLoad")} description={t("error")} />
      ) : items.length === 0 ? (
        <EmptyState
          icon="🎯"
          title={t("nothingPending")}
          description={t("allClear")}
        />
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2" aria-label="Approval queue">
          {items.map((approval) => (
            <li key={approval.approval_id} className="card p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="font-semibold text-slate-900 dark:text-slate-100">
                    {approval.vendor || t("unknownShort")}
                  </h2>
                  <p className="mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                    {approval.policy_name ?? approval.policy_id} · {formatDateTime(approval.created_at)}
                  </p>
                </div>
                <StatusBadge status={approval.status} />
              </div>
              <p className="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">
                {formatMoney(approval.total, approval.currency)}
              </p>
              {approval.project ? (
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Project: {approval.project}</p>
              ) : null}
              {approval.status === "pending" ? (
                <div className="mt-4 flex gap-2">
                  <button
                    type="button"
                    onClick={() => decide(approval, "approved")}
                    disabled={deciding === approval.approval_id}
                    className="btn-primary flex-1 text-sm"
                  >
                    {deciding === approval.approval_id ? "…" : t("approveLabel")}
                  </button>
                  <button
                    type="button"
                    onClick={() => decide(approval, "rejected")}
                    disabled={deciding === approval.approval_id}
                    className="btn-secondary flex-1 text-sm"
                  >
                    {t("rejectLabel")}
                  </button>
                </div>
              ) : (
                <p className="mt-4 text-xs text-slate-400">
                  {t("decidedByLabel")} {approval.decided_by ?? "system"} {t("atLabel")} {formatDateTime(approval.decided_at)}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}

      <Modal
        open={policyOpen}
        title={t("approvals")}
        onClose={() => setPolicyOpen(false)}
        footer={
          <>
            <button type="button" onClick={() => setPolicyOpen(false)} className="btn-secondary text-sm">
              Cancel
            </button>
            <button type="button" onClick={createPolicy} disabled={policySaving} className="btn-primary text-sm">
              {policySaving ? t("creatingLabel") : t("createPolicyLabel")}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label htmlFor="policy-name" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
              {t("policyNameLabel")}
            </label>
            <input
              id="policy-name"
              className="input"
              value={policyName}
              onChange={(event) => setPolicyName(event.target.value)}
              placeholder={t("highValuePlaceholder")}
            />
          </div>
          <div>
            <label htmlFor="policy-threshold" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
              {t("thresholdLabel")}
            </label>
            <input
              id="policy-threshold"
              type="number"
              min="0"
              step="1"
              className="input"
              value={policyThreshold}
              onChange={(event) => setPolicyThreshold(event.target.value)}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}
