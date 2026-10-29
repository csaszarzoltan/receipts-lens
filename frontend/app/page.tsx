"use client";
import Link from "next/link";
import ThemeToggle from "@/components/ThemeToggle";
import { useTranslation } from "@/lib/i18n";
import LanguageSwitcher from "@/components/LanguageSwitcher";
import CategoryPhoto from "@/components/CategoryPhoto";
import { PHOTOS, type PhotoKey } from "@/lib/photos";

const FEATURE_PHOTOS: PhotoKey[] = ["table", "market", "street", "home", "coffee", "herbs"];

/** Landing / marketing page for unauthenticated visitors. */
export default function HomePage() {
  const { t } = useTranslation();
  const features = [
    { title: t("featureInstantOcrTitle"), body: t("featureInstantOcrBody") },
    { title: t("featureForecastTitle"), body: t("featureForecastBody") },
    { title: t("featureAnomalyTitle"), body: t("featureAnomalyBody") },
    { title: t("featureBudgetTitle"), body: t("featureBudgetBody") },
    { title: t("featureMobileTitle"), body: t("featureMobileBody") },
    { title: t("featureSelfHostedTitle"), body: t("featureSelfHostedBody") },
  ];
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5 sm:px-6">
        <Link href="/" className="font-display flex items-center gap-2 text-xl font-semibold text-slate-900 dark:text-slate-100">
          <span aria-hidden="true" className="inline-block h-2.5 w-2.5 rounded-full bg-clay-500" />
          ReceiptLens
        </Link>
        <div className="flex items-center gap-1 sm:gap-2">
          <ThemeToggle />
          <Link
            href="/login"
            className="inline-flex min-h-11 items-center rounded-xl px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            {t("signInLabel")}
          </Link>
          <Link
            href="/dashboard"
            className="hidden min-h-11 items-center rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 sm:inline-flex"
          >
            {t("openTheAppLabel")}
          </Link>
        </div>
      </header>

      <main>
        <section className="mx-auto grid max-w-6xl items-center gap-10 px-4 pb-16 pt-6 sm:px-6 lg:grid-cols-2 lg:gap-14 lg:pb-24 lg:pt-12">
          <div className="text-center lg:text-left">
            <p className="inline-flex items-center rounded-full bg-clay-50 px-3 py-1 text-xs font-medium text-clay-700 ring-1 ring-inset ring-clay-200 dark:bg-clay-950 dark:text-clay-200 dark:ring-clay-800">
              {t("landingBadge")}
            </p>
            <h1 className="mx-auto mt-6 max-w-xl text-4xl leading-[1.1] text-slate-900 sm:text-5xl lg:mx-0 dark:text-slate-50">
              {t("landingTitle")}
            </h1>
            <p className="mx-auto mt-5 max-w-lg text-lg leading-relaxed text-slate-600 lg:mx-0 dark:text-slate-300">
              {t("landingDesc")}
            </p>
            <div className="mt-9 flex flex-wrap items-center justify-center gap-3 lg:justify-start">
              <Link
                href="/upload"
                className="inline-flex min-h-12 items-center rounded-full bg-brand-600 px-6 py-3 text-base font-medium text-white shadow-card transition-colors hover:bg-brand-700"
              >
                {t("uploadFirstReceiptCta")}
              </Link>
              <Link
                href="/forecast"
                className="inline-flex min-h-12 items-center rounded-full border border-slate-300 bg-white px-6 py-3 text-base font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
              >
                {t("seeTheForecastCta")}
              </Link>
            </div>
          </div>

          <div className="relative">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={PHOTOS.hero.src}
              alt=""
              aria-hidden="true"
              className="aspect-[4/5] w-full rounded-[2rem] object-cover shadow-lift sm:aspect-[5/4]"
            />
            <div className="absolute -bottom-5 left-4 flex items-center gap-3 rounded-2xl border border-slate-200/80 bg-white/95 p-3 pr-5 shadow-lift backdrop-blur dark:border-slate-700 dark:bg-slate-900/95 sm:left-8">
              <CategoryPhoto photo={PHOTOS.produce} size={44} />
              <div>
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{features[0].title}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">{features[0].body}</p>
              </div>
            </div>
          </div>
        </section>

        <section aria-label="Features" className="mx-auto grid max-w-6xl gap-5 px-4 pb-20 pt-6 sm:grid-cols-2 sm:px-6 lg:grid-cols-3">
          {features.map((feature, index) => (
            <article key={feature.title} className="card overflow-hidden">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={PHOTOS[FEATURE_PHOTOS[index]].src}
                alt=""
                aria-hidden="true"
                loading="lazy"
                className="h-40 w-full object-cover"
              />
              <div className="p-6">
                <h2 className="font-display text-xl font-semibold text-slate-900 dark:text-slate-100">{feature.title}</h2>
                <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">{feature.body}</p>
              </div>
            </article>
          ))}
        </section>

        <section className="mx-auto max-w-6xl px-4 pb-24 sm:px-6">
          <div className="relative isolate overflow-hidden rounded-[2rem] bg-slate-900 px-6 py-14 text-center text-white sm:px-12">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={PHOTOS.bakery.src} alt="" aria-hidden="true" loading="lazy" className="absolute inset-0 -z-10 h-full w-full object-cover" />
            <div className="absolute inset-0 -z-10 bg-slate-950/70" />
            <h2 className="font-display mx-auto max-w-xl text-3xl leading-tight sm:text-4xl">{features[5].title}</h2>
            <p className="mx-auto mt-4 max-w-lg text-base text-slate-100">{features[5].body}</p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Link href="/upload" className="inline-flex min-h-12 items-center rounded-full bg-white px-7 py-3 text-base font-medium text-slate-900 hover:bg-slate-100">
                {t("uploadFirstReceiptCta")}
              </Link>
            </div>
          </div>
        </section>
      </main>

      <div className="mx-auto mt-2 flex max-w-xs justify-center pb-6">
        <div className="w-full max-w-xs">
          <LanguageSwitcher />
        </div>
      </div>

      <footer className="border-t border-slate-200 py-8 text-center text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400">
        <p>{t("landingFooter")}</p>
        <p className="mt-1 text-xs">{t("photoCredits")}</p>
      </footer>
    </div>
  );
}
