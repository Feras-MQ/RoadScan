import assert from 'node:assert/strict';
import test from 'node:test';
import {addDamageEvent, frameLoop, frameSize, validRecognition} from '../src/liveFrames.ts';

const tick = () => new Promise(resolve => setTimeout(resolve, 0));
test('live frames preserve aspect ratio and remain bounded without enlarging small sources', () => {
  assert.deepEqual(frameSize(1920, 1080), [960, 540]);
  assert.deepEqual(frameSize(1080, 1920), [540, 960]);
  assert.deepEqual(frameSize(320, 240), [320, 240]);
  assert.throws(() => frameSize(0, 1080));
  assert.throws(() => frameSize(NaN, 1080));
});
test('a processed frame accepts only matching valid boxes and never treats busy as a result', () => {
  const result = {state:'completed' as const, reason:null, detections:[{class_id:'D00',box:[1,2,90,70],confidence:.6}],model_version:'fixture',width:100,height:80,elapsed_ms:4,confidence_threshold:.25,persisted:false as const};
  assert.equal(validRecognition(result, 100, 80), true);
  assert.equal(validRecognition({...result,width:101}, 100, 80), false);
  assert.equal(validRecognition({...result,state:'busy'}, 100, 80), false);
  assert.equal(validRecognition({...result,detections:[{...result.detections[0],box:[1,2,150,70]}]}, 100, 80), false);
});
test('stop aborts the current request and prevents another frame from starting', async () => {
  let calls = 0; let signal: AbortSignal | undefined;
  const loop = frameLoop(async s => {calls++; signal=s; await new Promise<void>(resolve => s.addEventListener('abort', () => resolve(), {once:true}))}, () => assert.fail('stop must not report an error'), 1);
  loop.start(); await tick(); loop.stop(); await tick(); await tick();
  assert.equal(signal?.aborted, true); assert.equal(calls, 1);
});
test('restart never overlaps a late request that ignores abort', async () => {
  let calls = 0; let release: () => void = () => {};
  const loop = frameLoop(async () => {calls++; if(calls===1) await new Promise<void>(resolve => {release=resolve})}, () => {}, 1000);
  loop.start(); await tick(); loop.start(); await tick();
  assert.equal(calls, 1); release(); await tick(); assert.equal(calls, 2); loop.stop();
});
test('a late failure from an old run cannot stop the replacement run', async () => {
  let reject: (e: Error) => void = () => {}; let calls=0; const failures: unknown[]=[];
  const loop=frameLoop(async () => {if(++calls===1) await new Promise<void>((_,fail) => {reject=fail})}, e => failures.push(e),1000);
  loop.start(); await tick(); loop.start(); reject(Error('obsolete')); await tick();
  assert.equal(calls,2); assert.deepEqual(failures,[]); loop.stop();
});
test('a slow frame times out and the serial loop can recover without overlap', async () => {
  let calls=0;let failures=0;let active=0;let peak=0;
  let recovered!:()=>void;
  const recovery=new Promise<void>(resolve=>{recovered=resolve});
  const loop=frameLoop(async signal=>{
    calls++;active++;peak=Math.max(peak,active);
    try {if(calls===1)await new Promise<void>((_,reject)=>signal.addEventListener('abort',()=>reject(new DOMException('Timed out','AbortError')),{once:true}))}
    finally{active--;if(calls>=2)recovered()}
  },()=>failures++,1,5);
  let timeout:ReturnType<typeof setTimeout>|undefined;
  loop.start();
  try {await Promise.race([recovery,new Promise<void>(resolve=>{timeout=setTimeout(resolve,2000)})])}
  finally {clearTimeout(timeout);loop.stop()}
  assert.equal(failures,1);assert.ok(calls>=2);assert.equal(peak,1);
});
test('video damage frames group into events that keep the most confident frame', () => {
  const f = (frame_index: number, confs: number[], cls = 'D00') => ({frame_index, timestamp_ms: frame_index * 200, detections: confs.map(confidence => ({class_id: cls, box: [0, 0, 5, 5], confidence}))});
  let events: ReturnType<typeof addDamageEvent<ReturnType<typeof f>>> = [];
  for (const frame of [f(0, []), f(1, [.4]), f(2, [.9]), f(4, [.5], 'D40'), f(8, [.3]), f(9, [])]) events = addDamageEvent(events, frame);
  assert.equal(events.length, 2);
  assert.deepEqual([events[0].first, events[0].last, events[0].best.frame_index, events[0].classes], [1, 4, 2, ['D00', 'D40']]);
  assert.deepEqual([events[1].first, events[1].last, events[1].confidence], [8, 8, .3]);
});
