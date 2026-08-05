import { cx } from "@/lib/utils";

/** Skeleton loading block — shimmer animation, used by loading states. */
export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cx(
        "relative overflow-hidden rounded-lg bg-slate-200/70 dark:bg-slate-800/70",
        className,
      )}
      aria-hidden="true"
    >
      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/40 to-transparent dark:via-white/10" />
    </div>
  );
}

/** Card-shaped skeleton used for list/grid loading placeholders. */
export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cx("rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900", className)}>
      <Skeleton className="mb-3 h-4 w-1/3" />
      <Skeleton className="mb-2 h-6 w-1/2" />
      <Skeleton className="h-4 w-2/3" />
    </div>
  );
}

/** Full-page loading state with heading placeholder. */
export function PageSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-48" />
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
      <SkeletonCard className="h-64" />
    </div>
  );
}
