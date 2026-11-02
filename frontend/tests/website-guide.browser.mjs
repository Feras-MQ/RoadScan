import {checkUnreadableReports} from './unreadable-reports.browser.mjs';
// Build first. Uses an already installed Playwright and Chrome; never installs a browser.
// Optional ROADSCAN_PLAYWRIGHT_MODULE is a file URL to an existing Playwright index.mjs.
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile, mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {checkReportWorkGuard} from './guide-report-work.browser.mjs';
import {checkVideoNavigation} from './video-navigation.browser.mjs';
import {checkMapWorkspace} from './map-workspace.browser.mjs';
import {checkNavigationMedia} from './navigation-media.browser.mjs';
import {checkPreciseNavigation} from './navigation-state.browser.mjs';
const {chromium} = await import(process.env.ROADSCAN_PLAYWRIGHT_MODULE || 'playwright');
const {expect} = await import(process.env.ROADSCAN_PLAYWRIGHT_EXPECT || 'playwright/test');
const dist = path.resolve(fileURLToPath(new URL('../dist/', import.meta.url)));
const artifacts = process.env.ROADSCAN_QA_OUTPUT || path.join(dist, 'guide-qa');
await mkdir(artifacts, {recursive: true});
const report = {id: 'synthetic-guide-0001', revision: 'qa-1', status: 'Needs Review', created_at: '2026-01-01T00:00:00Z', score: null, inference_state: 'not_configured', detections: [], duplicates: [], image_url: '/api/fixture-image.svg', note: '', model_version: 'manual', history: []};
const second = {...report, id: 'synthetic-guide-0002'};
const requests = [];
const server = createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');
  if (url.pathname.startsWith('/api/')) {
    requests.push({method: req.method, path: url.pathname});
    if (req.method !== 'GET') {res.writeHead(405); res.end('Synthetic QA does not accept writes'); return;}
    if (url.pathname === '/api/fixture-image.svg') {res.setHeader('Content-Type', 'image/svg+xml'); res.end('<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240"><rect width="320" height="240" fill="#888"/></svg>'); return;}
    const data = url.pathname === '/api/health' ? {status: 'ok', model: 'not_configured'}
      : url.pathname === '/api/stats' ? {total: 2, needs_review: 2, high_priority: 0, by_status: {}}
      : url.pathname === '/api/reports' ? {items: [report, second], total: 2}
      : url.pathname === `/api/reports/${report.id}` ? report
      : url.pathname === `/api/reports/${second.id}` ? second
      : url.pathname.endsWith('/audit') ? {items: []}
      : url.pathname === '/api/training' ? {approved: 1, stale: 0, counts: {train: 1, val: 0, test: 0}, can_export: true}
      : url.pathname === '/api/models' ? {items: [], available: false, can_manage: false, active_id: null} : null;
    res.writeHead(data ? 200 : 404, {'Content-Type': 'application/json'}); res.end(JSON.stringify(data || {detail: 'No fixture for this endpoint'})); return;
  }
  const filename = path.resolve(dist, '.' + (url.pathname === '/' ? '/index.html' : url.pathname));
  if (!filename.startsWith(dist + path.sep) && filename !== path.join(dist, 'index.html')) {res.writeHead(403); res.end(); return;}
  try {const data = await readFile(filename); res.setHeader('Content-Type', filename.endsWith('.js') ? 'text/javascript' : filename.endsWith('.css') ? 'text/css' : filename.endsWith('.svg') ? 'image/svg+xml' : 'text/html'); res.end(data);}
  catch {res.writeHead(404); res.end();}
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
let browser;
try {
  browser = await chromium.launch({headless: true, ...(process.env.ROADSCAN_CHROME ? {executablePath: process.env.ROADSCAN_CHROME} : {channel: 'chrome'})});
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}, reducedMotion: 'reduce'});
  await context.route('**/*', route => route.request().url().startsWith(origin + '/') ? route.continue() : route.abort());
  await context.addInitScript(() => sessionStorage.setItem('roadscan_token', 'synthetic-guide-only'));
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(origin);
  const guide = page.getByRole('dialog');
  const launch = () => page.getByRole('button', {name: 'Website guide', exact: true}).click();
  const topic = name => guide.getByRole('button', {name, exact: true}).last().click();
  const navigate = () => guide.getByRole('button', {name: 'Open this screen', exact: true}).click();
  const screen = name => expect(page.locator('[data-screen]')).toHaveAttribute('data-screen', name);
  await expect(page.getByText('Connected', {exact: true})).toBeVisible();
  await launch();
  await expect(guide).toBeVisible();
  await expect(page.locator('#website-guide-title')).toBeFocused();
  for (let i = 0; i < 18; i++) {await page.keyboard.press('Tab'); assert.ok(await guide.evaluate(el => el.contains(document.activeElement)));}
  const beforeQuestion = requests.length;
  await guide.getByLabel('What would you like to do?').fill('how do I upload a video');
  await guide.getByRole('button', {name: 'Find steps'}).click();
  await expect(guide.locator('h3#website-guide-topic')).toHaveText('Analyze a video');
  await guide.getByLabel('What would you like to do?').fill('how do I compare models?');
  await guide.getByRole('button', {name: 'Find steps'}).click();
  await expect(guide.locator('h3#website-guide-topic')).toHaveText('Compare models');
  assert.equal(requests.length, beforeQuestion, 'questions do not make requests');
  await page.screenshot({path: path.join(artifacts, 'desktop-en.png')});
  await navigate();
  await screen('reports');
  await expect(page.locator('#review-queue')).toHaveClass(/website-guide-highlight/);
  await expect(page.locator('#review-queue')).toBeFocused();
  await launch();
  await expect(page.locator('.website-guide-highlight')).toHaveCount(0);
  await topic('Export reports');
  await expect(guide).toContainText('no report export button');
  await guide.getByRole('button', {name: 'Back to topics'}).click();
  await expect(guide.locator('#website-guide-topic')).toHaveCount(0);
  await guide.getByLabel('What would you like to do?').fill('delete all reports');
  await guide.getByRole('button', {name: 'Find steps'}).click();
  await expect(guide).toContainText('I do not have a clear guide');
  await expect(guide.getByRole('button', {name: 'Open this screen'})).toHaveCount(0);
  await page.keyboard.press('Escape');
  await expect(guide).not.toBeVisible();
  await expect(page.getByRole('button', {name: 'Website guide', exact: true})).toBeFocused();
  await page.locator('.report-item').first().click();
  await expect(page.locator('#report-image')).toBeVisible();
  await launch(); await topic('Compare models'); await navigate();
  await expect(page.locator('#guide-model-vote')).toHaveClass(/website-guide-highlight/);
  await expect(page.locator('#guide-model-vote')).toBeInViewport();
  await launch(); await topic('Review and edit detections'); await navigate();
  await expect(page.locator('#review-annotations')).toBeFocused();
  await launch(); await topic('Save a review'); await navigate();
  await expect(page.locator('#review-decision')).toBeFocused();
  await page.getByLabel('Inspector note', {exact: true}).fill('Synthetic unsaved draft');
  await launch(); await topic('Find reports on the map'); await navigate();
  await expect(guide).toBeVisible(); await screen('reports');
  await expect(guide.getByRole('alert')).toContainText('unsaved review changes');
  await page.keyboard.press('Escape');
  await expect(page.getByLabel('Inspector note', {exact: true})).toHaveValue('Synthetic unsaved draft');
  await page.locator('.report-item').nth(1).click();
  await expect(page.locator('.unsaved-review-alert')).toBeVisible();
  await page.getByRole('button', {name: 'Keep editing', exact: true}).click();
  await page.getByLabel('Inspector note', {exact: true}).fill('');
  await launch(); await topic('Find reports on the map'); await navigate(); await screen('map');
  await page.getByRole('navigation', {name: 'Main navigation'}).getByRole('button', {name: 'Overview', exact: true}).click();
  await expect(page.locator('.website-guide-highlight')).toHaveCount(0);
  await launch(); await topic('Upload and analyze a photo'); await navigate();
  await expect(page.locator('#guide-inspection')).toBeFocused();
  await page.getByLabel('Upload road photo').setInputFiles({name: 'synthetic.svg.png', mimeType: 'image/png', buffer: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jf1sAAAAASUVORK5CYII=', 'base64')});
  await launch(); await topic('Analyze a video'); await navigate(); await screen('live');
  assert.ok(!requests.some(r => /recognize|video/.test(r.path)), 'guide never starts media analysis');
  await launch(); await topic('Upload and analyze a photo');
  await navigate(); await screen('dashboard');
  await expect(page.getByAltText('Selected road photo', {exact: true})).toBeVisible();
  await launch(); await topic('Connection and model settings'); await navigate(); await screen('settings');
  await expect(page.locator('#guide-settings')).toHaveClass(/website-guide-highlight/);
  await launch();
  await guide.getByLabel('What would you like to do?').fill('download the training examples');
  await guide.getByRole('button', {name: 'Find steps'}).click();
  await expect(guide.locator('#website-guide-topic')).toHaveText('Download training examples');
  await navigate(); await screen('learning');
  await expect(page.locator('#guide-learning')).toHaveClass(/website-guide-highlight/);
  await expect(page.getByRole('button', {name: 'Export approved dataset', exact: true})).toBeEnabled();
  assert.ok(!requests.some(request => request.path.endsWith('/export')), 'the guide opens Learning without downloading');
  await page.getByRole('navigation', {name: 'Main navigation'}).getByRole('button', {name: 'Settings', exact: true}).click();
  await page.getByRole('button', {name: 'Switch to Arabic'}).click();
  await page.setViewportSize({width: 390, height: 844});
  await page.getByRole('button', {name: 'دليل الموقع', exact: true}).click();
  await expect(guide).toHaveAttribute('dir', 'rtl');
  await guide.getByLabel('ماذا تريد أن تفعل؟').fill('مُقارنة النماذج');
  await guide.getByRole('button', {name: 'عرض الخطوات'}).click();
  await expect(guide.locator('#website-guide-topic')).toHaveText('مقارنة النماذج');
  assert.ok(await guide.evaluate(el => el.scrollWidth <= el.clientWidth + 1), 'mobile panel has no horizontal overflow');
  await page.screenshot({path: path.join(artifacts, 'mobile-ar.png')});
  await guide.getByRole('button', {name: 'افتح هذه الشاشة'}).click(); await screen('reports');
  await expect(page.locator('#guide-model-vote')).toHaveClass(/website-guide-highlight/);
  await page.getByRole('button', {name: 'دليل الموقع', exact: true}).click();
  await guide.getByRole('button', {name: 'إغلاق الدليل', exact: true}).click();
  await expect(page.locator('.website-guide-highlight')).toHaveCount(0);
  await page.getByRole('button', {name: 'Switch to English'}).click();
  await launch(); await topic('Troubleshoot common errors');
  await page.screenshot({path: path.join(artifacts, 'mobile-en.png')});
  await page.keyboard.press('Escape');
  await page.setViewportSize({width: 1440, height: 1000});
  await page.getByRole('button', {name: 'Switch to Arabic'}).click();
  await page.getByRole('button', {name: 'دليل الموقع', exact: true}).click();
  await page.screenshot({path: path.join(artifacts, 'desktop-ar.png')});
  await page.setViewportSize({width: 320, height: 568});
  await guide.evaluate(el => {el.scrollTop = el.scrollHeight;});
  await expect(guide.getByRole('button', {name: 'إغلاق الدليل', exact: true})).toBeInViewport();
  assert.ok(await guide.evaluate(el => el.scrollWidth <= el.clientWidth + 1), 'small mobile panel has no horizontal overflow');
  await guide.getByRole('button', {name: 'إغلاق الدليل', exact: true}).click();
  assert.deepEqual(errors, [], 'no browser runtime errors');
  assert.ok(requests.every(r => r.method === 'GET'), 'guide never writes or submits');
  const offline = await browser.newContext({viewport: {width: 390, height: 844}});
  await offline.route('**/*', route => route.request().url().startsWith(origin + '/') ? route.continue() : route.abort());
  const offlinePage = await offline.newPage();
  await offlinePage.goto(origin);
  await offlinePage.getByRole('navigation').getByRole('button', {name: 'Map & results', exact: true}).click();
  await expect(offlinePage.locator('.map-empty-state')).toContainText('Connect to see report locations');
  await expect(offlinePage.locator('.map-marker')).toHaveCount(0);
  await expect(offlinePage.locator('.map-filters input')).toBeDisabled();
  const offlineHelp = offlinePage.getByRole('button', {name: 'How this map works', exact: true});
  await offlineHelp.click();
  await expect(offlinePage.locator('#website-guide-topic')).toHaveText('Find reports on the map');
  await offlinePage.keyboard.press('Escape');
  await expect(offlineHelp).toBeFocused();
  await offlinePage.getByRole('button', {name: 'Website guide', exact: true}).click();
  await expect(offlinePage.getByRole('dialog')).toBeVisible();
  await offlinePage.getByRole('dialog').getByRole('button', {name: 'Connection and model settings', exact: true}).click();
  await offlinePage.getByRole('button', {name: 'Open this screen', exact: true}).click();
  await expect(offlinePage.locator('[data-screen]')).toHaveAttribute('data-screen', 'settings');
  await expect(offlinePage.getByRole('heading', {name: 'Connect your workspace', exact: true})).toBeVisible();
  await offline.close();
  for (const width of [1440, 390]) for (const mode of ['guide', 'sidebar', 'brand']) {
    await checkReportWorkGuard(browser, origin, report, expect, mode, width);
    await checkVideoNavigation(browser, origin, expect, mode, width);
  }
  await checkUnreadableReports(browser, origin, report, expect);
  await checkPreciseNavigation(browser, origin, report, expect);
  await checkNavigationMedia(browser, origin, expect);
  await checkMapWorkspace(browser, origin, report, expect, artifacts);
  console.log(JSON.stringify({result: 'PASS', coverage: 'EN/AR desktop/mobile; typed questions; fallback; all destinations; keyboard/focus; back/close/reopen; highlight cleanup; unsaved review guard; existing report-switch guard; pending photo preserved; guide actions do not submit; guard scenarios use explicit mocked vote/video requests', requests: requests.length, artifacts}, null, 2));
  await context.close();
} finally {await browser?.close(); await new Promise(resolve => server.close(resolve));}
