"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { getRole, setRole, ROLES, type Role, getSessionToken } from "@/lib/auth";
import { roleLabel } from "@/lib/roles";
import { useTranslation } from "@/lib/i18n";
import ThemeToggle from "@/components/ThemeToggle";
import NotificationPanel from "@/components/NotificationPanel";
import ProfileMenu from "@/components/ProfileMenu";

/** Sticky top bar — global search, household role, notifications, theme. */
export default function Topbar() {
  const { t } = useTranslation();
  const router = useRouter();
  const [role, setRoleState] = useState<Role>(getRole());
  const [identity, setIdentity] = useState<{ email: string; display_name: string | null } | null>(null);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  useEffect(() => {
    const token = getSessionToken();
    if (!token) return;
    import("@/lib/api").then(({ resolveSession }) =>
      resolveSession(token)
        .then((id) => setIdentity({ email: id.email, display_name: (id as { display_name?: string | null }).display_name ?? null }))
        .catch(() => {})
    );
  }, []);
  const searchRef = useRef<HTMLInputElement>(null);

  function submitSearch(event: React.FormEvent) {
    event.preventDefault();
    const query = searchRef.current?.value.trim() ?? "";
    router.push(`/receipts${query ? `?q=${encodeURIComponent(query)}` : ""}`);
  }

  const selectCls =
    "rounded-lg border border-slate-200 bg-white px-2 py-2 text-sm text-slate-700 focus:border-brand-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200";

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95">
      <div className="flex min-h-16 items-center gap-3 px-4 sm:px-6">
        <Link
          href="/dashboard"
          className="flex items-center gap-2 font-semibold text-slate-900 lg:hidden dark:text-slate-100"
        >
          <span aria-hidden="true">🔎</span>
          <span className="hidden sm:inline">ReceiptLens</span>
        </Link>

        <form onSubmit={submitSearch} className="min-w-0 flex-1 lg:max-w-md" role="search">
          <label htmlFor="global-search" className="sr-only">
            {t("search")}
          </label>
          <input
            id="global-search"
            ref={searchRef}
            type="search"
            placeholder={t("search")}
            className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          />
        </form>

        <div className="ml-auto flex items-center gap-2">
          {identity ? (
            <span className="hidden max-w-[14rem] truncate text-sm text-slate-600 dark:text-slate-300 md:inline" title={identity.email}>
              {t("signedInAs")} {identity.display_name || identity.email}
            </span>
          ) : null}
          {/* Household role selector — consumer label shown, wire value kept.
              The tenant selector was removed from the consumer view (F1.1). */}
          <div className="hidden items-center gap-2 md:flex">
            <select
              className={selectCls}
              value={role}
              onChange={(event) => {
                const next = event.target.value as Role;
                setRole(next);
                setRoleState(next);
              }}
              aria-label="Household role"
              title="Household role"
            >
              {ROLES.map((option) => (
                <option key={option} value={option}>
                  {roleLabel(option)}
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            onClick={() => setNotificationsOpen(true)}
            className="relative inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg text-lg hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label="Open notifications"
          >
            <span aria-hidden="true">🔔</span>
          </button>
          <ProfileMenu />
          {getSessionToken() && (
            <button
              type="button"
              onClick={async () => {
                const { logoutSession } = await import("@/lib/api");
                await logoutSession();
                router.push("/login");
              }}
              className="hidden rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100 md:inline-block"
              title={t("logout")}
            >
              {t("logout")}
            </button>
          )}
          <ThemeToggle />
        </div>
      </div>
      <NotificationPanel open={notificationsOpen} onClose={() => setNotificationsOpen(false)} />
    </header>
  );
}
