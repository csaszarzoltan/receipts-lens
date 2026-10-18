"use client";
import Link from 'next/link';
import {useRouter,usePathname} from 'next/navigation';
import {useState} from 'react';
import {useTranslation} from '@/lib/i18n';
import {logoutSession} from '@/lib/api';
import NotificationPanel from '@/components/NotificationPanel';
import ThemeToggle from '@/components/ThemeToggle';
import NavIcon from '@/components/NavIcon';
export default function Topbar(){
 const {t}=useTranslation(),router=useRouter(),pathname=usePathname();const [query,setQuery]=useState(''),[open,setOpen]=useState(false),[loggingOut,setLoggingOut]=useState(false),[error,setError]=useState(false);
 async function logout(){setLoggingOut(true);setError(false);try{await logoutSession();router.push('/login')}catch{setError(true)}finally{setLoggingOut(false)}}
 return <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95"><div className="flex min-h-16 items-center gap-2 px-4 sm:px-6">
  {pathname==='/receipts'?<Link href="/dashboard" className="flex-1 font-semibold">ReceiptLens</Link>:<form className="min-w-0 flex-1 lg:max-w-md" role="search" onSubmit={e=>{e.preventDefault();router.push(`/receipts${query.trim()?`?q=${encodeURIComponent(query.trim())}`:''}`)}}><label htmlFor="global-search" className="sr-only">{t('search')}</label><input id="global-search" type="search" className="input" value={query} onChange={e=>setQuery(e.target.value)} placeholder={t('searchByMerchant')}/></form>}
  <div className="ml-auto flex shrink-0 items-center gap-1"><button type="button" className="min-h-11 min-w-11 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" aria-label={t('notificationsTitle')} onClick={()=>setOpen(true)}><NavIcon href="/notifications" className="mx-auto h-5 w-5"/></button><Link href="/settings" aria-label={t('settings')} className="flex min-h-11 min-w-11 items-center justify-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"><NavIcon href="/settings"/></Link><button type="button" disabled={loggingOut} className="min-h-11 min-w-11 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" aria-label={t('logout')} onClick={logout}><NavIcon href="/logout" className="mx-auto h-5 w-5"/></button><span className="hidden sm:inline"><ThemeToggle/></span></div>
 </div>{error&&<p role="alert" className="px-4 pb-3 text-sm text-rose-700 dark:text-rose-300">{t('couldNotLoad')}</p>}<NotificationPanel open={open} onClose={()=>setOpen(false)}/></header>;
}
