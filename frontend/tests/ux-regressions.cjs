const {test}=require('node:test');const assert=require('node:assert/strict');const ts=require('typescript');const fs=require('node:fs');const vm=require('node:vm');const path=require('node:path');
function load(file,mocks={}) {const source=fs.readFileSync(path.join(__dirname,'..',file),'utf8');const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true}}).outputText;const module={exports:{}};vm.runInNewContext(js,{exports:module.exports,module,require:n=>mocks[n]||require(n),crypto:require('node:crypto').webcrypto,console,setTimeout,clearTimeout,URLSearchParams,File:global.File,...(mocks.__globals||{})},{filename:file});return module.exports;}
function hooks(){let slots=[],index=0;const react={Suspense:Symbol.for('react.suspense'),useState:initial=>{const i=index++;if(!(i in slots))slots[i]=typeof initial==='function'?initial():initial;return[slots[i],v=>slots[i]=typeof v==='function'?v(slots[i]):v]},useRef:initial=>{const i=index++;return slots[i]||(slots[i]={current:initial})},useCallback:fn=>fn,useEffect:()=>{},useMemo:fn=>fn()};return{react,render:fn=>{index=0;return fn()}};}
const i18n={useTranslation:()=>({t:key=>key,locale:'hu'}),t:key=>key,getLocale:()=> 'hu'};
test('REQ-UX-02/06 AC-UX-02/06 duplicate filenames and retry preserve file and key',async()=>{const h=hooks(),calls=[];const api={uploadReceipt:async(file,progress,key)=>{calls.push({file,key});if(calls.length===1)throw Error('network');return{receipt_id:'ok',receipt:{total:5,currency:'HUF'}}}};const m=load('lib/hooks/useUpload.ts',{'react':h.react,'@/lib/api':api,'@/lib/aiScanMock':{AI_MOCK_ENABLED:false},'@/lib/featureFlags':{AI_SCAN_ENABLED:false}});let hook=h.render(m.useUpload);const first={name:'same.png',type:'image/png',size:5},second={name:'same.png',type:'image/png',size:7};hook.enqueue([first,second]);await new Promise(r=>setTimeout(r,0));assert.equal(calls[0].file,first);assert.equal(calls[1].file,second);assert.ok(calls[0].key);assert.notEqual(calls[0].key,calls[1].key);hook=h.render(m.useUpload);hook.retry(hook.entries[0].id);await new Promise(r=>setTimeout(r,0));assert.equal(calls[2].file,first);assert.equal(calls[2].key,calls[0].key);assert.equal(h.render(m.useUpload).entries[0].status,'done');});
test('REQ-UX-03 AC-UX-03 unknown and zero confidence',()=>{const m=load('lib/confidence.ts');assert.equal(m.averageConfidence({}),null);assert.equal(m.averageConfidence({total:0,vendor:1}),0.5);assert.equal(m.averageConfidence({source:'vision',total:0}),0);assert.equal(m.averageConfidence({total:NaN}),null);});
test('REQ-UX-08 AC-UX-08 five mobile destinations include capture and retain receipts',()=>{const m=load('lib/nav.ts',{'./i18n':i18n});assert.equal(m.MOBILE_TABS.length,5);assert.deepEqual(Array.from(m.MOBILE_TABS,x=>x.href),['/dashboard','/receipts','/upload','/finances','/more']);});

