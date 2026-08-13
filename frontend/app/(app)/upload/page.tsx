"use client";

import { useState } from "react";
import Link from "next/link";
import { useUpload } from "@/lib/hooks/useUpload";
import DropZone from "@/components/DropZone";
import UploadQueue from "@/components/UploadQueue";
import EmptyState from "@/components/EmptyState";
import AiScanToggle from "@/components/AiScanToggle";
import AiResultPanel from "@/components/AiResultPanel";

/**
 * Upload page — drag & drop / camera capture, then the real OCR pipeline
 * (POST /product/receipts/upload) with per-file progress and a preview of
 * the extracted receipt. The "AI Scan" toggle switches the flow to the LLM
 * vision path (source + ai_result/tesseract_result in the response), and
 * the result panel renders the extraction with per-field confidence, the
 * source badge and a friendly fallback notice when Tesseract was used.
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

      <AiScanToggle checked={aiScan} onChange={setAiScan} />

      <DropZone onFiles={(files) => enqueue(files, { aiScan })} />

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
