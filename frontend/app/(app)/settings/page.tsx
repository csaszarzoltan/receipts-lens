"use client";

import Link from "next/link";
import { useTranslation } from "@/lib/i18n";

export default function SettingsPage() {
  const { t } = useTranslation();
  const SECTIONS = [
    { href: "/settings/profile", label: t("profile"), icon: "👤" },
    { href: "/settings/members", label: t("familyMembers"), icon: "👥" },
    { href: "/settings/permissions", label: t("permissions"), icon: "🔐" },
    { href: "/settings/privacy", label: t("privacy"), icon: "🛡️" },
    { href: "/settings/diagnostics", label: t("diagnostics"), icon: "🩺" },
  ];
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("settings")}</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Manage your household, members and privacy.
        </p>
      </div>
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-label="Settings sections">
        {SECTIONS.map((section) => (
          <li key={section.href}>
            <Link href={section.href} className="card flex min-h-24 items-center gap-4 p-5 transition-shadow hover:shadow-md">
              <span className="text-2xl" aria-hidden="true">{section.icon}</span>
              <span className="font-medium text-slate-800 dark:text-slate-100">{section.label}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
