"use client";

import { useState } from "react";
import useSWR from "swr";
import { addMember, getMembers } from "@/lib/api";
import type { Member } from "@/lib/types";
import { roleLabel } from "@/lib/roles";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";

export default function MembersSettingsPage() {
  const { data, error, isLoading, mutate } = useSWR<{ items: Member[] }>("/product/members", getMembers);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("reviewer");
  const [busy, setBusy] = useState(false);

  const members = data?.items ?? [];

  async function add() {
    setBusy(true);
    try {
      await addMember({ email, role });
      setEmail("");
      mutate();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Családtagok</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Household members and their roles.</p>
      </div>

      {isLoading ? (
        <SkeletonCard className="h-40" />
      ) : error ? (
        <EmptyState icon="⚠️" title="Could not load members" description="Check that the backend is running." />
      ) : members.length === 0 ? (
        <EmptyState icon="👥" title="No members yet" description="Add your first family member below." />
      ) : (
        <ul className="card divide-y divide-slate-100 dark:divide-slate-800" aria-label="Members">
          {members.map((member) => (
            <li key={member.member_id} className="flex items-center justify-between gap-3 px-5 py-3">
              <span className="font-medium text-slate-800 dark:text-slate-100">{member.email}</span>
              <span className="text-sm text-slate-500 dark:text-slate-400">{roleLabel(member.role)}</span>
              <span
                className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                  member.active
                    ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                    : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400"
                }`}
              >
                {member.active ? "Active" : "Inactive"}
              </span>
            </li>
          ))}
        </ul>
      )}

      <section className="card max-w-lg p-5" aria-label="Add member">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Add member</h2>
        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <input
            type="email"
            className="input flex-1"
            placeholder="csalad@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            aria-label="Member email"
          />
          <select className="input sm:w-52" value={role} onChange={(event) => setRole(event.target.value)} aria-label="Member role">
            <option value="admin">{roleLabel("admin")}</option>
            <option value="reviewer">{roleLabel("reviewer")}</option>
            <option value="integrator">{roleLabel("integrator")}</option>
          </select>
        </div>
        <button type="button" onClick={add} disabled={!email || busy} className="btn-primary mt-4 text-sm">
          {busy ? "Adding…" : "Add member"}
        </button>
      </section>
    </div>
  );
}
