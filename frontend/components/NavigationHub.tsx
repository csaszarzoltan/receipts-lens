"use client";
import Link from 'next/link';
import {useTranslation} from '@/lib/i18n';
import {NAV_ITEMS,BUSINESS_NAV_ITEMS} from '@/lib/nav';
import NavIcon from '@/components/NavIcon';
export default function NavigationHub({kind}:{kind:'finances'|'more'}){
 const {t}=useTranslation();
 const financeRoutes=['/budget','/reports','/forecast','/subscriptions'];
 const routes=kind==='finances'?financeRoutes:['/warranties','/statement','/chat','/insights','/tax','/settings'];
 const sections=kind==='finances'?[{title:t('moneyTools'),items:NAV_ITEMS.filter(i=>routes.includes(i.href))}]:[
 {title:t('usefulTools'),items:NAV_ITEMS.filter(i=>routes.includes(i.href))},
 {title:t('receiptTools'),items:NAV_ITEMS.filter(i=>['/review','/duplicates','/inbox'].includes(i.href))},
 {title:t('businessWorkspace'),items:BUSINESS_NAV_ITEMS}];
 return <div className="space-y-8"><h1 className="text-2xl font-bold">{t(kind==='finances'?'finances':'moreSections')}</h1>{sections.map(section=><section key={section.title}><h2 className="mb-3 text-lg font-semibold">{section.title}</h2><ul className="grid gap-3 sm:grid-cols-2">{section.items.map(item=><li key={item.href}><Link href={item.href} className="card flex min-h-20 items-center gap-4 p-5 hover:border-brand-400 focus-visible:ring-2 focus-visible:ring-brand-500"><NavIcon href={item.href}/><span className="font-medium">{t(item.labelKey)}</span><span className="ml-auto" aria-hidden="true">→</span></Link></li>)}</ul></section>)}</div>;
}
