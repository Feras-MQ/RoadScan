import assert from 'node:assert/strict';
import path from 'node:path';

// Actual React + Leaflet UI, synthetic API records and intercepted synthetic tiles only.
export async function checkStreetMap(browser,origin,baseReport,expect,artifacts) {
 for(const lang of ['en','ar'])for(const width of [1440,390]) {
  const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
  await context.addInitScript(language=>{sessionStorage.setItem('roadscan_token','street-map-synthetic-only');localStorage.setItem('roadscan_language',language);},lang);
  const tx=(en,ar)=>lang==='ar'?ar:en;
  const compact=(id,source='manual',classes=['D40'],latitude=24.7,longitude=46.7)=>({id,latitude,longitude,location_source:source,classes,score:null,status:'Confirmed',created_at:null});
  const saved=[compact('pin-one'),compact('pin-overlap','device_gps',[]),compact('pin-outside-page','manual',['D00'],24.71,46.71),compact('polar','manual',[],90,0),compact('simulation','simulated'),{...compact('missing'),latitude:null,longitude:null,location_source:'not_provided'}];
  const full=pin=>({...baseReport,...pin,detections:pin.classes.map(class_id=>({class_id,box:[1,1,30,30],confidence:.7})),image_url:'/api/fixture-image.svg'});
  let mode='normal',tileFailure=false,releasePins=null;
  const tiles=[],pinRequests=[],external=[],writes=[],errors=[];
  await context.route('**/*',async route=>{
   const req=route.request(),url=new URL(req.url());
   if(url.hostname==='tile.openstreetmap.org'){
    tiles.push({url:url.href,headers:req.headers()});
    if(tileFailure){await route.abort();return;}
    await route.fulfill({contentType:'image/svg+xml',headers:{'Cache-Control':'public, max-age=604800'},body:'<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" fill="#dee5dd"/><path d="M0 128H256M128 0V256" stroke="#fff" stroke-width="12"/><text x="10" y="30">SYNTHETIC TILE</text></svg>'});return;
   }
   if(url.origin!==origin){external.push(url.href);await route.abort();return;}
   if(!url.pathname.startsWith('/api/')){await route.continue();return;}
   if(/^\/api\/reports\/[^/]+\/image$/.test(url.pathname)){await route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240"><rect width="320" height="240" fill="#76878d"/><text x="20" y="80">SYNTHETIC REPORT</text></svg>'});return;}
   if(req.method()!=='GET'){writes.push(url.pathname);await route.fulfill({status:405,json:{detail:'No writes in street map tests'}});return;}
   if(url.pathname==='/api/reports/map'){
    pinRequests.push(url.searchParams.toString());
    if(mode==='delay')await new Promise(resolve=>{releasePins=resolve;});
    if(mode==='unavailable'){await route.fulfill({status:404,json:{detail:'Old backend'}});return;}
    const group=url.searchParams.get('location'),damage=url.searchParams.get('damage');
    assert.ok(['recorded','simulated'].includes(group));assert.equal(url.searchParams.get('limit'),'2000');
    const candidates=mode==='cap'?Array.from({length:2001},(_,i)=>compact('cap-'+i,'manual',['D40'],24.7+(i%30)*.0001,46.7+Math.floor(i/30)*.0001)):tileFailure?saved.map(p=>p.latitude!==null&&Math.abs(p.latitude)<85?{...p,latitude:p.latitude+2,longitude:p.longitude+2}:p):saved;
    const all=candidates.filter(p=>(group==='simulated'?p.location_source==='simulated':['manual','device_gps'].includes(p.location_source))&&p.latitude!==null&&(!damage||(damage==='none'?!p.classes.length:p.classes.includes(damage)))&&(!url.searchParams.get('status')||p.status===url.searchParams.get('status')));
    const data={items:all.slice(0,2000),total:all.length,returned:Math.min(all.length,2000),limit:2000,truncated:all.length>2000};
    if(mode==='invalid')data.items[0]={...data.items[0],location_source:'simulated'};
    await route.fulfill({json:data}).catch(()=>{});return;
   }
   if(url.pathname==='/api/reports'){
    let rows=saved;
    const group=url.searchParams.get('location');
    if(group)rows=rows.filter(p=>group==='none'?p.latitude===null:group==='simulated'?p.location_source==='simulated':['manual','device_gps'].includes(p.location_source));
    if(url.searchParams.get('search'))rows=rows.filter(p=>p.id.includes(url.searchParams.get('search')));
    if(url.searchParams.get('status'))rows=rows.filter(p=>p.status===url.searchParams.get('status'));
    // Make an off-page compact pin prove that the street layer does not depend on page rows.
    await route.fulfill({json:{items:rows.filter(p=>p.id!=='pin-outside-page').map(full),total:rows.length}});return;
   }
   if(url.pathname==='/api/stats'){await route.fulfill({json:{total:6,needs_review:0,high_priority:0,by_status:{Confirmed:6},by_location:{recorded:4,simulated:1,none:1}}});return;}
   const pin=saved.find(p=>url.pathname==='/api/reports/'+p.id);
   if(pin){await route.fulfill({json:full(pin)});return;}
   await route.continue();
  });
  const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
  const panel=page.locator('.street-map-panel');
  const load=()=>panel.getByRole('button',{name:tx('Load street map','تحميل خريطة الشوارع'),exact:true}).click();
  const off=()=>panel.getByRole('button',{name:tx('Turn street map off','إيقاف خريطة الشوارع'),exact:true}).click();
  const group=name=>page.locator('.evidence-switch').getByRole('button',{name:new RegExp(name)}).click();
  try{
   await page.goto(origin);await expect(page.locator('.connection-label')).toHaveText(tx('Connected','متصل'));
   await page.getByRole('navigation').getByRole('button',{name:tx('Map & results','الخريطة والنتائج'),exact:true}).click();
   await expect(panel).toBeVisible();assert.equal(tiles.length,0);assert.equal(pinRequests.length,0);
   await expect(page.locator('.coordinate-map')).toBeVisible();
   await expect(page.locator('.evidence-inspector a[href*="map_action=pano"]')).toHaveCount(1);
   await load();await expect(panel.locator('.leaflet-tile-loaded').first()).toBeVisible();
   await expect(page.locator('.evidence-inspector')).toBeHidden();
   await expect(panel.locator('.leaflet-marker-icon')).toHaveCount(3);
   await expect(panel.locator('.street-map-count')).toContainText('4');
   await expect(panel).toContainText(tx('outside the street map’s latitude range','خارج نطاق خطوط العرض'));
   await expect(panel.locator('.leaflet-control-attribution')).toBeVisible();
   await expect(panel.locator('.leaflet-control-attribution')).toContainText('OpenStreetMap contributors');
   for(const tile of tiles){assert.equal(tile.headers['x-api-key'],undefined);assert.equal(tile.headers.referer,origin+'/');assert.equal(new URL(tile.url).search,'');}
   await panel.locator('.leaflet-marker-icon').first().focus();await page.keyboard.press('Enter');
   await expect(panel.locator('#street-selected-title')).toBeFocused();
   await panel.locator('.street-map-selector select').selectOption('pin-overlap');
   await expect(panel.locator('.street-map-selection')).toContainText(tx('No detections','بلا اكتشافات'));
   await expect(panel.locator('a[href*="map_action=pano"]')).toHaveAttribute('href','https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=24.7%2C46.7');
   await panel.locator('.street-map-selector select').selectOption('pin-outside-page');
   await expect(panel.locator('.street-map-selection')).toContainText('pin-outside-page');
   await page.screenshot({path:path.join(artifacts,`street-map-${lang}-${width}.png`)});
   assert.ok(await panel.evaluate(el=>el.scrollWidth<=el.clientWidth+1),'mobile controls fit');
   await page.locator('.map-records button').nth(1).click();
   await expect(panel.locator('.leaflet-container')).toHaveCount(0);
   await expect(page.locator('.evidence-inspector')).toBeVisible();
   await expect(page.locator('.evidence-inspector h2')).toBeFocused();
   await load();await panel.locator('.street-map-selector select').selectOption('pin-outside-page');
   await panel.getByRole('button',{name:tx('Open report','فتح البلاغ'),exact:true}).click();
   await expect(page.locator('[data-screen]')).toHaveAttribute('data-screen','reports');
   await expect(page.locator('.panel.detail')).toContainText('PIN-OUTS');
   // Existing main guard: accept its report-leave warning. Guard refinement is a separate branch.
   const acceptReportLeave=dialog=>dialog.accept();page.on('dialog',acceptReportLeave);
   await page.getByRole('navigation').getByRole('button',{name:tx('Map & results','الخريطة والنتائج'),exact:true}).click();
   page.off('dialog',acceptReportLeave);
   await expect(panel.getByRole('button',{name:tx('Load street map','تحميل خريطة الشوارع'),exact:true})).toBeVisible();
   await load();await expect(panel.locator('.leaflet-marker-icon')).toHaveCount(3);
   await panel.locator('.street-map-filter select').selectOption('none');await expect(panel.locator('.leaflet-marker-icon')).toHaveCount(1);
   assert.ok(pinRequests.some(p=>p.includes('damage=none')));
   await panel.locator('.street-map-filter select').selectOption('D20');await expect(panel.locator('.leaflet-marker-icon')).toHaveCount(0);
   await expect(panel).toContainText(tx('No matching pins','لا توجد نقاط مطابقة'));
   await group(tx('Simulated locations','مواقع محاكاة'));await load();
   await expect(panel.locator('.street-pin-simulated')).toHaveCount(1);
   await panel.locator('.street-map-selector select').selectOption('simulation');
   await expect(panel.locator('.street-map-external')).toHaveCount(0);
   await group(tx('No usable location','بلا موقع صالح'));await expect(panel.locator('button')).toHaveCount(0);
   await group(tx('Recorded locations','مواقع مسجلة'));
   await page.locator('.map-filters input').fill('pin-one');await page.locator('.map-filters').getByRole('button',{name:tx('Search','بحث'),exact:true}).click();
   await expect(panel.getByRole('button',{name:tx('Load street map','تحميل خريطة الشوارع'),exact:true})).toBeDisabled();
   await expect(page.locator('.map-records button')).toHaveCount(1);
   await page.locator('.map-filters').getByRole('button',{name:tx('Clear filters','مسح عوامل التصفية'),exact:true}).click();
   const beforeFailure=tiles.length;tileFailure=true;await load();await expect(panel.locator('.street-map-fallback-note')).toBeVisible();assert.ok(tiles.length>beforeFailure,'failure uses uncached synthetic tile coordinates');
   await expect(page.locator('.coordinate-map')).toBeVisible();await expect(panel.locator('.leaflet-container')).toHaveCount(0);
   tileFailure=false;await panel.getByRole('button',{name:tx('Try street map again','إعادة محاولة تحميل خريطة الشوارع'),exact:true}).click();
   await expect(panel.locator('.leaflet-tile-loaded').first()).toBeVisible();await off();
   await expect(panel.locator('.leaflet-container')).toHaveCount(0);
   for(const failure of ['invalid','unavailable']){mode=failure;await load();await expect(panel.locator('.street-map-fallback-note')).toBeVisible();await off();}
   mode='delay';await load();await expect.poll(()=>Boolean(releasePins)).toBe(true);await off();releasePins();
   await expect(panel.locator('.leaflet-container')).toHaveCount(0);
   if(lang==='en'&&width===1440){mode='cap';await load();await expect(panel.locator('.leaflet-marker-icon')).toHaveCount(2000);await expect(panel.locator('.street-map-count')).toContainText('2001');await expect(panel.locator('.street-map-count')).toContainText('not a complete map');await off();}
   assert.deepEqual(external,[]);assert.deepEqual(writes,[]);assert.deepEqual(errors,[]);
   console.log(JSON.stringify({streetMap:'PASS',lang,width,tileRequestsIntercepted:tiles.length,pinRequests:pinRequests.length,realExternalRequests:0}));
  }finally{await context.close();}
 }
}
