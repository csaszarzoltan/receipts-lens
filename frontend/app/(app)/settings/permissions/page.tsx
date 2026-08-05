"use client";

import { useState } from "react";
import useSWR from "swr";
import { getPermissions, updatePermissions } from "@/lib/api";
import type { PermissionMatrix } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";

export default function PermissionsSettingsPage() {
  const { data, error, isLoading, mutate } = useSWR<PermissionMatrix>("/product/permissions", getPermissions);

  if (isLoading) return <SkeletonCard className="h-64" />;

  if (error || !data) {
    return <EmptyState icon="⚠️" title="Could not load permissions" description="Check that the backend is running." />;
  }

  const matrix = data;
  const roles = Object.keys(matrix.roles);
  const permissions = Array.from(new Set(Object.values(matrix.roles).flat())).sort();

  async function toggle(role: string, permission: string) {
    const current = matrix.roles[role] ?? [];
    const next = current.includes(permission)
      ? current.filter((item) => item !== permission)
      : [...current, permission];
    await updatePermissions({ role, permissions: next });
    mutate();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Permissions</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Role-based access matrix.</p>
        </div>
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full min-w-[520px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-slate-800 dark:text-slate-400">
              <th className="px-4 py-3">Permission</th>
              {roles.map((role) => (
                <th key={role} className="px-4 py-3 text-center capitalize">{role}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {permissions.map((permission) => (
              <tr key={permission}>
                <td className="px-4 py-2.5 font-medium text-slate-700 dark:text-slate-200">{permission}</td>
                {roles.map((role) => {
                  const granted = (data.roles[role] ?? []).includes(permission);
                  return (
                    <td key={role} className="px-4 py-2.5 text-center">
                      <input
                        type="checkbox"
                        checked={granted}
                        onChange={() => toggle(role, permission)}
                        className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                        aria-label={`${permission} for ${role}`}
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-400">
        Changes are saved immediately via PUT /product/permissions.
      </p>
    </div>
  );
}
