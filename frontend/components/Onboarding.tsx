"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getPreferences, savePreferences } from "@/lib/api";
import type { Preferences } from "@/lib/types";
import { cx } from "@/lib/utils";

const STEPS = [
  { id: "welcome", icon: "👋", title: "Welcome to ReceiptLens", body: "Scan a receipt to start tracking your expenses. ReceiptLens reads the vendor, total and line items automatically." },
  { id: "upload", icon: "📤", title: "Upload your first receipt", body: "Take a photo or drag & drop a receipt image. OCR extracts everything in seconds." },
  { id: "review", icon: "🔍", title: "Review & confirm", body: "Check the OCR result, fix anything that looks off, and mark it complete." },
  { id: "forecast", icon: "📈", title: "Stay ahead", body: "The forecast engine projects next month's spending and flags unusual charges." },
] as const;

/**
 * First-run onboarding flow — modal overlay with guided steps and a Skip
 * button. Shows only while preferences.onboarding_done is false.
 */
export default function Onboarding() {
  const router = useRouter();
  const [preferences, setPreferences] = useState<Preferences | null>(null);
  const [step, setStep] = useState(0);
  const [dismissed, setDismissed] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getPreferences()
      .then(setPreferences)
      .catch(() => setPreferences({ onboarding_done: true } as Preferences));
  }, []);

  if (preferences?.onboarding_done || dismissed) return null;

  async function finish(onboardingDone: boolean) {
    setSaving(true);
    try {
      await savePreferences({ onboarding_done: onboardingDone });
      setPreferences((prev) => (prev ? { ...prev, onboarding_done: true } : prev));
      setDismissed(true);
      if (step === STEPS.length - 1 && !onboardingDone) router.push("/upload");
    } catch {
      setDismissed(true);
    } finally {
      setSaving(false);
    }
  }

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;

  const button =
    "inline-flex min-h-11 items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:opacity-50";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label={STEPS[0].title}>
      <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" aria-hidden="true" />
      <div className="relative w-full max-w-md overflow-hidden rounded-2xl bg-white shadow-card animate-fade-in dark:bg-slate-900">
        {/* Progress indicator */}
        <div className="flex gap-1 px-6 pt-5" aria-label={`Step ${step + 1} of ${STEPS.length}`}>
          {STEPS.map((item, index) => (
            <div
              key={item.id}
              className={cx(
                "h-1.5 flex-1 rounded-full transition-colors",
                index <= step ? "bg-brand-600" : "bg-slate-200 dark:bg-slate-700",
              )}
            />
          ))}
        </div>
        <div className="px-6 py-6 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-brand-50 text-3xl dark:bg-brand-950" aria-hidden="true">
            {current.icon}
          </div>
          <p className="mt-3 text-xs font-medium uppercase tracking-wide text-brand-600 dark:text-brand-400">
            {`Step ${step + 1} of ${STEPS.length}`}
          </p>
          <h2 className="mt-1 text-xl font-semibold text-slate-900 dark:text-slate-100">{current.title}</h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{current.body}</p>
        </div>
        <div className="flex items-center justify-between gap-2 border-t border-slate-100 px-6 py-4 dark:border-slate-800">
          <button
            type="button"
            onClick={() => finish(true)}
            className={cx(button, "text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200")}
            disabled={saving}
          >
            Skip
          </button>
          <div className="flex gap-2">
            {step > 0 ? (
              <button
                type="button"
                onClick={() => setStep((value) => value - 1)}
                className={cx(button, "border border-slate-200 text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800")}
                disabled={saving}
              >
                Back
              </button>
            ) : null}
            <button
              type="button"
              onClick={() => (isLast ? finish(false) : setStep((value) => value + 1))}
              className={cx(button, "bg-brand-600 text-white hover:bg-brand-700")}
              disabled={saving}
            >
              {isLast ? "Finish" : "Next"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
