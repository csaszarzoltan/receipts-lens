"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { acceptInvite } from "@/lib/api";
import { setSessionToken } from "@/lib/auth";
import { householdRoleLabel } from "@/lib/roles";
import type { HouseholdRole } from "@/lib/types";
import { useTranslation, getLocale } from "@/lib/i18n";
import LanguageSwitcher from "@/components/LanguageSwitcher";
import ThemeToggle from "@/components/ThemeToggle";

/**
 * Family invite acceptance (F1.3): the invite link carries ?token=...; the
 * page resolves it against the backend, which creates the membership and
 * returns a session — the user is signed straight in.
 */
function InviteInner() {
  const { t } = useTranslation();
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<{ household: string; role: HouseholdRole } | null>(null);

  useEffect(() => {
    if (!token) return;
    setBusy(true);
    // The invite URL shape: /auth/invite?token=... — the household/invite ids
    // are resolved via the session-me round trip after accept. Here we use the
    // generic accept endpoint through the token-bearing path.
    // (The backend accept endpoint needs household+invite ids; for the UI we
    // first resolve via the magic-link-style flow — see below.)
    setError(null);
  }, [token]);

  async function accept() {
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      // Backend contract: accept needs household_id + invite_id + token.
      // The token alone is not enough at the HTTP layer; the email carries
      // the full link normally. To keep this page self-sufficient we resolve
      // the token through the invite accept flow using a best-effort lookup:
      // the verify endpoint consumes login tokens only, so invite acceptance
      // must come from a link that encodes the ids (added by the owner UI).
      const url = new URL(window.location.href);
      const householdId = url.searchParams.get("household") ?? "";
      const inviteId = url.searchParams.get("invite") ?? "";
      if (!householdId || !inviteId) {
        setError(t("inviteMissing"));
        return;
      }
      const session = await acceptInvite(householdId, inviteId, token);
      setSessionToken(session.session_token);
      setInfo({ household: session.household_id, role: session.role });
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t("inviteInvalid"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4 dark:from-brand-950 dark:to-slate-950">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-card dark:bg-slate-900">
        <div className="flex justify-end"><ThemeToggle /></div>
        <div className="text-center">
          <span className="text-3xl" aria-hidden="true">👨‍👩‍👧</span>
          <h1 className="mt-2 text-xl font-bold text-slate-900 dark:text-slate-100">{t("familyMembers")}</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {t("joinHouseholdHint")}
          </p>
        </div>

        <div className="mt-4">
          <LanguageSwitcher />
        </div>

        {info ? (
          <p className="mt-6 text-center text-sm text-emerald-600 dark:text-emerald-400">
            {info.household} ({householdRoleLabel(info.role, getLocale())})
          </p>
        ) : (
          <div className="mt-6 space-y-4">
            {error && (
              <p className="text-sm text-red-600 dark:text-red-400" role="alert">
                {error}
              </p>
            )}
            <button
              type="button"
              onClick={accept}
              disabled={!token || busy}
              className="btn-primary w-full"
            >
              {busy ? t("sending") : t("sendInvite")}
            </button>
            <p className="text-center text-sm text-slate-500 dark:text-slate-400">
              {t("orDivider")}{" "}
              <Link href="/login" className="font-medium text-brand-600 hover:underline dark:text-brand-400">
                {t("signInWithHousehold")}
              </Link>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function InvitePage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><p className="text-sm text-slate-500">Loading…</p></div>}>
      <InviteInner />
    </Suspense>
  );
}
