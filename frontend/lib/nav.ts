import { t, type Locale, type MessageKey } from "./i18n";
import { getLocale } from "./i18n";

export interface NavItem {
  href: string;
  /** i18n key — NOT the final label; use getNavLabel() to resolve. */
  labelKey: MessageKey;
  icon: string;
}

/**
 * Consumer navigation (F1.1 consumer pivot) — translated via i18n catalog.
 * Keep labels as keys — the Sidebar/MobileNav resolve them at render time.
 */
export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", labelKey: "dashboard", icon: "📊" },
  { href: "/receipts", labelKey: "receipts", icon: "🧾" },
  { href: "/upload", labelKey: "upload", icon: "📤" },
  { href: "/review", labelKey: "review", icon: "🔍" },
  { href: "/duplicates", labelKey: "duplicates", icon: "🔄" },
  { href: "/inbox", labelKey: "inbox", icon: "📧" },
  { href: "/subscriptions", labelKey: "subscriptions", icon: "🔁" },
  { href: "/forecast", labelKey: "forecast", icon: "📈" },
  { href: "/budget", labelKey: "budget", icon: "🎯" },
  { href: "/reports", labelKey: "reports", icon: "📄" },
  { href: "/settings", labelKey: "settings", icon: "⚙️" },
];

/**
 * Business section (F1.1) — B2B labels translated via i18n.
 */
export const BUSINESS_NAV_ITEMS: NavItem[] = [
  { href: "/approvals", labelKey: "approvals", icon: "✅" },
  { href: "/exports", labelKey: "exports", icon: "📦" },
  { href: "/accounting", labelKey: "accounting", icon: "📒" },
  { href: "/integrations", labelKey: "integrations", icon: "🔌" },
  { href: "/automations", labelKey: "automations", icon: "⚡" },
];

/** Resolve a NavItem label to translated string. */
export function getNavLabel(item: NavItem, locale?: Locale): string {
  return t(item.labelKey, locale ?? getLocale());
}

/** Primary mobile bottom-tab items (first five consumer destinations). */
export const MOBILE_TABS: NavItem[] = NAV_ITEMS.slice(0, 5);
