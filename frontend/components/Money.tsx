"use client";

import { formatMoney } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

interface MoneyProps {
  amount: number | null | undefined;
  currency?: string | null;
  className?: string;
}

/**
 * Currency-aware amount display using Intl.NumberFormat.
 *
 * Three states are kept apart: a known amount, a genuine zero, and an unknown
 * amount (null/undefined). An unknown amount renders a dash with an
 * accessible "Unknown" label so it is never mistaken for 0.00.
 */
export default function Money({ amount, currency, className }: MoneyProps) {
  const { t } = useTranslation();
  if (amount === null || amount === undefined || Number.isNaN(amount)) {
    return (
      <span className={className} title={t("moneyUnknown")} aria-label={t("moneyUnknown")}>
        —
      </span>
    );
  }
  return <span data-testid="money-amount" className={className}>{formatMoney(amount, currency)}</span>;
}
