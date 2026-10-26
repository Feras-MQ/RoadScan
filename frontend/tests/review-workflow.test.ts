import assert from 'node:assert/strict';
import {test} from 'node:test';
import {canReviewTransition, reviewPayload} from '../src/reviewWorkflow.ts';

test('review lifecycle supplies explicit backend actions and retains notes', () => {
  for (const [previous, target, action] of [
    ['Needs Review', 'Confirmed', 'confirm'], ['Confirmed', 'Assigned', 'assign'],
    ['Assigned', 'Resolved', 'resolve'], ['Resolved', 'Needs Review', 'review'],
    ['Needs Review', 'Duplicate', 'duplicate'],
  ]) {
    assert.deepEqual(reviewPayload(previous, target, 'Inspector note'), {status: target, note: 'Inspector note', action});
  }
});

test('notes can be updated without changing status', () => {
  assert.equal(reviewPayload('Resolved', 'Resolved', 'Follow-up note').action, 'review');
});

test('invalid shortcuts and unknown statuses are rejected before submission', () => {
  for (const [previous, target] of [
    ['Needs Review', 'Assigned'], ['Needs Review', 'Resolved'],
    ['Resolved', 'Confirmed'], ['Resolved', 'Duplicate'], ['Confirmed', 'unknown'],
  ]) {
    assert.equal(canReviewTransition(previous, target), false);
    assert.throws(() => reviewPayload(previous, target, ''), /Confirm a report/);
  }
});
