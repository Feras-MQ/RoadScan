import {inspectAnnotations, annotationSummary} from './reportDetections';
import type {StoredAnnotations} from './reportDetections';
import {useEffect, useRef, useState} from 'react';
import {ArrowUpRight, ChevronLeft, ChevronRight, FileImage, HelpCircle, MapPin, RefreshCw, Search} from 'lucide-react';
import {locationGroup, projectLocations} from './reportMap';
import {googleMapsUrl, locationSourceLabel} from './reportLocation';
import {reviewStatuses} from './reviewWorkflow';
import type {LocationCounts, LocationGroup, ReportLocation} from './reportMap';
import StreetMapPanel from './StreetMapPanel';
import LocationLinks from './LocationLinks';
import type {PinResult} from './streetMap';


export type EvidenceReport = ReportLocation & StoredAnnotations & {status:string; created_at:string; score:number|null; model_version:string};
type Props = {
  reports:EvidenceReport[]; total:number; page:number; lang:string; connected:boolean; busy:boolean; sessionKey:string;
  statusFilter:string; searchQuery:string; labelStatus:(status:string)=>string;
  group:LocationGroup; coverage:LocationCounts|null; onGroup:(group:LocationGroup)=>void;
  loadFailed:boolean;
  pinQueryKey:string; loadPins:(damage:string,signal:AbortSignal)=>Promise<PinResult>;
  onFilters:(status:string, search:string)=>void; onPage:(page:number)=>void; onOpen:(id:string)=>void;
  onNewInspection:()=>void; onHelp:()=>void;
};

function ReportPhoto({id, sessionKey, lang}:{id:string; sessionKey:string; lang:string}) {
  const [photo, setPhoto] = useState(''), [failed, setFailed] = useState(false), [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController(); let objectUrl = ''; setPhoto(''); setFailed(false);
    // Construct a same-origin path so a report can never redirect the access header elsewhere.
    fetch(`/api/reports/${encodeURIComponent(id)}/image`, {headers:{'X-API-Key':sessionKey}, signal:controller.signal})
      .then(async response => {if (!response.ok) throw Error('Image unavailable'); return response.blob();})
      .then(blob => {if (!controller.signal.aborted) {objectUrl = URL.createObjectURL(blob); setPhoto(objectUrl);}})
      .catch(() => {if (!controller.signal.aborted) setFailed(true);});
    return () => {controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl);};
  }, [id, sessionKey, attempt]);
  return <div className="evidence-photo">{failed ? <div role="alert"><FileImage/><p>{lang === 'ar' ? 'تعذر تحميل الصورة. يمكنك فتح البلاغ للمراجعة.' : 'Image unavailable. You can still open the report for review.'}</p><button onClick={() => setAttempt(n => n + 1)}><RefreshCw size={15}/>{lang === 'ar' ? 'إعادة المحاولة' : 'Retry image'}</button></div> : photo ? <img src={photo} alt={lang === 'ar' ? 'صورة البلاغ المحفوظة' : 'Saved report image'} onError={() => setFailed(true)}/> : <span role="status">{lang === 'ar' ? 'جارٍ تحميل الصورة.' : 'Loading image.'}</span>}</div>;
}

