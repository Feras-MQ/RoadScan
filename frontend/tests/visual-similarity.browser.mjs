import assert from 'node:assert/strict';

// Real DuplicateSearch component; the search endpoint is a synthetic fixture (backend behaviour is covered by pytest).
export async function checkVisualSimilarity(browser,origin,base,expect) {
  for(const lang of ['en','ar']) for(const width of [1440,390]) {
    const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
    await context.route('**/*',route=>route.request().url().startsWith(origin+'/')?route.continue():route.abort());
    await context.addInitScript(language=>{sessionStorage.setItem('roadscan_token','synthetic-visual');localStorage.setItem('roadscan_language',language)},lang);
    const tx=(en,ar)=>lang==='ar'?ar:en;
    const box=[{class_id:'D40',box:[10,10,60,60],confidence:.8}];
    const rows=[{...base,id:'fixture-no-coordinates',revision:'r-no-gps',detections:box,detections_readable:true,latitude:null,longitude:null,location_source:'not_provided'},
                {...base,id:'fixture-recorded',revision:'r-gps',detections:box,detections_readable:true,latitude:24.7,longitude:46.7,location_source:'manual'}];
    const searches=[],errors=[];let fail=false,partial=false;
    const page=await context.newPage();
    page.on('pageerror',error=>errors.push(error.message));
    await page.route(url=>url.pathname==='/api/reports'||url.pathname.startsWith('/api/reports/'),async route=>{
      const request=route.request(),url=new URL(request.url());
      if(url.pathname==='/api/reports')return route.fulfill({json:{items:rows,total:rows.length}});
      const row=rows.find(r=>url.pathname===`/api/reports/${r.id}`||url.pathname.startsWith(`/api/reports/${r.id}/`));
      if(!row)return route.continue();
      if(url.pathname.endsWith('/duplicates/search')) {
        const body=request.postDataJSON();searches.push({id:row.id,...body});
        if(fail)return route.fulfill({status:503,json:{detail:'Duplicate search unavailable or busy; check the configured DINOv2 runtime and try again'}});
        const complete={skipped_reports:0,new_crop_budget:16,partial_search:false,partial_reasons:[],threshold:.8};
        if(partial)return route.fulfill({json:{...complete,mode:'visual',eligible_reports:14,examined_reports:9,skipped_reports:1,new_crops_used:16,partial_search:true,partial_reasons:['new_crop_budget'],matches:[]}});
        return route.fulfill({json:body.mode==='visual'?{...complete,mode:'visual',eligible_reports:2,examined_reports:2,new_crops_used:3,matches:[{report_id:'fixture-similar-elsewhere',similarity:.931,distance_m:null}]}
                                                       :{...complete,mode:'nearby',eligible_reports:1,examined_reports:1,new_crops_used:0,matches:[{report_id:'fixture-similar-nearby',similarity:.854,distance_m:12.3}]}});
      }
      if(url.pathname.endsWith('/audit'))return route.fulfill({json:{items:[]}});
      if(url.pathname.endsWith('/training'))return route.fulfill({json:{approved:false,eligible:true,stale:false,capture_group:'',split:'train'}});
      return route.fulfill({json:row});
    });
    const section=page.getByRole('region',{name:tx('Similar damage search','البحث عن أضرار مشابهة')});
    const visual=section.getByRole('button',{name:tx('Find visually similar damage (any location)','البحث عن أضرار مشابهة بصريًا (أي موقع)')});
    const nearby=section.getByRole('button',{name:tx('Find nearby matches (50 m)','البحث عن تطابقات قريبة (50 م)')});
    try {
      await page.goto(origin);await expect(page.locator('.connection-label')).toHaveText(tx('Connected','متصل'));
      await page.getByRole('navigation').getByRole('button',{name:new RegExp(tx('Review queue','قائمة المراجعة'))}).click();
      await page.locator('.report-item').nth(0).click();
      await expect(visual).toBeEnabled();await expect(nearby).toBeDisabled();
      await expect(section).toContainText(tx('only the visual search is available. No location is assumed.','يتاح البحث البصري فقط. لا يُفترض أي موقع.'));
      await visual.click();
      const status=section.getByRole('status');
      await expect(status).toContainText(tx('open reports compared by appearance only','بلاغات مفتوحة قورنت حسب المظهر فقط'));
      await expect(status).toContainText(tx('not whole photos. Similar-looking damage does not confirm the same physical damage','لا الصور كاملة. تشابه مظهر الضرر لا يؤكد أنه الضرر نفسه'));
      await expect(status).toContainText('93.1%');await expect(status).not.toContainText(/\d m\b/);
      await expect(status).toContainText('2/2');await expect(status).toContainText('3/16');await expect(status.locator('.warning')).toHaveCount(0);
      await expect(section).toContainText(tx('Experimental similarity threshold 0.80','حد التشابه التجريبي 0.80'));
      assert.deepEqual(searches.at(-1),{id:'fixture-no-coordinates',revision:'r-no-gps',mode:'visual'});

      await page.locator('.report-item').nth(1).click();
      await expect(nearby).toBeEnabled();await nearby.click();
      await expect(status).toContainText(tx('nearby open reports checked','بلاغات مفتوحة قريبة تم فحصها'));
      await expect(status).toContainText('12.3 m');await expect(status).not.toContainText(tx('not whole photos','لا الصور كاملة'));
      assert.deepEqual(searches.at(-1),{id:'fixture-recorded',revision:'r-gps',mode:'nearby'});

      partial=true;await page.locator('.report-item').nth(0).click();await visual.click();
      await expect(status.locator('.warning')).toContainText(tx('Limited search: no match does not rule out similar reports.','بحث محدود: عدم وجود تطابق لا يستبعد وجود بلاغات مشابهة.'));
      await expect(status.locator('.warning')).toContainText(tx('new-crop limit reached','بلغ حد مناطق الضرر الجديدة'));
      await expect(status).toContainText('9/14');await expect(status).toContainText('16/16');
      await expect(status).toContainText(tx('No matches among the reports examined so far.','لا توجد تطابقات بين البلاغات التي فُحصت حتى الآن.'));
      await expect(status).not.toContainText(tx('This does not prove that no duplicate exists.','هذا لا يثبت عدم وجود تكرار.'));
      partial=false;fail=true;await visual.click();
      await expect(section.getByRole('alert')).toContainText('DINOv2 runtime');await expect(status).toHaveCount(0);
      await expect(visual).toBeEnabled();
      assert.equal(searches.length,4);assert.deepEqual(errors,[]);
      console.log(`PASS visual similarity ${lang}, ${width}px: no-coordinate visual search, nearby search with distance, completeness counts, limited-search warning, honest unavailable error.`);
    } finally {await context.close();}
  }
}