function nodes(element) {if(element===null||element===undefined||typeof element==='boolean')return[];if(Array.isArray(element))return element.flatMap(nodes);if(typeof element!=='object')return[element];return[element,...nodes(element.props?.children)];}
function uiMocks(h,extra={}) {return {'react':h.react,'@/lib/i18n':i18n,'@/lib/imageQuality':{assessImageQuality:async()=>({ok:true}),assessCanvas:()=>({ok:true})},'next/link':'a','@/components/SavingsBlockCard':'savings','@/lib/utils':{cx:(...x)=>x.filter(Boolean).join(' '),formatDate:x=>x,formatMoney:x=>String(x),defaultCurrencyForLocale:()=> 'HUF'},...extra};}
test('REQ-UX-01 AC-UX-01 file chooser is a real working button and disabled respects keyboard',()=>{
 const h=hooks();const m=load('components/DropZone.tsx',uiMocks(h,{'@/lib/hooks/useDialogFocus':{useDialogFocus:()=>({current:null})}}));
 const tree=h.render(()=>m.default({onFiles:()=>{}}));const flat=nodes(tree);let clicked=0;
 const input=flat.find(x=>x?.type==='input'&&x.props['data-testid']==='dropzone-input');input.ref.current={click:()=>clicked++};
 const button=flat.find(x=>x?.type==='button'&&x.props.children==='dropChooseFile');assert.ok(button);button.props.onClick();assert.equal(clicked,1);
 const disabled=h.render(()=>m.default({onFiles:()=>{},disabled:true}));const zone=nodes(disabled).find(x=>x?.props?.role==='button');assert.equal(zone.props.tabIndex,-1);zone.props.onKeyDown({key:'Enter',preventDefault(){}});assert.equal(clicked,1);
});
test('REQ-UX-07/11/18 AC-UX-07/11/18 queue uses translated copy and review destination',()=>{
 const h=hooks();const m=load('components/UploadQueue.tsx',uiMocks(h,{'@/components/Money':()=>null}));
 const tree=h.render(()=>m.default({entries:[{id:'a',fileName:'receipt.png',status:'done',progress:100,result:{receipt_id:'abc',status:'needs_review',receipt:{vendor:'Bolt',total:10,currency:'HUF'}}}],onRemove(){},onRetry(){}}));
 const all=nodes(tree);assert.ok(all.includes('uploadSaved'));assert.ok(all.some(x=>x?.props?.href==='/review?receipt=abc'));assert.ok(!all.includes('OCR complete'));
});
test('REQ-UX-09/13/19 AC-UX-09/13/19 empty dashboard focuses on first receipt; missing currency is explicit',()=>{
 const h=hooks();const data={monthly_by_category:{month:'2026-10',total_spent:0,currency:null,categories:[]},daily_remaining:null,recent_receipts:[],price_alerts:[],cancellable_subscriptions:[]};
 const m=load('app/(app)/dashboard/page.tsx',uiMocks(h,{'swr':key=>({data:key==='/api/v1/consumer/dashboard'?data:key==='dashboard-receipt-count'?{total:0}:undefined}), '@/lib/api':{},'@/lib/categories':{categoryLabel:(_,name)=>name},'@/components/Skeleton':{PageSkeleton:()=>null},'@/components/Money':()=>null,'@/components/UnpricedNote':()=>null,'@/components/CurrencySelector':()=>null,'@/components/SampleReceipt':()=>null,'@/components/DeadlinesCard':()=>null,'@/components/StatusBadge':()=>null}));
 const all=nodes(h.render(m.default));assert.ok(all.includes('firstReceiptTitle'));assert.ok(all.includes('chooseCurrency'));assert.ok(!all.includes('noBudgetSet'));assert.ok(!all.some(x=>x?.type==='savings'||typeof x?.type==='function'&&x.type.name==='HouseholdBlock'));assert.equal(all.filter(x=>x?.props?.href==='/upload').length,1);
});
test('REQ-UX-05 AC-UX-05 retryable session error preserves token while 401 clears it',async()=>{
 let effect,cleared=0,redirects=[];const h=hooks();h.react.useEffect=fn=>{effect=fn};
 class ApiError extends Error{constructor(status){super('failed');this.status=status;}}
 let status=503;
 const api={ApiError,resolveSession:async()=>{throw new ApiError(status)}};
 const m=load('components/AppShell.tsx',uiMocks(h,{'next/navigation':{useRouter:()=>({replace:url=>redirects.push(url)})},'@/lib/api':api,'@/lib/auth':{getSessionToken:()=> 'token',clearSessionToken:()=>cleared++},'@/components/Sidebar':()=>null,'@/components/MobileNav':()=>null,'@/components/Topbar':()=>null}));
 h.render(()=>m.default({children:null}));effect();await new Promise(r=>setTimeout(r,0));assert.equal(cleared,0);assert.equal(redirects.length,0);assert.ok(nodes(h.render(()=>m.default({children:null}))).includes('sessionRetryHint'));
 status=401;effect();await new Promise(r=>setTimeout(r,0));assert.equal(cleared,1);assert.deepEqual(redirects,['/login']);
});
test('REQ-UX-12 AC-UX-12 dialog traps Tab, handles Escape and returns focus',()=>{
 let effect,cleanup,closed=0;let focusTarget;const events={};
 class Element{constructor(){this.inert=false;this.tagName='DIV';this.hidden=false;this.isConnected=true;}focus(){doc.activeElement=this;}getClientRects(){return[{}]}}
 const old=new Element(),first=new Element(),last=new Element(),dialog=new Element(),background=new Element(),body=new Element();
 body.style={overflow:''};body.children=[dialog,background];dialog.parentElement=body;body.parentElement=null;
 dialog.querySelectorAll=()=>[first,last];dialog.contains=x=>[dialog,first,last].includes(x);first.closest=last.closest=()=>null;
 const doc={body,activeElement:old,addEventListener:(key,fn)=>events[key]=fn,removeEventListener:key=>delete events[key]};
 const react={useRef:()=>({current:dialog}),useEffect:fn=>effect=fn};
 // A separate ref is needed for the latest close callback.
 let n=0;react.useRef=value=>n++===0?{current:dialog}:{current:value};
 const m=load('lib/hooks/useDialogFocus.ts',{'react':react,__globals:{document:doc,HTMLElement:Element}});
 m.useDialogFocus(true,()=>closed++);cleanup=effect();assert.equal(doc.activeElement,first);assert.equal(background.inert,true);
 last.focus();let prevented=false;events.keydown({key:'Tab',shiftKey:false,preventDefault(){prevented=true}});assert.equal(doc.activeElement,first);assert.equal(prevented,true);
 first.focus();events.keydown({key:'Tab',shiftKey:true,preventDefault(){}});assert.equal(doc.activeElement,last);
 events.keydown({key:'Escape',preventDefault(){}});assert.equal(closed,1);cleanup();assert.equal(doc.activeElement,old);assert.equal(background.inert,false);assert.equal(body.style.overflow,'');
});

