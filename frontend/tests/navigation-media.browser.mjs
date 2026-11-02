import assert from 'node:assert/strict';
import {guideTopics} from '../src/guideContent.ts';

// All camera pixels and API responses are synthetic; no device permission is requested.
export async function checkNavigationMedia(browser, origin, expect) {
  for (const lang of ['en', 'ar']) for (const width of [1440, 390]) {
    const context = await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
    const tx = (en, ar) => lang === 'ar' ? ar : en;
    await context.route('**/*', route => route.request().url().startsWith(origin + '/') ? route.continue() : route.abort());
    await context.addInitScript(language => {
      sessionStorage.setItem('roadscan_token','synthetic-media-only'); localStorage.setItem('roadscan_language',language);
      window.fixtureTracks = []; window.deferCamera = false;
      Object.defineProperty(navigator.mediaDevices,'getUserMedia',{value:async () => {
        const canvas = document.createElement('canvas'); canvas.width=320; canvas.height=240;
        canvas.getContext('2d').fillRect(0,0,320,240);
        const stream=canvas.captureStream(10); window.fixtureTracks.push(...stream.getTracks());
        if(window.deferCamera) await new Promise(resolve => window.resolveCamera=resolve);
        return stream;
      }});
      Object.defineProperty(navigator.mediaDevices,'enumerateDevices',{value:async () => []});
    },lang);
    const page=await context.newPage(), prompts=[], errors=[]; let accept=false, frameRequests=0;
    page.on('dialog',async dialog=>{prompts.push(dialog.message());await (accept?dialog.accept():dialog.dismiss());});
    page.on('pageerror',error=>errors.push(error.message));
    const recognition={state:'completed',reason:null,detections:[],model_version:'synthetic',width:320,height:240,elapsed_ms:1,confidence_threshold:0.25,persisted:false};
    await page.route('**/api/health',route=>route.fulfill({json:{status:'ok',model:'configured'}}));
    await page.route('**/api/recognize?*',route=>route.fulfill({json:recognition}));
    await page.route('**/api/video-analysis?*',route=>route.fulfill({json:{id:'synthetic-completed',total_frames:1}}));
    await page.route('**/api/video-analysis/synthetic-completed/next',route=>route.fulfill({json:frameRequests++ ? {state:'finished',processed_count:1,complete:true} : {...recognition,jpeg_base64:'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5V8AAAAASUVORK5CYII=',frame_index:0,timestamp_ms:0,processed_count:1,total_frames:1}}));
    await page.route('**/api/video-analysis/synthetic-completed',route=>route.fulfill({status:204}));
    const nav=screen=>page.getByRole('navigation').getByRole('button',{name:tx(...{dashboard:['Overview','نظرة عامة'],live:['Live recognition','التعرف المباشر'],map:['Map & results','الخريطة والنتائج']}[screen]),exact:true}).click();
    const screen=value=>expect(page.locator('[data-screen]')).toHaveAttribute('data-screen',value);
    const ended=()=>expect.poll(()=>page.evaluate(()=>window.fixtureTracks.every(track=>track.readyState==='ended'))).toBe(true);
    async function guideLeave(){
      await page.locator('.website-guide-launcher').click();
      await page.getByRole('dialog').getByRole('button',{name:guideTopics.find(t=>t.id==='map').title[lang==='ar'?1:0],exact:true}).last().click();
      await page.getByRole('button',{name:tx('Open this screen','افتح هذه الشاشة'),exact:true}).click();
    }
    try {
      await page.goto(origin);await expect(page.locator('.connection-label')).toHaveText(tx('Connected','متصل'));
      await page.getByRole('button',{name:tx('Photo only','صورة فقط'),exact:true}).click();
      await expect(page.locator('.camera-view video')).toBeVisible();
      await nav('map');await screen('map');await ended();assert.equal(prompts.length,0,'photo-only preview leaves silently and releases its camera');
      await nav('dashboard');await page.evaluate(()=>window.deferCamera=true);
      await page.getByRole('button',{name:tx('Photo only','صورة فقط'),exact:true}).click();
      await expect.poll(()=>page.evaluate(()=>Boolean(window.resolveCamera))).toBe(true);
      await nav('map');await page.evaluate(()=>window.resolveCamera());await ended();assert.equal(prompts.length,0,'late camera acquisition is released after navigation');
      await page.evaluate(()=>window.deferCamera=false);
      await nav('live');await page.getByRole('button',{name:tx('Start live recognition','بدء التعرف المباشر'),exact:true}).click();
      await expect(page.locator('.live-result img')).toBeVisible();
      await page.getByRole('button',{name:tx('Stop recognition','إيقاف التعرف'),exact:true}).click();await ended();
      await nav('map');await screen('live');assert.equal(prompts.length,1,'stopped live results remain unsaved');await expect(page.locator('.live-result img')).toBeVisible();
      accept=true;await nav('map');await screen('map');assert.equal(prompts.length,2);accept=false;
      await nav('live');await page.getByLabel(tx('Recognition source','مصدر التعرف'),{exact:true}).selectOption('thorough');
      await page.locator('.full-video-panel input[type=file]').setInputFiles({name:'synthetic.mp4',mimeType:'video/mp4',buffer:Buffer.from('fixture only')});
      await page.locator('.full-video-panel .live-actions button').first().click();
      await expect(page.locator('.full-video-panel .live-actions button').first()).toBeEnabled();await expect(page.locator('.live-result img')).toBeVisible();
      await guideLeave();await screen('live');assert.equal(prompts.length,3,'completed unsaved video results retain guide protection');await page.keyboard.press('Escape');
      await expect(page.locator('.live-result img')).toBeVisible();accept=true;await nav('map');await screen('map');assert.equal(prompts.length,4);
      assert.deepEqual(errors,[]);
      console.log(`PASS media navigation ${lang}, ${width}px: silent photo preview, active/late camera cleanup, stopped live and completed video result Cancel/Continue, guide and sidebar.`);
    } finally {await context.close();}
  }
}
