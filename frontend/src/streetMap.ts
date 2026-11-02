import {locationGroup} from './reportMap.ts';
import type {LocationGroup, ReportLocation} from './reportMap.ts';

export type StreetPin = ReportLocation & {status:string; score:number|null; classes:string[]; created_at:string|null};
export type PinResult = {items:StreetPin[]; total:number; returned:number; limit:number; truncated:boolean};
export const damageClasses = ['D00', 'D10', 'D20', 'D40', 'OTHER'] as const;
export const MAX_STREET_PINS = 2000;
export const OSM_TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
export const OSM_TILE_OPTIONS = {
  maxZoom:19, minZoom:2, noWrap:true, referrerPolicy:'origin',
  updateWhenIdle:true, updateWhenZooming:false, keepBuffer:0, detectRetina:false,
  attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a>',
} as const;

/** A build may point at another OSM-derived tile service without editing source or adding keys. */
export function osmTileProvider(value=OSM_TILE_URL):{url:string;host:string}|null {
  try {
    const parsed=new URL(value);
    if(parsed.protocol!=='https:'||parsed.username||parsed.password||parsed.search||parsed.hash||!['{z}','{x}','{y}'].every(part=>value.includes(part)))return null;
    return {url:value,host:parsed.host};
  }catch{return null;}
}

/** Contract agreed on PR #1 comment 6573345086. Text search belongs to the paged report list. */
export function streetPinsPath(group:LocationGroup,status:string,damage:string) {
  if(group==='unlocated')return null;
  if(damage && damage!=='none' && !damageClasses.includes(damage as typeof damageClasses[number]))return null;
  const params=new URLSearchParams({location:group,limit:String(MAX_STREET_PINS)});
  if(status)params.set('status',status);
  if(damage)params.set('damage',damage);
  return '/api/reports/map?'+params;
}

/** Do not display a misleading complete layer when an API response is inconsistent. */
export function readPinResult(value:unknown, group:LocationGroup):PinResult|null {
  if (!value || typeof value !== 'object' || group === 'unlocated') return null;
  const result = value as PinResult;
  if (!Array.isArray(result.items) || ![result.total,result.returned,result.limit].every(n => Number.isSafeInteger(n) && n >= 0)
    || result.limit < 1 || result.limit > MAX_STREET_PINS || result.returned !== result.items.length
    || result.returned !== Math.min(result.total,result.limit) || result.truncated !== (result.total > result.returned)) return null;
  const ids = new Set<string>();
  for (const pin of result.items) {
    if (!pin || typeof pin.id !== 'string' || !pin.id || ids.has(pin.id) || locationGroup(pin) !== group
      || typeof pin.status !== 'string' || !(pin.created_at === null || typeof pin.created_at === 'string')
      || !(pin.score === null || typeof pin.score === 'number' && Number.isFinite(pin.score))
      || !Array.isArray(pin.classes) || pin.classes.some(c => !damageClasses.includes(c as typeof damageClasses[number]))) return null;
    ids.add(pin.id);
  }
  return result;
}

// Web Mercator cannot draw the poles. Keep those valid saved coordinates in the offline list.
export function canPlotStreetPin(pin:StreetPin) {
  return locationGroup(pin) !== 'unlocated' && Math.abs(pin.latitude!) <= 85.0511287798;
}

/** Status colours are workflow labels, never engineering severity or GPS confidence. */
export function pinStatusColor(status:string) {
  return ({'New':'#92400e','Needs Review':'#92400e','Confirmed':'#1d4ed8','Assigned':'#7e22ce','Resolved':'#166534','Duplicate':'#475569'} as Record<string,string>)[status] || '#475569';
}
