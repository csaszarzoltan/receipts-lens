"use client";

import ConfidenceBadge from "@/components/ConfidenceBadge";
import { cx, formatDate, formatMoney } from "@/lib/utils";
import type { AiExtraction, AiScanUploadResponse } from "@/lib/types";

interface AiResultPanelProps {
  result: AiScanUploadResponse | null;
}

/**
 * Pick the primary extraction to display, preferring the pipeline named by
 * `source`; falls back to the receipt fields for older schema responses.
 */
function primaryExtraction(result: AiScanUploadResponse): AiExtraction | null {
  if (result.source === "vision" && result.ai_result) return result.ai_result;
  if (result.source === "tesseract" && result.tesseract_result) {
    return result.tesseract_result;
  }
  const receipt = result.receipt;
  if (!receipt) return null;
  return {
    merchant: receipt.vendor ?? null,
    date: receipt.date ?? null,
    total: receipt.total ?? null,
    tax: receipt.tax ?? null,
    currency: receipt.currency ?? null,
    line_items: receipt.line_items ?? [],
    confidence: receipt.confidence ?? {},
  };
}

function FieldRow({
  label,
  value,
  confidence,
}: {
  label: string;
  value: string;
  confidence?: number;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-800/60">
      <span className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {label}
      </span>
      <span className="flex items-center gap-2 text-right">
        <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          {value}
        </span>
        {confidence !== undefined && <ConfidenceBadge value={confidence} label={label} />}
      </span>
    </div>
  );
}

/**
 * AI Scan result panel — shows the extraction source (vision vs tesseract),
 * the AI-extracted fields with per-field confidence, a friendly fallback
 * notice when Tesseract was used, and a compact AI-vs-OCR comparison when
 * both pipelines ran on the same image.
 */
export default function AiResultPanel({ result }: AiResultPanelProps) {
  if (!result) return null;

  const extraction = primaryExtraction(result);
  if (!extraction) return null;

  const isVision = result.source === "vision";
  const { confidence } = extraction;
  const lineItems = extraction.line_items ?? [];
  const lineConfidence = confidence.line_items;

  return (
    <section
      className="card overflow-hidden"
      aria-label="AI Scan results"
      data-testid="ai-result-panel"
    >
      {/* Header: title + source badge */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4 dark:border-slate-800">
        <h2 className="flex items-center gap-2 text-base font-semibold text-slate-900 dark:text-slate-100">
          <span aria-hidden="true">✨</span> AI Scan results
        </h2>
        <span
          className={cx(
            "inline-flex min-h-6 items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold",
            isVision
              ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
              : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
          )}
          title={`Extracted by ${result.source}`}
        >
          <span aria-hidden="true">{isVision ? "👁️" : "📄"}</span>
          {isVision ? "Vision AI" : "OCR"}
        </span>
      </div>

      {/* Friendly fallback notice when Tesseract was used */}
      {!isVision ? (
        <div
          role="status"
          className="mx-5 mt-4 flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-900/60 dark:bg-amber-950/50"
        >
          <span className="text-lg" aria-hidden="true">
            ⚠️
          </span>
          <div>
            <p className="text-sm font-medium text-amber-900 dark:text-amber-200">
              AI vision wasn&apos;t available — showing classic OCR results.
            </p>
            <p className="mt-0.5 text-xs text-amber-800/80 dark:text-amber-300/80">
              Blurry photos or handwritten amounts may be less accurate. Try
              the scan again, or check that your AI provider is configured.
            </p>
          </div>
        </div>
      ) : null}

      {/* Extracted fields with per-field confidence */}
      <div className="space-y-2 px-5 py-4">
        <FieldRow label="Merchant" value={extraction.merchant ?? "—"} confidence={confidence.merchant} />
        <FieldRow label="Date" value={formatDate(extraction.date)} confidence={confidence.date} />
        <FieldRow
          label="Total"
          value={formatMoney(extraction.total, extraction.currency)}
          confidence={confidence.total}
        />
        <FieldRow label="Tax" value={formatMoney(extraction.tax, extraction.currency)} confidence={confidence.tax} />
        <FieldRow
          label="Currency"
          value={extraction.currency ?? "—"}
          confidence={confidence.currency}
        />

        {/* Line items */}
        {lineItems.length > 0 ? (
          <div className="mt-3">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Line items
              </h3>
              {lineConfidence !== undefined ? (
                <ConfidenceBadge value={lineConfidence} label="Line items" />
              ) : null}
            </div>
            <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 dark:divide-slate-800 dark:border-slate-800">
              {lineItems.map((item, index) => (
                <li
                  key={`${item.name}-${index}`}
                  className="flex items-center justify-between gap-3 px-3 py-2 text-sm"
                >
                  <span className="truncate text-slate-700 dark:text-slate-200">
                    {item.name}
                  </span>
                  <span className="shrink-0 font-medium text-slate-900 dark:text-slate-100">
                    {formatMoney(item.amount ?? item.price, extraction.currency)}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {/* AI vs OCR comparison — both pipelines ran on the same image */}
        {result.ai_result && result.tesseract_result ? (
          <div className="mt-3 rounded-lg border border-slate-200 bg-white px-3 py-2.5 dark:border-slate-800 dark:bg-slate-900">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
              AI vs OCR comparison
            </p>
            <div className="mt-1.5 flex flex-wrap items-center gap-x-5 gap-y-1 text-sm">
              <span className="flex items-center gap-2 text-slate-700 dark:text-slate-200">
                <span aria-hidden="true">👁️</span>
                {formatMoney(result.ai_result.total, result.ai_result.currency)}
                {result.ai_result.confidence.total !== undefined ? (
                  <ConfidenceBadge value={result.ai_result.confidence.total} label="AI total" />
                ) : null}
              </span>
              <span className="flex items-center gap-2 text-slate-700 dark:text-slate-200">
                <span aria-hidden="true">📄</span>
                {formatMoney(result.tesseract_result.total, result.tesseract_result.currency)}
                {result.tesseract_result.confidence.total !== undefined ? (
                  <ConfidenceBadge value={result.tesseract_result.confidence.total} label="OCR total" />
                ) : null}
              </span>
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
