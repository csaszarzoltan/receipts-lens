"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { setSessionToken } from "@/lib/auth";

/**
 * Google SSO callback page — reads session_token from the URL fragment
 * (the backend redirects here with #session_token=...&expires_at=...),
 * persists the session, and navigates to the intended destination.
 *
 * Fragments are never sent to the server, so this must be handled client-side.
 */
function GoogleCallbackInner() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fragment: #session_token=...&expires_at=...&return_to=...
    const hash = window.location.hash.slice(1);
    if (!hash) {
      setError("A Google bejelentkezés sikertelen (hiányzó token).");
      return;
    }
    const params = new URLSearchParams(hash);
    const sessionToken = params.get("session_token");
    const returnTo = params.get("return_to") || "/dashboard";

    if (!sessionToken) {
      setError("A Google bejelentkezés sikertelen (hiányzó session).");
      return;
    }

    setSessionToken(sessionToken);
    // Clean the fragment so it doesn't re-trigger on refresh
    window.history.replaceState(null, "", window.location.pathname);
    router.push(returnTo);
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4 dark:from-brand-950 dark:to-slate-950">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-card dark:bg-slate-900">
        <div className="text-center">
          <span className="text-3xl" aria-hidden="true">🔎</span>
          <h1 className="mt-2 text-xl font-bold text-slate-900 dark:text-slate-100">ReceiptLens</h1>
        </div>
        {error ? (
          <p className="mt-6 text-center text-sm text-red-600 dark:text-red-400" role="alert">
            {error}
          </p>
        ) : (
          <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400" aria-live="polite">
            Bejelentkezés Google-lel…
          </p>
        )}
      </div>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><p className="text-sm text-slate-500">Betöltés…</p></div>}>
      <GoogleCallbackInner />
    </Suspense>
  );
}
