import assert from 'node:assert/strict';
import path from 'node:path';

// Real map/guide components with synthetic in-memory reports. No backend or external map is used.
export async function checkMapWorkspace(browser, origin, baseReport, expect, artifacts) {
  const baseRecords = [
    {...baseReport, id:'manual-0001', status:'Confirmed', latitude:24.7, longitude:46.7, location_source:'manual'},
    {...baseReport, id:'gps-000002', latitude:24.8, longitude:46.8, location_source:'device_gps'},
    {...baseReport, id:'overlap-03', latitude:24.7, longitude:46.7, location_source:'manual'},
    {...baseReport, id:'missing-04', location_source:'not_provided'},
    {...baseReport, id:'unknown-05', latitude:24.7, longitude:46.7, location_source:'unknown'},
    {...baseReport, id:'invalid-06', latitude:200, longitude:46.7, location_source:'manual'},
    ...Array.from({length:14}, (_, i) => ({...baseReport, id:`simulated-${i}`, latitude:24.6 + i * .01, longitude:46.6, location_source:'simulated'})),
    {...baseReport, id:'page-two-1', latitude:0, longitude:0, location_source:'manual'},
    {...baseReport, id:'page-two-2', latitude:1, longitude:1, location_source:'manual'},
  ];
  for (const mode of ['legacy', 'server']) for (const lang of ['en', 'ar']) for (const width of [1440, 390, 320]) {
    const records = mode === 'server' ? [...baseRecords, ...Array.from({length:18}, (_, i) => ({...baseReport, id:`extra-${i}`, latitude:24 + i * .01, longitude:46, location_source:'manual'}))] : baseRecords;
    const recordedCount = mode === 'server' ? 23 : 3, firstPagePins = mode === 'server' ? 20 : 3;
    const located = report => typeof report.latitude === 'number' && typeof report.longitude === 'number' && Math.abs(report.latitude) <= 90 && Math.abs(report.longitude) <= 180;
    const category = report => located(report) && ['manual', 'device_gps'].includes(report.location_source) ? 'recorded' : located(report) && report.location_source === 'simulated' ? 'simulated' : 'none';
    const context = await browser.newContext({viewport:{width, height:950}, reducedMotion:'reduce'});
    const requests = [], external = [], errors = [];
    let failedOnce = false, injectInvalid = false, releaseMap;
    await context.addInitScript(language => {sessionStorage.setItem('roadscan_token', 'synthetic-map-only'); localStorage.setItem('roadscan_language', language);}, lang);
    await context.route('**/*', async route => {
      const request = route.request(), url = new URL(request.url());
      if (url.origin !== origin) {external.push(url.href); await route.abort(); return;}
      if (!url.pathname.startsWith('/api/')) {await route.continue(); return;}
      requests.push({method:request.method(), path:url.pathname, query:url.search});
      assert.equal(request.method(), 'GET', 'map and help must not write');
      if (/\/api\/reports\/[^/]+\/image$/.test(url.pathname)) {
        await route.fulfill({contentType:'image/svg+xml', body:'<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240"><rect width="320" height="240" fill="#6b797e"/><text x="40" y="120" fill="white">SYNTHETIC TEST IMAGE</text></svg>'}); return;
      }
      let data;
      if (url.pathname === '/api/reports') {
        if (url.searchParams.get('search') === 'delayed-map') await new Promise(resolve => {releaseMap = resolve;});
        if (url.searchParams.get('search') === 'transient-failure' && !failedOnce) {failedOnce = true; await route.fulfill({status:503, json:{detail:'Synthetic temporary outage'}}); return;}
        if (mode === 'legacy') assert.equal(url.searchParams.get('location'), null, 'old server uses explicit page-only fallback');
        const filtered = records.filter(report => (!url.searchParams.get('location') || category(report) === url.searchParams.get('location')) && (!url.searchParams.get('status') || report.status === url.searchParams.get('status')) && (!url.searchParams.get('search') || report.id.includes(url.searchParams.get('search'))));
        if (injectInvalid && url.searchParams.get('location') === 'recorded') filtered.unshift({...baseReport, id:'legacy-invalid-returned', latitude:200, longitude:0, location_source:'manual'});
        const size = Number(url.searchParams.get('size') || 20), page = Number(url.searchParams.get('page') || 1);
        data = {items:filtered.slice((page - 1) * size, page * size), total:filtered.length};
      } else if (/^\/api\/reports\/[^/]+$/.test(url.pathname)) data = records.find(report => `/api/reports/${report.id}` === url.pathname);
      else if (url.pathname === '/api/stats') data = {total:records.length, needs_review:records.length - 1, high_priority:0, by_status:{}, ...(mode === 'server' ? {by_location:{recorded:23, simulated:14, none:3}} : {})};
      if (data) await route.fulfill({json:data}).catch(() => {}); else await route.continue();
    });
    const page = await context.newPage(); page.on('pageerror', error => errors.push(error.message));
    const tx = (en, ar) => lang === 'ar' ? ar : en;
    const nav = page.getByRole('navigation');
    const map = page.locator('.evidence-workspace'), groups = map.locator('.evidence-switch');
    const inspector = map.locator('.evidence-inspector');
    const group = (en, ar) => groups.getByRole('button', {name:new RegExp(tx(en, ar))});
    try {
      await page.goto(origin);
      await expect(page.locator('.connection-label')).toHaveText(tx('Connected', 'متصل'));
      await nav.getByRole('button', {name:new RegExp(tx('Review queue', 'قائمة المراجعة'))}).click();
      await page.getByRole('button', {name:tx('Next page', 'الصفحة التالية'), exact:true}).click();
      await expect(page.locator('.pagination')).toContainText('2 /');
      await nav.getByRole('button', {name:tx('Map & results', 'الخريطة والنتائج'), exact:true}).click();
      await expect(map.locator('h1')).toHaveText(tx('Find a report by location', 'اعثر على بلاغ حسب الموقع'));
      await expect(map.locator('.map-purpose')).toContainText(tx('no streets, routes or distance scale', 'بلا شوارع أو مسارات أو مقياس مسافة'));
      await expect(group('Recorded locations', 'مواقع مسجلة')).toContainText(String(recordedCount));
      await expect(map.locator('.map-coverage-note')).toContainText(mode === 'server' ? tx('Workspace coverage', 'تغطية مساحة العمل') : tx('Limited coverage', 'تغطية محدودة'));
      await expect(group('No usable location', 'بلا موقع صالح')).toContainText('3');
      await expect(group('Simulated locations', 'مواقع محاكاة')).toContainText('14');
      await expect(map.locator('.map-marker')).toHaveCount(firstPagePins);
      await expect(map.locator('.map-records button')).toHaveCount(firstPagePins);
      await expect(map.locator('.evidence-pagination')).toContainText(mode === 'server' ? '23' : '22');
      const positions = await map.locator('.map-marker').evaluateAll(nodes => nodes.map(node => [node.style.left, node.style.top]));
      assert.deepEqual(positions[0], positions[2], 'overlapping coordinates are not displaced or invented');
      await map.locator('.map-marker').nth(1).focus();
      await page.keyboard.press('Enter');
      await expect(inspector.locator('h2')).toBeFocused();
      await expect(inspector).toContainText('gps-000002');
      await map.locator('.map-records button').nth(2).click();
      await expect(inspector.locator('h2')).toBeFocused();
      await expect(inspector).toContainText('overlap-03');
      await expect(inspector.locator('a[href*="/maps/search/"]')).toHaveAttribute('href', 'https://www.google.com/maps/search/?api=1&query=24.7%2C46.7');
      await expect(inspector.locator('.map-external-note')).toContainText(tx('shares the selected coordinates', 'يشارك الإحداثيات المحددة'));
      await inspector.getByRole('button', {name:tx('Back to report list', 'العودة إلى قائمة البلاغات')}).click();
      await expect(map.locator('#map-report-list')).toBeFocused();
      await map.locator('.map-records button').nth(1).click();
      await expect(inspector).toContainText(tx('not independently verified', 'لم يُتحقق منه بشكل مستقل'));
      await group('No usable location', 'بلا موقع صالح').click();
      await expect(map.locator('.map-marker')).toHaveCount(0);
      await expect(map.locator('.map-records button')).toHaveCount(3);
      await map.locator('.map-records button').nth(1).click();
      await expect(inspector).toContainText('unknown-05');
      await expect(inspector.getByRole('link')).toHaveCount(0);
      await map.locator('.map-records button').nth(2).click();
      await expect(inspector).toContainText(tx('No valid coordinate pair', 'لم يُحفظ زوج صالح'));
      await group('Simulated locations', 'مواقع محاكاة').click();
      await expect(map.locator('.map-marker')).toHaveCount(14);
      await expect(map.locator('.map-simulation-note')).toBeVisible();
      await expect(inspector.getByRole('link')).toHaveCount(0);

      // Returning to a page never preserves a now-hidden report selection.
      await group('Recorded locations', 'مواقع مسجلة').click();
      await map.getByRole('button', {name:tx('Next map page', 'صفحة الخريطة التالية')}).click();
      await expect(inspector).toContainText(mode === 'server' ? 'extra-15' : 'page-two-1');
      await expect(map.locator('.map-marker')).toHaveCount(mode === 'server' ? 3 : 2);
      if (mode === 'legacy') await expect(inspector.locator('a[href*="/maps/search/"]')).toHaveAttribute('href', 'https://www.google.com/maps/search/?api=1&query=0%2C0');
      await expect(map.getByRole('button', {name:tx('Next map page', 'صفحة الخريطة التالية')})).toBeDisabled();
      await map.getByRole('button', {name:tx('Previous map page', 'صفحة الخريطة السابقة')}).click();
      await expect(map.locator('.map-marker')).toHaveCount(firstPagePins);

      await map.locator('.map-filters input').fill('missing');
      await map.locator('.map-filters').getByRole('button', {name:tx('Search', 'بحث'), exact:true}).click();
      await expect(map.locator('.map-empty-state')).toContainText(mode === 'server' ? tx('No matching reports', 'لا توجد بلاغات مطابقة') : tx('No recorded locations', 'لا توجد مواقع مسجلة'));
      await expect(map.locator('.map-filter-summary')).toContainText('missing');
      await map.locator('.map-empty-actions').getByRole('button', {name:new RegExp(tx('No usable location', 'بلا موقع صالح'))}).click();
      await expect(inspector).toContainText('missing-04');
      await map.locator('.map-filters').getByRole('button', {name:tx('Clear filters', 'مسح عوامل التصفية')}).click();
      await group('Recorded locations', 'مواقع مسجلة').click();
      await map.locator('.map-filters select').selectOption('Confirmed');
      await expect(map.locator('.map-records button')).toHaveCount(1);
      await nav.getByRole('button', {name:new RegExp(tx('Review queue', 'قائمة المراجعة'))}).click();
      await expect(page.getByLabel(tx('Filter reports by status', 'تصفية البلاغات حسب الحالة'))).toHaveValue('');
      await expect(page.locator('.pagination')).toContainText('2 /');
      await nav.getByRole('button', {name:tx('Map & results', 'الخريطة والنتائج'), exact:true}).click();
      await expect(map.locator('.map-filters select')).toHaveValue('');
      await expect(map.locator('.map-marker')).toHaveCount(firstPagePins);
      await map.locator('.map-filters input').fill('transient-failure');
      await map.locator('.map-filters').getByRole('button', {name:tx('Search', 'بحث'), exact:true}).click();
      await expect(page.getByRole('alert')).toContainText('Synthetic temporary outage');
      await expect(map.locator('.map-empty-state')).toContainText(tx('Map reports unavailable', 'بلاغات الخريطة غير متاحة'));
      await expect(map.locator('.evidence-pagination')).toHaveCount(0);
      await page.getByRole('button', {name:tx('Retry map', 'إعادة تحميل الخريطة'), exact:true}).click();
      await expect(page.getByRole('alert')).toHaveCount(0);
      await expect(map.locator('.map-empty-state')).toContainText(tx('No matching reports', 'لا توجد بلاغات مطابقة'));
      await map.locator('.map-filters input').fill('no-such-synthetic-report');
      await map.locator('.map-filters').getByRole('button', {name:tx('Search', 'بحث'), exact:true}).click();
      await expect(map.locator('.map-empty-state')).toContainText(tx('No matching reports on this page', 'لا توجد بلاغات مطابقة في هذه الصفحة'));
      await expect(inspector.locator('img')).toHaveCount(0);
      await map.locator('.map-filters').getByRole('button', {name:tx('Clear filters', 'مسح عوامل التصفية')}).click();
      await expect(map.locator('.map-marker')).toHaveCount(firstPagePins);
      await page.screenshot({path:path.join(artifacts, `map-${mode}-${lang}-${width}.png`), fullPage:true});
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({path:path.join(artifacts, `map-${mode}-${lang}-${width}-viewport.png`)});
      const overflow = await page.evaluate(() => [...document.querySelectorAll('body *')].filter(element => {const box = element.getBoundingClientRect(); return box.width && (box.right > window.innerWidth + 1 || box.left < -1);}).map(element => ({tag:element.tagName, class:element.className, width:element.getBoundingClientRect().width})));
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), `${lang} ${width}: no page overflow: ${JSON.stringify(overflow)}`);

      if (mode === 'server' && lang === 'en' && width === 1440) {
        injectInvalid = true;
        await page.getByRole('button', {name:'Refresh workspace', exact:true}).click();
        await expect(map.locator('.map-coverage-mismatch')).toContainText('Coverage totals differ');
        await expect(map.locator('.map-records button')).toHaveCount(20);
        await expect(map.locator('.map-marker')).toHaveCount(19);
        await expect(map.locator('.map-unlocated-note')).toContainText('unusable coordinates');
        await expect(inspector).toContainText('legacy-invalid-returned');
        await expect(inspector.getByRole('link')).toHaveCount(0);
        injectInvalid = false;
        await page.getByRole('button', {name:'Refresh workspace', exact:true}).click();
        await expect(map.locator('.map-coverage-mismatch')).toHaveCount(0);
        await expect(map.locator('.map-marker')).toHaveCount(20);
        await map.locator('.map-filters input').fill('delayed-map');
        await map.locator('.map-filters').getByRole('button', {name:'Search', exact:true}).click();
        await expect.poll(() => Boolean(releaseMap)).toBe(true);
        await expect(map.locator('.map-empty-state')).toContainText('Loading reports');
        await expect(map.locator('.map-marker')).toHaveCount(0);
        await nav.getByRole('button', {name:'Overview', exact:true}).click();
        releaseMap();
        await nav.getByRole('button', {name:'Map & results', exact:true}).click();
        await expect(map.locator('.map-marker')).toHaveCount(20);
        await expect(map.locator('.map-filters input')).toHaveValue('');
      }

      const help = map.getByRole('button', {name:tx('How this map works', 'كيف تعمل هذه الخريطة')});
      await help.click();
      const guide = page.getByRole('dialog');
      await expect(guide.locator('#website-guide-topic')).toHaveText(tx('Find reports on the map', 'عرض البلاغات على الخريطة'));
      await expect(guide.locator('#website-guide-topic')).toBeFocused();
      await page.keyboard.press('Escape'); await expect(help).toBeFocused();
      await help.click();
      await expect(guide.locator('#website-guide-topic')).toBeFocused();
      await guide.getByLabel(tx('What would you like to do?', 'ماذا تريد أن تفعل؟')).fill(tx('simulated locations', 'مواقع محاكاة'));
      await guide.getByRole('button', {name:tx('Find steps', 'عرض الخطوات')}).click();
      await expect(guide.locator('#website-guide-topic')).toHaveText(tx('Find reports on the map', 'عرض البلاغات على الخريطة'));
      await guide.getByLabel(tx('What would you like to do?', 'ماذا تريد أن تفعل؟')).fill(tx('where is my video report on the map', 'موقع بلاغ الفيديو'));
      await guide.getByRole('button', {name:tx('Find steps', 'عرض الخطوات')}).click();
      await expect(guide.locator('#website-guide-topic')).toHaveText(tx('Add a location to a new photo', 'إضافة موقع لصورة جديدة'));
      await expect(guide.locator('.website-guide-answer')).toContainText(tx('GPS is not extracted automatically', 'لا يُستخرج GPS تلقائيًا'));
      await guide.getByLabel(tx('What would you like to do?', 'ماذا تريد أن تفعل؟')).fill(tx('add a location', 'إضافة موقع'));
      await guide.getByRole('button', {name:tx('Find steps', 'عرض الخطوات')}).click();
      await expect(guide.locator('#website-guide-topic')).toHaveText(tx('Add a location to a new photo', 'إضافة موقع لصورة جديدة'));
      await guide.getByRole('button', {name:tx('Open this screen', 'افتح هذه الشاشة')}).click();
      await expect(page.locator('[data-screen]')).toHaveAttribute('data-screen', 'dashboard');
      await expect(page.locator('#guide-inspection')).toBeFocused();
      await nav.getByRole('button', {name:tx('Map & results', 'الخريطة والنتائج'), exact:true}).click();
      await expect(page.locator('.website-guide-highlight')).toHaveCount(0);
      await inspector.getByRole('button', {name:tx('Open image & review', 'فتح الصورة والمراجعة')}).click();
      await expect(page.locator('[data-screen]')).toHaveAttribute('data-screen', 'reports');
      await expect(page.locator('#report-image')).toBeVisible();
      await page.getByLabel(tx('Inspector note', 'ملاحظة المراجع'), {exact:true}).fill('Synthetic unsaved note');
      await nav.getByRole('button', {name:tx('Map & results', 'الخريطة والنتائج'), exact:true}).click();
      await expect(page.locator('[data-screen]')).toHaveAttribute('data-screen', 'reports');
      await expect(page.getByLabel(tx('Inspector note', 'ملاحظة المراجع'), {exact:true})).toHaveValue('Synthetic unsaved note');
      assert.deepEqual(external, [], 'no external map or coordinate request');
      assert.deepEqual(errors, []);
      console.log(`PASS map ${mode} ${lang} ${width}: groups, provenance, overlap, pagination, independent filters, direct help, focus, navigation, draft guard; ${requests.length} synthetic GETs`);
    } finally {releaseMap?.(); await context.close();}
  }
}
