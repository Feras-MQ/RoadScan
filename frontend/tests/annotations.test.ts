import assert from 'node:assert/strict';
import {test} from 'node:test';
import {dragBox, validAnnotations} from '../src/annotations.ts';

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
