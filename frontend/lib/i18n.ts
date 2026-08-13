/**
 * Internationalization — English-first message catalog with a `t()` lookup
 * and a `useTranslation()` hook ready for future locales (Hungarian catalog
 * included as a demonstration of the structure).
 */
import { useCallback, useState } from "react";

export type Locale = "en" | "hu";

export const messages = {
  en: {
    appName: "ReceiptLens",
    tagline: "Scan receipts. Track spending. Stay ahead.",
    dashboard: "Dashboard",
    receipts: "Receipts",
    upload: "Upload",
    review: "Review",
    approvals: "Approvals",
    duplicates: "Duplicates",
    automations: "Automations",
    accounting: "Accounting",
    exports: "Export Center",
    inbox: "Email Inbox",
    subscriptions: "Subscriptions",
    forecast: "Forecast",
    budget: "Budget",
    reports: "Reports",
    integrations: "Integrations",
    settings: "Settings",
    onboarding: "Onboarding",
    logout: "Log out",
    login: "Sign in",
    register: "Create account",
    totalReceipts: "Total receipts",
    totalSpent: "Total spent",
    needsReview: "Needs review",
    budgetStatus: "Budget status",
    spendingTrend: "Spending trend",
    thisMonth: "This month",
    noReceipts: "No receipts yet",
    noReceiptsHint: "Upload your first receipt to get started",
    uploadFirst: "Upload a receipt",
    allClear: "All clear!",
    nothingPending: "Nothing pending",
    noDuplicates: "No duplicates found",
    noRules: "No rules yet",
    noEmails: "No emails received",
    noSubscriptions: "No recurring expenses",
    notEnoughData: "Not enough data",
    notEnoughDataHint: "Need at least 2 periods of history",
    noBudgetSet: "No budget set",
    noBudgetSetHint: "Create a budget to track category spending",
    search: "Search",
    filter: "Filter",
    date: "Date",
    merchant: "Merchant",
    category: "Category",
    status: "Status",
    total: "Total",
    currency: "Currency",
    vendor: "Vendor",
    tax: "Tax",
    lineItems: "Line items",
    confidence: "Confidence",
    loading: "Loading…",
    error: "Something went wrong",
    retry: "Retry",
    save: "Save",
    cancel: "Cancel",
    delete: "Delete",
    edit: "Edit",
    next: "Next",
    back: "Back",
    done: "Done",
    skip: "Skip",
    uploadReceipt: "Upload receipt",
    dragDrop: "Drag & drop a receipt image here, or click to browse",
    cameraCapture: "Take a photo",
    processing: "Processing…",
    ocrPreview: "OCR result",
    uploadAnother: "Upload another",
    viewReceipt: "View receipt",
    forecastTitle: "Spending forecast",
    anomalies: "Anomalies",
    budgetVariance: "Budget variance",
    projectedSpend: "Projected spend",
    expectedOverage: "Expected overage",
    onTrack: "On track",
    warning: "Warning",
    overBudget: "Over budget",
    welcome: "Welcome to ReceiptLens",
    welcomeHint: "Scan a receipt to start tracking your expenses",
    step: "Step",
    of: "of",
    skipOnboarding: "Skip onboarding",
    finish: "Finish",
    darkMode: "Dark mode",
    lightMode: "Light mode",
  },
  hu: {
    appName: "ReceiptLens",
    tagline: "Nyugták beolvasása. Kiadáskövetés. Előre gondolkodás.",
    dashboard: "Áttekintés",
    receipts: "Vásárlások",
    upload: "Nyugta hozzáadása",
    review: "Ellenőrzés",
    approvals: "Jóváhagyások",
    duplicates: "Ismétlődések",
    automations: "Automatizálás",
    accounting: "Könyvelési ellenőrzés",
    exports: "Exportközpont",
    inbox: "Családi postafiók",
    subscriptions: "Előfizetések",
    forecast: "Előrejelzés",
    budget: "Háztartási keret",
    reports: "Összesítés",
    integrations: "Integrációk",
    settings: "Beállítások",
    onboarding: "Bevezető",
    logout: "Kijelentkezés",
    login: "Bejelentkezés",
    register: "Fiók létrehozása",
    totalReceipts: "Nyugták száma",
    totalSpent: "Összes kiadás",
    needsReview: "Ellenőrzésre vár",
    budgetStatus: "Költségvetés állapota",
    spendingTrend: "Kiadási trend",
    thisMonth: "E hónap",
    noReceipts: "Még nincs nyugta",
    noReceiptsHint: "Töltsd fel az első nyugtádat a kezdéshez",
    uploadFirst: "Nyugta feltöltése",
    allClear: "Minden rendben!",
    nothingPending: "Nincs függő jóváhagyás",
    noDuplicates: "Nincs duplikátum",
    noRules: "Még nincs szabály",
    noEmails: "Nincs beérkezett e-mail",
    noSubscriptions: "Nincs visszatérő kiadás",
    notEnoughData: "Nincs elég adat",
    notEnoughDataHint: "Legalább 2 időszak előzménye szükséges",
    noBudgetSet: "Nincs költségvetés",
    noBudgetSetHint: "Hozz létre költségvetést a kategóriánkénti kiadásokhoz",
    search: "Keresés",
    filter: "Szűrés",
    date: "Dátum",
    merchant: "Eladó",
    category: "Kategória",
    status: "Állapot",
    total: "Összesen",
    currency: "Valuta",
    vendor: "Eladó",
    tax: "ÁFA",
    lineItems: "Tételek",
    confidence: "Megbízhatóság",
    loading: "Betöltés…",
    error: "Hiba történt",
    retry: "Újra",
    save: "Mentés",
    cancel: "Mégse",
    delete: "Törlés",
    edit: "Szerkesztés",
    next: "Következő",
    back: "Vissza",
    done: "Kész",
    skip: "Kihagyás",
    uploadReceipt: "Nyugta feltöltése",
    dragDrop: "Húzd ide a nyugta képét, vagy kattints a tallózáshoz",
    cameraCapture: "Fotó készítése",
    processing: "Feldolgozás…",
    ocrPreview: "OCR eredmény",
    uploadAnother: "További feltöltés",
    viewReceipt: "Nyugta megtekintése",
    forecastTitle: "Kiadási előrejelzés",
    anomalies: "Anomáliák",
    budgetVariance: "Költségvetés eltérés",
    projectedSpend: "Várható kiadás",
    expectedOverage: "Várható túllépés",
    onTrack: "Rendben",
    warning: "Figyelmeztetés",
    overBudget: "Túllépés",
    welcome: "Üdvözlünk a ReceiptLens-ben",
    welcomeHint: "Olvass be egy nyugtát a kiadásaid követéséhez",
    step: "Lépés",
    of: "/",
    skipOnboarding: "Bevezető kihagyása",
    finish: "Befejezés",
    darkMode: "Sötét mód",
    lightMode: "Világos mód",
  },
} as const;

export type MessageKey = keyof typeof messages.en;

export function t(key: MessageKey, locale: Locale = "en"): string {
  return messages[locale]?.[key] ?? messages.en[key] ?? key;
}

const LOCALE_KEY = "receiptlens.locale";

export function getLocale(): Locale {
  if (typeof window === "undefined") return "en";
  try {
    const stored = window.localStorage.getItem(LOCALE_KEY);
    return stored === "hu" ? "hu" : "en";
  } catch {
    return "en";
  }
}

export function setLocale(locale: Locale): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LOCALE_KEY, locale);
  } catch {
    // ignore
  }
}

/**
 * React hook: returns the active locale, the translation function and a
 * setter that persists the choice to localStorage.
 */
export function useTranslation() {
  const [locale, setLocaleState] = useState<Locale>(() => getLocale());

  const changeLocale = useCallback((next: Locale) => {
    setLocale(next);
    setLocaleState(next);
  }, []);

  const translate = useCallback(
    (key: MessageKey): string => t(key, locale),
    [locale],
  );

  return { locale, setLocale: changeLocale, t: translate };
}
