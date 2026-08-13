import Link from "next/link";

export const metadata = { title: "Create account" };

/** Account creation placeholder — account management is a future feature. */
export default function RegisterPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4 dark:from-brand-950 dark:to-slate-950">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 text-center shadow-card dark:bg-slate-900">
        <span className="text-3xl" aria-hidden="true">📝</span>
        <h1 className="mt-2 text-xl font-bold text-slate-900 dark:text-slate-100">Create account</h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Account creation is coming soon. For now, pick any household and
          role on the sign-in page — data is isolated per household.
        </p>
        <Link href="/login" className="btn-primary mt-6">
          Back to sign in
        </Link>
      </div>
    </div>
  );
}
