import { t, type Locale, type MessageKey } from "./i18n";
import { getLocale } from "./i18n";

/** Sidebar sections. The order of NAV_ITEMS is kept for the mobile tab bar. */
export type NavGroup = "home" | "capture" | "analyse" | "account";

export interface NavItem {
  href: string;
  /** i18n key — NOT the final label; use getNavLabel() to resolve. */
  labelKey: MessageKey;
  icon: string;
  group?: NavGroup;
}

/**
 * Consumer navigation (F1.1 consumer pivot) — translated via i18n catalog.
 * Keep labels as keys — the Sidebar/MobileNav resolve them at render time.
 */
export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", labelKey: "dashboard", icon: "📊", group: "home" },
  { href: "/receipts", labelKey: "receipts", icon: "🧾", group: "capture" },
  { href: "/upload", labelKey: "upload", icon: "📤", group: "capture" },
  { href: "/review", labelKey: "review", icon: "🔍", group: "capture" },
  { href: "/duplicates", labelKey: "duplicates", icon: "🔄", group: "capture" },
  { href: "/inbox", labelKey: "inbox", icon: "📧", group: "capture" },
  { href: "/subscriptions", labelKey: "subscriptions", icon: "🔁", group: "analyse" },
  { href: "/forecast", labelKey: "forecast", icon: "📈", group: "analyse" },
  { href: "/budget", labelKey: "budget", icon: "🎯", group: "analyse" },
  { href: "/warranties", labelKey: "warranties", icon: "🛡️", group: "analyse" },
  { href: "/reports", labelKey: "reports", icon: "📄", group: "analyse" },
  { href: "/chat", labelKey: "chat", icon: "💬", group: "analyse" },
  { href: "/insights", labelKey: "insights", icon: "💡", group: "analyse" },
  { href: "/tax", labelKey: "taxTitle", icon: "🧾", group: "analyse" },
  { href: "/settings", labelKey: "settings", icon: "⚙️", group: "account" },
];

/** Sidebar sections in display order, each with its items in NAV_ITEMS order. */
export const NAV_SECTIONS: { group: NavGroup; labelKey?: MessageKey; items: NavItem[] }[] = [
  { group: "home", items: NAV_ITEMS.filter((i) => i.group === "home") },
  { group: "capture", labelKey: "navGroupCapture", items: NAV_ITEMS.filter((i) => i.group === "capture") },
  { group: "analyse", labelKey: "navGroupAnalyze", items: NAV_ITEMS.filter((i) => i.group === "analyse") },
  { group: "account", items: NAV_ITEMS.filter((i) => i.group === "account") },
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
