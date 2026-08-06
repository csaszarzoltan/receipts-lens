"use client";

import { useCallback, useRef, useState } from "react";
import { uploadReceipt, uploadReceiptWithAi } from "@/lib/api";
import { AI_MOCK_ENABLED, mockAiScanResponseForFile } from "@/lib/aiScanMock";
import type { AiScanUploadResponse, ReceiptItem } from "@/lib/types";

export interface UploadQueueEntry {
  id: string;
  fileName: string;
  progress: number;
  status: "queued" | "uploading" | "done" | "error";
  result?: ReceiptItem & { applied_rules?: unknown };
  /** Present when the file was uploaded in AI Scan mode. */
  aiResult?: AiScanUploadResponse;
  error?: string;
}

export interface EnqueueOptions {
  /** Run the upload through the LLM vision path (AI Scan mode). */
  aiScan?: boolean;
}

/**
 * Upload queue state machine — one entry per file with progress, then a
 * navigable result. Driven by the real uploadReceipt() / uploadReceiptWithAi()
 * API calls; in AI mode, when NEXT_PUBLIC_USE_MOCK_AI=1 is set for local
 * development, it resolves against the contract-shaped mock instead.
 */
export function useUpload() {
  const [entries, setEntries] = useState<UploadQueueEntry[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const counter = useRef(0);

  const update = useCallback((id: string, patch: Partial<UploadQueueEntry>) => {
    setEntries((prev) => prev.map((entry) => (entry.id === id ? { ...entry, ...patch } : entry)));
  }, []);

  const enqueue = useCallback(
    (files: FileList | File[], options: EnqueueOptions = {}) => {
      const aiScan = options.aiScan ?? false;
      const list = Array.from(files);
      const newEntries: UploadQueueEntry[] = list.map((file) => ({
        id: `upload-${++counter.current}`,
        fileName: file.name,
        progress: 0,
        status: "queued",
      }));
      setEntries((prev) => [...prev, ...newEntries]);
      newEntries.forEach((entry) => {
        const file = list.find((f) => f.name === entry.fileName);
        if (!file) return;
        setActiveId(entry.id);
        update(entry.id, { status: "uploading" });

        const settleDone = (aiResult: AiScanUploadResponse | undefined, result: ReceiptItem) => {
          update(entry.id, {
            status: "done",
            progress: 100,
            result,
            ...(aiResult ? { aiResult } : {}),
          });
          setActiveId((current) => (current === entry.id ? null : current));
        };

        if (aiScan) {
          const runAiUpload = async () => {
            if (AI_MOCK_ENABLED) {
              // Simulate a real upload's progress curve, then resolve the
              // contract-shaped mock (dev-only; see lib/aiScanMock.ts).
              update(entry.id, { progress: 45 });
              await new Promise((resolve) => setTimeout(resolve, 400));
              update(entry.id, { progress: 85 });
              await new Promise((resolve) => setTimeout(resolve, 400));
              const mock = mockAiScanResponseForFile(entry.fileName);
              settleDone(mock, mock);
              return;
            }
            const aiResult = await uploadReceiptWithAi(file, (percent) =>
              update(entry.id, { progress: percent }),
            );
            settleDone(aiResult, aiResult);
          };
          runAiUpload().catch((err: unknown) => {
            const message = err instanceof Error ? err.message : "AI Scan failed";
            update(entry.id, { status: "error", error: message });
            setActiveId((current) => (current === entry.id ? null : current));
          });
        } else {
          uploadReceipt(file, (percent) => update(entry.id, { progress: percent }))
            .then((result) => settleDone(undefined, result))
            .catch((err: unknown) => {
              const message = err instanceof Error ? err.message : "Upload failed";
              update(entry.id, { status: "error", error: message });
              setActiveId((current) => (current === entry.id ? null : current));
            });
        }
      });
    },
    [update],
  );

  const clear = useCallback(() => setEntries([]), []);
  const remove = useCallback(
    (id: string) => setEntries((prev) => prev.filter((entry) => entry.id !== id)),
    [],
  );

  const doneEntries = entries.filter((entry) => entry.status === "done");
  const lastResult = doneEntries.at(-1)?.result;
  /** Most recent AI-mode result (source + ai_result/tesseract_result). */
  const lastAiResult = doneEntries.at(-1)?.aiResult ?? null;

  return { entries, activeId, enqueue, clear, remove, lastResult, lastAiResult };
}
