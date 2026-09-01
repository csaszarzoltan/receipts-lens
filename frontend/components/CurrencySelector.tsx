"use client";
import { useEffect, useState } from "react";
import { savePreferences } from "@/lib/api";
const CURRENCIES = ["HUF", "EUR", "USD", "GBP", "CHF", "CZK", "PLN", "JPY", "CAD", "AUD"];
export default function CurrencySelector({ value, onSaved }: { value: string; onSaved?: () => void }) {
 const [currency,setCurrency]=useState(value||"USD"); const [status,setStatus]=useState("idle");
 useEffect(()=>setCurrency(value||"USD"),[value]);
 async function change(next:string){setCurrency(next);setStatus("saving");try{await savePreferences({base_currency:next});setStatus("saved");onSaved?.();}catch{setStatus("error");}}
 return <div><label htmlFor="pref-base-currency" className="mb-1 block text-sm font-medium">Default currency</label><select id="pref-base-currency" data-testid="base-currency-selector" className="input" value={currency} onChange={e=>change(e.target.value)}>{CURRENCIES.map(c=><option key={c}>{c}</option>)}</select><p role="status" className="mt-1 text-xs text-slate-400">{status==="saving"?"Saving…":status==="saved"?"Currency saved":status==="error"?"Could not save currency":"Dashboard totals and budgets use this currency."}</p></div>;
}
