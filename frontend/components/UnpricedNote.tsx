"use client";

import Link from "next/link";
import { useTranslation } from "@/lib/i18n";

/** Tells the user how many receipts are left out of a total because their amount is unconfirmed. */
export default function UnpricedNote({ count }: { count?: number }) {
  const { t } = useTranslation();
  if (!count || count <= 0) return null;
  return (
    <p className="mt-1 text-xs text-amber-700 dark:text-amber-400" data-testid="unpriced-note">
      {count} {t("unpricedReceiptsSuffix")}{" "}
      <Link href="/review" className="font-medium underline">
        {t("reviewThem")}
      </Link>
    </p>
  );
}
