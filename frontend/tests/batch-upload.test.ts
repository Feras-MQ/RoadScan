import assert from 'node:assert/strict';
import {test} from 'node:test';
import {prepareBatch, retryFailed, runBatch} from '../src/batchUpload.ts';
import type {BatchItem} from '../src/batchUpload.ts';

const photo = (name: string, type = 'image/jpeg', size = 1) => new File([new Uint8Array(size)], name, {type});

test('batch selection keeps every file with its validation outcome and rejects oversized batches', () => {
  const items = prepareBatch([photo('good.jpg'), photo('wrong.txt', 'text/plain'), photo('big.png', 'image/png', 3)], 2);
  assert.deepEqual(items.map(item => [item.file.name, item.status, item.error]), [
    ['good.jpg', 'queued', undefined], ['wrong.txt', 'rejected', 'unsupported'], ['big.png', 'rejected', 'too-large'],
  ]);
  assert.throws(() => prepareBatch(Array.from({length: 21}, (_, i) => photo(`${i}.jpg`)), 2), /too-many-files/);
});

test('uploads are sequential, failures do not lose following files, and saved/rejected files are not retried', async () => {
  const items = prepareBatch([photo('a.jpg'), photo('b.jpg'), photo('c.jpg'), photo('x.txt', 'text/plain')], 2);
  let active = 0, maximum = 0;
  const calls: string[] = [];
  await runBatch(items, async file => {
    active++; maximum = Math.max(maximum, active); calls.push(file.name);
    await Promise.resolve(); active--;
    if (file.name === 'b.jpg') throw new Error('network failed');
    return file.name;
  }, (index, item) => {items[index] = item}, () => false);
  assert.equal(maximum, 1);
  assert.deepEqual(calls, ['a.jpg', 'b.jpg', 'c.jpg']);
  assert.deepEqual(items.map(item => item.status), ['saved', 'unconfirmed', 'saved', 'rejected']);
  items[1] = {...items[1], status: 'queued'};
  const retried: string[] = [];
  await runBatch(items, async file => {retried.push(file.name); return 'retry-id'}, (i, item) => {items[i] = item}, () => false);
  assert.deepEqual(retried, ['b.jpg']);
  assert.equal(items[1].id, 'retry-id');
});

test('HTTP rejection is distinguished from an unknown server or connection outcome', async () => {
  const items = prepareBatch([photo('invalid.jpg'), photo('server.jpg')], 2);
  await runBatch(items, async file => {throw Object.assign(new Error('request failed'), {status: file.name === 'invalid.jpg' ? 422 : 500})}, (i, item) => {items[i] = item}, () => false);
  assert.deepEqual(items.map(item => item.status), ['failed', 'unconfirmed']);
});

test('bulk retry excludes unconfirmed reports even when another photo was explicitly rejected', async () => {
  const items: BatchItem[] = [
    {file: photo('possibly-saved.jpg'), status: 'unconfirmed'},
    {file: photo('rejected.jpg'), status: 'failed'},
    {file: photo('saved.jpg'), status: 'saved', id: 'existing'},
  ];
  const retried: string[] = [];
  await runBatch(retryFailed(items), async file => {retried.push(file.name); return 'new'}, () => {}, () => false);
  assert.deepEqual(retried, ['rejected.jpg']);
  assert.equal(items[0].status, 'unconfirmed');
});

test('stop finishes an in-flight report and leaves all later files queued for continuation', async () => {
  const items = prepareBatch([photo('first.jpg'), photo('later.jpg')], 2);
  let stop = false;
  let finish!: (id: string) => void;
  const pending = runBatch(items, () => new Promise<string>(resolve => {finish = resolve}), (i, item) => {items[i] = item}, () => stop);
  assert.equal(items[0].status, 'uploading');
  stop = true; finish('saved-before-stop'); await pending;
  assert.equal(items[0].id, 'saved-before-stop');
  assert.equal(items[1].status, 'queued');
});

test('session invalidation prevents another POST even if an existing upload fails', async () => {
  const items = prepareBatch([photo('first.jpg'), photo('later.jpg')], 2);
  let session = 1, calls = 0;
  const visibleUpdates: BatchItem[] = [];
  await runBatch(items, async () => {calls++; session++; throw Error('connection lost')}, (_, item) => {if (session === 1) visibleUpdates.push(item)}, () => session !== 1);
  assert.equal(calls, 1);
  assert.deepEqual(visibleUpdates.map(item => item.status), ['uploading']);
});
