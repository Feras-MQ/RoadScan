import {useEffect,useState} from 'react';
import {ArrowUpRight,ChevronLeft,ChevronRight,FileImage,MapPin,Navigation,RefreshCw,ScanLine} from 'lucide-react';
import {projectLocations} from './reportMap';
import {googleMapsUrl,recordedMapUrl,locationSourceLabel} from './reportLocation';
import type {ReportLocation} from './reportMap';
import type {Detection} from './annotations';

export type EvidenceReport=ReportLocation & {status:string;created_at:string;score:number|null;model_version:string;detections:Detection[]};
type Props={reports:EvidenceReport[];total:number;page:number;lang:string;connected:boolean;busy:boolean;sessionKey:string;onPage:(page:number)=>void;onOpen:(id:string)=>void};

function ReportPhoto({id,sessionKey,lang}:{id:string;sessionKey:string;lang:string}) {
  const [photo,setPhoto]=useState(''),[failed,setFailed]=useState(false),[attempt,setAttempt]=useState(0);
  useEffect(()=>{
    const controller=new AbortController();let objectUrl='';setPhoto('');setFailed(false);
    // Construct a same-origin path so a report can never redirect the access header elsewhere.
    fetch(`/api/reports/${encodeURIComponent(id)}/image`,{headers:{'X-API-Key':sessionKey},signal:controller.signal})
      .then(async response=>{if(!response.ok)throw Error('Image unavailable');return response.blob()})
      .then(blob=>{if(!controller.signal.aborted){objectUrl=URL.createObjectURL(blob);setPhoto(objectUrl)}})
      .catch(()=>{if(!controller.signal.aborted)setFailed(true)});
    return()=>{controller.abort();if(objectUrl)URL.revokeObjectURL(objectUrl)};
  },[id,sessionKey,attempt]);
  return <div className="evidence-photo">{failed?<div role="alert"><FileImage/><p>{lang==='ar'?'تعذر تحميل الصورة. البلاغ محفوظ.':'Image unavailable. The report is safe.'}</p><button onClick={()=>setAttempt(n=>n+1)}><RefreshCw size={15}/>{lang==='ar'?'إعادة المحاولة':'Retry image'}</button></div>:photo?<img src={photo} alt={lang==='ar'?'صورة البلاغ المحفوظة':'Saved report image'} onError={()=>setFailed(true)}/>:<span role="status">{lang==='ar'?'جارٍ تحميل الصورة…':'Loading image…'}</span>}</div>;
}

