"use client";
import {useEffect,useState} from 'react';
import {usePathname} from 'next/navigation';
import {getPreferences} from '@/lib/api';
import {useTranslation} from '@/lib/i18n';
import OnboardingFlow from '@/components/OnboardingFlow';

/**
 * First-run onboarding on the dashboard. It is an inline card, not a modal:
 * a blocking dialog covers the header, so the theme switch and the other
 * header controls would not respond until the user dismissed it.
 */
export default function Onboarding(){
 const {t}=useTranslation(),pathname=usePathname();const [open,setOpen]=useState(false);
 useEffect(()=>{let active=true;getPreferences().then(p=>{if(active)setOpen(!p.onboarding_done)}).catch(()=>{});return()=>{active=false}},[]);
 if(!open||pathname!=='/dashboard')return null;
 return <section aria-labelledby="onboarding-title" className="card mb-6 p-5 sm:p-6">
  <div className="mb-4 flex items-start justify-between gap-3">
   <h2 id="onboarding-title" className="text-base font-semibold text-slate-900 dark:text-slate-100">{t('onboardingStart')}</h2>
   <button type="button" aria-label={t('closeDialog')} onClick={()=>setOpen(false)} className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200">✕</button>
  </div>
  <OnboardingFlow onDone={()=>setOpen(false)}/>
 </section>;
}
