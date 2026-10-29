import type { ReactNode } from "react";
import { PHOTOS, type PhotoKey } from "@/lib/photos";

interface PhotoBannerProps {
  photo: PhotoKey;
  /** Page title. Rendered as the page's h1 so screen readers land on it. */
  title: ReactNode;
  subtitle?: ReactNode;
  /** Buttons or links shown under the subtitle. */
  actions?: ReactNode;
}

/**
 * Page header with a food photograph. Text sits on a dark gradient, so white
 * copy keeps AA contrast on every photo. Keep the photo decorative: the title
 * already says what the page is.
 */
export default function PhotoBanner({ photo, title, subtitle, actions }: PhotoBannerProps) {
  const image = PHOTOS[photo];
  return (
    <div className="relative isolate overflow-hidden rounded-2xl bg-slate-900 text-white shadow-lift">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={image.src} alt="" aria-hidden="true" className="absolute inset-0 -z-10 h-full w-full object-cover" />
      <div className="absolute inset-0 -z-10 bg-gradient-to-r from-slate-950/85 via-slate-950/55 to-slate-950/10" />
      <div className="flex min-h-48 flex-col justify-end gap-3 p-6 sm:min-h-56 sm:p-8">
        <h1 className="text-3xl leading-tight sm:text-4xl">{title}</h1>
        {subtitle ? <p className="max-w-xl text-sm text-slate-100 sm:text-base">{subtitle}</p> : null}
        {actions ? <div className="mt-2 flex flex-wrap gap-3">{actions}</div> : null}
      </div>
    </div>
  );
}
