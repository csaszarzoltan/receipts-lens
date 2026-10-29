"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import MobileNav from "@/components/MobileNav";
import Topbar from "@/components/Topbar";
import PhotoStrip from "@/components/PhotoStrip";
import { ApiError } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { getSessionToken, clearSessionToken } from "@/lib/auth";
import { routePhoto } from "@/lib/photos";

/**
 * Authenticated application shell — desktop sidebar + mobile bottom tab
 * bar + sticky top bar + main content column.
 *
 * Auth gate: when no valid session exists, the user is sent to /login.
 * Backend (RECEIPTLENS_ENV=production) already enforces Bearer-only
 * (X-Tenant-ID fallback disabled), so unauthenticated API calls get 401
 * and tenant data never mixes — this guard is the UX counterpart.
 */
export default function AppShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { t } = useTranslation();
  const [attempt, setAttempt] = useState(0);
  const [retryableError, setRetryableError] = useState(false);
  const [checking, setChecking] = useState(true);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setChecking(true);
    setRetryableError(false);
    async function check() {
      const token = getSessionToken();
      if (!token) {
        if (!cancelled) {
          setChecking(false);
          setAuthed(false);
          router.replace("/login");
        }
        return;
      }
      try {
        const { resolveSession } = await import("@/lib/api");
        await resolveSession(token);
        if (!cancelled) {
          setChecking(false);
          setAuthed(true);
        }
      } catch (err) {
        if (!cancelled) {
          setChecking(false);
          setAuthed(false);
          if (err instanceof ApiError && err.status === 401) {
            clearSessionToken();
            router.replace("/login");
          } else {
            setRetryableError(true);
          }
        }
      }
    }
    check();
    return () => { cancelled = true; };
  }, [router, attempt]);

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div role="status" aria-label="ReceiptLens" className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600 motion-reduce:animate-none" />
      </div>
    );
  }
  const stripPhoto = pathname ? routePhoto(pathname) : null;

  if (retryableError) return <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-6 text-center"><p role="alert">{t("sessionRetryHint")}</p><button type="button" className="btn-primary" onClick={() => setAttempt(value => value + 1)}>{t("retry")}</button></main>;
  if (!authed) return null;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-brand-600 focus:px-4 focus:py-2 focus:text-white"
      >
        {t("skipToContent")}
      </a>
      <Sidebar />
      <MobileNav />
      <div className="lg:pl-64">
        <Topbar />
        <main id="main-content" tabIndex={-1} className="px-4 pb-24 pt-6 sm:px-6 lg:pb-10">
          <div className="mx-auto max-w-6xl">
            {stripPhoto ? <PhotoStrip photo={stripPhoto} /> : null}
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
