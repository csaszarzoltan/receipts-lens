"use client";

import { useState } from "react";
import useSWR from "swr";
import { getPermissions, updatePermissions } from "@/lib/api";
import type { PermissionMatrix } from "@/lib/types";
import { roleLabel } from "@/lib/roles";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import { useTranslation, type MessageKey } from "@/lib/i18n";

export default function PermissionsSettingsPage() {
  const { t } = useTranslation();
  const [status, setStatus] = useState<"idle" | "saved" | "error">("idle");
  const { data, error, isLoading, mutate } = useSWR<PermissionMatrix>("/product/permissions", getPermissions);

  if (isLoading) return <SkeletonCard className="h-64" />;

  if (error || !data) {
    return <EmptyState icon="⚠️" title={t("couldNotLoad")} description={t("error")} />;
  }

  const matrix = data;
  const roles = Object.keys(matrix.roles);
  const permissions = Array.from(new Set(Object.values(matrix.roles).flat())).sort();

  async function toggle(role: string, permission: string) {
    const current = matrix.roles[role] ?? [];
    const next = current.includes(permission)
      ? current.filter((item) => item !== permission)
      : [...current, permission];
    try {
      await updatePermissions({ role, permissions: next });
      setStatus("saved");
    } catch {
      setStatus("error");
    }
    mutate();
  }

  /** A plain-language name and one-line explanation; unknown keys show as they are. */
  function describe(permission: string): { name: string; hint: string | null } {
    const nameKey = `perm_${permission}` as MessageKey;
    const name = t(nameKey);
    if (name === nameKey) return { name: permission, hint: null };
    return { name, hint: t(`${nameKey}_desc` as MessageKey) };
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("permissions")}</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{t("roleAccessMatrix")}</p>
        </div>
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full min-w-[520px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-slate-800 dark:text-slate-400">
              <th className="px-4 py-3">{t("permissionHeader")}</th>
              {roles.map((role) => (
                <th key={role} className="px-4 py-3 text-center">{roleLabel(role)}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {permissions.map((permission) => (
              <tr key={permission}>
                <td className="px-4 py-2.5">
                  <span className="block font-medium text-slate-800 dark:text-slate-100">{describe(permission).name}</span>
                  {describe(permission).hint ? (
                    <span className="block text-xs text-slate-600 dark:text-slate-400">{describe(permission).hint}</span>
                  ) : null}
                </td>
                {roles.map((role) => {
                  const granted = (data.roles[role] ?? []).includes(permission);
                  return (
                    <td key={role} className="px-4 py-2.5 text-center">
                      <input
                        type="checkbox"
                        checked={granted}
                        onChange={() => toggle(role, permission)}
                        className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                        aria-label={`${describe(permission).name} — ${roleLabel(role)}`}
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p
        className={status === "error" ? "text-xs font-medium text-rose-700 dark:text-rose-300" : "text-xs text-slate-600 dark:text-slate-400"}
        role="status"
      >
        {status === "saved" ? t("permSaved") : status === "error" ? t("permSaveError") : t("changesSavedNote")}
      </p>
    </div>
  );
}
