"use client";

import { useEffect, useRef, useState } from "react";
import { getReceiptImage } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";

/**
 * Receipt photo thumbnail. The image is fetched only once the tile scrolls near the
 * viewport, and its object URL is released on unmount. The alt text is empty: the
 * enclosing link already names the receipt.
 */
export default function ReceiptThumb({ receiptId }: { receiptId: string }) {
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
      ) : (
        <span className="flex h-full w-full items-center justify-center px-3 text-center text-xs text-slate-500 dark:text-slate-400">
          {failed ? t("imageUnavailable") : null}
        </span>
      )}
    </div>
  );
}
