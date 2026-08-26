"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE_URL, googleSsoEnabled } from "@/lib/api";
import { setAuthState } from "@/lib/auth";
import { roleLabel } from "@/lib/roles";
import { useTranslation } from "@/lib/i18n";

const ROLES = ["admin", "reviewer", "integrator"] as const;

/**
 * Login page — Google SSO button (when enabled) + household/role fallback selector.
 * The X-Tenant-ID header auth is the legacy dev path; the real consumer path
 * uses magic-link or Google SSO.
 */
export default function LoginPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const [tenant, setTenant] = useState("demo");
  const [role, setRole] = useState<(typeof ROLES)[number]>("admin");
  const [googleReady, setGoogleReady] = useState(false);

  useEffect(() => {
    googleSsoEnabled().then(setGoogleReady).catch(() => {});
  }, []);

  function signIn() {
    setAuthState(tenant, role);
    router.push("/dashboard");
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4 dark:from-brand-950 dark:to-slate-950">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-card dark:bg-slate-900">
        <div className="text-center">
          <span className="text-3xl" aria-hidden="true">🔎</span>
          <h1 className="mt-2 text-xl font-bold text-slate-900 dark:text-slate-100">ReceiptLens</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Sign in to your household
          </p>
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

        <div className="mt-6 space-y-4">
          <div>
            <label htmlFor="login-tenant" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
              Háztartás
            </label>
            <select id="login-tenant" className="input" value={tenant} onChange={(event) => setTenant(event.target.value)}>
              <option value="demo">demo</option>
              <option value="personal">personal</option>
              <option value="business">business</option>
            </select>
          </div>
          <div>
            <label htmlFor="login-role" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
              Szerepkör
            </label>
            <select id="login-role" className="input" value={role} onChange={(event) => setRole(event.target.value as (typeof ROLES)[number])}>
              {ROLES.map((option) => (
                <option key={option} value={option}>{roleLabel(option)}</option>
              ))}
            </select>
          </div>
          <button type="button" onClick={signIn} className="btn-primary w-full">
            Sign in
          </button>
        </div>

        <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
          Új itt?{" "}
          <Link href="/onboarding" className="font-medium text-brand-600 hover:underline dark:text-brand-400">
            Töltsd ki a bevezetőt
          </Link>
          {" · "}
          <Link href="/auth/magic-link" className="font-medium text-brand-600 hover:underline dark:text-brand-400">
            Belépés e-mail linkkel
          </Link>
        </p>
      </div>
    </div>
  );
}