test('REQ-UX-10 AC-UX-10 shared onboarding saves currency and never switches to a demo household',async()=>{
 const h=hooks(),saved=[],destinations=[];let failure=false,done=0;
 const m=load('components/OnboardingFlow.tsx',uiMocks(h,{'next/navigation':{useRouter:()=>({push:url=>destinations.push(url)})},'@/lib/api':{savePreferences:async data=>{if(failure)throw Error('offline');saved.push(data)},getPreferences:async()=>({})},'@/lib/hooks/useUpload':{useUpload:()=>({entries:[],lastResult:null,enqueue(){},remove(){},retry(){}})},'@/components/DropZone':'section','@/components/UploadQueue':'ul','@/components/CurrencySelector':'select'}));
 let tree=h.render(()=>m.default({onDone:()=>done++}));await nodes(tree).find(x=>x?.type==='button'&&x.props.children==='onboardingStart').props.onClick();
 assert.equal(saved[0].onboarding_done,true);assert.equal(saved[0].base_currency,'HUF');assert.deepEqual(destinations,['/upload']);assert.equal(done,1);
 failure=true;tree=h.render(()=>m.default({onDone:()=>done++}));await nodes(tree).find(x=>x?.type==='button'&&x.props.children==='skip').props.onClick();
 assert.equal(destinations.length,1);assert.ok(nodes(h.render(()=>m.default({}))).includes('onboardingSaveError'));
});
test('REQ-UX-14 AC-UX-14 category/date filters reach API and status labels remain distinct',()=>{
 const h=hooks(),searches=[],destinations=[],params=new URLSearchParams('category=Food&date_from=2026-10-01');
 const m=load('app/(app)/receipts/page.tsx',uiMocks(h,{'next/navigation':{useSearchParams:()=>params,useRouter:()=>({push:url=>destinations.push(url),replace:url=>destinations.push(url)})},'swr':(key,fetcher)=>{fetcher();return{data:{items:[],total:0,categories:['Food']}}},'@/lib/api':{searchReceipts:args=>searches.push(args)},'@/components/ReceiptCard':()=>null,'@/components/EmptyState':()=>null,'@/components/Pagination':()=>null,'@/components/Skeleton':{SkeletonCard:()=>null},'@/lib/categories':{categoryLabel:(_,x)=>x}}));
 const shell=h.render(m.default);const tree=h.render(()=>shell.props.children.type());const all=nodes(tree);
 assert.equal(searches[0].category,'Food');assert.equal(searches[0].date_from,'2026-10-01');assert.ok(all.includes('statusCompleted'));assert.ok(all.includes('statusApproved'));assert.ok(all.includes('statusRejected'));
 const select=all.find(x=>x?.type==='select'&&x.props.value==='Food');select.props.onChange({target:{value:'Other'}});assert.ok(destinations[0].includes('category=Other'));assert.ok(destinations[0].includes('date_from=2026-10-01'));
});
test('REQ-UX-15 AC-UX-15 primary navigation uses five translated destinations with touch-sized controls',()=>{
 const h=hooks();const nav=load('lib/nav.ts',{'./i18n':i18n});const m=load('components/MobileNav.tsx',uiMocks(h,{'next/navigation':{usePathname:()=>'/upload'},'@/lib/nav':nav,'@/components/NavIcon':'svg'}));
 const all=nodes(h.render(m.default));const links=all.filter(x=>x?.type==='a');assert.equal(links.length,5);assert.ok(links.every(x=>x.props.className.includes('min-h-16')));assert.ok(all.includes('mobileAddReceipt'));assert.ok(all.some(x=>x?.props?.['aria-label']==='primaryNavigation'));
});

