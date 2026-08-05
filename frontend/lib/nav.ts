export interface NavItem {
  href: string;
  label: string;
  icon: string;
}

/** Full navigation — sidebar (desktop) and slide-over (mobile). */
export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/receipts", label: "Receipts", icon: "🧾" },
  { href: "/upload", label: "Upload", icon: "📤" },
  { href: "/review", label: "Review", icon: "🔍" },
  { href: "/approvals", label: "Approvals", icon: "✅" },
  { href: "/duplicates", label: "Duplicates", icon: "🔄" },
  { href: "/automations", label: "Automations", icon: "⚡" },
  { href: "/accounting", label: "Accounting", icon: "📒" },
  { href: "/exports", label: "Export Center", icon: "📦" },
  { href: "/inbox", label: "Email Inbox", icon: "📧" },
  { href: "/subscriptions", label: "Subscriptions", icon: "🔁" },
  { href: "/forecast", label: "Forecast", icon: "📈" },
  { href: "/budget", label: "Budget", icon: "🎯" },
  { href: "/reports", label: "Reports", icon: "📄" },
  { href: "/integrations", label: "Integrations", icon: "🔌" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

/** Primary mobile bottom-tab items (first five). */
export const MOBILE_TABS: NavItem[] = NAV_ITEMS.slice(0, 5);
