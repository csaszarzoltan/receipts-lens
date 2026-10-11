"use client";

import { useState, type FormEvent } from "react";
import { createBudget } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";

const CURRENCIES = ["HUF", "EUR", "USD", "GBP", "CHF", "CZK", "PLN", "JPY", "CAD", "AUD"];

interface BudgetFormProps {
  defaultCurrency?: string;
  onCreated: () => void;
}

/** Creates a monthly budget for one category (POST /api/v1/budgets). */
export default function BudgetForm({ defaultCurrency, onCreated }: BudgetFormProps) {
  const { t, locale } = useTranslation();
  const [category, setCategory] = useState("");
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState(defaultCurrency ?? (locale === "hu" ? "HUF" : "USD"));
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");

  async function submit(event: FormEvent) {
    event.preventDefault();
    const value = Number(amount.replace(/\s/g, "").replace(",", "."));
    if (!category.trim() || !Number.isFinite(value) || value <= 0) {
      setStatus("error");
      return;
    }
    setStatus("saving");
    try {
      await createBudget({ category: category.trim(), amount: value, currency });
      setStatus("saved");
      setCategory("");
      setAmount("");
      onCreated();
    } catch {
      setStatus("error");
    }
  }

  return (
    <form onSubmit={submit} className="card max-w-xl space-y-4 p-5" aria-label={t("budgetCreateTitle")}>
      <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{t("budgetCreateTitle")}</h2>
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="sm:col-span-3">
          <label htmlFor="budget-category" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
            {t("budgetCategoryLabel")}
          </label>
          <input id="budget-category" className="input" value={category} onChange={(e) => setCategory(e.target.value)} required />
        </div>
        <div className="sm:col-span-2">
          <label htmlFor="budget-amount" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
            {t("budgetAmountLabel")}
          </label>
          <input
            id="budget-amount"
            className="input"
            inputMode="decimal"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="budget-currency" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
            {t("budgetCurrencyLabel")}
          </label>
          <select id="budget-currency" className="input" value={currency} onChange={(e) => setCurrency(e.target.value)}>
            {CURRENCIES.map((code) => (
              <option key={code}>{code}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button type="submit" className="btn-primary text-sm" disabled={status === "saving"}>
          {t("budgetCreateButton")}
        </button>
        {status === "saved" ? (
          <span role="status" className="text-sm text-emerald-700 dark:text-emerald-400">{t("budgetCreated")}</span>
        ) : null}
        {status === "error" ? (
          <span role="alert" className="text-sm text-rose-700 dark:text-rose-400">{t("budgetCreateFailed")}</span>
        ) : null}
      </div>
    </form>
  );
}
