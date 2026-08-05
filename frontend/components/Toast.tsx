"use client";

import { useEffect } from "react";

export type ToastKind = "info" | "success" | "error";

interface ToastProps {
  message: string;
  kind?: ToastKind;
  onDismiss: () => void;
  durationMs?: number;
}

const KIND_STYLES: Record<ToastKind, string> = {
  info: "border-sky-200 bg-sky-50 text-sky-800 dark:border-sky-900 dark:bg-sky-950 dark:text-sky-200",
  success:
    "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200",
  error: "border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200",
};

/** Single toast notification — auto-dismisses after a timeout. */
export default function Toast({ message, kind = "info", onDismiss, durationMs = 5000 }: ToastProps) {
  useEffect(() => {
    if (durationMs <= 0) return;
    const timer = window.setTimeout(onDismiss, durationMs);
    return () => window.clearTimeout(timer);
  }, [durationMs, onDismiss]);

  return (
    <div
      role="status"
      aria-live="polite"
      className={`pointer-events-auto flex min-h-11 items-center gap-3 rounded-xl border px-4 py-3 text-sm font-medium shadow-card animate-fade-in ${KIND_STYLES[kind]}`}
    >
      <span aria-hidden="true">{kind === "success" ? "✓" : kind === "error" ? "✕" : "ℹ"}</span>
      <span className="flex-1">{message}</span>
      <button
        type="button"
        onClick={onDismiss}
        className="rounded p-1 text-current opacity-60 transition-opacity hover:opacity-100"
        aria-label="Dismiss notification"
      >
        ✕
      </button>
    </div>
  );
}

/** Fixed-position toast stack container. */
export function ToastStack({
  toasts,
  onDismiss,
}: {
  toasts: Array<{ id: string; message: string; kind: ToastKind }>;
  onDismiss: (id: string) => void;
}) {
  return (
    <div
      className="pointer-events-none fixed inset-x-0 bottom-20 z-50 flex flex-col items-center gap-2 px-4 sm:bottom-6"
      aria-live="polite"
    >
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          message={toast.message}
          kind={toast.kind}
          onDismiss={() => onDismiss(toast.id)}
        />
      ))}
    </div>
  );
}
