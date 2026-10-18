"use client";
import Link from 'next/link';
import useSWR from 'swr';
import {getConsumerDashboard,searchReceipts,getPreferences} from '@/lib/api';
import type {ConsumerDashboard,HouseholdStatus} from '@/lib/types';
import {useTranslation} from '@/lib/i18n';
import {categoryLabel} from '@/lib/categories';
import {formatDate,formatMoney,defaultCurrencyForLocale} from '@/lib/utils';
import {PageSkeleton} from '@/components/Skeleton';
import Money from '@/components/Money';
import UnpricedNote from '@/components/UnpricedNote';
import CurrencySelector from '@/components/CurrencySelector';
import SampleReceipt from '@/components/SampleReceipt';
import DeadlinesCard from '@/components/DeadlinesCard';
import StatusBadge from '@/components/StatusBadge';
import SavingsBlockCard from '@/components/SavingsBlockCard';

export default function ConsumerDashboardPage(){
 const {t,locale}=useTranslation();
 const {data,error,isLoading,mutate}=useSWR<ConsumerDashboard>('/api/v1/consumer/dashboard',getConsumerDashboard);
 const {data:counts}=useSWR('dashboard-receipt-count',()=>searchReceipts({limit:1}));
 const {data:review}=useSWR('dashboard-review-count',()=>searchReceipts({status:'needs_review',limit:1}));
 const {data:prefs,mutate:refreshPrefs}=useSWR('/product/preferences',getPreferences);
 if(isLoading)return <PageSkeleton/>;
 if(error||!data)return <div role="alert" className="card p-6"><h1 className="text-2xl font-bold">{t('overviewTitle')}</h1><p className="my-4">{t('couldNotLoad')}</p><button type="button" className="btn-primary" onClick={()=>mutate()}>{t('retry')}</button></div>;
 const monthly=data.monthly_by_category,daily=data.daily_remaining;
 const empty=counts?.total===0 || !counts&&data.recent_receipts.length===0;
 const unknown=monthly.total_spent===0&&(monthly.unpriced_receipts??0)>0;
 const currencyPicker=<section className="card p-5"><h2 className="text-lg font-semibold">{t('chooseCurrency')}</h2><p className="mb-4 mt-2 text-sm text-slate-600 dark:text-slate-400">{t('chooseCurrencyHint')}</p><CurrencySelector value={prefs?.base_currency_source==='saved'?prefs.base_currency:defaultCurrencyForLocale(locale)} onSaved={()=>{refreshPrefs();mutate()}}/></section>;
 return <div className="space-y-6">
  <div className="flex flex-wrap items-center justify-between gap-3"><div><h1 className="text-2xl font-bold">{t('overviewTitle')}</h1><p className="mt-1 text-slate-600 dark:text-slate-400">{t('overviewSubtitle')}</p></div>{!empty&&<Link href="/upload" className="btn-primary">{t('addReceipt')}</Link>}</div>
  {empty?<><section className="card p-6 sm:p-8"><h2 className="text-xl font-semibold">{t('firstReceiptTitle')}</h2><p className="mt-3 max-w-lg text-slate-600 dark:text-slate-400">{t('firstReceiptHint')}</p><Link href="/upload" className="btn-primary mt-6">{t('startWithReceipt')}</Link></section><SampleReceipt/>{!monthly.currency&&currencyPicker}</>:<>
   <section data-testid="spending-summary" className="card p-6" aria-label={t('monthlySpending')}><p className="text-sm font-medium text-slate-600 dark:text-slate-400">{t('recordedSpending')} · {monthly.month}</p><p className="mt-2 text-4xl font-semibold tracking-tight"><Money amount={unknown?null:monthly.total_spent} currency={monthly.currency}/></p><p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{t('recordedSpendingHint')}</p><UnpricedNote count={monthly.unpriced_receipts}/>{Object.entries(monthly.other_currency_totals??{}).length>0&&<div className="mt-3 text-sm"><p>{t('otherCurrenciesHint')}</p>{Object.entries(monthly.other_currency_totals??{}).map(([code,value])=><p key={code}><Money amount={value} currency={code}/></p>)}</div>}</section>
   {!!review?.total&&<section className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 p-5 text-amber-950 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100"><h2 className="font-semibold">{review.total} {t('reviewCount')}</h2><Link href="/review" className="btn-primary">{t('checkReceipt')}</Link></section>}
   <section className="card p-5"><div className="flex items-center justify-between gap-3"><h2 className="text-lg font-semibold">{t('recentReceipts')}</h2><Link href="/receipts" className="text-brand-700 underline dark:text-brand-300">{t('allReceiptsLink')}</Link></div><ul className="mt-3 divide-y divide-slate-200 dark:divide-slate-800">{data.recent_receipts.map(r=><li key={r.receipt_id}><Link href={`/receipts/${r.receipt_id}`} className="flex min-h-20 flex-wrap items-center justify-between gap-3 py-3"><div className="min-w-0"><p className="break-words font-medium">{r.merchant||t('unknownVendorLabel')}</p><p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{formatDate(r.date)}</p></div><div className="text-right"><Money amount={r.total} currency={r.currency}/><div className="mt-1"><StatusBadge status={r.status}/></div></div></Link></li>)}</ul></section>
   <div className="grid gap-4 lg:grid-cols-2"><section className="card p-5"><h2 className="text-lg font-semibold">{t('monthlySpending')}</h2><ul className="mt-3 space-y-3">{monthly.categories.map(c=><li key={c.key} className="flex items-center justify-between gap-3"><span>{categoryLabel(t,c.key)}</span><Money amount={c.total} currency={monthly.currency}/></li>)}</ul><Link href="/reports" className="btn-secondary mt-4">{t('openReports')}</Link></section>
   <section className="card p-5"><h2 className="text-lg font-semibold">{daily?t('dailyRemaining'):t('noBudgetSet')}</h2>{daily?<><p className="mt-3 text-3xl font-semibold"><Money amount={daily.daily_remaining} currency={daily.currency}/></p><p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{t('incompleteDailyHint')}</p><UnpricedNote count={daily.unpriced_receipts}/><p className="mt-2 text-sm">{t('remaining')}: <Money amount={daily.remaining_this_month} currency={daily.currency}/></p>{(Object.keys(daily.other_currency_totals??{}).length>0||!!daily.other_budget_currencies?.length)&&<p className="mt-2 text-sm text-amber-800 dark:text-amber-300">{t('otherCurrenciesHint')}</p>}</>:<p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{t('noBudgetSetHint')}</p>}<Link href="/budget" className="btn-secondary mt-4">{t('budget')}</Link></section></div>
   {!monthly.currency&&currencyPicker}
   <HouseholdBlock household={data.household}/>
   <SavingsBlockCard savings={data.savings}/>
   <DeadlinesCard/>
   {data.price_alerts.length>0&&<section className="card p-5"><h2 className="text-lg font-semibold">{t('priceAlerts')}</h2><ul className="mt-3 space-y-3">{data.price_alerts.map(a=><li key={a.merchant}><Link href="/subscriptions" className="block rounded-lg bg-amber-50 p-4 text-amber-950 dark:bg-amber-950 dark:text-amber-100">{a.merchant} · <Money amount={a.monthly_cost} currency={a.currency}/></Link></li>)}</ul></section>}
   {data.cancellable_subscriptions.length>0&&<section className="card p-5"><h2 className="text-lg font-semibold">{t('cancellableSubscriptions')}</h2><Link href="/subscriptions" className="btn-secondary mt-4">{t('subscriptions')}</Link></section>}
  </>}
 </div>;
}

function spentOrUnknown(spent: number, unpriced: number | undefined): number | null {
  return spent === 0 && (unpriced ?? 0) > 0 ? null : spent;
}

function HouseholdBlock({ household }: { household: HouseholdStatus }) {
  const { t } = useTranslation();
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
          {t("householdStatus")}
        </h2>
        <span className="text-xl" aria-hidden="true">
          👨‍👩‍👧‍👦
        </span>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-3 text-center">
        <div>
          <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            <Money amount={household.shared_budget > 0 ? household.shared_budget : null} currency={household.currency} />
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{t("familyBudget")}</p>
        </div>
        <div>
          <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            <Money amount={spentOrUnknown(household.spent, household.unpriced_receipts)} currency={household.currency} />
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{t("spent")}</p>
        </div>
        <div>
          <p className="text-lg font-semibold text-emerald-700 dark:text-emerald-400">
            <Money
              amount={
                household.shared_budget <= 0 || spentOrUnknown(household.spent, household.unpriced_receipts) === null
                  ? null
                  : household.remaining
              }
              currency={household.currency}
            />
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{t("remaining")}</p>
        </div>
      </div>
      <UnpricedNote count={household.unpriced_receipts} />
      {household.spent_other_currencies && Object.keys(household.spent_other_currencies).length > 0 ? (
        <p className="mt-3 text-xs text-slate-500 dark:text-slate-400" data-testid="other-currency-spend">
          {t("alsoSpentOtherCurrencies")}{" "}
          {Object.entries(household.spent_other_currencies)
            .map(([code, amount]) => formatMoney(amount, code))
            .join(" · ")}
        </p>
      ) : null}
      {household.members.length > 0 ? (
        <ul className="mt-4 space-y-2">
          {household.members.map((member) => (
            <li
              key={member.member_id}
              className="flex items-center justify-between text-sm"
            >
              <span className="truncate text-slate-700 dark:text-slate-300">
                {member.email}
              </span>
              <span className="ml-3 shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                {member.role_label}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">
          {t("noMembersHint")}
        </p>
      )}
    </div>
  );
}
