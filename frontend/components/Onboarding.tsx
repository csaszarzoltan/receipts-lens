"use client";
import {useEffect,useState} from 'react';
import {usePathname} from 'next/navigation';
import {getPreferences} from '@/lib/api';
import {useTranslation} from '@/lib/i18n';
import Modal from '@/components/Modal';
import OnboardingFlow from '@/components/OnboardingFlow';
export default function Onboarding(){
 const {t}=useTranslation(),pathname=usePathname();const [open,setOpen]=useState(false);
 useEffect(()=>{let active=true;getPreferences().then(p=>{if(active)setOpen(!p.onboarding_done)}).catch(()=>{});return()=>{active=false}},[]);
 // The same flow is available as a page; it never interrupts an existing task.
 return <Modal open={open&&pathname==='/dashboard'} title={t('onboardingStart')} onClose={()=>setOpen(false)}><OnboardingFlow onDone={()=>setOpen(false)}/></Modal>;
}
