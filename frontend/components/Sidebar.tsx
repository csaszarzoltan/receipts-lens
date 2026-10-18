"use client";
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {PRIMARY_NAV_ITEMS} from '@/lib/nav';
import {useTranslation} from '@/lib/i18n';
import NavIcon from '@/components/NavIcon';
import {cx} from '@/lib/utils';
export default function Sidebar(){const pathname=usePathname();const {t}=useTranslation();return <aside className="hidden lg:block" aria-label={t('sidebarNavigation')}>
  <div className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
    <Link href="/dashboard" className="flex min-h-20 items-center gap-3 px-6 text-lg font-semibold"><NavIcon href="/receipts"/>ReceiptLens</Link>
    <Link href="/upload" className="btn-primary mx-4 mb-6 gap-2"><NavIcon href="/upload"/>{t('addReceipt')}</Link>
    <nav className="flex-1 space-y-2 px-3" aria-label={t('primaryNavigation')}>{PRIMARY_NAV_ITEMS.map(item=>{const active=pathname===item.href || item.href==='/receipts'&&pathname.startsWith('/receipts/') || item.href==='/receipts'&&['/review','/duplicates','/inbox'].some(p=>pathname.startsWith(p)) || item.href==='/finances'&&['/budget','/reports','/forecast','/subscriptions'].some(p=>pathname.startsWith(p));return <Link key={item.href} href={item.href} aria-current={active?'page':undefined} className={cx('flex min-h-12 items-center gap-3 rounded-xl px-4 font-medium',active?'bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300':'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-900')}><NavIcon href={item.href}/>{t(item.labelKey)}</Link>})}</nav>
    <Link href="/settings" className="m-4 flex min-h-11 items-center gap-3 rounded-lg px-3 text-slate-600 dark:text-slate-300"><NavIcon href="/settings"/>{t('settings')}</Link>
  </div>
</aside>}
