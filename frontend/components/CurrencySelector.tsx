"use client";
import { useEffect, useState } from "react";
import { savePreferences } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";

const CURRENCIES = ["HUF", "EUR", "USD", "GBP", "CHF", "CZK", "PLN", "RON", "JPY", "CAD", "AUD"];

/** The household's default currency: dashboard totals and budgets use it. */
export default function CurrencySelector({ value, onSaved }: { value: string; onSaved?: () => void }) {
  const { t } = useTranslation();
  const [currency, setCurrency] = useState(value);
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  useEffect(() => setCurrency(value), [value]);

  async function change(next: string) {
    setCurrency(next);
    setStatus("saving");
    try {
      await savePreferences({ base_currency: next });
      setStatus("saved");
      onSaved?.();
    } catch {
      setStatus("error");
    }
  }

  const note =
    status === "saving" ? t("savingLabel")
    : status === "saved" ? t("currencySaved")
    : status === "error" ? t("currencySaveError")
    : t("defaultCurrencyHint");

  return (
    <div>
      <label htmlFor="pref-base-currency" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
        {t("defaultCurrencyLabel")}
      </label>
      <select
        id="pref-base-currency"
        data-testid="base-currency-selector"
        className="input"
        value={currency}
        onChange={(e) => change(e.target.value)}
      >
        {CURRENCIES.map((c) => (
          <option key={c}>{c}</option>
        ))}
      </select>
      <p role="status" className="mt-1 text-xs text-slate-600 dark:text-slate-400">{note}</p>
    </div>
  );
}
