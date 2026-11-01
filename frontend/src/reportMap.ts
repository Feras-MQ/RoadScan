import {googleMapsUrl} from './reportLocation.ts';

export type ReportLocation = {id:string; latitude?:number|null; longitude?:number|null; location_source?:string};

export type LocationGroup = 'recorded' | 'unlocated' | 'simulated';
export type LocationCounts = {recorded:number; simulated:number; none:number};

export function readLocationCounts(value:unknown, total?:number):LocationCounts|null {
  if (!value || typeof value !== 'object') return null;
  const counts = value as LocationCounts;
  const values = [counts.recorded, counts.simulated, counts.none];
  return values.every(count => Number.isSafeInteger(count) && count >= 0) && values.reduce((sum, count) => sum + count, 0) === total ? counts : null;
}

export function mapRequestPath(page:number, group:LocationGroup, status:string, search:string, supportsLocation:boolean) {
  const params = new URLSearchParams({size:'20', page:String(page)});
  if (supportsLocation) params.set('location', group === 'unlocated' ? 'none' : group);
  if (status) params.set('status', status);
  if (search) params.set('search', search);
  return '/api/reports?' + params;
}

/** Unknown provenance is never treated as a verified real-world position. */
export function locationGroup(report: ReportLocation): LocationGroup {
  if (report.location_source === 'simulated' && googleMapsUrl(report.latitude, report.longitude)) return 'simulated';
  return ['manual', 'device_gps'].includes(report.location_source || '') && googleMapsUrl(report.latitude, report.longitude)
    ? 'recorded' : 'unlocated';
}

/** Fit recorded coordinates into an 800×500 local coordinate view; no invented basemap. */
export function projectLocations<T extends ReportLocation>(reports:T[]) {
  const located=reports.filter(r=>['manual','device_gps','simulated'].includes(r.location_source||'')&&googleMapsUrl(r.latitude,r.longitude)!==null);
  if(!located.length)return [];
  const anchor=located[0].longitude!;
  const latitude=located.reduce((sum,r)=>sum+r.latitude!,0)/located.length;
  const cosine=Math.max(.000001,Math.cos(latitude*Math.PI/180));
  const points=located.map(report=>({report,x:((report.longitude!-anchor+540)%360-180)*cosine,y:-report.latitude!}));
  const xs=points.map(p=>p.x),ys=points.map(p=>p.y);
  const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
  const scale=Math.min(680/Math.max(maxX-minX,.000001),360/Math.max(maxY-minY,.000001));
  return points.map(p=>({...p,x:400+(p.x-(minX+maxX)/2)*scale,y:250+(p.y-(minY+maxY)/2)*scale}));
}
