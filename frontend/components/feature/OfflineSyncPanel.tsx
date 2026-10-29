"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSWRConfig } from "swr";
import { uploadReceipt } from "@/lib/api";
import { commandFeatureItem, createFeatureItem, FeatureApiError, type FeatureItem } from "@/lib/featureApi";
import type { FeatureConfig } from "@/lib/featureConfigs";
import { ft } from "@/lib/featureI18n";
import { listQueued, removeQueued, type PendingCapture } from "@/lib/offlineCapture";
import { useTranslation } from "@/lib/i18n";

/** Idempotency keys derive from the queue entry, so a retry after a partial failure does not duplicate.
 * Keys must be at least 16 characters; the entry id is a UUID, so the prefix keeps them distinct per step.
 */
function stepKey(entry: PendingCapture, step: string): string {
  return `offline-${step}-${entry.id}`;
}

/**
 * Offline queue: photos captured without a connection wait here. When the browser is online
 * each one is uploaded, recorded as an offline sync item, and synced against the server.
 */
export default function OfflineSyncPanel({ config }: { config: FeatureConfig }) {
  const { locale } = useTranslation();
  const { mutate } = useSWRConfig();
  const t = (key: string) => ft(key, locale);
  const [queue, setQueue] = useState<PendingCapture[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  // A ref, not state: the mount effect and the online event can both call syncAll before React re-renders.
  const running = useRef(false);

  const reload = useCallback(() => listQueued().then(setQueue).catch(() => setQueue([])), []);

  const syncAll = useCallback(async () => {
    if (running.current || (typeof navigator !== "undefined" && navigator.onLine === false)) return;
    running.current = true;
    setBusy(true);
    setError(null);
    let synced = 0;
    try {
      for (const entry of await listQueued()) {
        const file = new File([entry.blob], entry.name, { type: entry.type });
        const receipt = await uploadReceipt(file, undefined, stepKey(entry, "upload"));
        let item: FeatureItem = await createFeatureItem(
          config.path,
          {
            client_reference: entry.name,
            payload: { device: (navigator.platform || "browser").slice(0, 64), receipt: receipt.receipt_id },
          },
          stepKey(entry, "create"),
        );
        for (const action of ["queue", "start_upload", "process"]) {
          item = await commandFeatureItem(config.path, item.id, { action, expected_revision: item.revision }, stepKey(entry, action));
        }
        // The client has never seen a server revision for this item, so the base is 0.
        item = await commandFeatureItem(
          config.path,
          item.id,
          { action: "sync", expected_revision: item.revision, payload: { base_revision: 0 } },
          stepKey(entry, "sync"),
        );
        await removeQueued(entry.id);
        synced += 1;
      }
      setMessage(synced > 0 ? t("capture.synced").replace("{n}", String(synced)) : null);
    } catch (err) {
      setError(err instanceof FeatureApiError ? err.message : t("capture.failed"));
    } finally {
      running.current = false;
      setBusy(false);
      await reload();
      await mutate(config.path);
    }
  }, [config.path, mutate, reload]);

  useEffect(() => {
    // Opening the page while online syncs whatever was queued while offline.
    void listQueued().then((rows) => {
      setQueue(rows);
      if (rows.length > 0 && navigator.onLine) void syncAll();
    }).catch(() => setQueue([]));
    const onOnline = () => void syncAll();
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, [reload, syncAll]);

  return (
    <div className="card space-y-3 p-5" data-testid="offline_sync-queue">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
          {t("capture.queuedCount").replace("{n}", String(queue.length))}
        </p>
        <button
          type="button"
          className="btn-primary text-sm"
          disabled={busy || queue.length === 0}
          data-testid="offline_sync-sync-now"
          onClick={() => void syncAll()}
        >
          {busy ? t("capture.syncing") : t("capture.syncNow")}
        </button>
      </div>
      {queue.length > 0 ? (
        <ul className="space-y-1 text-sm text-slate-700 dark:text-slate-300">
          {queue.map((entry) => (
            <li key={entry.id} className="truncate">{entry.name}</li>
          ))}
        </ul>
      ) : null}
      {message ? <p role="status" className="text-sm text-slate-700 dark:text-slate-300">{message}</p> : null}
      {error ? <p role="alert" className="text-sm text-rose-700 dark:text-rose-300">{error}</p> : null}
    </div>
  );
}
