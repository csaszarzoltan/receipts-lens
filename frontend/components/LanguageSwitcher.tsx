"use client";

import { SUPPORTED_LOCALES, LOCALE_LABELS, useTranslation, type Locale } from "@/lib/i18n";

/**
 * Pre-login language switcher — shared across all public routes.
 * Persists via setLocale() → localStorage["receiptlens.locale"] + html lang.
 * Use id="pre-login-locale" so E2E can target it uniformly.
 */
export default function LanguageSwitcher({ id = "pre-login-locale" }: { id?: string }) {
  const { t, locale, setLocale } = useTranslation();
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
        {t("language")}
      </label>
      <select
        id={id}
        className="input"
        value={locale}
        onChange={(event) => setLocale(event.target.value as Locale)}
        aria-label={t("language")}
      >
        {SUPPORTED_LOCALES.map((loc) => (
          <option key={loc} value={loc}>
            {LOCALE_LABELS[loc]}
          </option>
        ))}
      </select>
    </div>
  );
}
