// Build first. Uses an already installed Playwright and Chrome; never installs a browser.
// Optional ROADSCAN_PLAYWRIGHT_MODULE is a file URL to an existing Playwright index.mjs.
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile, mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {checkMapWorkspace} from './map-workspace.browser.mjs';
import {checkStreetMap} from './street-map.browser.mjs';
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
  browser=await chromium.launch({headless:true,...(process.env.ROADSCAN_CHROME?{executablePath:process.env.ROADSCAN_CHROME}:{channel:'chrome'})});
  if(process.env.ROADSCAN_MAP_TEST !== 'street')await checkMapWorkspace(browser,origin,report,expect,artifacts);
  await checkStreetMap(browser,origin,report,expect,artifacts);
  console.log('PASS: isolated map browser checks');
} finally {await browser?.close();await new Promise(resolve=>server.close(resolve));}
