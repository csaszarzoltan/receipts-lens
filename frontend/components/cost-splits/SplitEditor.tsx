"use client";
import {useEffect,useState} from "react";
import {listItems,type FeatureItem} from "@/lib/costSplits";
export default function SplitEditor(){const [items,setItems]=useState<FeatureItem[]>([]);const [status,setStatus]=useState("loading");useEffect(()=>{listItems().then(x=>{setItems(x);setStatus("ready")}).catch(()=>setStatus("error"))},[]);return <section data-testid="cost_splits-page"><h1>Megosztott vásárlások és költségfelosztás</h1><p data-testid="cost_splits-status" aria-live="polite">{status}</p><div data-testid="cost_splits-evidence">{items.length} elem</div><button data-testid="cost_splits-primary-action" type="button">Új művelet</button>{status==="error"&&<button data-testid="cost_splits-conflict" onClick={()=>location.reload()}>Újrapróbálás</button>}</section>}
