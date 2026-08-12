"use client";

import { useEffect, useState } from "react";
import { cx } from "@/lib/utils";

/**
 * Dark mode toggle — persists to localStorage and toggles the `dark` class
 * on <html> (Tailwind `darkMode: "class"`).
 *
 * Lazily initializes from localStorage / prefers-color-scheme so the
 * first render already carries the right state (no flash of wrong theme),
 * and a single effect keeps the class + storage in sync.
 */
function getInitialDark(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const stored = window.localStorage.getItem("receiptlens.theme");
    if (stored) return stored === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  } catch {
    return false;
  }
}

export default function ThemeToggle() {
  const [dark, setDark] = useState<boolean>(getInitialDark);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    try {
      window.localStorage.setItem("receiptlens.theme", dark ? "dark" : "light");
    } catch {
      /* storage unavailable — class still applies */
    }
  }, [dark]);

  return (
    <button
      type="button"
      onClick={() => setDark((value) => !value)}
      className={cx(
        "inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg text-lg transition-colors",
        "hover:bg-slate-100 dark:hover:bg-slate-800",
      )}
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
      title={dark ? "Light mode" : "Dark mode"}
    >
      <span aria-hidden="true">{dark ? "☀️" : "🌙"}</span>
    </button>
  );
}
