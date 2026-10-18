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
  { href: "/statement", labelKey: "statementCheck", icon: "🏦", group: "analyse" },
  { href: "/reports", labelKey: "reports", icon: "📄", group: "analyse" },
  { href: "/chat", labelKey: "chat", icon: "💬", group: "analyse" },
  { href: "/insights", labelKey: "insights", icon: "💡", group: "analyse" },
  { href: "/tax", labelKey: "taxTitle", icon: "🧾", group: "analyse" },
  { href: "/settings", labelKey: "settings", icon: "⚙️", group: "account" },
];

/** Stable routes are retained; only primary destinations are simplified. */
export const PRIMARY_NAV_ITEMS: NavItem[] = [
  {href:"/dashboard", labelKey:"overviewTitle", icon:"", group:"home"},
  {href:"/receipts", labelKey:"receipts", icon:"", group:"capture"},
  {href:"/finances", labelKey:"finances", icon:"", group:"analyse"},
  {href:"/more", labelKey:"moreSections", icon:"", group:"account"},
];
export const NAV_SECTIONS = [{group:"home" as NavGroup, items:PRIMARY_NAV_ITEMS}];

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
export const MOBILE_TABS: NavItem[] = [PRIMARY_NAV_ITEMS[0], PRIMARY_NAV_ITEMS[1], {href:"/upload",labelKey:"addReceipt",icon:""}, PRIMARY_NAV_ITEMS[2], PRIMARY_NAV_ITEMS[3]];
