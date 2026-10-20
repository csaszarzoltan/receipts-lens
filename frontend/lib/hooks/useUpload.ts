"use client";
import { mutate } from "swr";
import { useCallback, useRef, useState } from "react";
import { uploadReceipt, uploadReceiptWithAi } from "@/lib/api";
import { AI_MOCK_ENABLED, mockAiScanResponseForFile } from "@/lib/aiScanMock";
import { AI_SCAN_ENABLED } from "@/lib/featureFlags";
import type { AiScanUploadResponse, ReceiptItem } from "@/lib/types";

export interface UploadQueueEntry {
  id: string;
  fileName: string;
  progress: number;
  status: "queued" | "uploading" | "processing" | "done" | "error";
  result?: ReceiptItem & { applied_rules?: unknown; duplicate_of?: string | null };
  aiResult?: AiScanUploadResponse;
  error?: string;
  errorStatus?: number;
}
export interface EnqueueOptions { aiScan?: boolean; }
interface UploadTask { file: File; aiScan: boolean; key: string; running: boolean; }

export function useUpload() {
  const [entries, setEntries] = useState<UploadQueueEntry[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const tasks = useRef(new Map<string, UploadTask>());
  const update = useCallback((id: string, patch: Partial<UploadQueueEntry>) => {
    setEntries(prev => prev.map(entry => entry.id === id ? {...entry,...patch} : entry));
  }, []);
  const run = useCallback(async (id: string) => {
    const task = tasks.current.get(id);
    if (!task || task.running) return;
    task.running = true;
    setActiveId(id);
    update(id,{status:"uploading",progress:0,error:undefined,errorStatus:undefined});
    try {
      if (!task.file.type.startsWith("image/")) throw Object.assign(new Error("Unsupported image"),{status:415});
      if (task.file.size > 20 * 1024 * 1024) throw Object.assign(new Error("Image too large"),{status:413});
      const progress = (percent: number) => update(id,{progress:percent,status:percent >= 100 ? "processing" : "uploading"});
      const result = task.aiScan
        ? AI_MOCK_ENABLED ? mockAiScanResponseForFile(task.file.name)
          : await uploadReceiptWithAi(task.file,progress,task.key)
        : await uploadReceipt(task.file,progress,task.key);
      update(id,{status:"done",progress:100,result,...(task.aiScan ? {aiResult:result as AiScanUploadResponse} : {})});
    } catch (err) {
      update(id,{status:"error",error:err instanceof Error ? err.message : "Upload failed",
        errorStatus:typeof err === "object" && err !== null && "status" in err ? Number(err.status) : undefined});
    } finally {
      void mutate("/api/v1/quota").catch(() => undefined);
      task.running = false;
      setActiveId(current => current === id ? null : current);
    }
  },[update]);
  const enqueue = useCallback((files: FileList | File[], options: EnqueueOptions = {}) => {
    const newEntries = Array.from(files).map(file => {
      const id = crypto.randomUUID();
      tasks.current.set(id,{file,aiScan:!!options.aiScan && AI_SCAN_ENABLED,key:crypto.randomUUID(),running:false});
      return {id,fileName:file.name,progress:0,status:"queued" as const};
    });
    setEntries(prev=>[...prev,...newEntries]);
    newEntries.forEach(entry=>void run(entry.id));
  },[run]);
  const remove = useCallback((id: string) => {
    if (tasks.current.get(id)?.running) return;
    tasks.current.delete(id);
    setEntries(prev=>prev.filter(entry=>entry.id !== id));
  },[]);
  const clear = useCallback(() => {
    for (const [id,task] of tasks.current) if (!task.running) tasks.current.delete(id);
    setEntries(prev=>prev.filter(entry=>tasks.current.has(entry.id)));
  },[]);
  const retry = useCallback((id: string) => void run(id),[run]);
  const last = entries.filter(entry=>entry.status === "done").at(-1);
  return {entries,activeId,enqueue,clear,remove,retry,lastResult:last?.result,lastAiResult:last?.aiResult ?? null};
}
