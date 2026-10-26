import assert from 'node:assert/strict';
import {test} from 'node:test';
import {currentMedia, currentResult} from '../src/currentTask.ts';

test('an upload completing after disconnect cannot start its follow-up work', async () => {
  let session = 1;
  const initialSession = session;
  let finish!: (value: {id: string}) => void;
  const pending = currentResult(() => new Promise<{id: string}>(resolve => {finish = resolve}), () => session === initialSession);
  session++;
  finish({id: 'saved-on-server'});
  const result = await pending;
  assert.equal(result.current, false);
});

test('a stale refresh failure cannot disconnect a newer successful session', async () => {
  let generation = 1;
  let fail!: (reason: Error) => void;
  const pending = currentResult(() => new Promise( (_, reject) => {fail = reject}), () => generation === 1);
  generation = 2;
  fail(new Error('Old access key rejected'));
  assert.deepEqual(await pending, {current: false});
  await assert.rejects(currentResult(async () => {throw new Error('Current failure')}, () => true), /Current failure/);
});

test('a camera granted after navigation releases every acquired track', async () => {
  let current = true;
  let grant!: (value: {getTracks(): {stop(): void}[]}) => void;
  const stopped: number[] = [];
  const pending = currentMedia(() => new Promise<{getTracks(): {stop(): void}[]}>(resolve => {grant = resolve}), () => current);
  current = false;
  grant({getTracks: () => [0, 1].map(id => ({stop: () => {stopped.push(id)}}))});
  assert.deepEqual(await pending, {current: false});
  assert.deepEqual(stopped, [0, 1]);
});

test('an active camera is returned without stopping its tracks', async () => {
  let stopped = false;
  const media = {getTracks: () => [{stop: () => {stopped = true}}]};
  assert.deepEqual(await currentMedia(async () => media, () => true), {current: true, value: media});
  assert.equal(stopped, false);
});
