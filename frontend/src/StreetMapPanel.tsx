import {Component, lazy, Suspense, useEffect, useMemo, useRef, useState} from 'react';
import type {ReactNode} from 'react';
import {canPlotStreetPin, damageClasses, damageClassLabel, pinStatusColor} from './streetMap';
import type {PinResult} from './streetMap';
import type {LocationGroup} from './reportMap';
import {locationSourceLabel} from './reportLocation';
import LocationLinks from './LocationLinks';
import ReportPhoto from './ReportPhoto';
import './streetMap.css';
import {streetTileProvider} from './streetTileProvider';

const Canvas=lazy(()=>import('./StreetMapCanvas'));
class MapBoundary extends Component<{children:ReactNode; onFailure:()=>void},{failed:boolean}> {
  state={failed:false};
  static getDerivedStateFromError(){return {failed:true};}
  componentDidCatch(){this.props.onFailure();}
  render(){return this.state.failed?null:this.props.children;}
}
type Props={
  lang:string; sessionKey:string; group:LocationGroup; connected:boolean; busy:boolean; queryKey:string; searchActive:boolean;
  resetVersion:number; onViewingMap:(active:boolean)=>void;
  loadPins:(damageClass:string,signal:AbortSignal)=>Promise<PinResult>;
  labelStatus:(status:string)=>string; onOpen:(id:string)=>void; fallback:ReactNode;
};

