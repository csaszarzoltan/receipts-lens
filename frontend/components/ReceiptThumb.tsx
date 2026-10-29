"use client";

import { useEffect, useRef, useState } from "react";
import { getReceiptImage } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import type { Photo } from "@/lib/photos";

/**
 * Receipt photo thumbnail. The image is fetched only once the tile scrolls near the
 * viewport, and its object URL is released on unmount. The alt text is empty: the
 * enclosing link already names the receipt.
 */
export default function ReceiptThumb({ receiptId, fallback }: { receiptId: string; fallback?: Photo }) {
  const { t } = useTranslation();
  const ref = useRef<HTMLDivElement>(null);
  const [src, setSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let cancelled = false;
    let objectUrl: string | undefined;
    let observer: IntersectionObserver | undefined;

    const load = () => {
      getReceiptImage(receiptId)
        .then((blob) => {
          if (cancelled) return;
          objectUrl = URL.createObjectURL(blob);
          setSrc(objectUrl);
        })
        .catch(() => {
          if (!cancelled) setFailed(true);
        });
    };

    if (typeof IntersectionObserver === "undefined") {
      load();
    } else {
      observer = new IntersectionObserver(
        (entries) => {
          if (!entries.some((entry) => entry.isIntersecting)) return;
          observer?.disconnect();
          load();
        },
        { rootMargin: "200px" },
      );
      observer.observe(el);
    }

    return () => {
      cancelled = true;
      observer?.disconnect();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [receiptId]);

  return (
    <div ref={ref} className="relative aspect-[4/3] overflow-hidden rounded-lg bg-slate-100 dark:bg-slate-800">
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src} alt="" loading="lazy" className="h-full w-full object-cover" />
      ) : fallback ? (
        // Until the receipt photo arrives, show the category photo instead of a grey tile.
        // eslint-disable-next-line @next/next/no-img-element
        <img src={fallback.src} alt="" aria-hidden="true" loading="lazy" className="h-full w-full object-cover" />
      ) : null}
      {!src && failed ? (
        <span className="absolute inset-x-0 bottom-0 bg-slate-950/70 px-2 py-1 text-center text-xs text-white">
          {t("imageUnavailable")}
        </span>
      ) : null}
    </div>
  );
}
