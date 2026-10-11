"use client";
import { useState } from "react";
import { updateReceiptWorkspace } from "@/lib/api";
import { useTranslation, type MessageKey } from "@/lib/i18n";
import { defaultCurrencyForLocale } from "@/lib/utils";
import type { CurrencySource } from "@/lib/types";

const CURRENCIES = ["HUF", "EUR", "USD", "GBP", "CHF", "CZK", "PLN", "RON", "JPY", "CAD", "AUD"];

const SOURCE_KEY: Partial<Record<CurrencySource, MessageKey>> = {
  inferred_merchant: "currencyAssumedMerchant",
  inferred_tenant: "currencyAssumedTenant",
  default: "currencyAssumedDefault",
};

interface CurrencyFieldProps {
  receiptId: string;
  currency: string | null;
  source?: CurrencySource | null;
  assumed?: boolean;
  version: number;
  onSaved: () => void;
}

/** Shows the receipt currency, says whether it was guessed, and lets the user correct it. */
export default function CurrencyField({ receiptId, currency, source, assumed, version, onSaved }: CurrencyFieldProps) {
  const { t, locale } = useTranslation();
  const [value, setValue] = useState(currency ?? defaultCurrencyForLocale(locale));
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const badgeKey = assumed ? SOURCE_KEY[source ?? "default"] ?? "currencyAssumedDefault" : null;
  const userSet = source === "user";

  async function save() {
    setSaving(true);
    setMessage(null);
    try {
      await updateReceiptWorkspace(receiptId, { fields: { currency: value } }, version);
      setMessage(t("currencySaved"));
      onSaved();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : t("saveFailed"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-1" data-testid="currency-field">
      <div className="flex flex-wrap items-center gap-2">
        <label htmlFor="receipt-currency" className="text-xs uppercase tracking-wide text-slate-600 dark:text-slate-400">
          {t("currencyLabel")}
        </label>
        <select
          id="receipt-currency"
          className="input py-1 text-sm"
          value={value}
          onChange={(e) => setValue(e.target.value)}
        >
          {CURRENCIES.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        <button type="button" className="btn-secondary text-sm" disabled={saving || value === currency} onClick={save}>
          {t("currencySave")}
        </button>
        {badgeKey && (
          <span data-testid="currency-assumed" className="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-800 dark:bg-amber-900/40 dark:text-amber-200">
            {t(badgeKey)}
          </span>
        )}
        {userSet && <span className="text-xs text-slate-600 dark:text-slate-400">{t("currencyUserSet")}</span>}
      </div>
      {message && <p role="status" className="text-xs text-slate-600 dark:text-slate-400">{message}</p>}
    </div>
  );
}
