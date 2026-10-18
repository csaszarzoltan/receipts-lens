"use client";
import Link from 'next/link';
import {useState} from 'react';
import useSWR from 'swr';
import {getNotifications,markAllRead,updateNotification} from '@/lib/api';
import type {Notification} from '@/lib/types';
import {useTranslation} from '@/lib/i18n';
import {timeAgo} from '@/lib/utils';
import {useDialogFocus} from '@/lib/hooks/useDialogFocus';

function destination(item:Notification):string|null{
 if(!item.subject_id)return null;
 const id=encodeURIComponent(item.subject_id);
 if(item.kind==='review')return `/review?receipt=${id}`;
 if(item.kind==='approval')return `/approvals?receipt=${id}`;
 if(item.kind==='subscription')return `/subscriptions?subscription=${id}`;
 if(item.kind==='warranty')return `/warranties?receipt=${id}`;
 return `/receipts/${id}`;
}
export default function NotificationPanel({open,onClose}:{open:boolean;onClose:()=>void}){
 const {t}=useTranslation(),ref=useDialogFocus(open,onClose);const [failure,setFailure]=useState(false),[busy,setBusy]=useState(false);
 const {data,error,isLoading,mutate}=useSWR(open?'/product/notifications':null,()=>getNotifications(false));
 async function mark(item?:Notification){setBusy(true);setFailure(false);try{if(item)await updateNotification(item.notification_id,{read:!item.read});else await markAllRead();await mutate()}catch{setFailure(true)}finally{setBusy(false)}}
 if(!open)return null;
 return <div ref={ref} tabIndex={-1} role="dialog" aria-modal="true" aria-label={t('notificationsTitle')} className="fixed inset-0 z-50"><button type="button" tabIndex={-1} className="absolute inset-0 bg-slate-900/50" aria-label={t('closeDialog')} onClick={onClose}/><div className="absolute inset-y-0 right-0 flex w-96 max-w-[95vw] flex-col bg-white shadow-xl dark:bg-slate-950"><div className="flex items-center justify-between gap-2 border-b border-slate-200 p-4 dark:border-slate-800"><h2 className="text-lg font-semibold">{t('notificationsTitle')}</h2><button type="button" className="btn-secondary" onClick={onClose}>{t('closeDialog')}</button></div><div className="flex flex-wrap items-center gap-2 p-4"><button type="button" className="btn-secondary" disabled={busy} onClick={()=>mark()}>{t('notificationsMarkRead')}</button><Link href="/settings/notifications" onClick={onClose} className="text-brand-700 underline dark:text-brand-300">{t('notificationSettings')}</Link></div>{failure&&<p role="alert" className="px-4 text-rose-700 dark:text-rose-300">{t('notificationError')}</p>}<div className="flex-1 overflow-y-auto">{isLoading?<p role="status" className="p-4">{t('loading')}</p>:error?<div className="p-4"><p role="alert">{t('couldNotLoad')}</p><button type="button" className="btn-secondary mt-3" onClick={()=>mutate()}>{t('retry')}</button></div>:!data?.items.length?<div className="p-6"><p>{t('notificationsEmpty')}</p><p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{t('notificationsCaughtUp')}</p></div>:<ul className="divide-y divide-slate-200 dark:divide-slate-800">{data.items.map(item=><li key={item.notification_id} className="p-4"><p className="font-medium">{item.title}</p><p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{item.message}</p><p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{timeAgo(item.created_at)}</p><div className="mt-3 flex flex-wrap gap-2">{destination(item)&&<Link href={destination(item)!} onClick={onClose} className="btn-primary">{t('notificationOpen')}</Link>}<button type="button" className="btn-secondary" disabled={busy} onClick={()=>mark(item)}>{item.read?t('notificationRead'):t('notificationUnread')}</button></div></li>)}</ul>}</div></div></div>;
}
