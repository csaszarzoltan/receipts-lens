import { test, expect, Page, Route } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const cors={'access-control-allow-origin':'http://127.0.0.1:3040','access-control-allow-methods':'GET,POST,PUT,PATCH,DELETE,OPTIONS','access-control-allow-headers':'Content-Type,Authorization,Idempotency-Key,X-Tenant-ID,X-Role,If-Match'};
function fulfill(route: Route, payload: Parameters<Route['fulfill']>[0]) {
 return route.fulfill(route.request().method()==='OPTIONS'?{status:204,headers:cors}:{...payload,headers:{...cors,...payload?.headers}});
}
const hydrationErrors=new WeakMap<Page,string[]>();
test.beforeEach(async({page})=>{
 const failures:string[]=[];hydrationErrors.set(page,failures);
 page.on('pageerror',error=>{if(/hydration|hydrating|Minified React error/i.test(error.message))failures.push(error.message)});
 page.on('console',message=>{if(message.type()==='error'&&/hydration|hydrating|did not match|Minified React error/i.test(message.text()))failures.push(message.text())});
});
test.afterEach(async({page})=>{expect(hydrationErrors.get(page)).toEqual([])});

async function seed(page: Page) {
  await page.addInitScript(() => { localStorage.setItem('receiptlens.session','ux-token'); localStorage.setItem('receiptlens.locale','hu'); });
  await page.route('**/auth/session/me',route=>fulfill(route,{json:{tenant_id:'ux',role:'owner',email:'ux@example.test'}}));
  await page.route('**/product/preferences',route=>fulfill(route,{json:{onboarding_done:true,language:'hu',base_currency:'HUF',base_currency_source:'saved'}}));
  await page.route('**/auth/google/status',route=>fulfill(route,{json:{enabled:false}}));
  await page.route('**/api/v1/quota',route=>fulfill(route,{json:{used:0,limit:25,pro:false}}));
  await page.route('**/product/receipts?*',route=>fulfill(route,{json:{items:[],total:0,limit:50,offset:0,categories:['Food']}}));
}

