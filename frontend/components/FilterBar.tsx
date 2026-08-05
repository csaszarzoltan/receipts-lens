"use client";

import { useId } from "react";

interface FilterOption {
  value: string;
  label: string;
}

interface FilterDef {
  name: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: FilterOption[];
  allLabel?: string;
}

interface FilterBarProps {
  query?: string;
  onQueryChange?: (value: string) => void;
  searchPlaceholder?: string;
  filters?: FilterDef[];
}

const inputCls =
  "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500";

function FilterSelect({ filter }: { filter: FilterDef }) {
  const id = useId();
  return (
    <div>
      <label htmlFor={id} className="sr-only">
        {filter.label}
      </label>
      <select
        id={id}
        value={filter.value}
        onChange={(event) => filter.onChange(event.target.value)}
        className={inputCls}
        aria-label={filter.label}
      >
        <option value="">{filter.allLabel ?? `All ${filter.label.toLowerCase()}s`}</option>
        {filter.options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

/** Reusable search + filter controls row (stacked on mobile, inline on desktop). */
export default function FilterBar({
  query,
  onQueryChange,
  searchPlaceholder = "Search…",
  filters = [],
}: FilterBarProps) {
  const searchId = useId();
  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4 lg:items-center">
      {onQueryChange ? (
        <div className="lg:col-span-1">
          <label htmlFor={searchId} className="sr-only">
            {searchPlaceholder}
          </label>
          <input
            id={searchId}
            type="search"
            value={query ?? ""}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder={searchPlaceholder}
            className={inputCls}
            aria-label={searchPlaceholder}
          />
        </div>
      ) : null}
      {filters.map((filter) => (
        <FilterSelect key={filter.name} filter={filter} />
      ))}
    </div>
  );
}