test('REQ-UX-13 AC-UX-13 incomplete monthly and daily totals visibly keep missing counts',()=>{
 const h=hooks();const data={monthly_by_category:{month:'2026-10',total_spent:0,currency:'HUF',categories:[],unpriced_receipts:2},daily_remaining:{daily_remaining:100,remaining_this_month:2000,currency:'HUF',unpriced_receipts:2},recent_receipts:[{receipt_id:'r',merchant:'Shop',total:null,currency:null,status:'needs_review'}],price_alerts:[],cancellable_subscriptions:[]};
 const m=load('app/(app)/dashboard/page.tsx',uiMocks(h,{'swr':key=>({data:key==='/api/v1/consumer/dashboard'?data:key==='dashboard-receipt-count'?{total:1}:undefined}),'@/lib/api':{},'@/lib/categories':{categoryLabel:(_,name)=>name},'@/components/Skeleton':{PageSkeleton:()=>null},'@/components/Money':'money','@/components/UnpricedNote':'unpriced','@/components/CurrencySelector':'select','@/components/SampleReceipt':()=>null,'@/components/DeadlinesCard':()=>null,'@/components/StatusBadge':'status'}));
 const all=nodes(h.render(m.default));assert.equal(all.filter(x=>x?.type==='unpriced'&&x.props.count===2).length,2);assert.ok(all.some(x=>x?.type==='money'&&x.props.amount===null));assert.ok(all.includes('recordedSpendingHint'));assert.ok(all.includes('incompleteDailyHint'));
});
test('REQ-UX-17 AC-UX-17 notifications deep-link to exact receipt and expose write failure',async()=>{
 const h=hooks(),notification={notification_id:'n',subject_id:'r',kind:'review',title:'Check',message:'Amount',read:false,created_at:'2026-10-12'};
 const mocks=uiMocks(h,{'swr':()=>({data:{items:[notification]},mutate:async()=>{}}),'@/lib/api':{updateNotification:async()=>{throw Error('offline')},getNotifications:async()=>({items:[notification]}),markAllRead:async()=>{}},'@/lib/hooks/useDialogFocus':{useDialogFocus:()=>({current:null})}});mocks['@/lib/utils'].timeAgo=x=>x;
 const m=load('components/NotificationPanel.tsx',mocks);let all=nodes(h.render(()=>m.default({open:true,onClose(){}})));assert.ok(all.some(x=>x?.props?.href==='/review?receipt=r'));
 await all.find(x=>x?.type==='button'&&x.props.children==='notificationUnread').props.onClick();all=nodes(h.render(()=>m.default({open:true,onClose(){}})));assert.ok(all.includes('notificationError'));
});

