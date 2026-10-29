"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE_URL, googleSsoEnabled, requestMagicLink, verifyMagicLink } from "@/lib/api";
import { setAuthState, setSessionToken } from "@/lib/auth";
import ThemeToggle from "@/components/ThemeToggle";
import { useTranslation, SUPPORTED_LOCALES, LOCALE_LABELS, type Locale } from "@/lib/i18n";
import { PHOTOS } from "@/lib/photos";

/**
 * Login page: an email link or Google SSO. No household or role selector.
 * The shared demo household is only offered when NEXT_PUBLIC_DEMO_LOGIN=1 at build time.
 */
export default function LoginPage() {
  const { t, locale, setLocale } = useTranslation();
  const router = useRouter();
  const [googleReady, setGoogleReady] = useState(false);
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [sentTo, setSentTo] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    googleSsoEnabled().then(setGoogleReady).catch(() => {});
  }, []);

  /** The shared demo household is a development shortcut; a production build never sets this flag. */
  const demoEnabled = process.env.NEXT_PUBLIC_DEMO_LOGIN === "1";

  async function finishWithToken(token: string) {
    const session = await verifyMagicLink(token);
    if (session.session_token) setSessionToken(session.session_token);
    router.push("/dashboard");
  }

  async function signIn(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await requestMagicLink({ email: email.trim() });
      if (res.token) {
        // Only a backend outside production hands the token back; sign in straight away.
        await finishWithToken(res.token);
        return;
      }
      if (res.delivered) setSentTo(email.trim());
      else setError(t("magicLinkNoSmtp"));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t("magicLinkError"));
    } finally {
      setLoading(false);
    }
  }

  async function signInAsDemo() {
    setLoading(true);
    setAuthState("demo", "admin");
    try {
      const res = await requestMagicLink({ email: "demo-admin@receiptlens.local" });
      if (res.token) await finishWithToken(res.token);
      else router.push("/dashboard");
    } catch {
      router.push("/dashboard");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen bg-slate-50 dark:bg-slate-950 lg:grid-cols-2">
      <aside className="relative hidden overflow-hidden lg:block" aria-hidden="true">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={PHOTOS.hero.src} alt="" className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/85 via-slate-950/25 to-transparent" />
        <p className="font-display absolute inset-x-12 bottom-14 text-4xl leading-tight text-white">{t("landingTitle")}</p>
      </aside>
      <div className="flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-lift dark:bg-slate-900">
        <div className="flex justify-end"><ThemeToggle /></div>
        <div className="text-center">
          <span aria-hidden="true" className="mx-auto inline-block h-3 w-3 rounded-full bg-clay-500" />
          <h1 className="mt-2 text-xl font-bold text-slate-900 dark:text-slate-100">ReceiptLens</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {t("loginSubtitle")}
          </p>
        </div>

        {/* Language selector — 10 locales, no auth required. Stored in localStorage; synced to backend on login. */}
        <div className="mt-4">
          <label htmlFor="pre-login-locale" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
            {t("language")}
          </label>
          <select
            id="pre-login-locale"
            className="input"
            value={locale}
            onChange={(event) => setLocale(event.target.value as Locale)}
          >
            {SUPPORTED_LOCALES.map((loc) => (
              <option key={loc} value={loc}>{LOCALE_LABELS[loc]}</option>
            ))}
          </select>
        </div>

        {googleReady && (
          <div className="mt-6">
            <a
              href={`${API_BASE_URL}/auth/google/start?return_to=${encodeURIComponent("/dashboard")}`}
              className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
              </svg>
              {t("continueWithGoogle")}
            </a>
          </div>
        )}

        <form onSubmit={signIn} className="mt-6 space-y-4">
          <div>
            <label htmlFor="login-email" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
              {t("magicLinkEmailLabel")}
            </label>
            <input
              id="login-email"
              type="email"
              required
              autoComplete="email"
              className="input"
              placeholder={t("emailPlaceholder")}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>
          <button type="submit" disabled={loading || !email.trim()} className="btn-primary w-full">
            {loading ? "..." : t("login")}
          </button>
          {sentTo && (
            <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300" role="status">
              {t("magicLinkSent")} <strong>{sentTo}</strong>
            </p>
          )}
          {error && (
            <p className="text-sm text-red-600 dark:text-red-400" role="alert">
              {error}
            </p>
          )}
        </form>

        {demoEnabled && (
          <button type="button" onClick={signInAsDemo} disabled={loading} className="mt-3 w-full text-center text-sm text-slate-500 underline dark:text-slate-400">
            {t("demoLogin")}
          </button>
        )}

        <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
          {t("newHere")}{" "}
          <Link href="/auth/magic-link" className="font-medium text-brand-700 hover:underline dark:text-brand-300">
            {t("createHousehold")}
          </Link>
          {" · "}
          <Link href="/onboarding" className="font-medium text-brand-700 hover:underline dark:text-brand-300">
            {t("onboarding")}
          </Link>
        </p>
      </div>
      </div>
    </main>
  );
}
