"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { setAuthState } from "@/lib/auth";
import { roleLabel } from "@/lib/roles";

const ROLES = ["admin", "reviewer", "integrator"] as const;

/**
 * Login page — household/role selector (the backend authenticates via
 * X-Tenant-ID / X-Role headers; there is no password for the MVP).
 * Labels are consumer-facing (F1.1); the wire values stay untouched.
 */
export default function LoginPage() {
  const router = useRouter();
  const [tenant, setTenant] = useState("demo");
  const [role, setRole] = useState<(typeof ROLES)[number]>("admin");

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
        </p>
      </div>
    </div>
  );
}