test('REQ-UX-07 AC-UX-07 hydration starts with server locale, then adopts stored locale',()=>{
 let hydrating=true;const h=hooks();h.react.useSyncExternalStore=(subscribe,snapshot,serverSnapshot)=>hydrating?serverSnapshot():snapshot();
 const extra=load('lib/uxMessages.ts');const m=load('lib/i18n.ts',{'react':h.react,'./uxMessages':extra,'@/lib/utils':{preferredLocaleCode:()=> 'hu'},__globals:{window:{localStorage:{getItem:()=> 'hu'},addEventListener(){},removeEventListener(){}},document:{documentElement:{lang:'hu'}}}});
 assert.equal(h.render(m.useTranslation).locale,'en');hydrating=false;assert.equal(h.render(m.useTranslation).locale,'hu');
});
test('REQ-UX-06 AC-UX-06 settling uploads refreshes the quota cache',async()=>{
 const h=hooks(),refreshed=[];const m=load('lib/hooks/useUpload.ts',{'react':h.react,'swr':{mutate:async key=>refreshed.push(key)},'@/lib/api':{uploadReceipt:async()=>({receipt_id:'saved',receipt:{total:5,currency:'HUF'}})},'@/lib/aiScanMock':{AI_MOCK_ENABLED:false},'@/lib/featureFlags':{AI_SCAN_ENABLED:false}});
 h.render(m.useUpload).enqueue([{name:'receipt.png',type:'image/png',size:8}]);await new Promise(r=>setTimeout(r,0));assert.deepEqual(refreshed,['/api/v1/quota']);
});

function cameraHarness(getUserMedia) {
 const h=hooks(),files=[],frames=[];let cleanup,blobCallback,blobCalls=0;
 h.react.useEffect=fn=>{if(!cleanup)cleanup=fn()};
 const canvas={getContext:()=>({drawImage(){}}),toBlob:fn=>{blobCalls++;blobCallback=fn}};
 const m=load('components/DropZone.tsx',uiMocks(h,{
  '@/lib/hooks/useDialogFocus':{useDialogFocus:()=>({current:null})},
  __globals:{navigator:{mediaDevices:{getUserMedia}},requestAnimationFrame:fn=>frames.push(fn),document:{createElement:()=>canvas}},
 }));
 const render=()=>nodes(h.render(()=>m.default({onFiles:list=>files.push(...list)})));
 const button=(all,key)=>all.find(x=>x?.type==='button'&&nodes(x.props.children).includes(key));
 return{render,button,files,unmount:()=>cleanup(),flushFrames:()=>frames.splice(0).forEach(fn=>fn()),blob:()=>blobCallback,blobCalls:()=>blobCalls};
}
function deferred(){let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no});return{promise,resolve,reject};}
function fakeStream(){let stops=0;return{getTracks:()=>[{stop:()=>stops++}],stops:()=>stops};}

test('REQ-UX-18 camera double activation makes only one media request',async()=>{
 const request=deferred();let calls=0;const c=cameraHarness(()=>{calls++;return request.promise});
 const open=c.button(c.render(),'dropTakePhoto').props.onClick;
 const first=open(),second=open();assert.equal(calls,1);
 const stream=fakeStream();request.resolve(stream);await Promise.all([first,second]);
 const all=c.render();assert.equal(all.filter(x=>x?.props?.role==='dialog').length,1);
 c.button(all,'dropCancel').props.onClick();assert.equal(stream.stops(),1);
});

test('REQ-UX-18 cancelled camera request never opens and releases late stream',async()=>{
 const request=deferred(),c=cameraHarness(()=>request.promise);
 const pending=c.button(c.render(),'dropTakePhoto').props.onClick();
 const cancel=c.button(c.render(),'dropCancel');assert.ok(cancel,'pending permission request can be cancelled');cancel.props.onClick();
 const stream=fakeStream();request.resolve(stream);await pending;
 assert.equal(stream.stops(),1);assert.equal(c.render().filter(x=>x?.props?.role==='dialog').length,0);
});

test('REQ-UX-18 camera resolution after unmount releases tracks',async()=>{
 const request=deferred(),c=cameraHarness(()=>request.promise);
 const pending=c.button(c.render(),'dropTakePhoto').props.onClick();c.unmount();
 const stream=fakeStream();request.resolve(stream);await pending;assert.equal(stream.stops(),1);assert.equal(c.files.length,0);
});

test('REQ-UX-18 duplicate capture is prevented and cancelled encoding cannot upload',async()=>{
 const stream=fakeStream(),c=cameraHarness(async()=>stream);
 await c.button(c.render(),'dropTakePhoto').props.onClick();const all=c.render();
 const video=all.find(x=>x?.type==='video');video.ref.current={videoWidth:100,videoHeight:100,play:async()=>{}};video.props.onLoadedMetadata?.();c.flushFrames();
 const capture=c.button(c.render(),'dropCapture').props.onClick;capture();capture();assert.equal(c.blobCalls(),1);
 c.button(c.render(),'dropCancel').props.onClick();c.blob()(new Blob(['jpeg'],{type:'image/jpeg'}));
 assert.equal(c.files.length,0);assert.equal(stream.stops(),1);
});

