"use client";
import {useEffect,useState} from "react";
import {listItems,type FeatureItem} from "@/lib/periodClose";
export default function PeriodCloseWizard(){const [items,setItems]=useState<FeatureItem[]>([]);const [status,setStatus]=useState("loading");useEffect(()=>{listItems().then(x=>{setItems(x);setStatus("ready")}).catch(()=>setStatus("error"))},[]);return <section data-testid="period_close-page"><h1>Könyvelési időszak lezárása</h1><p data-testid="period_close-status" aria-live="polite">{status}</p><div data-testid="period_close-evidence">{items.length} elem</div><button data-testid="period_close-primary-action" type="button">Új művelet</button>{status==="error"&&<button data-testid="period_close-conflict" onClick={()=>location.reload()}>Újrapróbálás</button>}</section>}
