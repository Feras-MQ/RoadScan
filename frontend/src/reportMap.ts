import {googleMapsUrl} from './reportLocation.ts';

export type ReportLocation = {id:string; latitude?:number|null; longitude?:number|null; location_source?:string};

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
