"use client";

import React from "react";
import { createWarranty } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";

interface WarrantyFormProps {
  /** Values carried over from a receipt, when the user came from one. */
  prefill?: { item_name?: string; merchant?: string; purchase_date?: string; receipt_id?: string };
  onSaved: () => void;
  onCancel: () => void;
}

function today(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

/** Adds an item whose return window and warranty the household wants to keep track of. */
export default function WarrantyForm({ prefill, onSaved, onCancel }: WarrantyFormProps) {
  const { t } = useTranslation();
  const [itemName, setItemName] = React.useState(prefill?.item_name ?? "");
  const [merchant, setMerchant] = React.useState(prefill?.merchant ?? "");
  const [purchaseDate, setPurchaseDate] = React.useState(prefill?.purchase_date ?? today());
  const [returnDays, setReturnDays] = React.useState("14");
  const [months, setMonths] = React.useState("24");
  const [notes, setNotes] = React.useState("");
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await createWarranty({
        item_name: itemName.trim(),
        merchant: merchant.trim() || undefined,
        purchase_date: purchaseDate,
        return_days: Number(returnDays) || 0,
        warranty_months: Number(months) || 0,
        receipt_id: prefill?.receipt_id,
        notes: notes.trim() || undefined,
      });
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("warrantySaveError"));
    } finally {
      setSaving(false);
    }
  }

  const label = "mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200";

  return (
    <form onSubmit={submit} className="card space-y-4 p-5" aria-label={t("warrantyAdd")} data-testid="warranty-form">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label htmlFor="w-item" className={label}>{t("warrantyItemName")}</label>
          <input id="w-item" className="input" required maxLength={200} value={itemName}
                 onChange={(e) => setItemName(e.target.value)} />
        </div>
        <div>
          <label htmlFor="w-shop" className={label}>{t("warrantyMerchant")}</label>
          <input id="w-shop" className="input" maxLength={200} value={merchant}
                 onChange={(e) => setMerchant(e.target.value)} />
        </div>
        <div>
          <label htmlFor="w-date" className={label}>{t("warrantyPurchaseDate")}</label>
          <input id="w-date" type="date" className="input" required value={purchaseDate} max={today()}
                 onChange={(e) => setPurchaseDate(e.target.value)} />
        </div>
        <div>
          <label htmlFor="w-return" className={label}>{t("warrantyReturnDays")}</label>
          <input id="w-return" type="number" inputMode="numeric" min={0} max={365} className="input"
                 value={returnDays} onChange={(e) => setReturnDays(e.target.value)} />
        </div>
        <div>
          <label htmlFor="w-months" className={label}>{t("warrantyMonths")}</label>
          <input id="w-months" type="number" inputMode="numeric" min={0} max={120} className="input"
                 value={months} onChange={(e) => setMonths(e.target.value)} />
        </div>
        <div className="sm:col-span-2">
          <label htmlFor="w-notes" className={label}>{t("warrantyNotes")}</label>
          <input id="w-notes" className="input" maxLength={1000} value={notes}
                 onChange={(e) => setNotes(e.target.value)} />
        </div>
      </div>
      <p className="text-xs text-slate-600 dark:text-slate-400">{t("warrantyFormHint")}</p>
      {error ? <p role="alert" className="text-sm text-rose-700 dark:text-rose-300">{error}</p> : null}
      <div className="flex flex-wrap items-center gap-2">
        <button type="submit" className="btn-primary text-sm" disabled={saving || !itemName.trim()}>
          {saving ? t("savingLabel") : t("warrantySave")}
        </button>
        <button type="button" className="btn-secondary text-sm" onClick={onCancel}>{t("warrantyCancel")}</button>
      </div>
    </form>
  );
}
