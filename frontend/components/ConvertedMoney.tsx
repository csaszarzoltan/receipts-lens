"use client";

import { useEffect, useState } from "react";
import useSWR from "swr";
import Money from "@/components/Money";
import { convertCurrency, getPreferences } from "@/lib/api";

export default function ConvertedMoney({
  amount,
  currency,
}: {
  amount: number | null | undefined;
  currency?: string | null;
}) {
  const { data: prefs } = useSWR("/product/preferences", getPreferences);
  const [v, setV] = useState<number | null>(null);
  const source = (currency || "USD").toUpperCase();
  const target = (prefs?.base_currency || "USD").toUpperCase();

  useEffect(() => {
    let active = true;
    setV(null);
    if (amount == null || source === target) return;
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
        <span className="ml-1 text-sm text-slate-500" data-testid="converted-amount">
          (~
          <Money amount={v} currency={target} />)
        </span>
      ) : null}
    </span>
  );
}
