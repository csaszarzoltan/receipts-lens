"use client";

import { useState } from "react";
import Link from "next/link";
import { useUpload } from "@/lib/hooks/useUpload";
import { useQuota } from "@/lib/hooks/useQuota";
import QuotaBar from "@/components/QuotaBar";
import DropZone from "@/components/DropZone";
import SampleReceipt from "@/components/SampleReceipt";
import EnyugtaImport from "@/components/EnyugtaImport";
import UploadQueue from "@/components/UploadQueue";
import EmptyState from "@/components/EmptyState";
import AiScanToggle from "@/components/AiScanToggle";
import AiResultPanel from "@/components/AiResultPanel";
import { AI_SCAN_ENABLED } from "@/lib/featureFlags";
import { useTranslation } from "@/lib/i18n";

/**
 * Upload page — drag & drop / camera capture, then the real OCR pipeline
 * (POST /product/receipts/upload) with per-file progress and a preview of
 * the extracted receipt. The "AI Scan" toggle switches the flow to the LLM
 * vision path (source + ai_result/tesseract_result in the response), and
 * the result panel renders the extraction with per-field confidence, the
 * source badge and a friendly fallback notice when Tesseract was used.
 *
 * Production gating: AI Scan is a future paid feature — when
 * NEXT_PUBLIC_AI_SCAN_ENABLED is unset/false (the production default) the
 * toggle is hidden and an upgrade prompt is shown instead; uploads always
 * run classic Tesseract OCR (see docs/plans/production-rollout-2026-08-13.md).
 */
export default function UploadPage() {
  const { t } = useTranslation();
  const { entries, enqueue, clear, remove, retry, lastResult, lastAiResult } = useUpload();
  const { quota } = useQuota();
  const [aiScan, setAiScan] = useState(false);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("addReceipt")}</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {t("uploadDesc")}
        </p>
      </div>

      {quota ? <QuotaBar used={quota.used} limit={quota.limit} isPro={quota.pro} /> : null}

      <section id="receipt-capture" aria-label={t("addReceipt")}><DropZone label={lastResult ? t("addNextReceipt") : undefined} onFiles={(files) => enqueue(files, { aiScan: AI_SCAN_ENABLED && aiScan })} /></section>

      <SampleReceipt />

      <EnyugtaImport />

      {AI_SCAN_ENABLED ? <AiScanToggle checked={aiScan} onChange={setAiScan} /> : null}

      {entries.length > 0 ? (
        <section className="space-y-3" aria-label={t("uploadProgressLabel")}>
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              {t("uploadingTitle")} ({entries.length})
            </h2>
            <button
              type="button"
              onClick={clear}
              className="text-sm font-medium text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
            >
              {t("clearAllLabel")}
            </button>
          </div>
          <UploadQueue entries={entries} onRemove={remove} onRetry={retry} />
        </section>
      ) : (
        <EmptyState
          icon="📤"
          title={t("readyWhenYouAre")}
          description={t("readyWhenYouAreDesc")}
        />
      )}

      {/* AI-mode result panel — extraction source, confidence, fallback notice */}
      {lastAiResult ? <AiResultPanel result={lastAiResult} /> : null}

      <section className="card p-5">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
          {t("batchProcessingTitle")}
        </h2>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {t("batchProcessingDesc")}
        </p>
        <Link href="/receipts" className="btn-secondary mt-4 text-sm">
          {t("seeProcessedReceipts")}
        </Link>
      </section>
    </div>
  );
}
