"use client";
import {useEffect,useState} from "react";
import {listItems,type FeatureItem} from "@/lib/refunds";
export default function RefundWorkbench(){const [items,setItems]=useState<FeatureItem[]>([]);const [status,setStatus]=useState("loading");useEffect(()=>{listItems().then(x=>{setItems(x);setStatus("ready")}).catch(()=>setStatus("error"))},[]);return <section data-testid="refunds-page"><h1>Visszatérítések és sztornók egyeztetése</h1><p data-testid="refunds-status" aria-live="polite">{status}</p><div data-testid="refunds-evidence">{items.length} elem</div><button data-testid="refunds-primary-action" type="button">Új művelet</button>{status==="error"&&<button data-testid="refunds-conflict" onClick={()=>location.reload()}>Újrapróbálás</button>}</section>}
