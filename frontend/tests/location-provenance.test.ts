import test from 'node:test';
import assert from 'node:assert/strict';
import {locationSourceLabel,recordedMapUrl} from '../src/reportLocation.ts';

test('location labels distinguish GPS, manual, simulation and legacy unknown sources',()=>{
  assert.equal(locationSourceLabel('device_gps','en'),'Device GPS (reported)');
  assert.equal(locationSourceLabel('manual','en'),'Manually entered');
  assert.equal(locationSourceLabel('simulated','ar'),'موقع محاكاة');
  assert.equal(locationSourceLabel(undefined,'en'),'Source unspecified');
});
test('external maps keep latitude-longitude order and never expose simulated or ambiguous positions',()=>{
  assert.equal(recordedMapUrl({latitude:0,longitude:0,location_source:'manual'}),'https://www.google.com/maps/search/?api=1&query=0%2C0');
  assert.equal(recordedMapUrl({latitude:24.7,longitude:46.7,location_source:'device_gps'}),'https://www.google.com/maps/search/?api=1&query=24.7%2C46.7');
  for(const location_source of ['simulated','not_provided',''])assert.equal(recordedMapUrl({latitude:24,longitude:46,location_source}),null);
  assert.equal(recordedMapUrl({latitude:24,location_source:'manual'}),null);
});
