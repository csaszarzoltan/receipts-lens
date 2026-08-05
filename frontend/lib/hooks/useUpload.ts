"use client";

import { useCallback, useRef, useState } from "react";
import { uploadReceipt } from "@/lib/api";
import type { ReceiptItem } from "@/lib/types";

export interface UploadQueueEntry {
  id: string;
  fileName: string;
  progress: number;
  status: "queued" | "uploading" | "done" | "error";
  result?: ReceiptItem & { applied_rules?: unknown };
  error?: string;
}

/**
 * Upload queue state machine — one entry per file with progress, then a
 * navigable result. Driven by the real uploadReceipt() API call.
 */
export function useUpload() {
  const [entries, setEntries] = useState<UploadQueueEntry[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const counter = useRef(0);

  const update = useCallback((id: string, patch: Partial<UploadQueueEntry>) => {
    setEntries((prev) => prev.map((entry) => (entry.id === id ? { ...entry, ...patch } : entry)));
  }, []);

  const enqueue = useCallback(
    (files: FileList | File[]) => {
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
        uploadReceipt(file, (percent) => update(entry.id, { progress: percent }))
          .then((result) => {
            update(entry.id, { status: "done", progress: 100, result });
            setActiveId((current) => (current === entry.id ? null : current));
          })
          .catch((err: unknown) => {
            const message = err instanceof Error ? err.message : "Upload failed";
            update(entry.id, { status: "error", error: message });
            setActiveId((current) => (current === entry.id ? null : current));
          });
      });
    },
    [update],
  );

  const clear = useCallback(() => setEntries([]), []);
  const remove = useCallback(
    (id: string) => setEntries((prev) => prev.filter((entry) => entry.id !== id)),
    [],
  );

  const lastResult = entries.filter((entry) => entry.status === "done").at(-1)?.result;

  return { entries, activeId, enqueue, clear, remove, lastResult };
}
