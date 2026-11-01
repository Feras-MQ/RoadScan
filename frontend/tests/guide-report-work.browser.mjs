import assert from 'node:assert/strict';

// Exercise the real report components; only HTTP responses are synthetic.
export async function checkReportWorkGuard(browser, origin, report, expect) {
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}, reducedMotion: 'reduce'});
  await context.route('**/*', route => route.request().url().startsWith(origin + '/') ? route.continue() : route.abort());
  await context.addInitScript(() => {sessionStorage.setItem('roadscan_token', 'synthetic-guide-only'); localStorage.setItem('roadscan_language', 'en');});
  const page = await context.newPage();
  const models = ['a', 'b', 'c'].map(id => ({id, name: `Synthetic ${id}`, sha256: id.repeat(64), family: 'yolo'}));
  await page.route('**/api/models', route => route.fulfill({json: {items: models, available: true, can_manage: false, active_id: 'a'}}));
  await page.route(`**/api/reports/${report.id}`, route => route.fulfill({json: {...report, status: 'Confirmed'}}));
  await page.route(`**/api/reports/${report.id}/training`, route => route.fulfill({json: {approved: false, stale: false, eligible: true, split: 'train', capture_group: 'saved-group', approved_at: null}}));
  const writes = [], failures = [], errors = [];
  page.on('request', request => {if (request.method() !== 'GET') writes.push({method: request.method(), path: new URL(request.url()).pathname});});
  page.on('requestfailed', request => failures.push(new URL(request.url()).pathname));
  page.on('pageerror', error => errors.push(error.message));
  let releaseVote, voteCount = 0;
  await page.route(`**/api/reports/${report.id}/vote`, async route => {
    const ids = route.request().postDataJSON().model_ids;
    voteCount++;
    await new Promise(resolve => {releaseVote = resolve;});
    const detection = {class_id: 'D40', box: [10, 10, 40, 40], confidence: .7};
    await route.fulfill({json: {state: 'completed', revision: report.revision, width: 320, height: 240, consensus: [], agreements: [], disagreements: [], models: ids.map(id => ({...models.find(model => model.id === id), state: 'completed', detections: [detection], elapsed_ms: 10})), reason: null}}).catch(() => {});
  });
  try {
    await page.goto(origin);
    await page.getByRole('navigation', {name: 'Main navigation'}).getByRole('button', {name: /Review queue/}).click();
    await page.locator('.report-item').first().click();
    const picker = page.locator('.vote-picker');
    await picker.locator('summary').click();
    await expect(picker.getByRole('checkbox')).toHaveCount(3);
    await picker.getByRole('checkbox').nth(2).uncheck();
    const group = page.getByLabel('Training capture group', {exact: true});
    const split = page.getByLabel('Dataset split', {exact: true});
    const rights = page.getByRole('checkbox', {name: 'I checked these labels and have permission to use this image.', exact: true});
    const negative = page.getByRole('checkbox', {name: 'I inspected the full image: this is an intentional empty/negative example.', exact: true});
    await expect(group).toHaveValue('saved-group');
    await group.fill('draft-group'); await split.selectOption('val'); await rights.check(); await negative.check();
    await expect(page.locator('.review-statusbar')).toContainText('Saved report');

    async function leaveReport(accept) {
      await page.getByRole('button', {name: 'Website guide', exact: true}).click();
      const guide = page.getByRole('dialog');
      await guide.getByRole('button', {name: 'Find reports on the map', exact: true}).click();
      let prompt = '';
      const answer = async dialog => {prompt = dialog.message(); await (accept ? dialog.accept() : dialog.dismiss());};
      page.once('dialog', answer);
      await guide.getByRole('button', {name: 'Open this screen', exact: true}).click();
      page.removeListener('dialog', answer);
      assert.match(prompt, /running model vote/, 'leaving a selected report must warn about child work');
      await expect(page.locator('[data-screen]')).toHaveAttribute('data-screen', accept ? 'map' : 'reports');
      if (!accept) await page.keyboard.press('Escape');
    }
    async function assertDrafts() {
      await expect(group).toHaveValue('draft-group'); await expect(split).toHaveValue('val');
      await expect(rights).toBeChecked(); await expect(negative).toBeChecked();
      await expect(picker.getByRole('checkbox').nth(2)).not.toBeChecked();
    }
    await page.getByRole('button', {name: 'Run model vote', exact: true}).click();
    await expect.poll(() => voteCount).toBe(1);
    await leaveReport(false);
    await expect(page.getByRole('button', {name: 'Models are comparing…', exact: true})).toBeDisabled();
    await assertDrafts();
    assert.equal(failures.filter(path => path.endsWith('/vote')).length, 0, 'cancel keeps the vote request alive');
    releaseVote();
    await expect(page.locator('.vote-model-results > div')).toHaveCount(2);
    await leaveReport(false);
    await assertDrafts();
    await expect(page.locator('.vote-model-results > div')).toHaveCount(2);
    assert.equal(voteCount, 1, 'guide actions never run another vote');
    await leaveReport(true);
    await page.getByRole('navigation', {name: 'Main navigation'}).getByRole('button', {name: /Review queue/}).click();
    await expect(group).toHaveValue('saved-group'); await expect(split).toHaveValue('train');
    await expect(rights).not.toBeChecked(); await expect(negative).not.toBeChecked();
    await expect(page.locator('.vote-results')).toHaveCount(0);
    await picker.locator('summary').click();
    await expect(picker.getByRole('checkbox').nth(2)).toBeChecked();
    await page.getByRole('button', {name: 'Run model vote', exact: true}).click();
    await expect.poll(() => voteCount).toBe(2);
    await leaveReport(true);
    await expect.poll(() => failures.filter(path => path.endsWith('/vote')).length).toBe(1);
    releaseVote();
    assert.deepEqual(writes, Array.from({length: 2}, () => ({method: 'POST', path: `/api/reports/${report.id}/vote`})), 'only the two explicit synthetic vote clicks make requests; no model activation or training submission');
    assert.deepEqual(errors, []);
    console.log('PASS: report guard preserves running/completed votes, model choices and training fields on Cancel; Continue intentionally discards child state and aborts a running vote.');
  } finally {releaseVote?.(); await context.close();}
}
