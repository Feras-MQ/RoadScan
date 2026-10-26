import assert from 'node:assert/strict';
import {test} from 'node:test';
import {motionEnabled} from '../src/motionPreference.ts';
import {googleMapsUrl} from '../src/reportLocation.ts';

test('motion follows system preference until explicitly changed', () => {
  assert.equal(motionEnabled(null, true), false);
  assert.equal(motionEnabled(null, false), true);
  assert.equal(motionEnabled(true, true), true);
  assert.equal(motionEnabled(false, false), false);
});

test('map links encode real coordinates including zero and reject missing or invalid locations', () => {
  assert.equal(googleMapsUrl(0, -180), 'https://www.google.com/maps/search/?api=1&query=0%2C-180');
  for (const [lat, lon] of [[null, 0], [0, undefined], [NaN, 0], [0, Infinity], [91, 0], [0, -181]]) {
    assert.equal(googleMapsUrl(lat, lon), null);
  }
});
