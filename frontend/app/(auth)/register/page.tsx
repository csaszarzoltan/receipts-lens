"use client";

import Link from "next/link";
import LanguageSwitcher from "@/components/LanguageSwitcher";
import ThemeToggle from "@/components/ThemeToggle";
import { useTranslation } from "@/lib/i18n";

/** Account creation placeholder — account management is a future feature. */
export default function RegisterPage() {
  const { t } = useTranslation();
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4 dark:from-brand-950 dark:to-slate-950">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 text-center shadow-card dark:bg-slate-900">
        <div className="flex justify-end"><ThemeToggle /></div>
        <span className="text-3xl" aria-hidden="true">📝</span>
        <h1 className="mt-2 text-xl font-bold text-slate-900 dark:text-slate-100">{t("register")}</h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          {t("registerHint")}
        </p>
        <div className="mt-6 text-left">
          <LanguageSwitcher />
        </div>
        <Link href="/login" className="btn-primary mt-6 inline-flex">
          {t("backToSignIn")}
        </Link>
      </div>
    </div>
  );
}
