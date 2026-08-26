"use client";

import { useState } from "react";
import Link from "next/link";
import { useUpload } from "@/lib/hooks/useUpload";
import DropZone from "@/components/DropZone";
import UploadQueue from "@/components/UploadQueue";
import EmptyState from "@/components/EmptyState";
import AiScanToggle from "@/components/AiScanToggle";
import AiResultPanel from "@/components/AiResultPanel";
import { AI_SCAN_ENABLED } from "@/lib/featureFlags";

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
  const { entries, enqueue, clear, remove, lastAiResult } = useUpload();
  const [aiScan, setAiScan] = useState(false);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Nyugta hozzáadása</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Take a photo or drop a receipt image — OCR extracts the data instantly.
        </p>
      </div>

      {AI_SCAN_ENABLED ? (
        <AiScanToggle checked={aiScan} onChange={setAiScan} />
      ) : (
        <div
          data-testid="ai-scan-upgrade-prompt"
          className="flex items-start justify-between gap-4 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
        >
          <div className="min-w-0">
            <p className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
              <span aria-hidden="true">✨</span> AI Scan — coming soon
            </p>
            <p className="mt-1 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
              Vision AI reads blurry photos, handwritten amounts and unusual
              layouts. It will be part of the Pro plan — classic OCR works
              today for every upload.
            </p>
          </div>
          <span
            className="inline-flex shrink-0 items-center rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:bg-slate-800 dark:text-slate-400"
            title="AI Scan is not available in this environment"
          >
            Pro
          </span>
        </div>
      )}

      <DropZone onFiles={(files) => enqueue(files, { aiScan: AI_SCAN_ENABLED && aiScan })} />

      {entries.length > 0 ? (
        <section className="space-y-3" aria-label="Upload progress">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              Uploading ({entries.length})
            </h2>
            <button
              type="button"
              onClick={clear}
              className="text-sm font-medium text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
            >
              Clear all
            </button>
          </div>
          <UploadQueue entries={entries} onRemove={remove} />
        </section>
      ) : (
        <EmptyState
          icon="📤"
          title="Ready when you are"
          description="Your processed receipts will appear here with their OCR results."
        />
      )}

      {/* AI-mode result panel — extraction source, confidence, fallback notice */}
      {lastAiResult ? <AiResultPanel result={lastAiResult} /> : null}

      <section className="card p-5">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
          Batch processing
        </h2>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Dropping multiple files at once processes them in parallel via the
          batch API — each file above is uploaded individually for a live preview.
        </p>
        <Link href="/receipts" className="btn-secondary mt-4 text-sm">
          See processed receipts →
        </Link>
      </section>
    </div>
  );
}
