import assert from 'node:assert/strict';
import {guideTopics} from '../src/guideContent.ts';

export async function checkPreciseNavigation(browser,origin,base,expect) {
  for(const lang of ['en','ar'])for(const width of [1440,390]) {
    const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
    const tx=(en,ar)=>lang==='ar'?ar:en;
    await context.addInitScript(language=>{sessionStorage.setItem('roadscan_token','synthetic-navigation-only');localStorage.setItem('roadscan_language',language)},lang);
    await context.route('**/*',route=>route.request().url().startsWith(origin+'/')?route.continue():route.abort());
    const page=await context.newPage(),prompts=[],failures=[],errors=[];let answer='dismiss',releaseExport,releaseImport,releaseApproval;
    page.on('dialog',async dialog=>{prompts.push(dialog.message());await dialog[answer]();});
    page.on('requestfailed',r=>failures.push(new URL(r.url()).pathname));page.on('pageerror',e=>errors.push(e.message));
    let report={...base,status:'Confirmed'},training={approved:false,stale:false,eligible:true,split:'train',capture_group:'saved-group',approved_at:null};
    const models=['a','b','c'].map(id=>({id,name:'Synthetic '+id,sha256:id.repeat(64),family:'yolo',imgsz:640,bytes:1,classes:{0:'D40'},reported_metrics:{}}));
    await page.route('**/api/models',route=>route.fulfill({json:{items:models,available:true,can_manage:true,active_id:'a'}}));
    await page.route(`**/api/reports/${base.id}`,async route=>{
      if(route.request().method()==='PATCH'){const body=route.request().postDataJSON();report={...report,note:body.note??report.note,revision:'saved-revision'};}
      await route.fulfill({json:report});
    });
    await page.route(`**/api/reports/${base.id}/training`,async route=>{
      if(route.request().method()==='PUT') {await new Promise(resolve=>releaseApproval=resolve);training={...training,approved:true};}
      await route.fulfill({json:training}).catch(()=>{});
    });
    await page.route('**/api/training/export',async route=>{await new Promise(resolve=>releaseExport=resolve);await route.fulfill({contentType:'application/zip',body:'synthetic export'}).catch(()=>{});});
    await page.route('**/api/models/import?*',async route=>{await new Promise(resolve=>releaseImport=resolve);await route.fulfill({json:{imported:[],duplicates:[],rejected:[]}}).catch(()=>{});});
    const nav=screen=>page.getByRole('navigation').getByRole('button',{name:screen==='reports'?new RegExp(tx('Review queue','قائمة المراجعة')):tx(...{dashboard:['Overview','نظرة عامة'],live:['Live recognition','التعرف المباشر'],map:['Map & results','الخريطة والنتائج'],learning:['Learning','التعلّم'],settings:['Settings','الإعدادات']}[screen]),exact:screen!=='reports'}).click();
    const screen=value=>expect(page.locator('[data-screen]')).toHaveAttribute('data-screen',value);
    async function openReport(){await nav('reports');await page.locator('.report-item').first().click();await expect(page.locator('.training-approval input[type="text"],.training-approval input:not([type])').first()).toHaveValue('saved-group');}
    async function helpToMap(){await page.locator('.website-guide-launcher').click();await page.getByRole('dialog').getByRole('button',{name:guideTopics.find(t=>t.id==='map').title[lang==='ar'?1:0],exact:true}).last().click();await page.getByRole('button',{name:tx('Open this screen','افتح هذه الشاشة'),exact:true}).click();}
    try{
      await page.goto(origin);await expect(page.locator('.connection-label')).toHaveText(tx('Connected','متصل'));
      for(const destination of ['reports','live','learning','settings','map','dashboard']){await nav(destination);await screen(destination);}
      assert.equal(prompts.length,0,'all untouched screens navigate silently');
      await openReport();await nav('map');await screen('map');assert.equal(prompts.length,0,'initial model choices and saved training metadata are clean');
      await openReport();await page.locator('.annotation-toolbar button').last().click();await page.locator('.annotation-row .icon-button').first().click();await nav('map');await screen('map');assert.equal(prompts.length,0,'reverted annotation edits do not count as unsaved work');
      await nav('settings');await helpToMap();await screen('map');assert.equal(prompts.length,0,'guide does not duplicate or invent warnings');

      await openReport();const note=page.locator('#inspector-note');await note.fill('Synthetic review edit');
      await nav('map');await screen('reports');await expect(note).toHaveValue('Synthetic review edit');
      await helpToMap();await screen('reports');await expect(page.getByRole('dialog').getByRole('alert')).toContainText(tx('unsaved review changes','تغييرات مراجعة غير محفوظة'));
      await page.keyboard.press('Escape');assert.equal(prompts.length,0,'review guard blocks inline without a second confirm');
      await page.getByRole('button',{name:tx('Save review','حفظ المراجعة'),exact:true}).click();await expect(page.locator('.review-statusbar')).toContainText(tx('Saved report','بلاغ محفوظ'));
      // The app stays busy through its post-save refresh and refuses navigation until idle.
      await expect(page.locator('.save-row button')).toHaveText(tx('Save review','حفظ المراجعة'));await expect(page.locator('.save-row button')).toBeEnabled();
      await nav('map');await screen('map');assert.equal(prompts.length,0,'saved edits no longer warn');

      await openReport();const group=page.getByLabel(tx('Training capture group','مجموعة تصوير التدريب'),{exact:true});
      await group.fill('draft-group');await helpToMap();await screen('reports');assert.equal(prompts.length,1);await page.keyboard.press('Escape');await expect(group).toHaveValue('draft-group');
      await group.fill('saved-group');await nav('map');await screen('map');assert.equal(prompts.length,1,'reverted training draft is clean');
      await openReport();await page.locator('.vote-picker summary').click();await page.locator('.vote-picker input').nth(2).uncheck();await nav('map');await screen('reports');assert.equal(prompts.length,2);await page.locator('.vote-picker input').nth(2).check();await nav('map');await screen('map');assert.equal(prompts.length,2,'reverted vote choice is clean');

      await openReport();await page.locator('.training-approval .check-line input').first().check();await page.locator('.training-approval .check-line input').nth(1).check();await page.getByRole('button',{name:tx('Approve this example','اعتماد هذا المثال'),exact:true}).click();await expect.poll(()=>Boolean(releaseApproval)).toBe(true);
      await nav('map');await screen('reports');await page.locator('.report-item').nth(1).click();await expect(page.locator('.report-item').first()).toHaveAttribute('aria-current','true');assert.equal(prompts.length,2,'in-flight persisted writes block navigation and report replacement rather than pretending cancellation is safe');releaseApproval();releaseApproval=null;
      await expect(page.locator('.training-approved')).toBeVisible();await nav('map');await screen('map');assert.equal(prompts.length,2,'saved training approval no longer warns');

      await nav('learning');await page.getByRole('button',{name:tx('Export approved dataset','تصدير البيانات المعتمدة'),exact:true}).click();await expect.poll(()=>Boolean(releaseExport)).toBe(true);
      await nav('map');await screen('learning');assert.equal(prompts.length,3);assert.equal(failures.filter(p=>p.endsWith('/export')).length,0,'Cancel keeps export alive');
      answer='accept';await nav('map');await screen('map');assert.equal(prompts.length,4);await expect.poll(()=>failures.filter(p=>p.endsWith('/export')).length).toBe(1);releaseExport();releaseExport=null;answer='dismiss';
      await nav('settings');await expect(page.getByRole('button',{name:tx('Browse models','اختيار النماذج'),exact:true})).toBeEnabled();await page.getByLabel(tx('Model file','ملف النموذج'),{exact:true}).setInputFiles({name:'synthetic.pt',mimeType:'application/octet-stream',buffer:Buffer.from('fixture only')});await expect.poll(()=>Boolean(releaseImport)).toBe(true);
      await nav('map');await screen('settings');assert.equal(prompts.length,4,'model import must finish before leaving');releaseImport();releaseImport=null;await expect(page.getByRole('button',{name:tx('Browse models','اختيار النماذج'),exact:true})).toBeEnabled();await nav('map');await screen('map');assert.equal(prompts.length,4);
      await nav('reports');await page.locator('.report-item').first().click();await page.locator('.vote-picker summary').click();await expect(page.locator('.vote-picker input')).toHaveCount(3);await page.locator('.vote-picker input').nth(2).uncheck();
      await page.locator('.report-item').nth(1).click();await expect(page.locator('.report-item').first()).toHaveAttribute('aria-current','true');assert.equal(prompts.length,5,'report replacement also protects child choices');await expect(page.locator('.vote-picker input').nth(2)).not.toBeChecked();
      await page.locator('#inspector-note').fill('Unsaved review and model choices');await page.locator('.report-item').nth(1).click();await expect(page.locator('.unsaved-review-alert')).toContainText(tx('unfinished report-tool work','عمل أدوات البلاغ غير المكتمل'));assert.equal(prompts.length,5,'one parent discard decision covers review and child drafts');
      await page.locator('.unsaved-review-alert button').first().click();await expect(page.locator('#inspector-note')).toHaveValue('Unsaved review and model choices');await expect(page.locator('.vote-picker input').nth(2)).not.toBeChecked();
      await page.locator('.report-item').nth(1).click();await page.locator('.unsaved-review-alert button').last().click();await expect(page.locator('.report-item').nth(1)).toHaveAttribute('aria-current','true');assert.equal(prompts.length,5,'confirmed combined discard does not add a second child prompt');
      await nav('live');await page.getByLabel(tx('Recognition source','مصدر التعرف'),{exact:true}).selectOption('video');await page.getByLabel(tx('Choose recognition video','اختيار فيديو التعرف'),{exact:true}).setInputFiles({name:'synthetic.mov',mimeType:'video/quicktime',buffer:Buffer.from('synthetic selected video; no analysis')});
      await page.getByLabel(tx('Recognition source','مصدر التعرف'),{exact:true}).selectOption('thorough');await nav('map');await screen('map');assert.equal(prompts.length,5,'a reusable file behind another source mode is not unfinished work');
      await nav('live');await page.getByLabel(tx('Recognition source','مصدر التعرف'),{exact:true}).selectOption('thorough');await page.getByLabel(tx('Thorough analysis video','فيديو التحليل الكامل'),{exact:true}).setInputFiles({name:'synthetic.mp4',mimeType:'video/mp4',buffer:Buffer.from('selected file only')});await nav('map');await screen('map');assert.equal(prompts.length,5,'a selected thorough-analysis file without results navigates silently');
      assert.deepEqual(errors,[]);console.log(`PASS precise navigation ${lang}, ${width}px: clean, saved/reverted, child drafts, Cancel, export interruption, pending training/model writes, help, report replacement and single combined discard.`);
    }finally{releaseApproval?.();releaseImport?.();releaseExport?.();await context.close();}
  }
}
