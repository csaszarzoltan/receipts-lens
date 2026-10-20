"use client";
import Link from 'next/link';
import {useTranslation} from '@/lib/i18n';
import type {UploadQueueEntry} from '@/lib/hooks/useUpload';
import Money from '@/components/Money';

export default function UploadQueue({entries,onRemove,onRetry}:{entries:UploadQueueEntry[];onRemove:(id:string)=>void;onRetry:(id:string)=>void}) {
  const {t}=useTranslation();
  return <ul className="space-y-3" aria-label={t('uploadQueueLabel')}>
    {entries.map(entry=>{
      const busy=['queued','uploading','processing'].includes(entry.status);
      const error=entry.errorStatus===413?t('uploadSizeError'):entry.errorStatus===415?t('uploadFormatError'):entry.errorStatus===402?t('uploadQuotaError'):entry.errorStatus===409?t('uploadConflictError'):t('uploadRetryHint');
      return <li key={entry.id} className="card p-4">
        <div className="flex items-start justify-between gap-3"><div className="min-w-0 flex-1">
          <p className="truncate font-medium">{entry.fileName}</p>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400" role="status">
            {entry.status==='queued'&&t('uploadQueued')}{entry.status==='uploading'&&`${t('uploadProgress')} ${entry.progress}%`}
            {entry.status==='processing'&&t('uploadProcessing')}{entry.status==='done'&&t('uploadSaved')}
        {entry.status==='error'&&<span className="text-rose-700 dark:text-rose-300">{error}</span>}
          </p></div>
          {!busy&&<button type="button" onClick={()=>onRemove(entry.id)} aria-label={`${t('hideUpload')}: ${entry.fileName}`} className="min-h-11 min-w-11 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800">×</button>}
        </div>
        {entry.status==='uploading'&&<div role="progressbar" aria-valuenow={entry.progress} aria-valuemin={0} aria-valuemax={100} aria-label={entry.fileName} className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"><div className="h-full bg-brand-600 transition-all" style={{width:`${entry.progress}%`}}/></div>}
            {entry.status==='done'&&entry.result?.duplicate_of&&<p role="status" data-testid="duplicate-notice" className="mt-3 rounded bg-amber-100 px-3 py-2 text-sm text-amber-800 dark:bg-amber-900/40 dark:text-amber-200">{t('duplicateUploadNotice')} <Link className="font-medium underline" href={`/receipts/${entry.result.duplicate_of}`}>{t('viewReceipt')}</Link></p>}
        {entry.status==='error'&&<button type="button" className="btn-secondary mt-3" onClick={()=>onRetry(entry.id)}>{t('retry')}</button>}
        {entry.status==='done'&&entry.result&&<div className="mt-3 flex flex-wrap items-center gap-3">
          <span className="font-medium">{entry.result.receipt?.vendor||t('unknownVendorLabel')}</span>
          <Money amount={entry.result.receipt?.total} currency={entry.result.receipt?.currency}/>
          <Link className="btn-primary ml-auto" href={entry.result.status==='needs_review'?`/review?receipt=${encodeURIComponent(entry.result.receipt_id)}`:`/receipts/${entry.result.receipt_id}`}>
            {entry.result.status==='needs_review'?t('checkReceipt'):t('viewReceipt')}
          </Link>
        </div>}
      </li>;
    })}
  </ul>;
}
