"use client";

import { cx } from "@/lib/utils";

interface TaxBadgeProps {
  category: string | null | undefined;
}

const TONE: Record<string, string> = {
  "Meals": "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  "Travel": "bg-sky-50 text-sky-700 dark:bg-sky-950 dark:text-sky-300",
  "Transportation": "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  "Office": "bg-violet-50 text-violet-700 dark:bg-violet-950 dark:text-violet-300",
  "Rent": "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  "Advertising": "bg-pink-50 text-pink-700 dark:bg-pink-950 dark:text-pink-300",
  "Groceries": "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
};

function tone(category: string): string {
  for (const [key, cls] of Object.entries(TONE)) {
    if (category.startsWith(key) || category.includes(key)) return cls;
  }
  return "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400";
}

export default function TaxBadge({ category }: TaxBadgeProps) {
  if (!category) {
    return (
      <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-400 dark:bg-slate-800">
        —
      </span>
    );
  }
  return (
    <span
      className={cx(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        tone(category),
      )}
      title={category}
    >
      {category}
    </span>
  );
}
