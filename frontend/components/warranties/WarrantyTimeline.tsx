"use client";
import {useEffect,useState} from "react";
import {listItems,type FeatureItem} from "@/lib/warranties";
export default function WarrantyTimeline(){const [items,setItems]=useState<FeatureItem[]>([]);const [status,setStatus]=useState("loading");useEffect(()=>{listItems().then(x=>{setItems(x);setStatus("ready")}).catch(()=>setStatus("error"))},[]);return <section data-testid="warranties-page"><h1>Garanciák és visszaküldési határidők</h1><p data-testid="warranties-status" aria-live="polite">{status}</p><div data-testid="warranties-evidence">{items.length} elem</div><button data-testid="warranties-primary-action" type="button">Új művelet</button>{status==="error"&&<button data-testid="warranties-conflict" onClick={()=>location.reload()}>Újrapróbálás</button>}</section>}