export default function EvidenceMap({reports,total,page,lang,connected,busy,sessionKey,onPage,onOpen}:Props) {
  const tx=(en:string,ar:string)=>lang==='ar'?ar:en;
  const [simulation,setSimulation]=useState(false),[selectedId,setSelectedId]=useState('');
  const visible=reports.filter(r=>(r.location_source==='simulated')===simulation);
  const points=projectLocations(visible);
  const selected=visible.find(r=>r.id===selectedId)||points[0]?.report||visible[0];
  const selectedPoint=points.find(p=>p.report.id===selected?.id);
  const mapUrl=recordedMapUrl(selected);
  const source=(r:EvidenceReport)=>locationSourceLabel(r.location_source,lang);
  return <section className="evidence-workspace" aria-labelledby="evidence-title">
    <header className="evidence-heading"><div><div className="eyebrow">{tx('MAP & EVIDENCE','الخريطة والأدلة')}</div><h1 id="evidence-title">{tx('Every pin has a story.','وراء كل نقطة قصة.')}</h1><p>{tx('Choose a location. Inspect the evidence. Keep the human decision.','اختر موقعًا وافحص الأدلة واتخذ القرار بنفسك.')}</p></div><span className="evidence-count"><MapPin size={16}/>{points.length} {tx('located on this page','مواقع في هذه الصفحة')}</span></header>
    <div className="evidence-toolbar"><div className="evidence-switch" aria-label={tx('Location provenance','مصدر المواقع')}><button aria-pressed={!simulation} onClick={()=>{setSimulation(false);setSelectedId('')}}>{tx('Recorded locations','المواقع المسجلة')}</button><button aria-pressed={simulation} onClick={()=>{setSimulation(true);setSelectedId('')}}>{tx('Simulation','المحاكاة')}</button></div><p>{tx('Current report page and review filters apply.','تُطبق صفحة البلاغات وعوامل تصفية المراجعة الحالية.')}</p></div>
    <div className="evidence-layout">
      <div className="evidence-map-column"><div className={'coordinate-map '+(simulation?'is-simulation':'')} role="group" aria-label={tx('Report coordinate view','عرض إحداثيات البلاغات')}>
        <div className="map-context"><span>{tx('LOCAL COORDINATE VIEW','عرض إحداثيات محلي')}</span><small>{tx('No street tiles or inferred routes','بدون خريطة شوارع أو مسارات مفترضة')}</small></div><span className="map-north" aria-label={tx('North','الشمال')}><Navigation size={18}/>N</span>
        <div className="coordinate-canvas" dir="ltr">
          {selectedPoint&&<svg className="map-crosshair" viewBox="0 0 800 500" preserveAspectRatio="none" aria-hidden="true"><path d={`M ${selectedPoint.x} 0 V 500 M 0 ${selectedPoint.y} H 800`}/><circle cx={selectedPoint.x} cy={selectedPoint.y} r="29"/></svg>}
          {points.map((p,i)=><button key={p.report.id} className={'map-marker '+(selected?.id===p.report.id?'selected ':'')+(p.report.status==='Needs Review'||p.report.status==='New'?'awaiting':'')} style={{left:`${p.x/8}%`,top:`${p.y/5}%`}} aria-pressed={selected?.id===p.report.id} aria-label={tx('Inspect report ','فحص البلاغ ')+p.report.id.slice(0,8)} onClick={()=>setSelectedId(p.report.id)}><span>{i+1}</span></button>)}
          {!points.length&&<div className="map-empty"><MapPin size={34}/><h2>{!connected?tx('Connect to see your evidence','اتصل لعرض الأدلة'):tx('No locations on this page','لا توجد مواقع في هذه الصفحة')}</h2><p>{tx('Reports without coordinates remain available below. Add a location when uploading a new photo.','تظل البلاغات دون إحداثيات متاحة أدناه. أضف الموقع عند رفع صورة جديدة.')}</p></div>}
        </div><div className="map-legend"><span><i/>{tx('Selected report','البلاغ المحدد')}</span><span><i/>{tx('Needs review','بانتظار المراجعة')}</span><small>{simulation?tx('SIMULATED POSITIONS','مواقع محاكاة'):tx('Saved coordinates; accuracy depends on source','إحداثيات محفوظة؛ دقتها تعتمد على المصدر')}</small></div>
      </div><div className="map-records" aria-label={tx('All reports on this page, including overlapping pins','كل بلاغات الصفحة، بما فيها النقاط المتداخلة')}>{visible.map(r=><button key={r.id} aria-pressed={selected?.id===r.id} onClick={()=>setSelectedId(r.id)}><MapPin size={14}/><span>{r.id.slice(0,8).toUpperCase()}</span><small>{googleMapsUrl(r.latitude,r.longitude)?source(r):tx('No location','دون موقع')}</small></button>)}</div></div>
      <aside className="evidence-inspector" aria-label={tx('Evidence inspector','فاحص الأدلة')} aria-live="polite">{selected?<>
        <div className="mini-label">{tx('EVIDENCE INSPECTOR','فاحص الأدلة')}</div><h2>{tx('Report ','بلاغ ')}{selected.id.slice(0,8).toUpperCase()}</h2>
        <ReportPhoto key={selected.id+sessionKey} id={selected.id} sessionKey={sessionKey} lang={lang}/>
        <dl><div><dt>{tx('Saved annotations','التحديدات المحفوظة')}</dt><dd><ScanLine size={18}/>{selected.detections.length} <small>{tx('boxes','مربعات')}</small></dd></div><div><dt>{tx('Draft priority','أولوية مبدئية')}</dt><dd>{selected.score==null?'—':Math.round(selected.score)}<small>/ 100</small></dd></div><div><dt>{tx('Location source','مصدر الموقع')}</dt><dd className="evidence-source">{googleMapsUrl(selected.latitude,selected.longitude)?source(selected):tx('Not provided','غير متوفر')}</dd></div></dl>
        {googleMapsUrl(selected.latitude,selected.longitude)&&<p className="evidence-coordinates" dir="ltr">{selected.latitude!.toFixed(5)}, {selected.longitude!.toFixed(5)}</p>}
        <p className="evidence-help">{tx('A model vote is a second opinion. You can choose a minority model in the review.','تصويت النماذج رأي إضافي. يمكنك اختيار نموذج الأقلية أثناء المراجعة.')}</p>
        <button className="primary" disabled={busy||!connected} onClick={()=>onOpen(selected.id)}>{tx('Open image & review','فتح الصورة والمراجعة')}<ArrowUpRight size={17}/></button>
        {mapUrl&&<a className="evidence-external" href={mapUrl} target="_blank" rel="noreferrer">{tx('Open coordinates in Google Maps','فتح الإحداثيات في خرائط Google')}<ArrowUpRight size={14}/></a>}
      </>:<div className="empty"><FileImage size={30}/><strong>{tx('Your evidence will appear here','ستظهر أدلتك هنا')}</strong><span>{tx('Create a report or change the location filter.','أنشئ بلاغًا أو غيّر عامل تصفية المواقع.')}</span></div>}</aside>
    </div>
    <div className="evidence-pagination"><span>{tx('Loaded','المعروض')} {reports.length} / {total} {tx('reports','بلاغات')}</span><div><button aria-label={tx('Previous map page','صفحة الخريطة السابقة')} disabled={busy||page<=1} onClick={()=>onPage(page-1)}><ChevronLeft size={17}/></button><span>{page} / {Math.max(1,Math.ceil(total/20))}</span><button aria-label={tx('Next map page','صفحة الخريطة التالية')} disabled={busy||page*20>=total} onClick={()=>onPage(page+1)}><ChevronRight size={17}/></button></div></div>
  </section>;
}
