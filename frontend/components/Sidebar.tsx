"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { BUSINESS_NAV_ITEMS, NAV_ITEMS, getNavLabel } from "@/lib/nav";
import { cx } from "@/lib/utils";

function isActive(href: string, pathname: string): boolean {
  if (href === "/dashboard") return pathname === "/dashboard" || pathname === "/";
  if (href === "/settings") return pathname.startsWith("/settings");
  return pathname === href || pathname.startsWith(`${href}/`);
}

/** Desktop navigation sidebar — hidden below the lg breakpoint. */
export default function Sidebar() {
  const pathname = usePathname();
  const [businessOpen, setBusinessOpen] = useState(false);

  return (
    <aside className="hidden lg:block" aria-label="Sidebar navigation">
      <div className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
        <Link
          href="/dashboard"
          className="flex min-h-16 items-center gap-2 border-b border-slate-200 px-5 font-semibold text-slate-900 dark:border-slate-800 dark:text-slate-100"
        >
          <span aria-hidden="true" className="text-xl">🔎</span>
          <span>ReceiptLens</span>
        </Link>
        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <ul className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const active = isActive(item.href, pathname);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={cx(
                      "flex min-h-11 items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                      active
                        ? "bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300"
                        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-slate-100",
                    )}
                  >
                    <span aria-hidden="true" className="text-base">{item.icon}</span>
                    {getNavLabel(item)}
                  </Link>
                </li>
              );
            })}
          </ul>

          {/* Business section — hidden behind a separate entry point (F1.1). */}
          <div className="mt-4 border-t border-slate-200 pt-3 dark:border-slate-800">
            <button
              type="button"
              onClick={() => setBusinessOpen((open) => !open)}
              aria-expanded={businessOpen}
              className="flex min-h-9 w-full items-center justify-between rounded-lg px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
            >
              <span>Business</span>
              <span aria-hidden="true">{businessOpen ? "▾" : "▸"}</span>
            </button>
            {businessOpen ? (
              <ul className="mt-1 space-y-1">
                {BUSINESS_NAV_ITEMS.map((item) => {
                  const active = isActive(item.href, pathname);
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        aria-current={active ? "page" : undefined}
                        className={cx(
                          "flex min-h-10 items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                          active
                            ? "bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300"
                            : "text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-slate-100",
                        )}
                      >
                        <span aria-hidden="true" className="text-base">{item.icon}</span>
                        {getNavLabel(item)}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            ) : null}
          </div>
        </nav>
        <div className="border-t border-slate-200 px-5 py-3 text-xs text-slate-400 dark:border-slate-800 dark:text-slate-500">
          ReceiptLens v1.4.0
        </div>
      </div>
    </aside>
  );
}