test('REQ-UX-18 capture waits for preview and emits only one JPEG',async()=>{
 const stream=fakeStream(),c=cameraHarness(async()=>stream);
 await c.button(c.render(),'dropTakePhoto').props.onClick();const all=c.render();
 assert.equal(c.button(all,'dropCapture').props.disabled,true);
 const video=all.find(x=>x?.type==='video');video.ref.current={videoWidth:100,videoHeight:100,play:async()=>{}};video.props.onLoadedMetadata();c.flushFrames();
 assert.equal(c.button(c.render(),'dropCapture').props.disabled,false);
 c.button(c.render(),'dropCapture').props.onClick();const done=c.blob();done(new Blob(['jpeg'],{type:'image/jpeg'}));done(new Blob(['duplicate']));
 assert.equal(c.files.length,1);assert.equal(c.files[0].type,'image/jpeg');assert.equal(stream.stops(),1);
 assert.equal(c.render().filter(x=>x?.props?.role==='dialog').length,0);
});

test('REQ-UX-18 failed image encoding keeps camera open and allows retry',async()=>{
 const stream=fakeStream(),c=cameraHarness(async()=>stream);
 await c.button(c.render(),'dropTakePhoto').props.onClick();const all=c.render();
 const video=all.find(x=>x?.type==='video');video.ref.current={videoWidth:100,videoHeight:100,play:async()=>{}};video.props.onLoadedMetadata();c.flushFrames();
 c.button(c.render(),'dropCapture').props.onClick();c.blob()(null);
 assert.equal(c.files.length,0);assert.equal(stream.stops(),0);
 assert.ok(c.render().some(x=>x?.props?.role==='alert'&&x.props.children==='dropCaptureFailed'));
 c.button(c.render(),'dropCapture').props.onClick();assert.equal(c.blobCalls(),2);c.blob()(new Blob(['jpeg']));assert.equal(c.files.length,1);
});

test('REQ-UX-12 camera opener stays focusable while busy for focus return',async()=>{
 const request=deferred(),c=cameraHarness(()=>request.promise);
 const pending=c.button(c.render(),'dropTakePhoto').props.onClick();
 const opening=c.button(c.render(),'dropCameraOpening');assert.notEqual(opening.props.disabled,true);assert.equal(opening.props['aria-disabled'],true);
 request.resolve(fakeStream());await pending;
 const open=c.button(c.render(),'dropTakePhoto');assert.notEqual(open.props.disabled,true);assert.equal(open.props['aria-disabled'],true);
 c.button(c.render(),'dropCancel').props.onClick();assert.equal(c.button(c.render(),'dropTakePhoto').props['aria-disabled'],false);
});

test('REQ-UX-09/13 dashboard preserves household and savings for existing receipts',()=>{
 const h=hooks();
 const household={shared_budget:1000,spent:250,remaining:750,currency:'HUF',members:[{member_id:'m1',email:'member@example.test',role_label:'Felnőtt tag'}],unpriced_receipts:0,spent_other_currencies:{EUR:10}};
 const savings={period:'2026-10',potential_saving:50,total_spent:250,currency:'HUF',avg_by_category:{},top_candidates:[{merchant:'Bolt',potential_saving:50,delta_pct:5}]};
 const data={monthly_by_category:{month:'2026-10',total_spent:250,currency:'HUF',categories:[]},daily_remaining:null,recent_receipts:[{receipt_id:'r1',merchant:'Bolt',total:250,currency:'HUF'}],price_alerts:[],cancellable_subscriptions:[],household,savings};
 const m=load('app/(app)/dashboard/page.tsx',uiMocks(h,{'swr':key=>({data:key==='/api/v1/consumer/dashboard'?data:key==='dashboard-receipt-count'?{total:1}:undefined}),'@/lib/api':{},'@/lib/categories':{categoryLabel:(_,name)=>name},'@/components/Skeleton':{PageSkeleton:()=>null},'@/components/Money':'money','@/components/UnpricedNote':'unpriced','@/components/CurrencySelector':'select','@/components/SampleReceipt':()=>null,'@/components/DeadlinesCard':()=>null,'@/components/StatusBadge':'status','@/components/SavingsBlockCard':'savings'}));
 const all=nodes(h.render(m.default));
 const block=all.find(x=>typeof x?.type==='function'&&x.type.name==='HouseholdBlock');assert.ok(block,'household data remains visible');
 const rendered=nodes(h.render(()=>block.type(block.props)));assert.ok(rendered.includes('member@example.test'));
 for(const amount of [1000,250,750])assert.ok(rendered.some(x=>x?.type==='money'&&x.props.amount===amount&&x.props.currency==='HUF'));
 assert.ok(all.some(x=>x?.type==='savings'&&x.props.savings===savings));
});

