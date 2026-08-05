import { cx } from "@/lib/utils";

interface KpiCardProps {
  title: string;
  value: string;
  sub?: string;
  icon: string;
  tone?: "default" | "success" | "warning" | "danger";
}

const TONES = {
  default: "text-slate-900 dark:text-slate-100",
  success: "text-emerald-600 dark:text-emerald-400",
  warning: "text-amber-600 dark:text-amber-400",
  danger: "text-rose-600 dark:text-rose-400",
};

/** Dashboard KPI card — title, prominent value, optional subtitle. */
export default function KpiCard({ title, value, sub, icon, tone = "default" }: KpiCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
        <span className="text-xl" aria-hidden="true">{icon}</span>
      </div>
      <p className={cx("mt-2 text-2xl font-semibold tracking-tight", TONES[tone])}>{value}</p>
      {sub ? <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">{sub}</p> : null}
    </div>
  );
}
