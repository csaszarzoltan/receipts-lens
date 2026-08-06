"use client";

import { cx } from "@/lib/utils";

interface AiScanToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  id?: string;
}

/**
 * "AI Scan" toggle for the upload flow. Enables the LLM vision extraction
 * path (with automatic Tesseract fallback) instead of classic OCR.
 *
 * Accessible switch semantics: role="switch" + aria-checked, keyboard
 * togglable (Enter/Space), labelled for screen readers.
 */
export default function AiScanToggle({
  checked,
  onChange,
  disabled = false,
  id = "ai-scan-toggle",
}: AiScanToggleProps) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="min-w-0">
        <label htmlFor={id} className="flex cursor-pointer items-center gap-2">
          <span className="text-lg" aria-hidden="true">
            ✨
          </span>
          <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            AI Scan
          </span>
        </label>
        <p className="mt-1 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
          Vision AI reads blurry photos, handwritten amounts and unusual
          layouts — and falls back to classic OCR automatically if it is
          unavailable.
        </p>
      </div>
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label="AI Scan"
        disabled={disabled}
        onClick={() => onChange(!checked)}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onChange(!checked);
          }
        }}
        className={cx(
          "relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:opacity-50 dark:focus-visible:ring-offset-slate-950",
          checked
            ? "bg-brand-600 hover:bg-brand-700"
            : "bg-slate-300 hover:bg-slate-400 dark:bg-slate-700 dark:hover:bg-slate-600",
        )}
      >
        <span
          className={cx(
            "inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform",
            checked ? "translate-x-6" : "translate-x-1",
          )}
          aria-hidden="true"
        />
      </button>
    </div>
  );
}
