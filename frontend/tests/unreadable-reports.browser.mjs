import assert from 'node:assert/strict';

// Real React components, isolated synthetic HTTP/storage. Parent integration tests the actual API.
export async function checkUnreadableReports(browser,origin,base,expect) {
  for(const lang of ['en','ar']) for(const width of [1440,390]) {
    const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
    await context.route('**/*',route=>route.request().url().startsWith(origin+'/')?route.continue():route.abort());
    await context.addInitScript(language=>{sessionStorage.setItem('roadscan_token','synthetic-unreadable');localStorage.setItem('roadscan_language',language)},lang);
    const tx=(en,ar)=>lang==='ar'?ar:en;
    const variants=[['unreadable',null,false],['empty',[],true],['legacy',[{class_id:'D40',box:[1,2,30,40]}],true],['badbox',[{class_id:'D40'}],true]];
    const rows=variants.map(([name,detections,detections_readable])=>({...base,id:'fixture-'+name,revision:'r0-'+name,detections,detections_readable,score:name==='empty'?null:90,latitude:24.7,longitude:46.7,location_source:'manual'}));
    let raw='{broken',revision=0;const writes=[],toolCalls=[],errors=[],audits=[];
    const models=['a','b'].map(id=>({id,name:'Synthetic '+id,sha256:id.repeat(64),family:'yolo'}));
    const page=await context.newPage();let accept=false,dialogs=0;
    page.on('dialog',async dialog=>{dialogs++;await (accept?dialog.accept():dialog.dismiss());});
    page.on('pageerror',error=>errors.push(error.message));
    await page.route('**/api/models',route=>route.fulfill({json:{items:models,available:true,can_manage:false}}));
    await page.route('**/api/reports**',async route=>{
      const request=route.request(),url=new URL(request.url());
      if(url.pathname==='/api/reports')return route.fulfill({json:{items:rows,total:rows.length}});
      const row=rows.find(r=>url.pathname===`/api/reports/${r.id}` || url.pathname.startsWith(`/api/reports/${r.id}/`));
      if(!row)return route.continue();
      if(url.pathname.endsWith('/audit'))return route.fulfill({json:{items:row.id===rows[0].id?audits:[]}});
      if(url.pathname.endsWith('/vote')) {
        toolCalls.push('vote');assert.equal(request.postDataJSON().revision,row.revision);
        return route.fulfill({json:{state:'completed',revision:row.revision,width:320,height:240,consensus:[],agreements:[],disagreements:[],models:models.map(m=>({...m,state:'completed',detections:[{class_id:'D40',box:[10,10,40,40],confidence:.7}],elapsed_ms:1})),reason:null}});
      }
      if(url.pathname.endsWith('/training')) {toolCalls.push('training:'+row.id);return route.fulfill({json:{approved:false,eligible:true,stale:false,capture_group:'',split:'train'}});}
      if(request.method()==='PATCH') {
        const body=request.postDataJSON();assert.equal(body.revision,row.revision,'save uses latest revision');writes.push({id:row.id,...body});
        if('detections' in body) {
          assert.ok(body.detections.length,'replacement cannot silently become empty');
          if(!row.detections_readable){audits.push({actor:'Synthetic reviewer',at:'2026-01-01T00:00:00Z',action:'review',details:{manual_detections:true,previous_detections_unreadable:true}});raw=JSON.stringify(body.detections);}
          row.detections=body.detections;row.detections_readable=true;row.score=12;
        }
        row.note=body.note;row.status=body.status;row.revision='saved-'+(++revision);
      }
      return route.fulfill({json:row});
    });
    const nav=screen=>page.getByRole('navigation').getByRole('button',{name:screen==='reports'?new RegExp(tx('Review queue','قائمة المراجعة')):tx('Map & results','الخريطة والنتائج'),exact:screen!=='reports'}).click();
    const save=()=>page.locator('.save-row button').click();
    const current=screen=>expect(page.locator('[data-screen]')).toHaveAttribute('data-screen',screen);
    async function open(index){await page.locator('.report-item').nth(index).click();await expect(page.locator('#report-image')).toBeVisible();}
    try {
      await page.goto(origin);await expect(page.locator('.connection-label')).toHaveText(tx('Connected','متصل'));
      await expect(page.locator('.evidence-case').first()).toContainText(tx('Annotations unreadable','التحديدات غير قابلة للقراءة'));
      await expect(page.locator('.evidence-case').first()).not.toContainText('90/100');
      await nav('map');await expect(page.locator('.evidence-inspector')).toContainText(tx('Annotations unreadable','التحديدات غير قابلة للقراءة'));
      await page.locator('.evidence-inspector button.primary').click();await current('reports');
      await expect(page.locator('#annotation-data-warning')).toContainText(tx('not a report with zero detections','لا يعني أن البلاغ بلا تحديدات'));
      await expect(page.locator('.review-trail')).not.toContainText(tx('0 current boxes','0 تحديدات حالية'));
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),'unreadable warning fits the viewport');
      if(process.env.ROADSCAN_QA_OUTPUT) await page.screenshot({path:process.env.ROADSCAN_QA_OUTPUT+'/unreadable-'+lang+'-'+width+'.png',fullPage:true});
      await expect(page.locator('.annotation-toolbar button').last()).toBeDisabled();await expect(page.locator('.empty-annotations')).toHaveCount(0);await expect(page.locator('.vote-panel,.training-approval')).toHaveCount(0);
      assert.deepEqual(toolCalls,[],'unreadable report does not call downstream tools');
      await page.locator('#inspector-note').fill('Synthetic note only');await page.locator('#review-status').selectOption('Confirmed');await save();
      await expect(page.locator('.review-statusbar')).toContainText(tx('Saved report','بلاغ محفوظ'));assert.equal(raw,'{broken');assert.equal('detections' in writes.at(-1),false);
      await nav('map');await current('map');assert.equal(dialogs,0,'saved unreadable review leaves silently');await nav('reports');
      await page.locator('#start-annotation-replacement').click();await expect(page.locator('.save-row button')).toBeDisabled();
      await page.locator('#inspector-note').fill('Note survives replacement cancellation');await page.locator('#review-status').selectOption('Assigned');
      await page.locator('#cancel-annotation-replacement').click();await expect(page.locator('#inspector-note')).toHaveValue('Note survives replacement cancellation');await expect(page.locator('#review-status')).toHaveValue('Assigned');assert.equal(raw,'{broken');
      await save();await expect(page.locator('.review-statusbar')).toContainText(tx('Saved report','بلاغ محفوظ'));assert.equal('detections' in writes.at(-1),false);
      await page.locator('#start-annotation-replacement').click();await page.locator('.annotation-toolbar button').last().click();
      await page.locator('#cancel-annotation-replacement').click();await expect(page.locator('.annotation-row')).toHaveCount(1);assert.equal(dialogs,1,'Cancel confirmation keeps draft');
      accept=true;await page.locator('#cancel-annotation-replacement').click();accept=false;await expect(page.locator('.annotation-row')).toHaveCount(0);assert.equal(raw,'{broken');
      await page.locator('#start-annotation-replacement').click();await page.getByRole('button',{name:tx('Run model vote','تشغيل تصويت النماذج'),exact:true}).click();
      await expect(page.locator('.vote-model-results button').first()).toBeEnabled();await page.locator('.vote-model-results button').first().click();await expect(page.locator('.annotation-row')).toHaveCount(1);
      await nav('map');await current('reports');assert.equal(raw,'{broken','model apply is draft only');
      await save();await expect(page.locator('#annotation-data-warning')).toHaveCount(0);assert.equal(writes.at(-1).detections[0].confidence,.7);assert.notEqual(raw,'{broken');
      await expect(page.locator('.audit-event')).toContainText(tx('unreadable annotations replaced','استبدال تحديدات غير قابلة للقراءة'));
      await nav('map');await current('map');await nav('reports');await open(1);await expect(page.locator('#annotation-data-warning')).toHaveCount(0);await expect(page.locator('.empty-annotations')).toBeVisible();
      await open(2);await expect(page.locator('.annotation-legacy-warning')).toBeVisible();const weight=page.locator('.coordinate-inputs input').last();await expect(weight).toHaveValue('');
      await weight.fill('0.7');await weight.fill('');await expect(page.locator('.review-statusbar')).toContainText(tx('Saved report','بلاغ محفوظ'));
      await page.locator('#inspector-note').fill('Legacy note preserved');await save();await expect(page.locator('.review-statusbar')).toContainText(tx('Saved report','بلاغ محفوظ'));assert.equal('detections' in writes.at(-1),false);assert.equal(rows[2].detections[0].confidence,undefined);
      await page.locator('.coordinate-inputs input').first().fill('2');await expect(page.locator('.save-row button')).toBeDisabled();await weight.fill('0.7');await save();await expect(page.locator('.annotation-legacy-warning')).toHaveCount(0);
      await open(3);await expect(page.locator('#annotation-data-warning')).toContainText(tx('Annotations not displayable','التحديدات غير قابلة للعرض'));await expect(page.locator('.annotation-row')).toHaveCount(0);
      await page.locator('#inspector-note').fill('Geometry missing');await save();await expect(page.locator('.review-statusbar')).toContainText(tx('Saved report','بلاغ محفوظ'));assert.equal('detections' in writes.at(-1),false);assert.deepEqual(rows[3].detections,[{class_id:'D40'}]);
      assert.equal(toolCalls.filter(call=>call==='training:fixture-badbox').length,0);assert.deepEqual(errors,[]);
      console.log(`PASS unreadable reports ${lang}, ${width}px: overview/list/map/detail, raw-preserving status/note saves, explicit replacement/empty guard/cancel/model apply/save/audit, legacy missing confidence, invalid geometry, dirty semantics.`);
    } finally {await context.close();}
  }
}
