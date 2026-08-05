"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { savePreferences } from "@/lib/api";
import { setAuthState } from "@/lib/auth";

const STEPS = [
  { icon: "👋", title: "Welcome", body: "ReceiptLens scans receipts, tracks spending and forecasts your budget — fully self-hosted." },
  { icon: "🏷️", title: "Choose a workspace", body: "Pick a tenant and role. For a personal setup, keep the demo tenant and admin role." },
  { icon: "📤", title: "Upload your first receipt", body: "You'll be taken to the upload page where you can photograph or drop a receipt." },
] as const;

/**
 * Dedicated onboarding page — a standalone first-time setup flow at /onboarding
 * (the modal version lives in components/Onboarding.tsx and auto-shows when
 * preferences.onboarding_done is false).
 */
export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [tenant, setTenant] = useState("demo");
  const [role, setRole] = useState<"admin" | "reviewer" | "integrator">("admin");

  async function finish() {
    setAuthState(tenant, role);
    await savePreferences({ onboarding_done: true }).catch(() => undefined);
    router.push("/upload");
  }

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4 dark:from-brand-950 dark:to-slate-950">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-card dark:bg-slate-900">
        <div className="flex gap-1" aria-label={`Step ${step + 1} of ${STEPS.length}`}>
          {STEPS.map((item, index) => (
            <div
              key={item.title}
              className={`h-1.5 flex-1 rounded-full transition-colors ${
                index <= step ? "bg-brand-600" : "bg-slate-200 dark:bg-slate-700"
              }`}
            />
          ))}
        </div>

        <div className="py-8 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-brand-50 text-3xl dark:bg-brand-950" aria-hidden="true">
            {current.icon}
          </div>
          <p className="mt-3 text-xs font-medium uppercase tracking-wide text-brand-600 dark:text-brand-400">
            Step {step + 1} of {STEPS.length}
          </p>
          <h1 className="mt-1 text-xl font-semibold text-slate-900 dark:text-slate-100">{current.title}</h1>
          <p className="mt-2 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{current.body}</p>
        </div>

        {step === 1 ? (
          <div className="mb-6 space-y-3">
            <div>
              <label htmlFor="onboard-tenant" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
                Tenant
              </label>
              <select id="onboard-tenant" className="input" value={tenant} onChange={(event) => setTenant(event.target.value)}>
                <option value="demo">demo</option>
                <option value="personal">personal</option>
                <option value="business">business</option>
              </select>
            </div>
            <div>
              <label htmlFor="onboard-role" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
                Role
              </label>
              <select id="onboard-role" className="input" value={role} onChange={(event) => setRole(event.target.value as typeof role)}>
                <option value="admin">admin</option>
                <option value="reviewer">reviewer</option>
                <option value="integrator">integrator</option>
              </select>
            </div>
          </div>
        ) : null}

        <div className="flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={() => {
              setAuthState(tenant, role);
              savePreferences({ onboarding_done: true }).catch(() => undefined);
              router.push("/dashboard");
            }}
            className="text-sm font-medium text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
          >
            Skip
          </button>
          <div className="flex gap-2">
            {step > 0 ? (
              <button type="button" onClick={() => setStep((value) => value - 1)} className="btn-secondary text-sm">
                Back
              </button>
            ) : null}
            <button type="button" onClick={() => (isLast ? finish() : setStep((value) => value + 1))} className="btn-primary text-sm">
              {isLast ? "Get started →" : "Next"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