export default function StreetMapPanel({lang,sessionKey,group,connected,busy,queryKey,searchActive,resetVersion,onViewingMap,loadPins,labelStatus,onOpen,fallback}:Props) {
  const tx=(en:string,ar:string)=>lang==='ar'?ar:en;
  const [enabled,setEnabled]=useState(false),[attempt,setAttempt]=useState(0),[damageClass,setDamageClass]=useState('');
  const [data,setData]=useState<{key:string;result:PinResult}|null>(null),[error,setError]=useState(false),[loading,setLoading]=useState(false);
  const [selectedId,setSelectedId]=useState('');
  const loader=useRef(loadPins);loader.current=loadPins;
  const selection=useRef<HTMLHeadingElement>(null),selector=useRef<HTMLSelectElement>(null);
  const key=queryKey+'|'+damageClass;
  useEffect(()=>{if(searchActive)setEnabled(false);},[searchActive]);
  useEffect(()=>setEnabled(false),[resetVersion]);
  useEffect(()=>{
    const controller=new AbortController();setData(null);setError(false);setSelectedId('');
    setLoading(enabled&&connected&&!searchActive&&group!=='unlocated');
    if(enabled&&connected&&!searchActive&&group!=='unlocated')loader.current(damageClass,controller.signal).then(result=>{
      if(!controller.signal.aborted)setData({key,result});
    }).catch(()=>{if(!controller.signal.aborted)setError(true);})
      .finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return()=>controller.abort();
  },[enabled,connected,group,key,attempt,damageClass,searchActive]);
  const result=enabled&&connected&&data?.key===key?data.result:null;
  const pins=useMemo(()=>result?.items.filter(canPlotStreetPin)||[],[result]);
  const selected=pins.find(pin=>pin.id===selectedId);
  const showMap=Boolean(enabled&&result&&pins.length&&!error&&!loading&&connected&&!searchActive&&group!=='unlocated');
  useEffect(()=>{onViewingMap(showMap);return()=>onViewingMap(false);},[showMap,onViewingMap]);
  function select(id:string){setSelectedId(id);window.requestAnimationFrame(()=>{selection.current?.focus({preventScroll:true});selection.current?.scrollIntoView({block:'nearest',behavior:'instant'});});}
  function disable(){setEnabled(false);setData(null);setError(false);setSelectedId('');}
  return <>
    <section className="street-map-panel" aria-labelledby="street-map-title">
      <h2 id="street-map-title">{tx('Street map (optional)','خريطة الشوارع (اختيارية)')}</h2>
      <p>{tx('Load street map connects to the OpenStreetMap tile provider shown here. It receives your IP address, this site’s origin and the viewed map region. Report photos, notes and access keys are not sent. Map tiles are not available offline.','تحميل خريطة الشوارع يتصل بمزوّد خرائط OpenStreetMap الموضح هنا. يتلقى عنوان IP وأصل هذا الموقع والمنطقة المعروضة. لا تُرسل صور البلاغات أو الملاحظات أو مفاتيح الدخول. الخرائط غير متاحة دون إنترنت.')} <bdi>{streetTileProvider?.host||tx('Tile provider is not configured correctly.','مزوّد الخرائط غير مهيأ بشكل صحيح.')}</bdi></p>
      {group==='unlocated'?<p>{tx('These reports have no usable location. Review them in the list; no place is guessed.','هذه البلاغات بلا موقع صالح. راجعها في القائمة؛ لا يُخمَّن أي موقع.')}</p>:<>
        {searchActive&&<p role="status">{tx('Street pins are off while a report search is active. Clear the search to load street pins; the matching report list and coordinate diagram still work below.','نقاط الشوارع متوقفة أثناء البحث عن بلاغ. امسح البحث لتحميلها؛ تظل قائمة البلاغات المطابقة ومخطط الإحداثيات متاحين أدناه.')}</p>}
        <div className="street-map-actions">{!enabled?<button className="secondary" disabled={!connected||busy||searchActive||!streetTileProvider} onClick={()=>setEnabled(true)}>{tx('Load street map','تحميل خريطة الشوارع')}</button>:<button className="secondary" onClick={disable}>{tx('Turn street map off','إيقاف خريطة الشوارع')}</button>}
          {enabled&&error&&<button className="secondary" disabled={!connected||busy} onClick={()=>setAttempt(n=>n+1)}>{tx('Try street map again','إعادة محاولة تحميل خريطة الشوارع')}</button>}</div>
        {enabled&&<label className="street-map-filter">{tx('Damage class — street pins only','فئة الضرر — نقاط الشوارع فقط')}<select value={damageClass} disabled={busy||!connected} onChange={e=>setDamageClass(e.target.value)}>
          <option value="">{tx('All classes, including no detections','كل الفئات، بما فيها بلا اكتشافات')}</option>
          {damageClasses.map(c=><option key={c} value={c}>{damageClassLabel(c,lang)}</option>)}<option value="none">{tx('No detections','بلا اكتشافات')}</option>
        </select></label>}
        {enabled&&<p>{tx('Street pins use this location group and the map filters. The damage-class filter applies only to street pins; the report list below keeps its existing pages.','تستخدم نقاط الشوارع مجموعة المواقع هذه وتصفيات الخريطة. تصفية فئة الضرر تخص نقاط الشوارع فقط؛ تحتفظ قائمة البلاغات أدناه بصفحاتها الحالية.')}</p>}
        {group==='simulated'&&enabled&&<p className="street-map-simulation-note">{tx('SIMULATED LOCATIONS — demonstration pins, not evidence of where damage occurred.','مواقع محاكاة — نقاط توضيحية، وليست دليلاً على مكان وقوع الضرر.')}</p>}
        {loading&&<p role="status">{tx('Loading matching pin records…','جارٍ تحميل سجلات النقاط المطابقة…')}</p>}
        {enabled&&error&&<p className="street-map-fallback-note" role="status">{tx('Street map unavailable. The coordinate diagram and report list remain available below. No automatic retry.','خريطة الشوارع غير متاحة. يظل مخطط الإحداثيات وقائمة البلاغات متاحين أدناه. لا تُعاد المحاولة تلقائياً.')}</p>}
        {result&&!error&&<p className="street-map-count" role="status">{tx(`Returned ${result.returned} of ${result.total} matching pins (limit ${result.limit}).`,`أُعيدت ${result.returned} من ${result.total} نقطة مطابقة (الحد ${result.limit}).`)} {result.truncated&&<strong>{tx('Some matching pins are omitted. Narrow the filters; this is not a complete map.','بعض النقاط المطابقة غير معروضة. ضيّق التصفيات؛ هذه ليست خريطة كاملة.')}</strong>}</p>}
        {result&&!error&&result.unreadable>0&&<p className="street-map-unreadable" role="status">{tx(`${result.unreadable} matching reports have unreadable saved detection data, including any beyond the pin limit. These are not zero-detection reports; damage-class filters exclude them.`,`${result.unreadable} بلاغات مطابقة لها بيانات اكتشافات محفوظة غير قابلة للقراءة، بما فيها ما يتجاوز حد النقاط. ليست بلاغات بلا اكتشافات؛ تستبعدها مرشحات فئات الضرر.`)}</p>}
        {result&&!error&&pins.length!==result.returned&&<p>{tx('Some coordinates are outside the street map’s latitude range. Their saved locations have not been moved; use the coordinate diagram and report list.','بعض الإحداثيات خارج نطاق خطوط العرض لخريطة الشوارع. لم تُحرَّك مواقعها المحفوظة؛ استخدم مخطط الإحداثيات وقائمة البلاغات.')}</p>}
        {result&&!error&&!pins.length&&<p role="status">{tx('No matching pins can be drawn on the street map. No tiles are loaded for these results.','لا توجد نقاط مطابقة يمكن رسمها على خريطة الشوارع. لا تُحمَّل خرائط لهذه النتائج.')}</p>}
        {showMap&&<MapBoundary key={attempt} onFailure={()=>setError(true)}><Suspense fallback={<p role="status">{tx('Opening map…','جارٍ فتح الخريطة…')}</p>}><Canvas pins={pins} lang={lang} simulated={group==='simulated'} selectedId={selectedId} labelStatus={labelStatus} onSelect={select} onFailure={()=>setError(true)}/></Suspense></MapBoundary>}
        {showMap&&<>
          <p>{tx('Pin colours show review status, not damage severity. Numbers refer to the selector below. Overlapping pins remain separately selectable.','توضح ألوان النقاط حالة المراجعة، لا شدة الضرر. تشير الأرقام إلى القائمة أدناه. يمكن اختيار كل بلاغ على حدة حتى عند تداخل النقاط.')}</p>
          <ul className="street-map-legend">{Array.from(new Set(pins.map(pin=>pin.status))).map(status=><li key={status}><i style={{background:pinStatusColor(status)}}/>{labelStatus(status)}</li>)}</ul>
          <label className="street-map-selector">{tx('Select a street-map report','اختر بلاغاً من خريطة الشوارع')}<select ref={selector} value={selected?.id||''} onChange={e=>select(e.target.value)}><option value="">{tx('Choose a pin or report','اختر نقطة أو بلاغاً')}</option>{pins.map((pin,i)=><option key={pin.id} value={pin.id}>{i+1} · {pin.id} · {labelStatus(pin.status)}</option>)}</select></label>
          {selected&&<section className="street-map-selection" aria-labelledby="street-selected-title">
            <h3 id="street-selected-title" ref={selection} tabIndex={-1}>{tx('Selected street-map report','البلاغ المحدد على خريطة الشوارع')} <bdi>{selected.id}</bdi></h3>
            {/* First-party fetch for the selected pin only; never passed to Leaflet or the tile provider. */}
            <ReportPhoto key={selected.id+sessionKey} id={selected.id} sessionKey={sessionKey} lang={lang}/>
            <dl><div><dt>{tx('Review status','حالة المراجعة')}</dt><dd>{labelStatus(selected.status)}</dd></div><div><dt>{tx('Saved damage classes','فئات الضرر المحفوظة')}</dt><dd>{selected.classes===null?tx('Unreadable detection data','بيانات الاكتشافات غير قابلة للقراءة'):selected.classes.map(code=>damageClassLabel(code,lang)).join(' · ')||tx('No detections','بلا اكتشافات')}</dd></div><div><dt>{tx('Location source','مصدر الموقع')}</dt><dd>{locationSourceLabel(selected.location_source,lang)}</dd></div></dl>
            <p><bdi>{selected.latitude}, {selected.longitude}</bdi></p>
            <p className="street-map-review-hint">{tx('Saved coordinates are not independently verified. Check the photo preview, then open the report to inspect detection boxes and save your review.','لم يُتحقق من الإحداثيات المحفوظة بشكل مستقل. راجع معاينة الصورة، ثم افتح البلاغ لفحص التحديدات وحفظ مراجعتك.')}</p>
            <div className="street-map-selection-actions">
              <button className="primary" disabled={busy||!connected} onClick={()=>onOpen(selected.id)}>{tx('Open report to review','فتح البلاغ للمراجعة')}</button>
              <button type="button" className="secondary" onClick={()=>selector.current?.focus()}>{tx('Back to pin selector','العودة إلى قائمة النقاط')}</button>
            </div>
            <LocationLinks report={selected} lang={lang}/>
          </section>}
        </>}
      </>}
    </section>
    {showMap?<details className="map-location-help"><summary>{tx('Show this page’s offline coordinate diagram','عرض مخطط الإحداثيات المحلي لهذه الصفحة')}</summary>{fallback}</details>:fallback}
  </>;
}
