/**
 * Shared formatting helpers — currency, dates, file sizes, classes.
 */

const LOCALE_TO_INTL: Record<string, string> = {
  en: "en-US", hu: "hu-HU", de: "de-DE", fr: "fr-FR", es: "es-ES",
  it: "it-IT", pt: "pt-PT", nl: "nl-NL", pl: "pl-PL", ro: "ro-RO",
};

const LOCALE_STORAGE_KEY = "receiptlens.locale";

/**
 * The UI language code: the saved choice, else the browser's first supported
 * language, else English. Kept here (no React) so server components can format too.
 */
export function preferredLocaleCode(): string {
  if (typeof window === "undefined") return "en";
  try {
    const stored = window.localStorage.getItem(LOCALE_STORAGE_KEY);
    if (stored && LOCALE_TO_INTL[stored]) return stored;
  } catch { /* storage blocked: use the browser's language */ }
  const preferred = navigator.languages?.length ? navigator.languages : [navigator.language];
  for (const tag of preferred) {
    const base = String(tag ?? "").toLowerCase().split("-")[0];
    if (LOCALE_TO_INTL[base]) return base;
  }
  return "en";
}

function currentIntlLocale(): string {
  return LOCALE_TO_INTL[preferredLocaleCode()] ?? "en-US";
}

/** The currency a new household most likely uses, from its language. */
export function defaultCurrencyForLocale(locale: string): string {
  // HUF only for Hungarian. Other locales get their country's currency; where the language is
  // spoken in several currency areas (English) or the locale is unknown, EUR.
  const byLocale: Record<string, string> = {
    hu: "HUF", de: "EUR", fr: "EUR", es: "EUR", it: "EUR", pt: "EUR", nl: "EUR", pl: "PLN", ro: "RON",
  };
  return byLocale[locale] ?? "EUR";
}

/**
 * The household's working currency: the one it chose or its receipts state;
 * with neither, the one that fits its language.
 */
export function effectiveBaseCurrency(
  prefs: { base_currency?: string | null; base_currency_source?: string | null } | undefined,
  locale: string,
): string {
  if (prefs?.base_currency && prefs.base_currency_source !== "default") return prefs.base_currency;
  return defaultCurrencyForLocale(locale);
}

/** Currencies that are quoted in whole units (no cents in everyday use). */
const WHOLE_UNIT_CURRENCIES = new Set(["HUF", "JPY"]);

/**
 * Format an amount in a given currency, e.g. 1234.5, "USD" → "$1,234.50".
 *
 * Whole-unit currencies (HUF, JPY) drop the empty cents when the amount is a
 * whole number. With no currency the amount is a plain number: guessing a
 * symbol would state a currency nobody knows.
 */
export function formatMoney(
  amount: number | null | undefined,
  currency: string | null | undefined = "USD",
  locale?: string,
): string {
  if (amount === null || amount === undefined || Number.isNaN(amount)) return "—";
  const effLocale = locale ?? currentIntlLocale();
  const whole = !!currency && WHOLE_UNIT_CURRENCIES.has(currency) && Number.isInteger(amount);
  const digits = whole ? 0 : 2;
  try {
    if (!currency) {
      return new Intl.NumberFormat(effLocale, {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      }).format(amount);
    }
    return new Intl.NumberFormat(effLocale, {
      style: "currency",
      currency,
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(amount);
  } catch {
    // Unknown currency code — fall back to a plain formatted number.
    return `${currency ?? ""} ${amount.toFixed(digits)}`.trim();
  }
}

/** Format an ISO date (YYYY-MM-DD) or ISO datetime for display. */
export function formatDate(
  iso: string | null | undefined,
  locale?: string,
): string {
  if (!iso) return "—";
  const date = new Date(iso.length === 10 ? `${iso}T00:00:00` : iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat(locale ?? currentIntlLocale(), {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(date);
}

/** "2026-10" → "October 2026" / "2026. október". */
export function formatMonth(yearMonth: string | null | undefined, locale?: string): string {
  if (!yearMonth || !/^\d{4}-\d{2}$/.test(yearMonth)) return yearMonth ?? "—";
  return new Intl.DateTimeFormat(locale ?? currentIntlLocale(), { year: "numeric", month: "long" })
    .format(new Date(`${yearMonth}-01T00:00:00`));
}

/** Format a datetime with time, e.g. "Aug 5, 2026, 3:04 PM". */
export function formatDateTime(
  iso: string | null | undefined,
  locale?: string,
): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat(locale ?? currentIntlLocale(), {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

/** Human-readable file size, e.g. 1536 → "1.5 KB". */
export function formatFileSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return "—";
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unit = units[0];
  for (let i = 1; i < units.length && value >= 1024; i += 1) {
    value /= 1024;
    unit = units[i];
  }
  return `${value.toFixed(value >= 10 ? 0 : 1)} ${unit}`;
}

/** Percentage with one decimal, e.g. 0.9234 → "92.3%". */
export function formatPercent(ratio: number): string {
  if (!Number.isFinite(ratio)) return "—";
  return `${(ratio * 100).toFixed(1)}%`;
}

/** Combine Tailwind class names, skipping falsy entries. */
export function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}

/** Safe HTML escaping for any dynamic user content (defense-in-depth). */
export function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/** Convert a value to a slug for stable keys/URLs. */
export function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/** Relative "time ago" label for activity feeds. */
export function timeAgo(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return formatDate(iso);
}

/** Parses "4 400,50", "4,400.50" and "4400.5"; returns NaN for anything else. */
export function parseAmount(raw: string): number {
  const compact = raw.replace(/[\s ]/g, "");
  if (!/^\d[\d.,]*$/.test(compact)) return Number.NaN;
  const lastComma = compact.lastIndexOf(",");
  const lastDot = compact.lastIndexOf(".");
  let normal = compact;
  if (lastComma >= 0 && lastDot >= 0) {
    const decimal = lastComma > lastDot ? "," : ".";
    const group = decimal === "," ? "." : ",";
    normal = compact.split(group).join("").replace(decimal, ".");
  } else if (lastComma >= 0) {
    normal = compact.replace(",", ".");
  }
  return Number(normal);
}
