"use client";
import {useEffect,useState} from "react";
import {listItems,type FeatureItem} from "@/lib/qualityTasks";
export default function QualityTaskCenter(){const [items,setItems]=useState<FeatureItem[]>([]);const [status,setStatus]=useState("loading");useEffect(()=>{listItems().then(x=>{setItems(x);setStatus("ready")}).catch(()=>setStatus("error"))},[]);return <section data-testid="data_quality-page"><h1>Adatminőségi feladatközpont</h1><p data-testid="data_quality-status" aria-live="polite">{status}</p><div data-testid="data_quality-evidence">{items.length} elem</div><button data-testid="data_quality-primary-action" type="button">Új művelet</button>{status==="error"&&<button data-testid="data_quality-conflict" onClick={()=>location.reload()}>Újrapróbálás</button>}</section>}
