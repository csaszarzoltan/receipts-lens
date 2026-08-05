"use client";

import type { ReactNode } from "react";
import Sidebar from "@/components/Sidebar";
import MobileNav from "@/components/MobileNav";
import Topbar from "@/components/Topbar";

/**
 * Authenticated application shell — desktop sidebar + mobile bottom tab
 * bar + sticky top bar + main content column.
 */
export default function AppShell({ children }: { children: ReactNode }) {
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