export default function EvidenceMap({reports, total, page, lang, connected, busy, sessionKey, statusFilter, searchQuery, labelStatus, group, coverage, loadFailed, pinQueryKey, loadPins, onGroup, onFilters, onPage, onOpen, onNewInspection, onHelp}:Props) {
  const tx = (en:string, ar:string) => lang === 'ar' ? ar : en;
  const [selectedId, setSelectedId] = useState('');
  const [streetActive,setStreetActive]=useState(false),[streetReset,setStreetReset]=useState(0);
  const [query, setQuery] = useState(searchQuery), [selectionVersion, setSelectionVersion] = useState(0);
  const inspector = useRef<HTMLHeadingElement>(null), listHeading = useRef<HTMLHeadingElement>(null);
  useEffect(() => setQuery(searchQuery), [searchQuery]);
  useEffect(() => {
    if (selectionVersion) {inspector.current?.focus({preventScroll:true}); inspector.current?.scrollIntoView({block:'nearest', behavior:'instant'});}
  }, [selectionVersion]);
  const groups: {id:LocationGroup; label:string}[] = [
    {id:'recorded', label:tx('Recorded locations', 'مواقع مسجلة')},
    {id:'unlocated', label:tx('No usable location', 'بلا موقع صالح')},
    {id:'simulated', label:tx('Simulated locations', 'مواقع محاكاة')},
  ];
  const counts = coverage ? {recorded:coverage.recorded, unlocated:coverage.none, simulated:coverage.simulated} : {recorded:0, unlocated:0, simulated:0};
  if (!coverage) reports.forEach(report => counts[locationGroup(report)]++);
  // Keep every server-returned row reviewable, even if legacy coordinates cannot be plotted.
  const visible = coverage ? reports : reports.filter(report => locationGroup(report) === group);
  const points = projectLocations(visible.filter(report => locationGroup(report) === group));
  const selected = visible.find(report => report.id === selectedId) || visible[0];
  const selectedPoint = points.find(point => point.report.id === selected?.id);
  const validCoordinates = selected && googleMapsUrl(selected.latitude, selected.longitude);
  const unavailable = busy || !connected;
  function changeGroup(next:LocationGroup) {onGroup(next); setSelectedId('');}
  function selectReport(id:string) {setStreetActive(false);setStreetReset(version=>version+1);setSelectedId(id); setSelectionVersion(version => version + 1);}
  const emptyTitle = !connected ? tx('Connect to see report locations', 'اتصل لعرض مواقع البلاغات')
    : busy ? tx('Loading reports…', 'جارٍ تحميل البلاغات…')
    : loadFailed ? tx('Map reports unavailable', 'بلاغات الخريطة غير متاحة')
    : !reports.length ? tx('No matching reports on this page', 'لا توجد بلاغات مطابقة في هذه الصفحة')
    : group === 'recorded' ? tx('No recorded locations on this page', 'لا توجد مواقع مسجلة في هذه الصفحة')
    : group === 'unlocated' ? tx('No reports without a usable location', 'لا توجد بلاغات بلا موقع صالح')
    : tx('No simulated locations on this page', 'لا توجد مواقع محاكاة في هذه الصفحة');

  return <section className="evidence-workspace" aria-labelledby="evidence-title" aria-busy={busy}>
    <header className="evidence-heading"><div><div className="eyebrow">{tx('MAP & RESULTS', 'الخريطة والنتائج')}</div><h1 id="evidence-title">{tx('Find a report by location', 'اعثر على بلاغ حسب الموقع')}</h1><p>{tx('Select a numbered pin or a report below, check its saved location, then open the image for review.', 'اختر نقطة مرقمة أو بلاغًا أدناه، وتحقق من موقعه المحفوظ، ثم افتح الصورة للمراجعة.')}</p></div><button className="secondary map-help-button" onClick={onHelp}><HelpCircle size={18}/>{tx('How this map works', 'كيف تعمل هذه الخريطة')}</button></header>
    <div className="map-purpose"><MapPin size={22}/><p><strong>{tx('Saved locations, with optional streets', 'مواقع محفوظة مع شوارع اختيارية')}</strong>{tx(' — the local coordinate diagram below has no streets, routes or distance scale. Load street map only if you want external map tiles. Neither view verifies where damage occurred.', ' — مخطط الإحداثيات المحلي أدناه بلا شوارع أو مسارات أو مقياس مسافة. حمّل خريطة الشوارع فقط إذا أردت خرائط خارجية. لا يتحقق أي من العرضين من مكان وقوع الضرر.')}</p></div>
    <form className="map-filters" onSubmit={event => {event.preventDefault(); onFilters(statusFilter, query.trim());}}>
      <label>{tx('Search report ID or note', 'ابحث برقم البلاغ أو الملاحظة')}<div className="map-search"><input maxLength={200} aria-label={tx('Search report ID or note', 'ابحث برقم البلاغ أو الملاحظة')} value={query} onChange={event => setQuery(event.target.value)} disabled={unavailable} placeholder={tx('Report ID or note…', 'رقم البلاغ أو الملاحظة…')}/><button className="secondary" disabled={unavailable}><Search size={17}/>{tx('Search', 'بحث')}</button></div></label>
      <label>{tx('Review status', 'حالة المراجعة')}<select value={statusFilter} disabled={unavailable} onChange={event => onFilters(event.target.value, searchQuery)}><option value="">{tx('All statuses', 'كل الحالات')}</option>{reviewStatuses.map(status => <option key={status} value={status}>{labelStatus(status)}</option>)}</select></label>
      {(statusFilter || searchQuery) && <button type="button" className="text-button" disabled={unavailable} onClick={() => {setQuery(''); onFilters('', '');}}>{tx('Clear filters', 'مسح عوامل التصفية')}</button>}
    </form>
    <p className="map-filter-summary">{tx('Map filters:', 'تصفية الخريطة:')} {statusFilter ? labelStatus(statusFilter) : tx('All statuses', 'كل الحالات')}{searchQuery && <> · {tx('Search:', 'البحث:')} <bdi>{searchQuery}</bdi></>}. {tx('Map pages and filters are separate from Review queue.', 'صفحات الخريطة وتصفيتها مستقلة عن قائمة المراجعة.')}</p>
    <p className="map-coverage-note">{!connected ? tx('Connect to load location coverage.', 'اتصل لتحميل تغطية المواقع.') : coverage ? tx('Workspace coverage: group totals below include all reports, before search or status filters. Browse each group with its own result pages.', 'تغطية مساحة العمل: تشمل أعداد المجموعات أدناه كل البلاغات قبل البحث أو تصفية الحالة. تصفح صفحات النتائج لكل مجموعة.') : tx('Limited coverage: location groups and counts describe only this loaded page. Use Next page to check more reports; these are not workspace-wide location totals.', 'تغطية محدودة: تصف مجموعات المواقع وأعدادها هذه الصفحة المحملة فقط. استخدم الصفحة التالية لفحص المزيد؛ هذه ليست أعداد المواقع لكل مساحة العمل.')}</p>
    {coverage && !unavailable && !loadFailed && !statusFilter && !searchQuery && total !== counts[group] && <p className="map-coverage-mismatch" role="status">{tx('Coverage totals differ from these results. Use Refresh workspace above to update coverage; the result pages below use the latest report-list total.', 'تختلف أعداد التغطية عن هذه النتائج. استخدم تحديث مساحة العمل أعلاه لتحديث التغطية؛ تستخدم صفحات النتائج أدناه أحدث إجمالي لقائمة البلاغات.')}</p>}
    <div className="evidence-toolbar"><div className="evidence-switch" role="group" aria-label={tx('Location groups', 'مجموعات المواقع')}>{groups.map(item => <button key={item.id} aria-pressed={group === item.id} disabled={unavailable} onClick={() => changeGroup(item.id)}>{item.label}<span>{counts[item.id]}</span></button>)}</div></div>
    {group === 'simulated' && <p className="map-simulation-note">{tx('Simulation only. These coordinates were labeled as simulated; they do not establish where damage occurred.', 'للمحاكاة فقط. صُنفت هذه الإحداثيات كمحاكاة؛ ولا تثبت مكان وقوع الضرر.')}</p>}
    <div className={'evidence-layout'+(streetActive?' street-map-expanded':'')}>
      <div className="evidence-map-column">
        <StreetMapPanel key={sessionKey+'|'+group} lang={lang} group={group} connected={connected} busy={busy} queryKey={pinQueryKey} searchActive={Boolean(searchQuery)} resetVersion={streetReset} onViewingMap={setStreetActive} loadPins={loadPins} labelStatus={labelStatus} onOpen={onOpen} fallback={visible.length > 0 && group !== 'unlocated' && points.length > 0 && <div className={'coordinate-map ' + (group === 'simulated' ? 'is-simulation' : '')} role="group" aria-label={tx('Report coordinate diagram', 'مخطط إحداثيات البلاغات')}>
          <div className="map-context"><span>{group === 'simulated' ? tx('SIMULATED COORDINATES', 'إحداثيات محاكاة') : tx('SAVED COORDINATES', 'إحداثيات محفوظة')}</span><small>{tx('North ↑ · East → · Auto-fit to this page', 'الشمال ↑ · الشرق → · ضبط حسب هذه الصفحة')}</small></div>
          <div className="coordinate-canvas" dir="ltr">
            {selectedPoint && <svg className="map-crosshair" viewBox="0 0 800 500" preserveAspectRatio="none" aria-hidden="true"><path d={`M ${selectedPoint.x} 0 V 500 M 0 ${selectedPoint.y} H 800`}/><circle cx={selectedPoint.x} cy={selectedPoint.y} r="29"/></svg>}
            {points.map((point, index) => <button key={point.report.id} disabled={unavailable} className={'map-marker ' + (selected?.id === point.report.id ? 'selected' : '')} style={{left:`${point.x / 8}%`, top:`${point.y / 5}%`}} aria-pressed={selected?.id === point.report.id} aria-label={tx('Select pin ', 'اختر النقطة ') + (index + 1) + tx(', report ', '، البلاغ ') + point.report.id} onClick={() => selectReport(point.report.id)}>{index + 1}</button>)}
          </div><p className="map-legend">{tx('Numbers match the list below. Pins can overlap; every report is selectable in the list. Color only marks your selection.', 'الأرقام تطابق القائمة أدناه. قد تتداخل النقاط؛ يمكنك اختيار أي بلاغ من القائمة. اللون يميز اختيارك فقط.')}</p>
        </div>}/>
        {!visible.length ? <div className="map-empty-state" role="status"><MapPin size={30}/><h2>{emptyTitle}</h2><p>{!connected ? tx('Use Connect your workspace above. The guide is available without connecting.', 'استخدم اتصل بمساحة العمل أعلاه. الدليل متاح دون اتصال.') : loadFailed ? tx('Use Retry map above or change the filters. No report list was loaded.', 'استخدم إعادة تحميل الخريطة أعلاه أو غيّر التصفية. لم تُحمّل قائمة البلاغات.') : !total ? tx('Clear search or status filters, or create a new inspection. A photo does not automatically provide a GPS location.', 'امسح البحث أو تصفية الحالة، أو أنشئ فحصًا جديدًا. الصورة لا توفر موقع GPS تلقائيًا.') : tx('Try another location group or report page. Reports without a usable location can still be reviewed.', 'جرّب مجموعة مواقع أو صفحة أخرى. يمكنك مراجعة البلاغات التي بلا موقع صالح.')} </p>{connected && !busy && <div className="map-empty-actions">{groups.filter(item => item.id !== group && counts[item.id]).map(item => <button className="secondary" key={item.id} onClick={() => changeGroup(item.id)}>{item.label} ({counts[item.id]})</button>)}{(statusFilter || searchQuery) && <button className="secondary" onClick={() => {setQuery(''); onFilters('', '');}}>{tx('Clear filters', 'مسح عوامل التصفية')}</button>}<button className="text-button" onClick={onNewInspection}>{tx('New inspection', 'فحص جديد')}</button></div>}</div> : <>
          {group === 'unlocated' && <p className="map-unlocated-note">{tx('These reports have missing or invalid coordinates, or an unspecified location source. They remain available for image review, but cannot be pinned reliably.', 'إحداثيات هذه البلاغات مفقودة أو غير صالحة، أو مصدر موقعها غير محدد. تبقى صورها متاحة للمراجعة، لكن لا يمكن وضع نقاط موثوقة لها.')}</p>}
          {group !== 'unlocated' && points.length !== visible.length && <p className="map-unlocated-note">{tx('Some returned reports have unusable coordinates or location sources. They remain in the list without pins.', 'بعض البلاغات المعادة لها إحداثيات أو مصادر موقع غير صالحة. تبقى في القائمة دون نقاط.')}</p>}
          <p className="map-visible-count" role="status">{points.length} {tx('pins', 'نقاط')} · {visible.length} {tx('reports listed on this page', 'بلاغات في قائمة هذه الصفحة')}</p>
          <h2 className="map-list-heading" id="map-report-list" ref={listHeading} tabIndex={-1}>{tx('Reports in this group', 'بلاغات هذه المجموعة')} <span>({visible.length})</span></h2>
          <div className="map-records" role="group" aria-labelledby="map-report-list">{visible.map(report => {
            const pin = points.findIndex(point => point.report.id === report.id);
            return <button key={report.id} disabled={unavailable} aria-pressed={selected?.id === report.id} onClick={() => selectReport(report.id)}><span className="map-list-number">{pin >= 0 ? pin + 1 : <FileImage size={16}/>}</span><span className="map-list-report"><strong>{tx('Report ', 'بلاغ ')}<bdi>{report.id.slice(0,8).toUpperCase()}</bdi></strong><small>{locationSourceLabel(report.location_source, lang)} · {labelStatus(report.status)}</small></span><ArrowUpRight size={16}/></button>;
          })}</div>
        </>}
      </div>
      <aside className="evidence-inspector" aria-label={tx('Selected report details', 'تفاصيل البلاغ المختار')}>{selected ? <>
        <div className="mini-label">{tx('SELECTED REPORT', 'البلاغ المختار')}</div><h2 ref={inspector} tabIndex={-1}>{tx('Report ', 'بلاغ ')}<bdi>{selected.id.slice(0,8).toUpperCase()}</bdi></h2><p className="map-report-id"><bdi>{selected.id}</bdi></p>
        <ReportPhoto key={selected.id + sessionKey} id={selected.id} sessionKey={sessionKey} lang={lang}/>
        <dl><div><dt>{tx('Review status', 'حالة المراجعة')}</dt><dd className="evidence-source">{labelStatus(selected.status)}</dd></div><div><dt>{tx('Saved boxes', 'التحديدات المحفوظة')}</dt><dd className={inspectAnnotations(selected).kind==='ready' ? undefined : 'evidence-source'}>{inspectAnnotations(selected).kind==='ready' ? selected.detections!.length : annotationSummary(selected,lang)}</dd></div><div><dt>{tx('Location source', 'مصدر الموقع')}</dt><dd className="evidence-source">{locationSourceLabel(selected.location_source, lang)}</dd></div></dl>
        {validCoordinates ? <p className="evidence-coordinates">{tx('Latitude, longitude', 'خط العرض، خط الطول')}<br/><bdi>{selected.latitude!.toFixed(5)}, {selected.longitude!.toFixed(5)}</bdi></p> : <p className="evidence-help">{tx('No valid coordinate pair was saved.', 'لم يُحفظ زوج صالح من الإحداثيات.')}</p>}
        <p className="evidence-help">{group === 'simulated' ? tx('Simulation is for demonstrations, not evidence of a real location.', 'المحاكاة للعرض وليست دليلًا على موقع فعلي.') : group === 'unlocated' ? tx('Location cannot be verified from this record. Review the image without assuming a place.', 'لا يمكن التحقق من الموقع من هذا السجل. راجع الصورة دون افتراض مكان.') : selected.location_source === 'device_gps' ? tx('GPS was reported by the submitting source. It is not independently verified and may differ from the photo location.', 'أبلغ مصدر الإرسال عن GPS. لم يُتحقق منه بشكل مستقل وقد يختلف عن مكان الصورة.') : tx('Coordinates were entered manually. They are not verified GPS or a location inferred from the image.', 'أُدخلت الإحداثيات يدويًا. ليست GPS موثقًا ولا موقعًا مستنتجًا من الصورة.')}</p>
        <button className="primary" disabled={unavailable} onClick={() => onOpen(selected.id)}>{tx('Open image & review', 'فتح الصورة والمراجعة')}<ArrowUpRight size={17}/></button>
        <LocationLinks report={selected} lang={lang}/>
        <button className="text-button map-back-to-list" onClick={() => {listHeading.current?.focus(); listHeading.current?.scrollIntoView({block:'start'});}}>{tx('Back to report list', 'العودة إلى قائمة البلاغات')}</button>
      </> : <div className="empty"><FileImage size={30}/><strong>{tx('Select a report to inspect', 'اختر بلاغًا للاطلاع عليه')}</strong><span>{tx('Its image, review status and location source will appear here.', 'ستظهر هنا صورته وحالة مراجعته ومصدر موقعه.')}</span></div>}</aside>
    </div>
    {!loadFailed && <div className="evidence-pagination"><span>{tx('This page:', 'هذه الصفحة:')} {reports.length} {tx('loaded', 'محملة')} · {total} {coverage ? tx('matching in this location group', 'مطابقة في مجموعة المواقع هذه') : tx('matching across all location groups', 'مطابقة عبر كل مجموعات المواقع')}</span><div><button aria-label={tx('Previous map page', 'صفحة الخريطة السابقة')} disabled={unavailable || page <= 1} onClick={() => onPage(page - 1)}><ChevronLeft size={17}/></button><span>{tx('Page', 'الصفحة')} {page} / {Math.max(1, Math.ceil(total / 20))}</span><button aria-label={tx('Next map page', 'صفحة الخريطة التالية')} disabled={unavailable || page * 20 >= total} onClick={() => onPage(page + 1)}><ChevronRight size={17}/></button></div></div>}
    <details className="map-location-help"><summary>{tx('Where do locations come from?', 'من أين تأتي المواقع؟')}</summary><p>{tx('For a single photo, use Overview → New inspection → Browse files → Add location (optional). Enter both latitude and longitude, then label the source Manual or Simulated demo before creating the report. This screen does not collect GPS, extract it from photos or video frames, or add locations to saved reports.', 'للصورة الواحدة، استخدم نظرة عامة ← فحص جديد ← اختيار صور ← إضافة موقع (اختياري). أدخل خط العرض وخط الطول، ثم اختر المصدر يدوي أو محاكاة للعرض قبل إنشاء البلاغ. هذه الشاشة لا تجمع GPS ولا تستخرجه من الصور أو إطارات الفيديو ولا تضيف مواقع للبلاغات المحفوظة.')}</p><button className="secondary" disabled={unavailable} onClick={onNewInspection}>{tx('Go to New inspection', 'انتقل إلى فحص جديد')}</button></details>
  </section>;
}
