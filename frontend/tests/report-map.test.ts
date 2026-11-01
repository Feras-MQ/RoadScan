import assert from 'node:assert/strict';
import test from 'node:test';
import {locationGroup, mapRequestPath, projectLocations, readLocationCounts} from '../src/reportMap.ts';

const project=(reports:Parameters<typeof projectLocations>[0])=>projectLocations(reports.map(r=>({...r,location_source:'manual'})));

test('map excludes missing, nonfinite and out-of-range coordinates without inventing positions',()=>{
  const points=project([{id:'valid',latitude:24.7,longitude:46.7},{id:'missing'},{id:'nan',latitude:NaN,longitude:0},{id:'range',latitude:91,longitude:0}]);
  assert.deepEqual(points.map(p=>p.report.id),['valid']);assert.equal(points[0].x,400);assert.equal(points[0].y,250);
});
test('north stays above south and east stays right with a padded aspect-preserving fit',()=>{
  const p=project([{id:'sw',latitude:24,longitude:46},{id:'ne',latitude:25,longitude:47}]);
  assert.ok(p[0].x<p[1].x&&p[0].y>p[1].y);assert.ok(p.every(q=>q.x>=60&&q.x<=740&&q.y>=70&&q.y<=430));
});
test('coincident and dateline locations stay finite and keep every report',()=>{
  const same=project([{id:'a',latitude:0,longitude:0},{id:'b',latitude:0,longitude:0}]);assert.equal(same.length,2);assert.deepEqual(same.map(p=>[p.x,p.y]),[[400,250],[400,250]]);
  const edge=project([{id:'west',latitude:0,longitude:179},{id:'east',latitude:0,longitude:-179}]);assert.ok(edge[0].x<edge[1].x);assert.ok(edge.every(p=>Number.isFinite(p.x)&&Number.isFinite(p.y)));
});

test('unknown provenance never becomes a pin',()=>{assert.equal(projectLocations([{id:'unknown',latitude:24,longitude:46}]).length,0);assert.equal(projectLocations([{id:'gps',latitude:24,longitude:46,location_source:'device_gps'}]).length,1)});

test('location groups keep missing, invalid and unknown sources reviewable and simulation separate', () => {
  for (const location_source of ['manual', 'device_gps']) {
    assert.equal(locationGroup({id:'zero', latitude:0, longitude:0, location_source}), 'recorded');
    assert.equal(locationGroup({id:'missing', latitude:24, location_source}), 'unlocated');
    assert.equal(locationGroup({id:'invalid', latitude:91, longitude:46, location_source}), 'unlocated');
  }
  for (const location_source of [undefined, 'not_provided', 'unknown']) {
    assert.equal(locationGroup({id:'legacy', latitude:24, longitude:46, location_source}), 'unlocated');
  }
  assert.equal(locationGroup({id:'demo', latitude:24, longitude:46, location_source:'simulated'}), 'simulated');
  assert.equal(locationGroup({id:'demo-missing', location_source:'simulated'}), 'unlocated');
  assert.equal(projectLocations([{id:'demo-missing', location_source:'simulated'}]).length, 0);
});

test('whole-workspace coverage requires complete sane counts; legacy stats use page-only fallback', () => {
  const valid = {recorded:22, simulated:3, none:4};
  assert.equal(readLocationCounts(valid, 29), valid);
  assert.deepEqual(readLocationCounts({recorded:0, simulated:0, none:0}, 0), {recorded:0, simulated:0, none:0});
  for (const value of [undefined, null, {}, {recorded:22}, {...valid, none:-1}, {...valid, none:NaN}, {...valid, none:1.5}, {...valid, none:'4'}]) assert.equal(readLocationCounts(value, 29), null);
  assert.equal(readLocationCounts(valid, 30), null);
});

test('map requests page independently, use only the additive location parameter, and encode search', () => {
  assert.equal(mapRequestPath(2, 'recorded', '', '', true), '/api/reports?size=20&page=2&location=recorded');
  assert.equal(mapRequestPath(1, 'unlocated', '', '', true), '/api/reports?size=20&page=1&location=none');
  assert.equal(mapRequestPath(1, 'simulated', '', '', true), '/api/reports?size=20&page=1&location=simulated');
  const url = new URL(mapRequestPath(3, 'recorded', 'Needs Review', 'a&location=simulated', false), 'http://local.test');
  assert.equal(url.searchParams.get('location'), null);
  assert.equal(url.searchParams.get('page'), '3');
  assert.equal(url.searchParams.get('status'), 'Needs Review');
  assert.equal(url.searchParams.get('search'), 'a&location=simulated');
});
