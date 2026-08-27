"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getPreferences, savePreferences, uploadReceipt } from "@/lib/api";
import { setAuthState } from "@/lib/auth";
import { cx } from "@/lib/utils";
import { getLocale, useTranslation } from "@/lib/i18n";

/**
 * Consumer onboarding — the 3-step first-run flow (F1.5 of
 * docs/plans/consumer-pivot-2026-08-13.md, §4):
 *
 *   1. "Mi ez?" — the one-sentence positioning promise (§3.1):
 *      "Snap the receipt. We show where your money goes —"
 *   2. Camera / upload access — capture the first receipt via the
 *      device camera or a file picker (DropZone pattern).
 *   3. First receipt — a live upload of the chosen photo. The OCR result
 *      is shown in place (vendor, total, confidence), then the flow
 *      finishes on the consumer dashboard (/dashboard).
 *
 * Flow rules:
 *   - sticky step indicator (forward/back, always skippable)
 *   - the step-1 promise never appears after the flow is completed
 *     (state persistence: preferences.onboarding_done)
 *   - step 2 can proceed without a photo (skip photo → upload remains
 *     available from the dashboard); the camera requires a permission
 *     grant or a device picker, both handled by <input capture>
 *   - finishing always persists onboarding_done=true before navigating
 */
function getSteps(t: (k: string) => string) {
  return [
    {
      icon: "💡",
      title: t("onboardingStepWhat"),
      body: t("onboardingPromise"),
      hint: t("onboardingPromiseHint"),
    },
    {
      icon: "📷",
      title: t("onboardingStepCamera"),
      body: t("onboardingCameraBody"),
      hint: t("onboardingCameraHint"),
    },
    {
      icon: "🧾",
      title: t("onboardingStepFirst"),
      body: t("onboardingFirstBody"),
      hint: t("onboardingFirstHint"),
    },
  ] as const;
}

interface UploadOutcome {
  vendor: string | null;
  total: number | null;
  currency: string | null;
  confidenceLevel: string | null;
}

