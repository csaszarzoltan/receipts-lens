"use client";
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {MOBILE_TABS} from '@/lib/nav';
import {useTranslation} from '@/lib/i18n';
import {cx} from '@/lib/utils';
import NavIcon from '@/components/NavIcon';
export default function MobileNav(){const pathname=usePathname();const {t}=useTranslation();return <nav aria-label={t('primaryNavigation')} className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur lg:hidden dark:border-slate-800 dark:bg-slate-950/95"><div className="grid grid-cols-5">{MOBILE_TABS.map(item=>{
 const active=pathname===item.href || item.href==='/receipts'&&(pathname.startsWith('/receipts/')||['/review','/duplicates','/inbox'].includes(pathname)) || item.href==='/finances'&&['/budget','/reports','/forecast','/subscriptions'].includes(pathname) || item.href==='/more'&&['/warranties','/statement','/chat','/insights','/tax','/settings'].some(p=>pathname.startsWith(p));
 return <Link key={item.href} href={item.href} aria-current={active?'page':undefined} className={cx('flex min-h-16 flex-col items-center justify-center gap-1 text-xs font-medium focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-500',active?'text-brand-700 dark:text-brand-300':'text-slate-600 dark:text-slate-400')}><span className={item.href==='/upload'?'rounded-full bg-brand-600 p-2 text-white':''}><NavIcon href={item.href}/></span><span className="whitespace-nowrap">{t(item.href==='/upload'?'mobileAddReceipt':item.labelKey)}</span></Link>
})}</div></nav>}
