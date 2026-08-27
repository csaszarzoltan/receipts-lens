"use client";
import Link from "next/link";
import { useTranslation } from "@/lib/i18n";

/** Landing / marketing page for unauthenticated visitors. */
export default function HomePage() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-50 via-white to-white dark:from-brand-950 dark:via-slate-950 dark:to-slate-950">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-6 sm:px-6">
        <Link href="/" className="flex items-center gap-2 text-lg font-bold text-slate-900 dark:text-slate-100">
          <span aria-hidden="true">\uD83D\uDD0E</span> ReceiptLens
        </Link>
        <div className="flex items-center gap-2">
          <Link
            href="/login"
            className="inline-flex min-h-11 items-center rounded-lg px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            {t("signInLabel")}
          </Link>
          <Link
            href="/dashboard"
            className="inline-flex min-h-11 items-center rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            {t("openTheAppLabel")}
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 pb-20 sm:px-6">
        <section className="py-16 text-center sm:py-24">
          <p className="mx-auto inline-flex items-center rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700 dark:border-brand-900 dark:bg-brand-950 dark:text-brand-300">
            {t("landingBadge")}
          </p>
          <h1 className="mx-auto mt-6 max-w-2xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl dark:text-slate-50">
            {t("landingTitle")}
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-lg text-slate-600 dark:text-slate-300">
            {t("landingDesc")}
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/upload"
              className="inline-flex min-h-12 items-center rounded-xl bg-brand-600 px-6 py-3 text-base font-semibold text-white shadow-card transition-colors hover:bg-brand-700"
            >
              {t("uploadFirstReceiptCta")}
            </Link>
            <Link
              href="/forecast"
              className="inline-flex min-h-12 items-center rounded-xl border border-slate-300 bg-white px-6 py-3 text-base font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              {t("seeTheForecastCta")}
            </Link>
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-label="Features">
          {[
            { icon: "\uD83E\uDDFE", title: t("featureInstantOcrTitle"), body: t("featureInstantOcrBody") },
            { icon: "\uD83D\uDCC8", title: t("featureForecastTitle"), body: t("featureForecastBody") },
            { icon: "\uD83D\uDEA8", title: t("featureAnomalyTitle"), body: t("featureAnomalyBody") },
            { icon: "\uD83C\uDFAF", title: t("featureBudgetTitle"), body: t("featureBudgetBody") },
            { icon: "\uD83D\uDCF1", title: t("featureMobileTitle"), body: t("featureMobileBody") },
            { icon: "\uD83D\uDD12", title: t("featureSelfHostedTitle"), body: t("featureSelfHostedBody") },
          ].map((feature) => (
            <div key={feature.title} className="card p-6">
              <span className="text-2xl" aria-hidden="true">{feature.icon}</span>
              <h2 className="mt-3 font-semibold text-slate-900 dark:text-slate-100">{feature.title}</h2>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{feature.body}</p>
            </div>
          ))}
        </section>
      </main>

      <footer className="border-t border-slate-200 py-8 text-center text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400">
        {t("landingFooter")}
      </footer>
    </div>
  );
}
