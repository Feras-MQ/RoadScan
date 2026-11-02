import assert from 'node:assert/strict';
import {test} from 'node:test';
import {dragBox, validAnnotations, sameAnnotations} from '../src/annotations.ts';

test('reverse drags are normalized and clamped to original image pixels', () => {
  assert.deepEqual(dragBox([80, 70], [-30, -10], 100, 80), [0, 0, 80, 70]);
  assert.deepEqual(dragBox([20, 10], [110, 100], 100, 80), [20, 10, 100, 80]);
  assert.equal(dragBox([10, 10], [11, 11], 100, 80), null);
});

test('invalid boxes and unsupported classes cannot be submitted', () => {
  const d = {class_id: 'D40', box: [10, 10, 90, 70], confidence: 1};
  assert.equal(validAnnotations([d], 100, 80), true);
  for (const change of [{box: [0, 0, 101, 80]}, {box: [40, 10, 20, 70]}, {class_id: 'fake'}, {confidence: NaN}, {confidence: 1.1}]) {
    assert.equal(validAnnotations([{...d, ...change}], 100, 80), false);
  }
  assert.equal(validAnnotations(Array(101).fill(d), 100, 80), false);
});

test('review equality ignores annotation/key ordering without changing either input', () => {
  const a = {class_id:'D40', box:[1,2,30,40], confidence:0.8, source:'model'};
  const b = {class_id:'D00', box:[5,6,50,60], confidence:1};
  const left=[a,b], right=[{confidence:1,box:[5,6,50,60],class_id:'D00'},{source:'model',confidence:0.8,box:[1,2,30,40],class_id:'D40'}];
  const before=JSON.stringify({left,right});
  assert.equal(sameAnnotations(left,right),true);
  assert.equal(JSON.stringify({left,right}),before);
  for(const change of [{class_id:'D10'},{box:[1,2,31,40]},{confidence:0.9},{source:'human'}])
    assert.equal(sameAnnotations([a],[{...a,...change}]),false);
  assert.equal(sameAnnotations([a,a,b],[a,b,b]),false);
  assert.equal(sameAnnotations([a],[a,a]),false);
  assert.equal(sameAnnotations([],[]),true);
});
