import type { Photo } from "@/lib/photos";

/**
 * Small square photo used as a list icon (category rows, receipt fallbacks).
 * Decorative: the adjacent text names the category, so the image has no alt.
 */
export default function CategoryPhoto({ photo, size = 44 }: { photo: Photo; size?: number }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={photo.src}
      alt=""
      aria-hidden="true"
      width={size}
      height={size}
      loading="lazy"
      decoding="async"
      className="shrink-0 rounded-xl object-cover ring-1 ring-inset ring-slate-900/5"
      style={{ width: size, height: size }}
    />
  );
}
