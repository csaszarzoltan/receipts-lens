"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { requestMagicLink, verifyMagicLink } from "@/lib/api";
import { setSessionToken } from "@/lib/auth";

/**
 * Magic-link flow (F1.3):
 *   - With ?token=... → verify the token and sign straight in.
 *   - Without a token → email form; the returned link is shown when the
 *     backend runs in dev mode (no SMTP), otherwise the email is "sent".
 */
function MagicLinkInner() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token");

  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [link, setLink] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    setBusy(true);
    verifyMagicLink(token)
      .then((session) => {
        setSessionToken(session.session_token);
        router.push("/dashboard");
      })
      .catch((err: unknown) => {
        setError(
          err instanceof Error ? err.message : "A belépési link érvénytelen vagy lejárt.",
        );
        setBusy(false);
      });
  }, [token, router]);

  async function request() {
    setBusy(true);
    setError(null);
    try {
      const result = await requestMagicLink({ email });
      if (result.magic_link) {
        setLink(result.magic_link);
      } else if (result.delivered) {
        setLink(null);
        setError(null);
      } else {
        setError("Az e-mail küldés jelenleg nem elérhető (nincs SMTP beállítva).");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Hiba a belépési link kérésekor.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4 dark:from-brand-950 dark:to-slate-950">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-card dark:bg-slate-900">
        <div className="text-center">
          <span className="text-3xl" aria-hidden="true">🔎</span>
          <h1 className="mt-2 text-xl font-bold text-slate-900 dark:text-slate-100">ReceiptLens</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Jelszó nélküli belépés e-mailben
          </p>
        </div>

        {token ? (
          <p className="mt-6 text-center text-sm text-slate-600 dark:text-slate-300" aria-live="polite">
            {busy ? "Bejelentkezés…" : error ?? "A link ellenőrzése…"}
          </p>
        ) : (
          <div className="mt-6 space-y-4">
            <div>
              <label htmlFor="magic-email" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
                E-mail cím
              </label>
              <input
                id="magic-email"
                type="email"
                className="input"
                placeholder="te@pelda.hu"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>
            <button type="button" onClick={request} disabled={!email || busy} className="btn-primary w-full">
              {busy ? "Küldés…" : "Belépési link küldése"}
            </button>

            {error && (
              <p className="text-sm text-red-600 dark:text-red-400" role="alert">
                {error}
              </p>
            )}
            {link && (
              <div className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                <p className="mb-1 font-medium">Fejlesztési mód — a link itt van (nincs SMTP):</p>
                <a href={link} className="break-all text-brand-600 hover:underline dark:text-brand-400">
                  {link}
                </a>
              </div>
            )}

            <p className="text-center text-sm text-slate-500 dark:text-slate-400">
              Vagy{" "}
              <Link href="/login" className="font-medium text-brand-600 hover:underline dark:text-brand-400">
                jelentkezz be háztartással
              </Link>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function MagicLinkPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><p className="text-sm text-slate-500">Loading…</p></div>}>
      <MagicLinkInner />
    </Suspense>
  );
}
