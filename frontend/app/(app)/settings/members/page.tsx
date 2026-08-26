"use client";

import { useState } from "react";
import useSWR from "swr";
import { createInvite, getMembers } from "@/lib/api";
import type { HouseholdRole, Member } from "@/lib/types";
import { householdRoleLabel } from "@/lib/roles";
import { getTenant } from "@/lib/auth";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import { useTranslation } from "@/lib/i18n";

export default function MembersSettingsPage() {
  const { t } = useTranslation();
  const { data, error, isLoading, mutate } = useSWR<{ items: Member[] }>("/product/members", getMembers);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<HouseholdRole>("adult");
  const [busy, setBusy] = useState(false);
  const [inviteLink, setInviteLink] = useState<string | null>(null);
  const [inviteError, setInviteError] = useState<string | null>(null);

  const members = data?.items ?? [];
  const householdId = getTenant();

  async function add() {
    setBusy(true);
    setInviteError(null);
    setInviteLink(null);
    try {
      const invite = await createInvite(householdId, { email, role });
      if (invite.magic_link) setInviteLink(invite.magic_link);
      setEmail("");
      mutate();
    } catch (err: unknown) {
      setInviteError(err instanceof Error ? err.message : "A meghívó küldése nem sikerült.");
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
        <EmptyState icon="⚠️" title={t("couldNotLoad")} description={t("error")} />
      ) : members.length === 0 ? (
        <EmptyState icon="👥" title="No members yet" description="Add your first family member below." />
      ) : (
        <ul className="card divide-y divide-slate-100 dark:divide-slate-800" aria-label="Members">
          {members.map((member) => (
            <li key={member.member_id} className="flex items-center justify-between gap-3 px-5 py-3">
              <span className="font-medium text-slate-800 dark:text-slate-100">{member.email}</span>
              <span className="text-sm text-slate-500 dark:text-slate-400">{householdRoleLabel(member.role)}</span>
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
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Tag meghívása</h2>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          A meghívott e-mailben kap linket (fejlesztési módban a link itt jelenik meg).
        </p>
        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <input
            type="email"
            className="input flex-1"
            placeholder="csalad@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            aria-label="Member email"
          />
          <select className="input sm:w-52" value={role} onChange={(event) => setRole(event.target.value as HouseholdRole)} aria-label="Member role">
            <option value="owner">{householdRoleLabel("owner")}</option>
            <option value="adult">{householdRoleLabel("adult")}</option>
            <option value="child">{householdRoleLabel("child")}</option>
            <option value="view_only">{householdRoleLabel("view_only")}</option>
          </select>
        </div>
        <button type="button" onClick={add} disabled={!email || busy} className="btn-primary mt-4 text-sm">
          {busy ? "Küldés…" : "Meghívó küldése"}
        </button>
        {inviteLink && (
          <div className="mt-3 rounded-lg bg-slate-50 p-3 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300">
            <p className="mb-1 font-medium">Fejlesztési mód — meghívó link:</p>
            <a href={inviteLink} className="break-all text-brand-600 hover:underline dark:text-brand-400">
              {inviteLink}
            </a>
          </div>
        )}
        {inviteError && (
          <p className="mt-3 text-sm text-red-600 dark:text-red-400" role="alert">
            {inviteError}
          </p>
        )}
      </section>
    </div>
  );
}
