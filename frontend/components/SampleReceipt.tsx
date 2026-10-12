"use client";

import useSWR from "swr";
import { searchReceipts } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { defaultCurrencyForLocale, formatMoney } from "@/lib/utils";

const ITEMS_HUF: Array<[string, number]> = [
  ["Tej 1,5 l", 459],
  ["Kenyér 1 kg", 619],
  ["Alma 1 kg", 899],
  ["Sajt 20 dkg", 1290],
];
const ITEMS_OTHER: Array<[string, number]> = [
  ["Milk 1.5 l", 1.15],
  ["Bread 1 kg", 1.55],
  ["Apples 1 kg", 2.25],
  ["Cheese 200 g", 3.2],
];

/**
 * An example of a read receipt for a household that has none yet. It is drawn
 * here, not stored: nothing is added to the household's data.
 */
export default function SampleReceipt() {
  const { t, locale } = useTranslation();
  const { data } = useSWR("/product/receipts?limit=1&sample-check", () => searchReceipts({ limit: 1 }));
  if (!data || data.items.length > 0) return null;

  const currency = defaultCurrencyForLocale(locale) === "HUF" ? "HUF" : "EUR";
  const items = currency === "HUF" ? ITEMS_HUF : ITEMS_OTHER;
  const total = Math.round(items.reduce((sum, [, price]) => sum + price, 0) * 100) / 100;

  return (
    <section className="card overflow-hidden" aria-label={t("sampleTitle")} data-testid="sample-receipt">
      <div className="border-b border-slate-100 px-5 py-4 dark:border-slate-800">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{t("sampleTitle")}</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{t("sampleDesc")}</p>
      </div>
      <div className="grid gap-6 p-5 sm:grid-cols-2">
        <div
          role="img"
          aria-label={t("sampleReceiptLabel")}
          className="mx-auto w-full max-w-xs rounded-sm border border-dashed border-slate-300 bg-slate-50 p-4 font-mono text-xs text-slate-800 shadow-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        >
          <p className="text-center font-semibold uppercase tracking-wide">Kisbolt Kft.</p>
          <p className="text-center text-slate-600 dark:text-slate-300">2026-10-05</p>
          <ul className="mt-3 space-y-1" aria-hidden="true">
            {items.map(([name, price]) => (
              <li key={name} className="flex justify-between gap-3">
                <span>{name}</span>
                <span className="tabular-nums">{formatMoney(price, currency)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 flex justify-between border-t border-dashed border-slate-400 pt-2 font-semibold">
            <span>{t("sampleTotal").toUpperCase()}</span>
            <span className="tabular-nums">{formatMoney(total, currency)}</span>
          </p>
        </div>
        <div className="space-y-3 text-sm">
        <dl className="space-y-3">
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-slate-600 dark:text-slate-400">{t("sampleShop")}</dt>
            <dd className="mt-0.5 font-medium text-slate-900 dark:text-slate-100">Kisbolt Kft.</dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-slate-600 dark:text-slate-400">{t("sampleDate")}</dt>
            <dd className="mt-0.5 font-medium text-slate-900 dark:text-slate-100">2026-10-05</dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-slate-600 dark:text-slate-400">{t("sampleTotal")}</dt>
            <dd className="mt-0.5 text-lg font-semibold tabular-nums text-slate-900 dark:text-slate-100">
              {formatMoney(total, currency)}
            </dd>
          </div>
        </dl>
          <p className="flex items-start gap-2 text-emerald-800 dark:text-emerald-300">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true" className="mt-0.5 shrink-0">
              <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
              <path d="M4.8 8.2l2.2 2.2 4.2-4.6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>
              {t("sampleLinesMatch")} <strong className="tabular-nums">{formatMoney(total, currency)}</strong>
            </span>
          </p>
        </div>
      </div>
    </section>
  );
}
