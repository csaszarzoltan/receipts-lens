export default function WorkflowState({title,description,kind="neutral"}:{title:string;description:string;kind?:"neutral"|"error"|"success"}) {
 const tone=kind==="error"?"border-red-200 bg-red-50 text-red-900 dark:border-red-950 dark:bg-red-950/40 dark:text-red-300":kind==="success"?"border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-950 dark:bg-emerald-950/40 dark:text-emerald-300":"border-slate-200 bg-white text-slate-800 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200";
 return <div role={kind==="error"?"alert":"status"} className={`rounded-xl border p-5 ${tone}`}><h2 className="font-semibold">{title}</h2><p className="mt-1 text-sm">{description}</p></div>
}
