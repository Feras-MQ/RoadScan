import assert from 'node:assert/strict';
import test from 'node:test';
import {projectLocations} from '../src/reportMap.ts';

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
