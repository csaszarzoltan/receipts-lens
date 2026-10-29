"use client";
import Link from 'next/link';
import {Suspense,useEffect,useState} from 'react';
import {useRouter,useSearchParams} from 'next/navigation';
import useSWR from 'swr';
import {getApprovals,searchReceipts} from '@/lib/api';
import type {Approval} from '@/lib/types';
import ReceiptCard from '@/components/ReceiptCard';
import EmptyState from '@/components/EmptyState';
import Pagination from '@/components/Pagination';
import {SkeletonCard} from '@/components/Skeleton';
import {categoryLabel} from '@/lib/categories';
import {useTranslation} from '@/lib/i18n';

function ReceiptsContent(){
 const {t}=useTranslation(),router=useRouter(),params=useSearchParams();
 const query=params.get('q')??'',category=params.get('category')??'',status=params.get('status')??'',dateFrom=params.get('date_from')??'',dateTo=params.get('date_to')??'';
 const offset=Math.max(0,Number(params.get('offset'))||0),limit=50;
 const [searchDraft,setSearchDraft]=useState(query);
 useEffect(()=>setSearchDraft(query),[query]);
 const [debouncedQuery,setDebouncedQuery]=useState(query);
 useEffect(()=>{const timer=setTimeout(()=>setDebouncedQuery(query),300);return()=>clearTimeout(timer)},[query]);
 const invalidDates=Boolean(dateFrom&&dateTo&&dateFrom>dateTo);
 const search={query:debouncedQuery||undefined,category:category||undefined,status:status||undefined,date_from:dateFrom||undefined,date_to:dateTo||undefined,offset,limit};
 const {data,error,isLoading,mutate}=useSWR(invalidDates?null:['receipts',search],()=>searchReceipts(search));
 // Approvals are optional: a failed read just means the cards show receipt status only.
 const {data:approvalData}=useSWR('approvals-for-receipts',()=>getApprovals().catch(()=>({items:[]})));
 const latestApproval=new Map<string,Approval>();
 for(const a of approvalData?.items??[]){const prev=latestApproval.get(a.receipt_id);if(!prev||a.created_at>prev.created_at)latestApproval.set(a.receipt_id,a)}
 function change(key:string,value:string,replace=false){const next=new URLSearchParams(params.toString());if(value)next.set(key,value);else next.delete(key);if(key!=='offset')next.delete('offset');const url=`/receipts${next.size?'?'+next.toString():''}`;replace?router.replace(url,{scroll:false}):router.push(url,{scroll:false})}
 const hasFilters=Boolean(query||category||status||dateFrom||dateTo);
 const statuses=[['needs_review','statusNeedsReview'],['completed','statusCompleted'],['pending','statusPending'],['approved','statusApproved'],['rejected','statusRejected'],['failed','statusFailed']] as const;
 return <div className="space-y-6">
  <div className="flex flex-wrap items-center justify-between gap-3"><div><h1 className="text-2xl font-bold">{t('receipts')}</h1><p className="mt-1 text-sm text-slate-600 dark:text-slate-400" role="status">{data?`${data.total} ${t('receiptsTotalSuffix')}`:t('receiptsSearchHint')}</p></div><Link href="/upload" className="btn-primary">{t('addReceipt')}</Link></div>
  <nav aria-label={t('receiptTools')} className="flex flex-wrap gap-2"><Link href="/receipts" className="btn-secondary" aria-current={!status?'page':undefined}>{t('receipts')}</Link><Link href="/receipts?status=needs_review" className="btn-secondary" aria-current={status==='needs_review'?'page':undefined}>{t('needsReview')}</Link><Link href="/duplicates" className="btn-secondary">{t('duplicates')}</Link><Link href="/inbox" className="btn-secondary">{t('inbox')}</Link></nav>
  <section className="card grid gap-4 p-4 sm:grid-cols-2 lg:grid-cols-3" aria-label={t('filter')}>
   <label className="text-sm font-medium">{t('search')}<input type="search" className="input mt-1" value={searchDraft} placeholder={t('searchByMerchant')} onChange={e=>{setSearchDraft(e.target.value);change('q',e.target.value,true)}}/></label>
   <label className="text-sm font-medium">{t('category')}<select className="input mt-1" value={category} onChange={e=>change('category',e.target.value)}><option value="">{t('allCategories')}</option>{Array.from(new Set([...(data?.categories??[]),...(category?[category]:[])])).map(c=><option key={c} value={c}>{categoryLabel(t,c)}</option>)}</select></label>
   <label className="text-sm font-medium">{t('status')}<select className="input mt-1" value={status} onChange={e=>change('status',e.target.value)}><option value="">{t('allStatuses')}</option>{statuses.map(([value,label])=><option key={value} value={value}>{t(label)}</option>)}</select></label>
   <label className="text-sm font-medium">{t('dateFromLabel')}<input type="date" className="input mt-1" value={dateFrom} onChange={e=>change('date_from',e.target.value)}/></label>
   <label className="text-sm font-medium">{t('dateToLabel')}<input type="date" className="input mt-1" value={dateTo} onChange={e=>change('date_to',e.target.value)}/></label>
   {hasFilters&&<button type="button" className="btn-secondary self-end" onClick={()=>router.push('/receipts',{scroll:false})}>{t('clearFilters')}</button>}
  </section>
  {invalidDates?<p role="alert" className="text-rose-700 dark:text-rose-300">{t('filtersInvalid')}</p>:isLoading?<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{Array.from({length:6},(_,i)=><SkeletonCard key={i}/>)}</div>:error?<div role="alert"><p>{t('couldNotLoad')}</p><button type="button" className="btn-secondary mt-3" onClick={()=>mutate()}>{t('retry')}</button></div>:!data?.items.length?<EmptyState title={hasFilters?t('noMatchingReceipts'):t('noReceiptsYetTitle')} description={hasFilters?t('noMatchingHint'):t('uploadReceiptHint')} action={hasFilters?undefined:{label:t('addReceipt'),href:'/upload'}}/>:<>
   <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-label={t('receiptListLabel')}>{data.items.map(item=><li key={item.receipt_id} className="flex flex-col"><ReceiptCard item={item} approval={latestApproval.get(item.receipt_id)}/></li>)}</ul>
   {data.total>limit&&<Pagination total={data.total} offset={offset} limit={limit} onPageChange={value=>change('offset',String(value))}/>}</>}
 </div>;
}
export default function ReceiptsPage(){return <Suspense fallback={<SkeletonCard className="h-64"/>}><ReceiptsContent/></Suspense>}
