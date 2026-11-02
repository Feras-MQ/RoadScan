import {recordedMapUrl,recordedStreetViewUrl} from './reportLocation';
import type {ReportLocation} from './reportMap';

/** Plain links only. Rendering never requests imagery or transmits a report location. */
export default function LocationLinks({report,lang}:{report:ReportLocation;lang:string}) {
  const maps=recordedMapUrl(report),street=recordedStreetViewUrl(report);
  if(!maps||!street)return null;
  const tx=(en:string,ar:string)=>lang==='ar'?ar:en;
  return <div className="street-map-external">
    <a className="evidence-external" href={maps} target="_blank" rel="noopener noreferrer">{tx('Open in Google Maps (external)','فتح في خرائط Google (خارجي)')}</a>
    <a className="evidence-external" href={street} target="_blank" rel="noopener noreferrer">{tx('Open Google Street View (external)','فتح Google Street View (خارجي)')}</a>
    <p className="map-external-note">{tx('Opening either link shares the selected coordinates with Google. Street View may show a nearby place, be unavailable or be out of date. It is reference imagery, not evidence of current damage.','فتح أي من الرابطين يشارك الإحداثيات المحددة مع Google. قد يعرض Street View مكاناً قريباً أو يكون غير متاح أو قديماً. هي صور مرجعية وليست دليلاً على الضرر الحالي.')}</p>
  </div>;
}
