import { PHOTOS, type PhotoKey } from "@/lib/photos";

/**
 * Slim photo band shown above a page's content. Decorative only: the page
 * title below it carries the meaning, so the image has no alt text.
 */
export default function PhotoStrip({ photo }: { photo: PhotoKey }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={PHOTOS[photo].src}
      alt=""
      aria-hidden="true"
      loading="lazy"
      decoding="async"
      className="mb-6 h-28 w-full rounded-2xl object-cover shadow-card sm:h-36"
    />
  );
}
