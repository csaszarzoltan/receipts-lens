"use client";
import {useEffect,useState} from 'react';
import {useRouter} from 'next/navigation';
import {getPreferences,savePreferences} from '@/lib/api';
import {useTranslation} from '@/lib/i18n';
import {useUpload} from '@/lib/hooks/useUpload';
import DropZone from '@/components/DropZone';
import UploadQueue from '@/components/UploadQueue';
import CurrencySelector from '@/components/CurrencySelector';
import {defaultCurrencyForLocale,effectiveBaseCurrency} from '@/lib/utils';
export default function OnboardingFlow({onDone}:{onDone?:()=>void}){
 const {t,locale}=useTranslation(),router=useRouter();const upload=useUpload();
 const [currency,setCurrency]=useState(defaultCurrencyForLocale(locale));
 useEffect(()=>{getPreferences().then(p=>setCurrency(effectiveBaseCurrency(p,locale))).catch(()=>{});},[locale]);
 const [saving,setSaving]=useState(false),[error,setError]=useState(false);
 async function finish(destination:string){setSaving(true);setError(false);try{await savePreferences({onboarding_done:true,base_currency:currency});onDone?.();router.push(destination)}catch{setError(true)}finally{setSaving(false)}}
 return <div className="space-y-5"><p className="text-base text-slate-600 dark:text-slate-300">{t('firstReceiptHint')}</p>
  <CurrencySelector value={currency} onChange={setCurrency}/>
  <DropZone disabled={saving} onFiles={files=>upload.enqueue(files)}/>
  <UploadQueue entries={upload.entries} onRemove={upload.remove} onRetry={upload.retry}/>
  {error&&<p role="alert" className="text-rose-700 dark:text-rose-300">{t('onboardingSaveError')}</p>}
  <div className="flex flex-wrap justify-between gap-3"><button type="button" className="btn-secondary" disabled={saving} onClick={()=>finish('/dashboard')}>{t('skip')}</button><button type="button" className="btn-primary" disabled={saving} onClick={()=>finish(upload.lastResult?`/receipts/${upload.lastResult.receipt_id}`:'/upload')}>{saving?t('savingLabel'):upload.lastResult?t('finish'):t('onboardingStart')}</button></div>
 </div>;
}
