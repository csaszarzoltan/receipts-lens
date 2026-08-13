import { cx } from "@/lib/utils";

type Status = "needs_review" | "completed" | "pending" | "approved" | "rejected" | "failed" | string;

const TONES: Record<string, string> = {
  needs_review: "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  completed: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  approved: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  pending: "bg-sky-50 text-sky-700 dark:bg-sky-950 dark:text-sky-300",
  rejected: "bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300",
  failed: "bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300",
  exportable: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  warning: "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  blocked: "bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300",
  on_track: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  over_budget: "bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300",
  active: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
};

function labelFor(status: string): string {
  const labels: Record<string, string> = {
    needs_review: "Ellenőrzésre vár",
    completed: "Kész",
    pending: "Folyamatban",
    approved: "Jóváhagyva",
    rejected: "Elutasítva",
    failed: "Sikertelen",
    exportable: "Exportálható",
    warning: "Figyelmeztetés",
    blocked: "Blokkolt",
    on_track: "Terv szerint",
    over_budget: "Keret felett",
    active: "Aktív",
  };
  return labels[status] ?? status.replace(/_/g, " ");
}

/** Status/readiness badge — tone mapped per status value. */
export default function StatusBadge({ status }: { status: Status }) {
  return (
    <span
      className={cx(
        "inline-flex min-h-6 items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize",
        TONES[status] ?? "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
      )}
    >
      {labelFor(status)}
    </span>
  );
}
