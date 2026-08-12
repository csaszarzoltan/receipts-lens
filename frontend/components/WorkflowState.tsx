export default function WorkflowState({title,description,kind="neutral"}:{title:string;description:string;kind?:"neutral"|"error"|"success"}) {
 const tone=kind==="error"?"border-red-200 bg-red-50 text-red-900 dark:border-red-900/50 dark:bg-red-950/50 dark:text-red-100":kind==="success"?"border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900/50 dark:bg-emerald-950/50 dark:text-emerald-100":"border-slate-200 bg-white text-slate-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100";
 return <div role={kind==="error"?"alert":"status"} className={`rounded-xl border p-5 ${tone}`}><h2 className="font-semibold">{title}</h2><p className="mt-1 text-sm">{description}</p></div>
}
