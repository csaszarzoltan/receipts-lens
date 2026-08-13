"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { BUSINESS_NAV_ITEMS, MOBILE_TABS, NAV_ITEMS } from "@/lib/nav";
import { cx } from "@/lib/utils";

/**
 * Mobile navigation — bottom tab bar (5 primary destinations) plus a
 * slide-over menu (hamburger) listing every section. Hidden on lg+.
 * The B2B features appear under a separate "Business" sub-heading so the
 * consumer tab bar stays jargon-free (F1.1 consumer pivot).
 */
export default function MobileNav() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  const activeTab = (href: string) =>
    pathname === href || (href === "/dashboard" && pathname === "/");

  return (
    <>
      {/* Bottom tab bar */}
      <nav
        className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 backdrop-blur lg:hidden dark:border-slate-800 dark:bg-slate-950/95"
        aria-label="Mobile tab bar"
      >
        <div className="grid grid-cols-6">
          {MOBILE_TABS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cx(
                "flex min-h-14 flex-col items-center justify-center gap-0.5 text-[11px] font-medium",
                activeTab(item.href)
                  ? "text-brand-600 dark:text-brand-400"
                  : "text-slate-500 dark:text-slate-400",
              )}
              aria-current={activeTab(item.href) ? "page" : undefined}
            >
              <span aria-hidden="true" className="text-lg leading-none">{item.icon}</span>
              {item.label}
            </Link>
          ))}
          <button
            type="button"
            onClick={() => setMenuOpen(true)}
            className="flex min-h-14 flex-col items-center justify-center gap-0.5 text-[11px] font-medium text-slate-500 dark:text-slate-400"
            aria-label="Open all sections"
            aria-expanded={menuOpen}
          >
            <span aria-hidden="true" className="text-lg leading-none">☰</span>
            More
          </button>
        </div>
      </nav>

      {/* Slide-over menu for the remaining sections */}
      {menuOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="All sections">
          <button
            type="button"
            className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm"
            onClick={() => setMenuOpen(false)}
            aria-label="Close menu"
          />
          <div className="absolute inset-y-0 right-0 flex w-72 max-w-[85vw] flex-col bg-white shadow-card animate-fade-in dark:bg-slate-950">
            <div className="flex min-h-16 items-center justify-between border-b border-slate-200 px-5 dark:border-slate-800">
              <span className="font-semibold text-slate-900 dark:text-slate-100">All sections</span>
              <button
                type="button"
                onClick={() => setMenuOpen(false)}
                className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                aria-label="Close menu"
              >
                ✕
              </button>
            </div>
            <nav className="flex-1 overflow-y-auto px-3 py-4">
              <ul className="space-y-1">
                {NAV_ITEMS.map((item) => (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={() => setMenuOpen(false)}
                      className="flex min-h-11 items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-900"
                    >
                      <span aria-hidden="true">{item.icon}</span>
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>

              {/* Business section — separate entry point (F1.1). */}
              <div className="mt-4 border-t border-slate-200 pt-3 dark:border-slate-800">
                <p className="px-3 pb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Business
                </p>
                <ul className="space-y-1">
                  {BUSINESS_NAV_ITEMS.map((item) => (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        onClick={() => setMenuOpen(false)}
                        className="flex min-h-11 items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-slate-100"
                      >
                        <span aria-hidden="true">{item.icon}</span>
                        {item.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            </nav>
          </div>
        </div>
      ) : null}
    </>
  );
}
