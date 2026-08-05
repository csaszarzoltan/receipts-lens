import { formatMoney } from "@/lib/utils";

interface MoneyProps {
  amount: number | null | undefined;
  currency?: string | null;
  className?: string;
}

/** Currency-aware amount display using Intl.NumberFormat. */
export default function Money({ amount, currency, className }: MoneyProps) {
  return <span className={className}>{formatMoney(amount, currency)}</span>;
}
