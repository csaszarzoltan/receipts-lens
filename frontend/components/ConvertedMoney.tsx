"use client";

import { useEffect, useState } from "react";
import useSWR from "swr";
import Money from "@/components/Money";
import { convertCurrency, getPreferences } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { effectiveBaseCurrency } from "@/lib/utils";

export default function ConvertedMoney({
  amount,
  currency,
}: {
  amount: number | null | undefined;
  currency?: string | null;
}) {
  const { locale } = useTranslation();
  const { data: prefs } = useSWR("/product/preferences", getPreferences);
  const [v, setV] = useState<number | null>(null);
  // An unknown currency is never converted: that would invent an exchange rate for it.
  const source = (currency || "").toUpperCase();
  const target = effectiveBaseCurrency(prefs, locale).toUpperCase();

  useEffect(() => {
    let active = true;
    setV(null);
    if (amount == null || !source || source === target) return;
    convertCurrency({ amount, base: source, quote: target })
      .then((r) => active && setV(r.converted))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [amount, source, target]);

  return (
    <span>
      <Money amount={amount} currency={source} />
      {v != null ? (
        <span className="ml-1 text-sm text-slate-500 dark:text-slate-400" data-testid="converted-amount">
          (~
          <Money amount={v} currency={target} />)
        </span>
      ) : null}
    </span>
  );
}
