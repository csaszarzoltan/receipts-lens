"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import useSWR from "swr";
import { getReceipt, getReceiptBoxes, getReceiptHistory, getReceiptImage, updateLineItems, updateMetadata } from "@/lib/api";
import type { HistoryEntry, LineItem, OCRBox, ReceiptItem } from "@/lib/types";
import ConfidenceBadge from "@/components/ConfidenceBadge";
import StatusBadge from "@/components/StatusBadge";
import Money from "@/components/Money";
import { Skeleton, SkeletonCard } from "@/components/Skeleton";
import { formatDate, formatDateTime, formatMoney } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

function ReceiptDetailContent({ id }: { id: string }) {
  const { t } = useTranslation();
  const { data: page, error, isLoading, mutate } = useSWR(`/receipt-detail/${id}`, () =>
    getReceipt(id),
  );
  const { data: boxesData } = useSWR(id ? `/boxes/${id}` : null, () => getReceiptBoxes(id));
  const { data: historyData } = useSWR(id ? `/history/${id}` : null, () => getReceiptHistory(id));

  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [tags, setTags] = useState("");
  const [project, setProject] = useState("");
  const [costCenter, setCostCenter] = useState("");
  const [lineItems, setLineItems] = useState<LineItem[]>([]);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const item: ReceiptItem | undefined = page;

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    getReceiptImage(id)
      .then((blob) => {
        if (!cancelled) setImageUrl(URL.createObjectURL(blob));
      })
      .catch(() => setImageUrl(null));
    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    if (item) {
      setTags(item.metadata?.tags?.join(", ") ?? "");
      setProject(item.metadata?.project ?? "");
      setCostCenter(item.metadata?.cost_center ?? "");
      setLineItems(item.receipt.line_items ?? []);
    }
  }, [item]);

  const saveMetadata = useCallback(async () => {
    if (!item) return;
    setSaving(true);
    setSaveMessage(null);
    try {
      await updateMetadata(id, {
        tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean),
        project: project || null,
        cost_center: costCenter || null,
      });
      setSaveMessage(t("metadataSaved"));
      mutate();
    } catch (err) {
      setSaveMessage(err instanceof Error ? err.message : t("saveFailed"));
    } finally {
      setSaving(false);
    }
  }, [item, id, tags, project, costCenter, mutate]);

  const saveLineItems = useCallback(async () => {
    if (!item) return;
    setSaving(true);
    setSaveMessage(null);
    try {
      await updateLineItems(id, lineItems, item.version);
      setSaveMessage(t("lineItemsSaved"));
      setEditing(false);
      mutate();
    } catch (err) {
      setSaveMessage(err instanceof Error ? err.message : t("saveFailed"));
    } finally {
      setSaving(false);
    }
  }, [item, id, lineItems, mutate]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-56" />
        <div className="grid gap-4 lg:grid-cols-2">
          <SkeletonCard className="h-80" />
          <SkeletonCard className="h-80" />
        </div>
      </div>
    );
  }

  if (error || !item) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Receipt</h1>
        <p className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-300">
          {t("receiptNotFound")}
        </p>
      </div>
    );
  }

  const receipt = item.receipt;
  const boxes: OCRBox[] = boxesData?.boxes ?? [];
  const history: HistoryEntry[] = historyData?.items ?? [];
  const confidenceValues = Object.values(receipt.confidence ?? {}).filter((value) => value > 0);
  const avgConfidence = confidenceValues.length
    ? confidenceValues.reduce((sum, value) => sum + value, 0) / confidenceValues.length
    : 1;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {receipt.vendor || t("unknownVendorLabel")}
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <StatusBadge status={item.status} />
            <ConfidenceBadge value={avgConfidence} label={t("averageOcrConfidence")} />
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {formatDateTime(item.created_at)}
            </span>
          </div>
        </div>
        <a href="/receipts" className="btn-secondary">{t("allReceiptsLink")}</a>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Receipt image */}
        <section className="card overflow-hidden" aria-label="Receipt image">
          <h2 className="border-b border-slate-200 px-5 py-3 text-sm font-semibold text-slate-900 dark:border-slate-800 dark:text-slate-100">
            {t("scannedReceiptTitle")}
          </h2>
          {imageUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={imageUrl}
              alt={`Scanned receipt from ${receipt.vendor || "unknown vendor"}`}
              className="h-80 w-full object-contain bg-slate-100 dark:bg-slate-900"
              loading="lazy"
            />
          ) : (
            <div className="flex h-80 items-center justify-center text-sm text-slate-400">
              {t("imageUnavailable")}
            </div>
          )}
        </section>

        {/* Extracted fields */}
        <section className="card" aria-label="Extracted data">
          <h2 className="border-b border-slate-200 px-5 py-3 text-sm font-semibold text-slate-900 dark:border-slate-800 dark:text-slate-100">
            {t("extractedDataTitle")}
          </h2>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-3 px-5 py-4 text-sm">
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-400">Vendor</dt>
              <dd className="mt-0.5 font-medium text-slate-900 dark:text-slate-100">{receipt.vendor || "—"}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-400">Date</dt>
              <dd className="mt-0.5 font-medium text-slate-900 dark:text-slate-100">{formatDate(receipt.date)}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-400">Total</dt>
              <dd className="mt-0.5 text-lg font-semibold text-slate-900 dark:text-slate-100">
                <Money amount={receipt.total} currency={receipt.currency} />
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-400">Tax</dt>
              <dd className="mt-0.5 font-medium text-slate-900 dark:text-slate-100">
                <Money amount={receipt.tax} currency={receipt.currency} />
              </dd>
            </div>
            <div className="col-span-2">
              <dt className="text-xs uppercase tracking-wide text-slate-400">Category</dt>
              <dd className="mt-0.5 font-medium text-slate-900 dark:text-slate-100">
                {receipt.category ?? t("uncategorizedLabel")}
              </dd>
            </div>
          </dl>

          <h3 className="border-t border-slate-200 px-5 pt-3 text-sm font-semibold text-slate-900 dark:border-slate-800 dark:text-slate-100">
            {t("metadataTitle")}
          </h3>
          <div className="space-y-3 px-5 py-4">
            <div>
              <label htmlFor="tags" className="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">
                {t("tagsLabel")}
              </label>
              <input id="tags" className="input" value={tags} onChange={(event) => setTags(event.target.value)} placeholder={t("tagsPlaceholder")} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="project" className="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">{t("projectLabel")}</label>
                <input id="project" className="input" value={project} onChange={(event) => setProject(event.target.value)} />
              </div>
            </div>
            <button type="button" onClick={saveMetadata} disabled={saving} className="btn-secondary text-sm">
              {saving ? t("savingLabel") : t("saveMetadataLabel")}
            </button>
          </div>
        </section>
      </div>

      {/* Line items */}
      <section className="card" aria-label="Line items">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3 dark:border-slate-800">
          <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{t("lineItemsTitle")}</h2>
          {!editing ? (
            <button type="button" onClick={() => setEditing(true)} className="text-sm font-medium text-brand-600 hover:underline dark:text-brand-400">
              {t("editItemsLabel")}
            </button>
          ) : null}
        </div>
        {lineItems.length === 0 ? (
          <p className="px-5 py-6 text-sm text-slate-500 dark:text-slate-400">{t("noLineItems")}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[480px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-slate-800 dark:text-slate-400">
                  <th className="px-5 py-2">{t("itemHeader")}</th>
                  <th className="px-5 py-2 text-right">{t("priceHeader")}</th>
                  <th className="px-5 py-2 text-right">{t("qtyHeader")}</th>
                  <th className="px-5 py-2">{t("categoryHeader")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {lineItems.map((line, index) => (
                  <tr key={`${line.name}-${index}`}>
                    <td className="px-5 py-2 font-medium text-slate-800 dark:text-slate-100">{line.name}</td>
                    <td className="px-5 py-2 text-right text-slate-600 dark:text-slate-300">
                      {editing ? (
                        <input
                          type="number"
                          step="0.01"
                          value={line.price}
                          onChange={(event) => {
                            const next = [...lineItems];
                            next[index] = { ...line, price: Number(event.target.value) };
                            setLineItems(next);
                          }}
                          className="input w-24 text-right"
                          aria-label={`Price for ${line.name}`}
                        />
                      ) : (
                        formatMoney(line.price, receipt.currency)
                      )}
                    </td>
                    <td className="px-5 py-2 text-right text-slate-600 dark:text-slate-300">{line.quantity ?? 1}</td>
                    <td className="px-5 py-2 text-slate-600 dark:text-slate-300">{line.category ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {editing ? (
          <div className="flex items-center gap-2 border-t border-slate-200 px-5 py-3 dark:border-slate-800">
            <button type="button" onClick={saveLineItems} disabled={saving} className="btn-primary text-sm">
              {saving ? t("savingLabel") : t("saveLineItemsLabel")}
            </button>
            <button type="button" onClick={() => setEditing(false)} className="btn-secondary text-sm">
              {t("cancel")}
            </button>
            <span className="text-xs text-slate-400">{t("optimisticConcurrencyHint")} v{item.version})</span>
          </div>
        ) : null}
        {saveMessage ? (
          <p className="px-5 py-2 text-xs text-emerald-600 dark:text-emerald-400" role="status">{saveMessage}</p>
        ) : null}
      </section>

      {/* OCR boxes + history */}
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="card" aria-label="OCR boxes">
          <h2 className="border-b border-slate-200 px-5 py-3 text-sm font-semibold text-slate-900 dark:border-slate-800 dark:text-slate-100">
            {t("ocrTextTitle")} ({boxes.length})
          </h2>
          <ul className="max-h-64 overflow-y-auto px-5 py-4">
            {boxes.length === 0 ? (
              <li className="text-sm text-slate-400">{t("noOcrBoxes")}</li>
            ) : (
              boxes.map((box, index) => (
                <li key={index} className="mb-2 flex items-center justify-between gap-3 text-sm">
                  <span className="truncate text-slate-700 dark:text-slate-200">{box.text}</span>
                  <ConfidenceBadge value={box.confidence} />
                </li>
              ))
            )}
          </ul>
        </section>
      </div>

      <section className="card" aria-label="History">
        <h2 className="border-b border-slate-200 px-5 py-3 text-sm font-semibold text-slate-900 dark:border-slate-800 dark:text-slate-100">
          {t("historyTitle")}
        </h2>
        {history.length === 0 ? (
          <p className="px-5 py-4 text-sm text-slate-400">{t("noHistory")}</p>
        ) : (
          <ol className="px-5 py-4">
            {history.map((entry, index) => (
              <li key={index} className="relative pb-4 pl-6 last:pb-0">
                <span className="absolute left-1 top-1.5 h-2.5 w-2.5 rounded-full bg-brand-500" aria-hidden="true" />
                <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{entry.action}</p>
                <p className="text-xs text-slate-400">
                  {formatDateTime(entry.created_at)} · {entry.actor_role}
                </p>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}

export default function ReceiptDetailPage({ params }: { params: { id: string } }) {
  return (
    <Suspense fallback={<SkeletonCard className="h-96" />}>
      <ReceiptDetailContent id={params.id} />
    </Suspense>
  );
}
