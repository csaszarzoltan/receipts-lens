"use client";

import { useEffect, useRef, useState } from "react";
import { useSWRConfig } from "swr";
import { uploadReceipt } from "@/lib/api";
import { commandFeatureItem, createFeatureItem, FeatureApiError, newIdempotencyKey } from "@/lib/featureApi";
import type { FeatureConfig } from "@/lib/featureConfigs";
import { ft } from "@/lib/featureI18n";
import { queueCapture, listQueued } from "@/lib/offlineCapture";
import { useTranslation } from "@/lib/i18n";

/**
 * Phone capture: uploads the photo as a receipt, opens a mobile capture item for it and
 * attaches the receipt. Without a connection the photo is queued for the offline page.
 */
export default function MobileCapturePanel({ config }: { config: FeatureConfig }) {
  const { locale } = useTranslation();
  const { mutate } = useSWRConfig();
  const t = (key: string) => ft(key, locale);
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [queued, setQueued] = useState(0);

  useEffect(() => {
    listQueued().then((rows) => setQueued(rows.length)).catch(() => setQueued(0));
  }, []);

  async function capture(file: File) {
    if (busy) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      if (typeof navigator !== "undefined" && navigator.onLine === false) {
        await queueCapture(file);
        setQueued((count) => count + 1);
        setMessage(t("capture.queuedOffline"));
        return;
      }
      setMessage(t("capture.uploading"));
      const receipt = await uploadReceipt(file, undefined, newIdempotencyKey());
      const created = await createFeatureItem(
        config.path,
        {
          client_reference: file.name,
          payload: {
            ...(receipt.receipt?.vendor ? { merchant: receipt.receipt.vendor } : {}),
            ...(typeof receipt.receipt?.total === "number" ? { amount: receipt.receipt.total } : {}),
          },
        },
        newIdempotencyKey(),
      );
      await commandFeatureItem(
        config.path,
        created.id,
        { action: "attach", expected_revision: created.revision, payload: { receipt: receipt.receipt_id } },
        newIdempotencyKey(),
      );
      await mutate(config.path);
      setMessage(t("capture.done"));
    } catch (err) {
      setError(err instanceof FeatureApiError ? err.message : t("capture.failed"));
    } finally {
      setBusy(false);
      if (input.current) input.current.value = "";
    }
  }

  return (
    <div className="card space-y-3 p-5" data-testid="mobile_receipts-capture">
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          className="btn-primary text-sm"
          disabled={busy}
          data-testid="mobile_receipts-pick"
          onClick={() => input.current?.click()}
        >
          {busy ? t("capture.uploading") : t("capture.pick")}
        </button>
        <input
          ref={input}
          type="file"
          accept="image/*,application/pdf"
          capture="environment"
          className="hidden"
          data-testid="mobile_receipts-file"
          aria-label={t("capture.pick")}
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void capture(file);
          }}
        />
        {queued > 0 ? (
          <p className="text-sm text-slate-600 dark:text-slate-400">{t("capture.queuedCount").replace("{n}", String(queued))}</p>
        ) : null}
      </div>
      {message ? <p role="status" className="text-sm text-slate-700 dark:text-slate-300">{message}</p> : null}
      {error ? <p role="alert" className="text-sm text-rose-700 dark:text-rose-300">{error}</p> : null}
    </div>
  );
}
