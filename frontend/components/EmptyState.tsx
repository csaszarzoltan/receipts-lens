import { PHOTOS, type PhotoKey } from "@/lib/photos";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: {
    label: string;
    href: string;
  };
  /** Photo shown above the message. Defaults to the table shot. */
  photo?: PhotoKey;
}

/**
 * Consistent empty-state block used by every list/view page — a photo, a primary
 * message, a secondary explanation and an optional CTA.
 */
export default function EmptyState({ title, description, action, photo = "table" }: EmptyStateProps) {
  const image = PHOTOS[photo];
  return (
    <div className="flex flex-col items-center justify-center overflow-hidden rounded-2xl border border-slate-200/80 bg-white text-center shadow-card dark:border-slate-800 dark:bg-slate-900">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={image.src} alt="" aria-hidden="true" loading="lazy" className="h-40 w-full object-cover sm:h-48" />
      <div className="flex flex-col items-center px-6 py-8">
        <h2 className="font-display text-xl font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
        <p className="mt-1 max-w-sm text-sm text-slate-500 dark:text-slate-400">{description}</p>
        {action ? (
          <a
            href={action.href}
            className="mt-5 inline-flex min-h-11 items-center justify-center rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
          >
            {action.label}
          </a>
        ) : null}
      </div>
    </div>
  );
}