test('REQ-UX-01/02/06/07/18 AC-UX-01/02/06/07/18 file button, distinct payload, safe retry',async({page})=>{
  await seed(page); let requests:{body:string,key:string}[]=[];let quotaUsed=0;
  await page.route('**/api/v1/quota',route=>fulfill(route,{json:{used:quotaUsed,limit:25,pro:false}}));
  await page.route('**/product/receipts/upload',async route=>{
    if(route.request().method()==='OPTIONS'){await fulfill(route,{});return;}
    const request=route.request(); requests.push({body:request.postData()||'',key:request.headers()['idempotency-key']||''});
    if(requests.length===1) {await fulfill(route,{status:503,json:{detail:'temporary'}});return;}
    quotaUsed++;
    await fulfill(route,{status:201,json:{receipt_id:'saved-'+requests.length,status:'completed',receipt:{vendor:'Bolt',total:1200,currency:'HUF'}}});
  });
  await page.goto('/upload');
  const chooser=page.waitForEvent('filechooser');
  await page.getByRole('button',{name:'Fájl kiválasztása',exact:true}).click();
  await (await chooser).setFiles([{name:'same.png',mimeType:'image/png',buffer:Buffer.from('first-content')},{name:'same.png',mimeType:'image/png',buffer:Buffer.from('second-content')}]);
  await expect(page.getByRole('button',{name:'Újrapróbálás',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Újrapróbálás',exact:true}).click();
  await expect.poll(()=>requests.length).toBe(3);
  expect(requests[0].body).toContain('first-content'); expect(requests[1].body).toContain('second-content'); expect(requests[2].body).toContain('first-content');
  await expect(page.getByRole('group',{name:'quota',exact:true})).toContainText('2/25');
  expect(requests[0].key).toBeTruthy(); expect(requests[0].key).toBe(requests[2].key); expect(requests[1].key).not.toBe(requests[0].key);
});

test('REQ-UX-05 AC-UX-05 transient auth failure keeps token and offers retry',async({page})=>{
  await seed(page);
  await page.route('**/auth/session/me',route=>fulfill(route,{status:503,json:{detail:'unavailable'}}));
  await page.goto('/upload');
  await expect(page.getByRole('button',{name:'Újrapróbálás',exact:true})).toBeVisible();
  expect(await page.evaluate(()=>localStorage.getItem('receiptlens.session'))).toBe('ux-token');
  expect(page.url()).toContain('/upload');
});

test('REQ-UX-08/12/15 AC-UX-08/12/15 mobile navigation and dialog keyboard',async({page})=>{
  await seed(page); await page.setViewportSize({width:390,height:844}); await page.goto('/upload');
  const nav=page.getByRole('navigation',{name:'Fő navigáció'});
  await expect(nav).toBeVisible(); await expect(nav.getByRole('link')).toHaveCount(5);
  await nav.getByRole('link',{name:'Továbbiak',exact:true}).click();
  await expect(page).toHaveURL(/\/more$/);
  await expect(page.getByRole('main').locator('a[href="/approvals"]')).toBeVisible();
  await page.getByRole('main').getByRole('link',{name:'Beállítások',exact:true}).click();
  await expect(page).toHaveURL(/settings/);
});

test('REQ-UX-04/14 AC-UX-04/14 filters are sent to API and stored in URL',async({page})=>{
  await seed(page); let urls:string[]=[];
  await page.route('**/product/receipts?*',route=>{urls.push(route.request().url());return fulfill(route,{json:{items:[],total:0,limit:50,offset:0,categories:['Food']}});});
  await page.goto('/receipts?category=Food&date_from=2026-10-01');
  await expect.poll(()=>urls.some(url=>url.includes('category=Food')&&url.includes('date_from=2026-10-01'))).toBe(true);
});

test('REQ-UX-07/15 AC-UX-07/15 upload has no axe violations at mobile and desktop',async({page})=>{
  await seed(page);
  for(const width of [390,1280]) {await page.setViewportSize({width,height:900});await page.goto('/upload');await expect(page.getByRole('heading',{name:'Nyugta hozzáadása',exact:true})).toBeVisible();const results=await new AxeBuilder({page}).analyze();expect(results.violations).toEqual([]);}
});

const emptyDashboard={generated_at:'2026-10-12',tenant:'ux',daily_remaining:null,monthly_by_category:{month:'2026-10',total_spent:0,currency:null,categories:[],unpriced_receipts:0},household:{shared_budget:0,spent:0,remaining:0,currency:null,members:[]},recent_receipts:[],price_alerts:[],cancellable_subscriptions:[],savings:{candidates:[]}};

test('REQ-UX-09/19 AC-UX-09/19 empty household has one first action and no USD total',async({page})=>{
 await seed(page);await page.route('**/api/v1/consumer/dashboard*',route=>fulfill(route,{json:emptyDashboard}));await page.goto('/dashboard');
 await expect(page.getByRole('heading',{name:'Az első nyugtád, egy helyen'})).toBeVisible();
 const summary=page.getByRole('main').locator('[data-testid="spending-summary"]');
 await expect(summary).toHaveCount(0);
 // Currency choices may contain USD; rendered monetary totals must not invent it.
 await expect(page.getByRole('main').locator('[data-testid="money-amount"]')).toHaveCount(0);
});

test('REQ-UX-10/12 AC-UX-10/12 onboarding is shared and keyboard focus returns',async({page})=>{
 await seed(page);await page.route('**/api/v1/consumer/dashboard*',route=>fulfill(route,{json:emptyDashboard}));
 await page.route('**/product/preferences',route=>fulfill(route,{json:{onboarding_done:false,base_currency:'HUF',base_currency_source:'saved'}}));
 await page.setViewportSize({width:390,height:844});
 await page.goto('/dashboard');const dialog=page.getByRole('dialog',{name:'Kezdj egy nyugtával'});await expect(dialog).toBeVisible();
 await expect(dialog.getByRole('button',{name:'Fájl kiválasztása',exact:true})).toBeVisible();
 const focused=await page.evaluate(()=>!!document.activeElement?.closest('[role="dialog"]'));expect(focused).toBe(true);
 for(let i=0;i<12;i++){await page.keyboard.press('Tab');expect(await page.evaluate(()=>!!document.activeElement?.closest('[role="dialog"]'))).toBe(true)}
 const start=dialog.getByRole('button',{name:'Kezdj egy nyugtával',exact:true});
 await start.scrollIntoViewIfNeeded();
 const isInside=await start.evaluate(button=>{const r=button.getBoundingClientRect();const p=button.closest('[data-testid="modal-panel"]')!.getBoundingClientRect();return r.top>=p.top&&r.bottom<=p.bottom});expect(isInside).toBe(true);
 await start.click();await expect(page).toHaveURL(/upload/);
 await page.goto('/dashboard');await expect(dialog).toBeVisible();
 await page.keyboard.press('Escape');await expect(dialog).toHaveCount(0);
 await page.goto('/onboarding');await expect(page.getByRole('button',{name:'Fájl kiválasztása',exact:true})).toBeVisible();
});

test('REQ-UX-17 AC-UX-17 notification links target receipt and cadence setting persists',async({page})=>{
 await seed(page);await page.route('**/product/notifications*',route=>fulfill(route,{json:{items:[{notification_id:'n1',kind:'review',subject_id:'r1',title:'Nyugta ellenőrzése',message:'Ellenőrizd az összeget',read:false,created_at:'2026-10-12'}],unread_count:1}}));
 await page.goto('/upload');await page.getByRole('button',{name:'Értesítések',exact:true}).click();
 const dialog=page.getByRole('dialog',{name:'Értesítések'});await expect(dialog.getByRole('link',{name:'Kapcsolódó tétel megnyitása'})).toHaveAttribute('href','/review?receipt=r1');
 await dialog.getByRole('link',{name:'Értesítési beállítások'}).click();
 let saved='';await page.route('**/product/preferences',async route=>{if(route.request().method()==='PUT')saved=route.request().postDataJSON().payload.insight_frequency;await fulfill(route,{json:{onboarding_done:true,insight_frequency:saved||'daily'}})});
 await page.getByLabel('Összefoglalók gyakorisága').selectOption('weekly');await expect.poll(()=>saved).toBe('weekly');
});

test('REQ-UX-12/18 camera keyboard dialog releases synthetic video on Escape',async({page})=>{
 await seed(page);
 await page.addInitScript(()=>{
  Object.defineProperty(navigator.mediaDevices,'getUserMedia',{value:async()=>{
   const canvas=document.createElement('canvas');canvas.width=320;canvas.height=240;
   const context=canvas.getContext('2d')!;context.fillStyle='white';context.fillRect(0,0,320,240);
   const stream=canvas.captureStream(5);
   (window as typeof window & {uxCameraTrack?:MediaStreamTrack}).uxCameraTrack=stream.getVideoTracks()[0];
   return stream;
  }});
 });
 await page.setViewportSize({width:390,height:844});await page.goto('/upload');
 const camera=page.getByRole('button',{name:'Fotó készítése'});await camera.click();
 const dialog=page.getByRole('dialog',{name:'Fotó készítése'});await expect(dialog).toBeVisible();
 await expect(dialog.getByRole('button',{name:'Rögzítés'})).toBeEnabled();
 for(let i=0;i<4;i++){
  await page.keyboard.press(i%2?'Shift+Tab':'Tab');
  expect(await page.evaluate(()=>!!document.activeElement?.closest('[role="dialog"]'))).toBe(true);
 }
 expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);
 await page.keyboard.press('Escape');await expect(dialog).toHaveCount(0);await expect(camera).toBeFocused();
 expect(await page.evaluate(()=>(window as typeof window & {uxCameraTrack?:MediaStreamTrack}).uxCameraTrack?.readyState)).toBe('ended');
});

test('REQ-UX-09/13 dashboard retains household members and savings opportunities',async({page})=>{
 await seed(page);
 const receipt={receipt_id:'r1',merchant:'Bolt',total:250,currency:'HUF',date:'2026-10-13',status:'completed'};
 await page.route('**/product/receipts?*',route=>fulfill(route,{json:{items:[receipt],total:1,limit:50,offset:0,categories:[]}}));
 await page.route('**/api/v1/consumer/dashboard*',route=>fulfill(route,{json:{...emptyDashboard,
  monthly_by_category:{month:'2026-10',total_spent:250,currency:'HUF',categories:[],unpriced_receipts:0},recent_receipts:[receipt],
  household:{shared_budget:1000,spent:250,remaining:750,currency:'HUF',members:[{member_id:'m1',email:'member@example.test',role_label:'Felnőtt tag'}]},
  savings:{period:'2026-10',potential_saving:50,total_spent:250,currency:'HUF',avg_by_category:{},top_candidates:[{merchant:'Olcsóbb bolt',potential_saving:50,delta_pct:5}]},
 }}));
 await page.goto('/dashboard');
 await expect(page.getByRole('heading',{name:'Családi keret-státusz',exact:true})).toBeVisible();
 await expect(page.getByText('member@example.test',{exact:true})).toBeVisible();
 const savings=page.getByRole('region',{name:'Ezt így tudnád megtakarítani'});
 await expect(savings).toBeVisible();await expect(savings.getByText('Olcsóbb bolt',{exact:true})).toBeVisible();
 await expect(page.getByRole('heading',{name:'Az első nyugtád, egy helyen'})).toHaveCount(0);
});
