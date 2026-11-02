import assert from 'node:assert/strict';
import test from 'node:test';
import {recordedStreetViewUrl} from '../src/reportLocation.ts';
import {readPinResult,canPlotStreetPin,OSM_TILE_URL,OSM_TILE_OPTIONS,streetPinsPath,osmTileProvider,damageClassLabel} from '../src/streetMap.ts';
import type {StreetPin} from '../src/streetMap.ts';
import {matchGuideTopic} from '../src/guideContent.ts';
const pin:StreetPin={id:'synthetic-1',latitude:0,longitude:0,location_source:'manual',status:'Confirmed',score:null,classes:[],created_at:'2026-01-01T00:00:00Z'};
const response={items:[pin],returned:1,total:1,limit:2000,truncated:false,unreadable:0};

test('street view links use recorded finite coordinates only, including zero and boundaries',()=>{
  assert.equal(recordedStreetViewUrl(pin),'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=0%2C0');
  assert.equal(recordedStreetViewUrl({...pin,latitude:90,longitude:-180,location_source:'device_gps'}),'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=90%2C-180');
  for(const location_source of ['simulated','unknown','not_provided',undefined])assert.equal(recordedStreetViewUrl({...pin,location_source}),null);
  for(const latitude of [null,undefined,NaN,Infinity,91])assert.equal(recordedStreetViewUrl({...pin,latitude}),null);
  assert.equal(recordedStreetViewUrl(null),null);
});
test('pin responses require honest bounded counts and matching provenance without losing empty detections',()=>{
  assert.deepEqual(readPinResult(response,'recorded'),response);
  assert.equal(readPinResult(response,'simulated'),null);
  assert.equal(readPinResult(response,'unlocated'),null);
  assert.ok(readPinResult({...response,total:2001,returned:1,limit:1,truncated:true},'recorded'));
  for(const bad of [{returned:2},{total:0},{limit:2001},{limit:0},{truncated:true},{total:2},{items:[pin,pin],returned:2,total:2},{items:[{...pin,location_source:'unknown'}]},{items:[{...pin,classes:['INVENTED']}]},{items:[{...pin,latitude:NaN}]},{items:[{...pin,score:Infinity}]}])assert.equal(readPinResult({...response,...bad},'recorded'),null);
  assert.equal(readPinResult(null,'recorded'),null);
});
test('valid polar coordinates remain unchanged and are excluded from Mercator drawing only',()=>{
  const polar={...pin,latitude:90};
  assert.ok(readPinResult({...response,items:[polar]},'recorded'));
  assert.equal(canPlotStreetPin(polar),false);assert.equal(polar.latitude,90);
  assert.equal(canPlotStreetPin(pin),true);
  assert.equal(canPlotStreetPin({...pin,location_source:'simulated'}),true);
});
test('unreadable detection data stays distinct from empty detections and counts include omitted pins',()=>{
  const unreadable={...pin,id:'legacy',classes:null};
  const mixed={...response,items:[pin,unreadable],total:2,returned:2,unreadable:1};
  assert.deepEqual(readPinResult(mixed,'recorded'),mixed);
  assert.ok(readPinResult({...mixed,items:[pin],total:5,returned:1,limit:1,truncated:true,unreadable:4},'recorded'));
  for(const count of [-1,0,2,1.5,undefined])assert.equal(readPinResult({...mixed,unreadable:count},'recorded'),null);
  assert.equal(readPinResult({...response,total:5,limit:1,truncated:true,unreadable:5},'recorded'),null);
  assert.equal(readPinResult({...response,unreadable:undefined},'recorded')?.unreadable,0,'older readable-only endpoint');
  assert.equal(damageClassLabel('D40','en'),'D40 · Pothole');
  assert.equal(damageClassLabel('D00','ar'),'D00 · شق طولي');
  for(const code of ['D00','D10','D20','D40','OTHER'])for(const lang of ['en','ar'])assert.notEqual(damageClassLabel(code,lang),code+' · '+code);
});
test('standard tile settings disclose origin, use normal browser cache, and avoid prefetch/retina requests',()=>{
  assert.equal(OSM_TILE_URL,'https://tile.openstreetmap.org/{z}/{x}/{y}.png');
  assert.equal(OSM_TILE_OPTIONS.referrerPolicy,'origin');
  assert.equal(OSM_TILE_OPTIONS.keepBuffer,0);
  assert.equal(OSM_TILE_OPTIONS.detectRetina,false);
  assert.equal(OSM_TILE_OPTIONS.updateWhenIdle,true);
  assert.equal(OSM_TILE_OPTIONS.updateWhenZooming,false);
  assert.match(OSM_TILE_OPTIONS.attribution,/OpenStreetMap contributors/);
});
test('pin requests follow the agreed contract and never mix location groups',()=>{
  assert.equal(streetPinsPath('unlocated','',''),null);
  assert.equal(streetPinsPath('recorded','','invalid'),null);
  assert.equal(streetPinsPath('recorded','',''),'/api/reports/map?location=recorded&limit=2000');
  const url=new URL(streetPinsPath('simulated','Needs Review','none')!,'https://local.test');
  assert.equal(url.searchParams.get('location'),'simulated');assert.equal(url.searchParams.get('damage'),'none');
  assert.equal(url.searchParams.get('status'),'Needs Review');assert.equal(url.searchParams.get('search'),null);
});
test('tile provider configuration is HTTPS and key-free, with visible destination identity',()=>{
  assert.deepEqual(osmTileProvider(),{url:OSM_TILE_URL,host:'tile.openstreetmap.org'});
  assert.equal(osmTileProvider('https://tiles.example/{z}/{x}/{y}.png')?.host,'tiles.example');
  for(const value of ['http://tiles.example/{z}/{x}/{y}.png','https://secret@tiles.example/{z}/{x}/{y}.png',OSM_TILE_URL+'?key=secret','https://tiles.example/no-template','javascript:alert(1)'])assert.equal(osmTileProvider(value),null);
});
test('street map and Street View questions lead to curated map help without executing mixed requests',()=>{
  for(const question of ['street map','how do I open street view','خريطة الشوارع','عرض الشارع'])assert.equal(matchGuideTopic(question)?.id,'map');
  assert.equal(matchGuideTopic('street view and export PDF'),null);
  assert.equal(matchGuideTopic('delete report and open street map'),null);
});