function pixels(w,h,fn){const d=new Uint8ClampedArray(w*h*4);for(let y=0;y<h;y++)for(let x=0;x<w;x++){const v=fn(x,y),i=(y*w+x)*4;d[i]=d[i+1]=d[i+2]=v;d[i+3]=255}return d;}
function boxBlur(d,w,h,r){const o=new Uint8ClampedArray(d.length);for(let y=0;y<h;y++)for(let x=0;x<w;x++){let s=0,c=0;for(let dy=-r;dy<=r;dy++)for(let dx=-r;dx<=r;dx++){const xx=x+dx,yy=y+dy;if(xx>=0&&yy>=0&&xx<w&&yy<h){s+=d[(yy*w+xx)*4];c++}}const v=s/c,i=(y*w+x)*4;o[i]=o[i+1]=o[i+2]=v;o[i+3]=255}return o;}
test('REQ-I1 AC1 assessPixels flags blurred and dark photos and accepts a sharp one',()=>{
 const m=load('lib/imageQuality.ts');const W=120,H=120;
 const sharp=pixels(W,H,(x,y)=>(Math.floor(x/2)+Math.floor(y/6))%2?235:25);
 const blurred=boxBlur(sharp,W,H,6);const dark=pixels(W,H,(x,y)=>(Math.floor(x/2)%2?30:5));
 assert.deepEqual({ok:m.assessPixels(sharp,W,H).ok},{ok:true});
 assert.equal(m.assessPixels(blurred,W,H).ok,false);assert.equal(m.assessPixels(blurred,W,H).reason,'blurry');
 assert.equal(m.assessPixels(dark,W,H).reason,'dark');
 assert.equal(m.assessPixels(new Uint8ClampedArray(4),1,1).ok,true,'unmeasurable input never blocks');
});
test('REQ-I1 AC2 blurry picked file is held until the user chooses; sharp files upload at once',async()=>{
 const h=hooks();const files=[];const results={'blur.jpg':{ok:false,reason:'blurry'},'sharp.jpg':{ok:true}};
 const m=load('components/DropZone.tsx',uiMocks(h,{'@/lib/hooks/useDialogFocus':{useDialogFocus:()=>({current:null})},'@/lib/imageQuality':{assessImageQuality:async f=>results[f.name],assessCanvas:()=>({ok:true})}}));
 const render=()=>nodes(h.render(()=>m.default({onFiles:l=>files.push(...l.map(f=>f.name))})));
 const input=render().find(x=>x?.type==='input'&&x.props['data-testid']==='dropzone-input');
 input.props.onChange({target:{files:[{name:'blur.jpg'},{name:'sharp.jpg'}],value:''}});await new Promise(r=>setTimeout(r,0));
 assert.deepEqual(files,['sharp.jpg'],'only the sharp file is uploaded');
 const all=render();assert.ok(all.includes('qualityTitle'),'warning shown');
 const anyway=all.find(x=>x?.type==='button'&&x.props.children==='dropUploadAnyway');assert.ok(anyway);assert.ok(all.some(x=>x?.type==='button'&&x.props.children==='dropRetake'));
 anyway.props.onClick();assert.deepEqual(files,['sharp.jpg','blur.jpg']);assert.ok(!render().includes('qualityTitle'));
});

test('REQ-I4 AC1 receipts whose lines do not add up come first in the review queue, order otherwise stable',()=>{
 const m=load('lib/reviewOrder.ts');const mk=(id,lm)=>({receipt_id:id,receipt:{},checks:lm===undefined?undefined:{lines_match:lm,line_sum:1}});
 const out=m.sortReviewItems([mk('a',true),mk('b',false),mk('c',null),mk('d',false),mk('e')]).map(x=>x.receipt_id);
 assert.deepEqual(Array.from(out),['b','d','a','c','e']);
 assert.equal(m.hasLineMismatch(mk('x',false)),true);assert.equal(m.hasLineMismatch(mk('x',null)),false);
});
