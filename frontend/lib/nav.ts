export interface NavItem {
  href: string;
  label: string;
  icon: string;
}

/**
 * Consumer navigation (F1.1 consumer pivot) — household-facing labels from
 * docs/plans/consumer-pivot-2026-08-13.md §3.3. The main navigation must
 * contain zero business jargon: the B2B features live in BUSINESS_NAV_ITEMS
 * behind the separate "Business" entry point (see Sidebar / MobileNav).
 */
export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Áttekintés", icon: "📊" },
  { href: "/receipts", label: "Vásárlások", icon: "🧾" },
  { href: "/upload", label: "Nyugta hozzáadása", icon: "📤" },
  { href: "/review", label: "Ellenőrzés", icon: "🔍" },
  { href: "/duplicates", label: "Ismétlődések", icon: "🔄" },
  { href: "/inbox", label: "Családi postafiók", icon: "📧" },
  { href: "/subscriptions", label: "Előfizetések", icon: "🔁" },
  { href: "/forecast", label: "Előrejelzés", icon: "📈" },
  { href: "/budget", label: "Háztartási keret", icon: "🎯" },
  { href: "/reports", label: "Összesítés", icon: "📄" },
  { href: "/settings", label: "Beállítások", icon: "⚙️" },
];

/**
 * Business section (F1.1) — B2B/accounting features are NOT deleted, they
 * are hidden behind a separate entry point ("Business") with their original
 * labels. Keep in sync with the plan §2.5 / §3.3.
 */
export const BUSINESS_NAV_ITEMS: NavItem[] = [
  { href: "/approvals", label: "Approvals", icon: "✅" },
  { href: "/exports", label: "Export Center", icon: "📦" },
  { href: "/accounting", label: "Accounting", icon: "📒" },
  { href: "/integrations", label: "Integrations", icon: "🔌" },
  { href: "/automations", label: "Automations", icon: "⚡" },
];

/** Primary mobile bottom-tab items (first five consumer destinations). */
export const MOBILE_TABS: NavItem[] = NAV_ITEMS.slice(0, 5);
