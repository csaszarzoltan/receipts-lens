"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import MobileNav from "@/components/MobileNav";
import Topbar from "@/components/Topbar";
import { getSessionToken, clearSessionToken } from "@/lib/auth";

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
  const [checking, setChecking] = useState(true);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    let cancelled = false;
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
        console.error("resolveSession failed:", err);
        clearSessionToken();
        if (!cancelled) {
          setChecking(false);
          setAuthed(false);
          router.replace("/login");
        }
      }
    }
    check();
    return () => { cancelled = true; };
  }, [router]);

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950">
        <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>
      </div>
    );
  }

  if (!authed) return null;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-brand-600 focus:px-4 focus:py-2 focus:text-white"
      >
        Skip to content
      </a>
      <Sidebar />
      <MobileNav />
      <div className="lg:pl-64">
        <Topbar />
        <main id="main-content" tabIndex={-1} className="px-4 pb-24 pt-6 sm:px-6 lg:pb-10">
          <div className="mx-auto max-w-6xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
