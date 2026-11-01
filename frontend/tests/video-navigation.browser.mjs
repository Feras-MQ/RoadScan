import assert from 'node:assert/strict';

export async function checkVideoNavigation(browser, origin, expect, mode, width) {
  const context = await browser.newContext({viewport: {width, height: 1000}, reducedMotion: 'reduce'});
  await context.route('**/*', route => route.request().url().startsWith(origin + '/') ? route.continue() : route.abort());
  await context.addInitScript(() => {sessionStorage.setItem('roadscan_token', 'synthetic-guide-only'); localStorage.setItem('roadscan_language', 'en');});
  const page = await context.newPage();
  const writes = [], failed = [], errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {if (request.method() !== 'GET') writes.push({method: request.method(), path: new URL(request.url()).pathname});});
  page.on('requestfailed', request => failed.push(new URL(request.url()).pathname));
  await page.route('**/api/health', route => route.fulfill({json: {status: 'ok', model: 'configured'}}));
  let releaseFrame, nextRequests = 0, stops = 0;
  await page.route('**/api/video-analysis?*', route => {
    assert.equal(route.request().method(), 'POST');
    assert.equal(new URL(route.request().url()).searchParams.get('sample'), '5');
    return route.fulfill({json: {id: 'synthetic-video', total_frames: null}});
  });
  await page.route('**/api/video-analysis/synthetic-video/next', async route => {
    nextRequests++;
    await new Promise(resolve => {releaseFrame = resolve;});
    await route.fulfill({json: {state: 'finished', processed_count: 0, complete: true}}).catch(() => {});
  });
  await page.route('**/api/video-analysis/synthetic-video', route => {stops++; return route.fulfill({status: 204});});
  try {
    await page.goto(origin);
    let idlePrompts = 0;
    const idlePrompt = async dialog => {idlePrompts++; await dialog.dismiss();};
    page.on('dialog', idlePrompt);
    await page.getByRole('navigation', {name: 'Main navigation'}).getByRole('button', {name: 'Map & results', exact: true}).click();
    await page.getByRole('link', {name: 'RoadScan overview', exact: true}).click();
    assert.equal(idlePrompts, 0, 'idle dashboard/map navigation needs no confirmation');
    page.removeListener('dialog', idlePrompt);
    await page.getByRole('navigation', {name: 'Main navigation'}).getByRole('button', {name: 'Live recognition', exact: true}).click();
    await page.getByLabel('Recognition source', {exact: true}).selectOption('thorough');
    await expect(page.locator('.full-video-heading h1')).toHaveText('Every frame. At your pace.');
    await page.getByLabel('Frames to analyze', {exact: true}).selectOption('5');
    await expect(page.locator('.full-video-heading h1')).toHaveText('Up to 5 frames per second.');
    await expect(page.locator('.full-video-panel > p').first()).toContainText('Frames between samples are not analyzed');
    await page.getByRole('button', {name: 'Switch to Arabic'}).click();
    await expect(page.getByLabel('الإطارات المحللة', {exact: true})).toHaveValue('5');
    await expect(page.locator('.full-video-heading h1')).toHaveText('حتى 5 إطارات في الثانية.');
    await expect(page.locator('.full-video-panel > p').first()).toContainText('لا تُحلل الإطارات بين العينات');
    await page.getByRole('button', {name: 'دليل الموقع', exact: true}).click();
    const arabicGuide = page.getByRole('dialog');
    await arabicGuide.getByRole('button', {name: 'تحليل فيديو', exact: true}).last().click();
    await expect(arabicGuide).toContainText('الإطارات المحللة');
    await expect(arabicGuide).toContainText('استخدام الإطار المختار للتقرير');
    await arabicGuide.getByRole('button', {name: 'إغلاق الدليل', exact: true}).click();
    await page.getByRole('button', {name: 'Switch to English'}).click();
    await page.getByLabel('Frames to analyze', {exact: true}).selectOption('0');
    await expect(page.locator('.full-video-heading h1')).toHaveText('Every frame. At your pace.');
    await page.getByLabel('Frames to analyze', {exact: true}).selectOption('5');
    await page.getByLabel('Video analysis quality', {exact: true}).selectOption('detail');
    await page.getByLabel('Thorough analysis video', {exact: true}).setInputFiles({name: 'synthetic.mp4', mimeType: 'video/mp4', buffer: Buffer.from('Synthetic UI fixture; never decoded')});
    await page.getByRole('button', {name: 'Analyze 5 frames per second', exact: true}).click();
    await expect.poll(() => nextRequests).toBe(1);
    async function leave(accept) {
      const guide = page.getByRole('dialog');
      if (mode === 'guide') {
        await page.getByRole('button', {name: 'Website guide', exact: true}).click();
        await guide.getByRole('button', {name: 'Find reports on the map', exact: true}).click();
      }
      let prompt = '';
      const answer = async dialog => {prompt = dialog.message(); await (accept ? dialog.accept() : dialog.dismiss());};
      page.once('dialog', answer);
      if (mode === 'guide') await guide.getByRole('button', {name: 'Open this screen', exact: true}).click();
      else if (mode === 'brand') await page.getByRole('link', {name: 'RoadScan overview', exact: true}).click();
      else await page.getByRole('navigation', {name: 'Main navigation'}).getByRole('button', {name: 'Map & results', exact: true}).click();
      page.removeListener('dialog', answer);
      assert.match(prompt, /stop ongoing work/);
      await expect(page.locator('[data-screen]')).toHaveAttribute('data-screen', accept ? mode === 'brand' ? 'dashboard' : 'map' : 'live');
      if (mode === 'guide' && !accept) await page.keyboard.press('Escape');
    }
    await leave(false);
    await expect(page.getByLabel('Frames to analyze', {exact: true})).toHaveValue('5');
    await expect(page.getByLabel('Video analysis quality', {exact: true})).toHaveValue('detail');
    await expect(page.getByRole('button', {name: 'Stop analysis', exact: true})).toBeEnabled();
    assert.equal(stops, 0, 'Cancel does not stop the live video job');
    let sameScreenPrompt = false;
    const sameScreen = async dialog => {sameScreenPrompt = true; await dialog.dismiss();};
    page.once('dialog', sameScreen);
    await page.getByRole('navigation', {name: 'Main navigation'}).getByRole('button', {name: 'Live recognition', exact: true}).click();
    page.removeListener('dialog', sameScreen);
    assert.equal(sameScreenPrompt, false);
    await expect(page.getByRole('button', {name: 'Stop analysis', exact: true})).toBeEnabled();
    await leave(true);
    await expect.poll(() => stops).toBeGreaterThan(0);
    await expect.poll(() => failed.filter(path => path.endsWith('/next')).length).toBe(1);
    releaseFrame();
    assert.equal(nextRequests, 1);
    assert.ok(writes.every(request => request.path.startsWith('/api/video-analysis')), 'only explicitly started synthetic video and its cleanup are requested');
    assert.deepEqual(errors, []);
    console.log(`PASS: video navigation (${mode}, ${width}px), Cancel preserves analysis/settings, Continue stops, current-screen/idle safe, EN/AR headings reflect sampling.`);
  } finally {releaseFrame?.(); await context.close();}
}
