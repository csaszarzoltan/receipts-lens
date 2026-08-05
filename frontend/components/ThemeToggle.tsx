"use client";

import { useEffect, useState } from "react";
import { cx } from "@/lib/utils";

/**
 * Dark mode toggle — persists to localStorage and toggles the `dark` class
 * on <html> (Tailwind `darkMode: "class"`).
 */
export default function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem("receiptlens.theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    setDark(stored ? stored === "dark" : prefersDark);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    window.localStorage.setItem("receiptlens.theme", dark ? "dark" : "light");
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
