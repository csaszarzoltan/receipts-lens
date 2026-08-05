import Link from "next/link";

/** Landing / marketing page for unauthenticated visitors. */
export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-50 via-white to-white dark:from-brand-950 dark:via-slate-950 dark:to-slate-950">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-6 sm:px-6">
        <Link href="/" className="flex items-center gap-2 text-lg font-bold text-slate-900 dark:text-slate-100">
          <span aria-hidden="true">🔎</span> ReceiptLens
        </Link>
        <div className="flex items-center gap-2">
          <Link
            href="/login"
            className="inline-flex min-h-11 items-center rounded-lg px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            Sign in
          </Link>
          <Link
            href="/dashboard"
            className="inline-flex min-h-11 items-center rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            Open the app
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 pb-20 sm:px-6">
        <section className="py-16 text-center sm:py-24">
          <p className="mx-auto inline-flex items-center rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700 dark:border-brand-900 dark:bg-brand-950 dark:text-brand-300">
            ✨ Self-hosted · OCR-powered · Forecasts included
          </p>
          <h1 className="mx-auto mt-6 max-w-2xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl dark:text-slate-50">
            Scan receipts. Track spending. Stay ahead.
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-lg text-slate-600 dark:text-slate-300">
            ReceiptLens turns paper and digital receipts into structured expense data with
            multi-language OCR, anomaly detection and next-month spending forecasts.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/upload"
              className="inline-flex min-h-12 items-center rounded-xl bg-brand-600 px-6 py-3 text-base font-semibold text-white shadow-card transition-colors hover:bg-brand-700"
            >
              Upload your first receipt
            </Link>
            <Link
              href="/forecast"
              className="inline-flex min-h-12 items-center rounded-xl border border-slate-300 bg-white px-6 py-3 text-base font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              See the forecast
            </Link>
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-label="Features">
          {[
            { icon: "🧾", title: "Instant OCR", body: "Vendor, totals and line items extracted from any receipt — in 10 languages." },
            { icon: "📈", title: "Spending forecast", body: "Moving-average + trend projections tell you what next month looks like." },
            { icon: "🚨", title: "Anomaly detection", body: "Z-score and MAD detection flag unusual spending before it surprises you." },
            { icon: "🎯", title: "Budget variance", body: "See which categories are on track, warning, or already over budget." },
            { icon: "📱", title: "Mobile first", body: "Capture receipts with your camera, review on the go, sync everywhere." },
            { icon: "🔒", title: "Self-hosted", body: "Your data stays on your server. No per-image cloud fees, ever." },
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
        ReceiptLens — an open-source expense tracking API + UI.
      </footer>
    </div>
  );
}