export default function OnboardingPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [outcome, setOutcome] = useState<UploadOutcome | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  // State persistence (acceptance 4): a user who already completed onboarding
  // must not be shown the flow again — redirect straight to the dashboard.
  useEffect(() => {
    let cancelled = false;
    getPreferences()
      .then((preferences) => {
        if (!cancelled && preferences.onboarding_done) {
          router.replace("/dashboard");
        }
      })
      .catch(() => {
        // Preferences unreachable — let the flow render; finish() persists
        // through the same API and still completes.
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  const STEPS = getSteps(t as any);
  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;

  async function finish() {
    setSaving(true);
    try {
      await savePreferences({ onboarding_done: true });
    } catch {
      // Persistence failure is non-fatal — the flow still completes.
    }
    setAuthState("demo", "admin");
    router.push("/dashboard");
  }

  function skip() {
    void finish();
  }

  async function handleFiles(list: FileList | null) {
    const file = list?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      // Plain OCR upload mirrors the upload page default: Tesseract with the
      // F1.4 confidence level. (The AI vision path is an optional, cost-guarded
      // extra behind /upload's AI Scan toggle — onboarding must always complete.)
      const result = await uploadReceipt(file);
      setOutcome({
        vendor: result.receipt?.vendor ?? null,
        total: result.receipt?.total ?? null,
        currency: result.receipt?.currency ?? null,
        confidenceLevel: result.receipt?.confidence_level ?? null,
      });
    } catch (err) {
      setUploadError(
        err instanceof Error ? err.message : t("onboardingUploadFailed"),
      );
    } finally {
      setUploading(false);
    }
  }

  function openFilePicker() {
    fileInput.current?.click();
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4 py-8 dark:from-brand-950 dark:to-slate-950">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-card dark:bg-slate-900">
        {/* Sticky step indicator — forward/back state, never lost */}
        <div className="flex gap-1" role="group" aria-label={`${step + 1} ${t("onboardingStepOf")} ${STEPS.length} ${t("onboardingTotalOf")}`}>
          {STEPS.map((item, index) => (
            <div
              key={item.title}
              className={cx(
                "h-1.5 flex-1 rounded-full transition-colors",
                index <= step ? "bg-brand-600" : "bg-slate-200 dark:bg-slate-700",
              )}
            />
          ))}
        </div>

        <div className="py-8 text-center">
          <div
            className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-brand-50 text-3xl dark:bg-brand-950"
            aria-hidden="true"
          >
            {current.icon}
          </div>
          <p className="mt-3 text-xs font-medium uppercase tracking-wide text-brand-600 dark:text-brand-400">
            {`${step + 1} ${t("onboardingStepOf")} ${STEPS.length} ${t("onboardingTotalOf")}`}
          </p>
          <h1 className="mt-1 text-xl font-semibold text-slate-900 dark:text-slate-100">{current.title}</h1>
          <p className="mt-2 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{current.body}</p>
          {current.hint ? (
            <p className="mt-2 text-xs leading-relaxed text-slate-400 dark:text-slate-500">{current.hint}</p>
          ) : null}
        </div>

        {step === 1 ? (
          <div className="mb-6 space-y-3">
            <button
              type="button"
              onClick={openFilePicker}
              className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white shadow-card transition-colors hover:bg-brand-700"
            >
              {t("onboardingTakePhoto")}
            </button>
            <button
              type="button"
              onClick={openFilePicker}
              className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              {t("onboardingUploadFromDevice")}
            </button>
          </div>
        ) : null}

        {step === 2 ? (
          <div className="mb-6 space-y-3">
            {uploading ? (
              <div
                className="flex min-h-32 flex-col items-center justify-center rounded-xl border border-slate-200 bg-slate-50 p-6 text-center dark:border-slate-800 dark:bg-slate-950"
                role="status"
                aria-live="polite"
              >
                <span className="text-3xl" aria-hidden="true">
                  ⏳
                </span>
                <p className="mt-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                  {t("onboardingProcessing")}
                </p>
              </div>
            ) : outcome ? (
              <div
                className="rounded-xl border border-emerald-200 bg-emerald-50 p-5 text-center dark:border-emerald-900 dark:bg-emerald-950"
                role="status"
                aria-live="polite"
              >
                <p className="text-xs font-medium uppercase tracking-wide text-emerald-700 dark:text-emerald-300">
                  {t("onboardingDone")}
                </p>
                <p className="mt-2 text-lg font-semibold text-slate-900 dark:text-slate-100">
                  {outcome.vendor ?? t("vendor")}
                </p>
                <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {outcome.total !== null
                    ? `${outcome.total.toLocaleString(({ en: "en-US", hu: "hu-HU", de: "de-DE", fr: "fr-FR", es: "es-ES", it: "it-IT", pt: "pt-PT", nl: "nl-NL", pl: "pl-PL", ro: "ro-RO" } as Record<string, string>)[getLocale()] ?? "en-US", { maximumFractionDigits: 2 })} ${outcome.currency ?? ""}`
                    : t("noReceipts")}
                </p>
                {outcome.confidenceLevel ? (
                  <p className="mt-1 text-xs text-emerald-700 dark:text-emerald-300">
                    {t("onboardingConfidence")} {outcome.confidenceLevel}
                  </p>
                ) : null}
              </div>
            ) : (
              <div>
                <button
                  type="button"
                  onClick={openFilePicker}
                  className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white shadow-card transition-colors hover:bg-brand-700"
                >
                  {t("addReceipt")}
                </button>
                {uploadError ? (
                  <p className="mt-2 text-sm text-rose-600 dark:text-rose-400" role="alert">
                    {uploadError}
                  </p>
                ) : null}
              </div>
            )}
          </div>
        ) : null}

        <div className="flex items-center justify-between gap-2">
          <button type="button" onClick={skip} disabled={saving} className="text-sm font-medium text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200">
            {t("skip")}
          </button>
          <div className="flex gap-2">
            {step > 0 ? (
              <button type="button" onClick={() => setStep((value) => value - 1)} disabled={saving || uploading} className="btn-secondary text-sm">
                {t("back")}
              </button>
            ) : null}
            {isLast ? (
              <button type="button" onClick={() => void finish()} disabled={saving || uploading} className="btn-primary text-sm">
                {saving ? t("loading") : t("finish")}
              </button>
            ) : (
              <button type="button" onClick={() => setStep((value) => value + 1)} className="btn-primary text-sm">
                {t("next")}
              </button>
            )}
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-slate-400 dark:text-slate-500">
          <Link href="/dashboard" className="underline-offset-2 hover:underline">
            {t("onboardingAlreadyHaveAccount")}
          </Link>
        </p>
      </div>

      {/* One picker for both camera capture (mobile: opens the camera) and
          gallery upload — <input capture> requests the camera permission
          where supported. */}
      <input
        ref={fileInput}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        data-testid="onboarding-file-input"
        onChange={(event) => {
          void handleFiles(event.target.files);
          event.target.value = "";
        }}
      />
    </div>
  );
}
