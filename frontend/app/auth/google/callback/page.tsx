"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { setSessionToken } from "@/lib/auth";
import { useTranslation } from "@/lib/i18n";
import LanguageSwitcher from "@/components/LanguageSwitcher";
import ThemeToggle from "@/components/ThemeToggle";

/**
 * Google SSO callback page — reads session_token from the URL fragment
 * (the backend redirects here with #session_token=...&expires_at=...&return_to=...),
 * persists the session, and navigates to the intended destination.
 *
 * Fragments are never sent to the server, so this must be handled client-side.
 * The return_to value is already sanitized server-side (only /-prefixed paths).
 */
function GoogleCallbackInner() {
  const { t } = useTranslation();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const err = params.get("error");
    if (err) {
      setError(`${t("googleSignInFailed")}: ${err}`);
      return;
    }

    // Fragment: #session_token=...&expires_at=...&return_to=...
    const hash = window.location.hash.slice(1);
    if (!hash) {
      const qToken = params.get("session_token");
      if (qToken) {
        setSessionToken(qToken);
        window.history.replaceState(null, "", window.location.pathname);
        router.push(params.get("return_to") || "/dashboard");
        return;
      }
      setError(t("googleMissingToken"));
      return;
    }
    const frag = new URLSearchParams(hash);
    const sessionToken = frag.get("session_token");
    const returnTo = frag.get("return_to") || "/dashboard";

    if (!sessionToken) {
      setError(t("googleMissingSession"));
      return;
    }

    // Basic open-redirect guard client-side as well
    const safeReturnTo = returnTo.startsWith("/") && !returnTo.startsWith("//") ? returnTo : "/dashboard";

    setSessionToken(sessionToken);
    window.history.replaceState(null, "", window.location.pathname);
    router.push(safeReturnTo);
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4 dark:from-brand-950 dark:to-slate-950">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-card dark:bg-slate-900">
        <div className="flex justify-end"><ThemeToggle /></div>
        <div className="text-center">
          <span className="text-3xl" aria-hidden="true">🔎</span>
          <h1 className="mt-2 text-xl font-bold text-slate-900 dark:text-slate-100">ReceiptLens</h1>
        </div>
        <div className="mt-4">
          <LanguageSwitcher />
        </div>

        {error ? (
          <p className="mt-6 text-center text-sm text-red-600 dark:text-red-400" role="alert">
            {error}
          </p>
        ) : (
          <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400" aria-live="polite">
            {t("googleSigningIn")}
          </p>
        )}
      </div>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><p className="text-sm text-slate-500">Loading…</p></div>}>
      <GoogleCallbackInner />
    </Suspense>
  );
}
