import type {CSSProperties} from 'react';
import {useCallback, useEffect, useRef, useState, useSyncExternalStore} from 'react';
import {motionEnabled, motionQuery, subscribeMotion} from './motionPreference';
import {googleMapsUrl} from './reportLocation';
import type {PointerEvent} from 'react';
import {canReviewTransition, reviewPayload, reviewStatuses} from './reviewWorkflow';
import {dragBox, validAnnotations} from './annotations';
import {currentMedia, currentResult} from './currentTask';
import type {Detection} from './annotations';
import LiveRecognition from './LiveRecognition';
import ModelLibrary from './ModelLibrary';
import ModelVote from './ModelVote';
import TrainingApproval from './TrainingApproval';
import Learning from './Learning';
import RoadScene from './RoadScene';
import PriorityExplanation from './PriorityExplanation';
import DuplicateSearch from './DuplicateSearch';
import BatchUpload from './BatchUpload';
import {MAX_BATCH_FILES, prepareBatch, retryFailed, runBatch} from './batchUpload';
import type {BatchItem} from './batchUpload';
import {Activity, ArrowUpRight, Camera, CheckCircle2, ChevronLeft, ChevronRight, ClipboardList, CloudUpload, FileImage, Globe2, History, LayoutDashboard, LockKeyhole, LogOut, MapPin, Pencil, Plus, RefreshCw, ScanLine, Search, Settings2, ShieldCheck, Pause, Play, Square, SwitchCamera, Trash2, Upload, X, AlertTriangle, Image as ImageIcon} from 'lucide-react';

type HistoryEvent = {from: string | null; to: string; actor: string; at: string};
type AuditEvent = {actor: string; action: string; at: string; details: {manual_detections?: boolean}};
type Report = {id: string; revision:string; source_metadata?:{initial_prediction?:{detections?:Detection[];elapsed_ms?:number}}; status: string; created_at: string; score: number | null; inference_state: string; detections: Detection[]; duplicates: {report_id: string; similarity: number}[]; image_url: string; note: string; model_version: string; reviewer?: string; history?: HistoryEvent[]; latitude?: number | null; longitude?: number | null; location_source?: string};
type Stats = {total: number; needs_review: number; high_priority: number; by_status: Record<string, number>};
type Health = {status: string; model: string; model_reason: string; demo?:boolean; demo_token?:string|null;max_upload_mb?:number};
type Desktop = {getToken: () => Promise<string | null>; selectModel: () => Promise<{ok: boolean; message: string}>};
declare global {interface Window {roadscanDesktop?: Desktop}}
const initials = (s: string) => s.slice(0, 8).toUpperCase();
const names: Record<string, [string, string]> = {D00: ['Longitudinal crack', 'شق طولي'], D10: ['Transverse crack', 'شق عرضي'], D20: ['Alligator crack', 'تشققات شبكية'], D40: ['Pothole', 'حفرة'], OTHER:['Other surface damage','أضرار سطحية أخرى']};
const statusArabic: Record<string, string> = {'New': 'جديد', 'Needs Review': 'بانتظار المراجعة', Confirmed: 'مؤكد', Assigned: 'مسند', Resolved: 'مغلق', Duplicate: 'مكرر'};
const displayDate = (s: string, lang: string) => new Date(/[Zz]|[+-]\d\d:\d\d$/.test(s) ? s : s + 'Z').toLocaleString(lang === 'ar' ? 'ar-SA' : 'en-GB');

export default function App() {
  const [lang, setLang] = useState(() => localStorage.getItem('roadscan_language') === 'ar' ? 'ar' : 'en');
  const tx = (en: string, ar: string) => lang === 'ar' ? ar : en;
  const systemReduced = useSyncExternalStore(subscribeMotion, () => window.matchMedia(motionQuery).matches, () => true);
  const [motionOverride, setMotionOverride] = useState<boolean | null>(null);
  const playing = motionEnabled(motionOverride, systemReduced);
  const toggleMotion = () => setMotionOverride(!playing);
  const languageRef=useRef(lang);languageRef.current=lang;
  const labelStatus = (s: string) => lang === 'ar' ? statusArabic[s] || s : s;
  const [token, setToken] = useState(() => sessionStorage.getItem('roadscan_token') || '');
  const [draftToken, setDraftToken] = useState('');
  const [connected, setConnected] = useState(false);
  const [health, setHealth] = useState<Health | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [recent, setRecent] = useState<Report[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState('');
  const [search, setSearch] = useState('');
  const [searchDraft, setSearchDraft] = useState('');
  const [selected, setSelected] = useState<Report | null>(null);
  const [pendingReport,setPendingReport]=useState<string|null>(null);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [section, setSection] = useState<'dashboard' | 'reports' | 'settings' | 'live' | 'learning'>('dashboard');
  const [autoStartLive, setAutoStartLive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [batch, setBatch] = useState<BatchItem[]>([]);
  const batchRunning = useRef(false);
  const batchStop = useRef(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [note, setNote] = useState('');
  const [status, setStatus] = useState('Needs Review');
  const [boxes, setBoxes] = useState<Detection[]>([]);
  const [edited, setEdited] = useState(false);
  const [drawMode, setDrawMode] = useState(false);
  const [showAnnotations, setShowAnnotations] = useState(true);
  const [damageClass, setDamageClass] = useState('D00');
  const [dimensions, setDimensions] = useState([0, 0]);
  const [dragStart, setDragStart] = useState<number[] | null>(null);
  const [dragEnd, setDragEnd] = useState<number[] | null>(null);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [facing, setFacing] = useState<'environment' | 'user'>('environment');
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const selectionGeneration = useRef(0);
  const refreshGeneration = useRef(0);
  const sessionGeneration = useRef(0);
  const cameraGeneration = useRef(0);
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [locationSource, setLocationSource] = useState('manual');

  useEffect(() => {document.documentElement.lang = lang; document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'; localStorage.setItem('roadscan_language', lang)}, [lang]);
  const request = useCallback(async (path: string, options: RequestInit = {}, override?: string) => {
    const headers = new Headers(options.headers);
    if (override ?? token) headers.set('X-API-Key', override ?? token);
    const response = await fetch(path, {...options, headers});
    if (!response.ok) {
      let reason = `Request failed (${response.status})`;
      try {const body = await response.json(); reason = typeof body.detail === 'string' ? body.detail : Array.isArray(body.detail) ? body.detail.map((d: {msg: string}) => d.msg).join('; ') : reason} catch { /* preserve HTTP error */ }
      if (response.status === 401 || response.status === 403) reason += languageRef.current === 'ar' ? ' — تحقق من الرمز والصلاحيات في الإعدادات.' : ' — Check your token and role in Settings.';
      throw Object.assign(new Error(reason), {status: response.status});
    }
    return response.status === 204 ? null : response.json();
  }, [token]);
  const refresh = useCallback(async (key?: string, session = sessionGeneration.current) => {
    if (session !== sessionGeneration.current) return false;
    const generation = ++refreshGeneration.current;
    const params = new URLSearchParams({size: '20', page: String(page)});
    if (filter) params.set('status', filter);
    if (search) params.set('search', search);
    const result = await currentResult(() => Promise.all([request('/api/reports?' + params, {}, key), request('/api/stats', {}, key), request('/api/reports?size=5', {}, key)]), () => session === sessionGeneration.current && generation === refreshGeneration.current);
    if (!result.current) return false;
    const [data, counts, latest] = result.value;
    setReports(data.items); setTotal(data.total); setStats(counts); setRecent(latest.items); setConnected(true);
    return true;
  }, [request, page, filter, search]);
  useEffect(() => {
    let active=true;const session=sessionGeneration.current;
    fetch('/api/health').then(r => r.json()).then((value:Health) => {
      if(!active)return;setHealth(value);
      if(session===sessionGeneration.current && value.demo && value.demo_token==='roadscan-live-qa-local-only' && sessionStorage.getItem('roadscan_token')!==value.demo_token) {
        ++sessionGeneration.current;++refreshGeneration.current;setConnected(false);setError('');
        sessionStorage.setItem('roadscan_token',value.demo_token);setToken(value.demo_token);
      }
    }).catch(() => {if(active)setHealth(null)});
    return () => {active=false};
  }, []);
  useEffect(() => {const session = sessionGeneration.current; if (token) refresh(undefined, session).catch(e => {if (session === sessionGeneration.current) {setConnected(false); setError(e.message)}})}, [token, refresh]);
  useEffect(() => {const session = sessionGeneration.current; let active = true; window.roadscanDesktop?.getToken().then(t => {if (t && active && session === sessionGeneration.current) {sessionStorage.setItem('roadscan_token', t); setToken(t)}}).catch(() => {}); return () => {active = false}}, []);
  useEffect(() => {if (!file) {setPreview(null); return} const u = URL.createObjectURL(file); setPreview(u); return () => URL.revokeObjectURL(u)}, [file]);
  useEffect(() => {
    setImageSrc(null); setDimensions([0, 0]); setDrawMode(false);
    if (!selected) return;
    const controller = new AbortController(); let url = '';
    fetch(selected.image_url, {headers: {'X-API-Key': token}, signal: controller.signal}).then(r => {if (!r.ok) throw Error('Cannot load report image'); return r.blob()}).then(b => {if (!controller.signal.aborted) {url = URL.createObjectURL(b); setImageSrc(url)}}).catch(e => {if (!controller.signal.aborted) setError(e.message)});
    return () => {controller.abort(); if (url) URL.revokeObjectURL(url)};
  }, [selected?.id, token]);
  const stopCamera = useCallback(() => {++cameraGeneration.current; stream.current?.getTracks().forEach(t => t.stop()); stream.current = null; setCameraOpen(false)}, []);
  useEffect(() => () => {++sessionGeneration.current; ++cameraGeneration.current; stream.current?.getTracks().forEach(t => t.stop()); stream.current = null}, []);
  useEffect(() => {if (section !== 'dashboard') stopCamera()}, [section, stopCamera]);
  useEffect(() => {if (cameraOpen && video.current) {video.current.srcObject = stream.current; video.current.play().catch(() => {})}}, [cameraOpen, facing]);
  async function openCamera(nextFacing = facing) {
    stopCamera(); setError('');
    const generation = cameraGeneration.current;
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw Error('Camera unavailable');
      const result = await currentMedia(() => navigator.mediaDevices.getUserMedia({video: {facingMode: {ideal: nextFacing}}, audio: false}), () => generation === cameraGeneration.current);
      if (!result.current) return;
      stream.current = result.value; setFacing(nextFacing); setCameraOpen(true);
    } catch {if (generation === cameraGeneration.current) setError(tx('Camera unavailable. Allow camera access in your browser, or use Browse files.', 'الكاميرا غير متاحة. اسمح بالوصول في المتصفح أو استخدم اختيار ملف.'))}
  }
  function capture() {
    const v = video.current; if (!v?.videoWidth) return;
    const session = sessionGeneration.current;
    const c = document.createElement('canvas'); c.width = v.videoWidth; c.height = v.videoHeight; c.getContext('2d')!.drawImage(v, 0, 0);
    c.toBlob(b => {if (b && session === sessionGeneration.current) acceptFile(new File([b], `road-${Date.now()}.jpg`, {type: 'image/jpeg'}))}, 'image/jpeg', .9); stopCamera();
  }
  function acceptFile(f: File | null) {
    if (batch.length || batchRunning.current) {setError(tx('Clear the current photo batch before selecting another photo.', 'امسح مجموعة الصور الحالية قبل اختيار صورة أخرى.')); return}
    setError(''); if (!f) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(f.type) || f.size > (health?.max_upload_mb ?? 50) * 1024 * 1024) {setError(tx('Choose a JPEG, PNG or WebP image within the upload limit shown below (up to 25 megapixels).', 'اختر صورة JPEG أو PNG أو WebP ضمن حد الرفع المبين أدناه (حتى 25 ميجابكسل).')); return}
    setLatitude(''); setLongitude(''); setLocationSource('manual'); setFile(f);
  }
  function acceptFiles(files: File[]) {
    if (busy || batch.length || batchRunning.current) {setError(tx('Finish or clear the current selection first.', 'أكمل الاختيار الحالي أو امسحه أولاً.')); return}
    if (files.length < 2) {acceptFile(files[0] || null); return}
    if (files.length > MAX_BATCH_FILES) {setError(tx(`Choose at most ${MAX_BATCH_FILES} photos per batch. No files were selected.`, `اختر ${MAX_BATCH_FILES} صورة كحد أقصى لكل مجموعة. لم يتم اختيار أي ملف.`)); return}
    setBatch(prepareBatch(files, (health?.max_upload_mb ?? 50) * 1024 * 1024));
    setFile(null); setLatitude(''); setLongitude(''); setLocationSource('manual'); setError(''); setMessage('');
  }
  async function uploadBatch(retry = false) {
    if (!connected || busy || batchRunning.current) return;
    const session = sessionGeneration.current;
    const items = retry ? retryFailed(batch) : batch;
    batchRunning.current = true; batchStop.current = false; setBatch(items); setBusy(true); setError(''); setMessage('');
    try {
      await runBatch(items, async photo => {
        const body = new FormData(); body.append('photo', photo);
        const result = await request('/api/reports', {method: 'POST', body});
        if (typeof result?.id !== 'string' || !result.id) throw Error(tx('No report ID returned. Check the review queue before retrying.', 'لم يتم إرجاع رقم البلاغ. تحقق من قائمة المراجعة قبل إعادة المحاولة.'));
        return result.id;
      }, (index, item) => {if (session === sessionGeneration.current) setBatch(current => current.map((value, i) => i === index ? item : value))}, () => batchStop.current || session !== sessionGeneration.current);
      if (session === sessionGeneration.current) {
        setMessage(batchStop.current ? tx('Photo batch paused. Continue the remaining photos from Overview.', 'توقفت مجموعة الصور مؤقتاً. تابع الصور المتبقية من نظرة عامة.') : tx('Photo batch complete. Each file’s result is shown in Overview.', 'اكتملت معالجة المجموعة. تظهر نتيجة كل ملف في نظرة عامة.'));
        try {await refresh(undefined, session)} catch {setError(tx('Saved reports remain stored. Refresh the review queue to update its list.', 'تبقى البلاغات المحفوظة مخزنة. حدّث قائمة المراجعة لتحديث بياناتها.'))}
      }
    } finally {if (session === sessionGeneration.current) {batchRunning.current = false; setBusy(false)}}
  }
  async function chooseReport(id: string, session = sessionGeneration.current, discard = false) {
    if (session !== sessionGeneration.current) return;
    if (batchRunning.current) {setError(tx('Wait for the current photo batch to finish or stop it before opening a report.', 'انتظر اكتمال مجموعة الصور الحالية أو أوقفها قبل فتح بلاغ.')); return}
    if (!discard && selected && (edited || note !== (selected.note || '') || status !== selected.status)) {setPendingReport(id);return;}
    setPendingReport(null);
    const generation = ++selectionGeneration.current; setBusy(true); setError('');
    try {
      const result = await currentResult(() => Promise.all([request(`/api/reports/${id}`), request(`/api/reports/${id}/audit`)]), () => session === sessionGeneration.current && generation === selectionGeneration.current);
      if (!result.current) return;
      const [r, events] = result.value;
      setSelected(r); setShowAnnotations(true); setDrawMode(false); setStatus(r.status); setNote(r.note || ''); setBoxes(r.detections); setEdited(false); setAudit(events.items); setSection('reports');
    } catch (e) {setError(String(e instanceof Error ? e.message : e))} finally {if (session === sessionGeneration.current && generation === selectionGeneration.current) setBusy(false)}
  }
  async function upload() {
    if (!file) return; setBusy(true); setError(''); setMessage('');
    const session = sessionGeneration.current;
    try {
      const body = new FormData(); body.append('photo', file);
      if (latitude || longitude) {
        if (!latitude || !longitude || !Number.isFinite(Number(latitude)) || !Number.isFinite(Number(longitude)) || Math.abs(Number(latitude)) > 90 || Math.abs(Number(longitude)) > 180) throw Error(tx('Enter valid latitude and longitude together.', 'أدخل خط العرض وخط الطول ضمن النطاق الصحيح.'));
        body.append('latitude', latitude); body.append('longitude', longitude); body.append('location_source', locationSource);
      }
      const result = await currentResult(() => request('/api/reports', {method: 'POST', body}), () => session === sessionGeneration.current);
      if (!result.current) return;
      const r = result.value; setFile(null); setLatitude(''); setLongitude('');
      setMessage(tx('Report created. Ready for human review.', 'تم إنشاء البلاغ وهو جاهز للمراجعة.')); await chooseReport(r.id, session);
      try {await refresh(undefined, session)} catch {if (session === sessionGeneration.current) setError(tx('Report saved. Refresh the queue to load the latest list.', 'تم حفظ البلاغ. حدّث القائمة لعرض آخر البيانات.'))}
    } catch (e) {if (session === sessionGeneration.current) setError(String(e instanceof Error ? e.message : e))} finally {if (session === sessionGeneration.current) setBusy(false)}
  }
  async function save() {
    if (!selected) return; setBusy(true); setError(''); setMessage('');
    const session = sessionGeneration.current;
    try {
      const payload: Record<string, unknown> = reviewPayload(selected.status, status, note);
      payload.revision = selected.revision;
      if (edited) {if (!validAnnotations(boxes, dimensions[0], dimensions[1])) throw Error(tx('Correct box coordinates before saving.', 'صحح إحداثيات المربعات قبل الحفظ.')); payload.detections = boxes}
      const result = await currentResult(() => request(`/api/reports/${selected.id}`, {method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)}), () => session === sessionGeneration.current);
      if (!result.current) return;
      const r = result.value;
      setSelected(r); setShowAnnotations(true); setDrawMode(false); setStatus(r.status); setNote(r.note || ''); setBoxes(r.detections); setEdited(false); setMessage(tx('Review saved.', 'تم حفظ المراجعة.'));
      const events = await request(`/api/reports/${r.id}/audit`);
      if (session === sessionGeneration.current) setAudit(events.items);
      try {await refresh(undefined, session)} catch {if (session === sessionGeneration.current) setError(tx('Review saved. Refresh to load the latest activity.', 'تم حفظ المراجعة. حدّث الصفحة لعرض آخر النشاط.'))}
    } catch (e) {if (session === sessionGeneration.current) setError(String(e instanceof Error ? e.message : e))} finally {if (session === sessionGeneration.current) setBusy(false)}
  }
  async function connect() {
    const value = draftToken.trim(); if (!value) {setError(tx('Enter your access token.', 'أدخل رمز الوصول.')); return}
    const session = ++sessionGeneration.current; ++selectionGeneration.current;
    setBusy(true); setError('');
    try {if (!await refresh(value, session)) return; sessionStorage.setItem('roadscan_token', value); setToken(value); setDraftToken('')} catch (e) {if (session === sessionGeneration.current) setError(String(e instanceof Error ? e.message : e))} finally {if (session === sessionGeneration.current) setBusy(false)}
  }
  function disconnect() {batchStop.current = true; batchRunning.current = false; setBatch([]); ++sessionGeneration.current; ++selectionGeneration.current; ++refreshGeneration.current; stopCamera(); sessionStorage.removeItem('roadscan_token'); setToken(''); setConnected(false); setBusy(false); setReports([]); setRecent([]); setTotal(0); setStats(null); setSelected(null); setPendingReport(null); setAudit([]); setFile(null); setLatitude(''); setLongitude(''); setNote(''); setBoxes([]); setEdited(false); setMessage(''); setError('')}
  async function installModel() {if (!window.roadscanDesktop) return; const session = sessionGeneration.current; setBusy(true); try {const result = await currentResult(() => window.roadscanDesktop!.selectModel(), () => session === sessionGeneration.current); if (result.current) {const r = result.value; if (r.ok) setMessage(r.message); else setError(r.message)}} catch (e) {setError(String(e))} finally {if (session === sessionGeneration.current) setBusy(false)}}
  function point(e: PointerEvent<SVGSVGElement>) {const bounds = e.currentTarget.getBoundingClientRect(); return [(e.clientX - bounds.left) / bounds.width * dimensions[0], (e.clientY - bounds.top) / bounds.height * dimensions[1]]}
  function addBox(box: number[]) {setShowAnnotations(true);setBoxes(b => [...b, {class_id: damageClass, box, confidence: 1}]); setEdited(true)}
  function updateBox(index: number, update: Partial<Detection>) {setBoxes(b => b.map((d, i) => i === index ? {...d, ...update} : d)); setEdited(true)}
  const drag = dragStart && dragEnd ? dragBox(dragStart, dragEnd, dimensions[0], dimensions[1]) : null;
  const ready = health?.model === 'configured';
  const mapUrl = googleMapsUrl(selected?.latitude, selected?.longitude);
  const scoreValue = selected?.score;

  return <div className="shell" data-motion={playing ? 'full' : 'reduced'}>
    <aside className="sidebar">
      <a className="brand" href="#" onClick={e => {e.preventDefault(); setSection('dashboard')}} aria-label="RoadScan overview"><span className="brand-icon"><ScanLine size={24}/></span><span><strong>RoadScan<span className="brand-period">.</span></strong><small>{tx('ROAD INTELLIGENCE', 'ذكاء الطرق')}</small></span></a>
      <div className="nav-title">{tx('YOUR WORKSPACE', 'مساحة العمل')}</div>
      <nav aria-label={tx('Main navigation', 'التنقل الرئيسي')}>
        <button aria-current={section === 'dashboard' ? 'page' : undefined} className={'nav ' + (section === 'dashboard' ? 'active' : '')} onClick={() => setSection('dashboard')}><LayoutDashboard size={19}/>{tx('Overview', 'نظرة عامة')}</button>
        <button aria-current={section === 'live' ? 'page' : undefined} className={'nav ' + (section === 'live' ? 'active' : '')} onClick={() => {setAutoStartLive(false); setSection('live')}}><Camera size={19}/>{tx('Live recognition', 'التعرف المباشر')}</button>
        <button aria-current={section === 'reports' ? 'page' : undefined} className={'nav ' + (section === 'reports' ? 'active' : '')} onClick={() => setSection('reports')}><ClipboardList size={19}/>{tx('Review queue', 'قائمة المراجعة')}<span className="nav-count">{stats?.needs_review ?? '—'}</span></button>
        <button aria-current={section === 'learning' ? 'page' : undefined} className={'nav ' + (section === 'learning' ? 'active' : '')} onClick={() => setSection('learning')}><RefreshCw size={19}/>{tx('Learning', 'التعلّم')}</button>
        <button aria-current={section === 'settings' ? 'page' : undefined} className={'nav ' + (section === 'settings' ? 'active' : '')} onClick={() => setSection('settings')}><Settings2 size={19}/>{tx('Settings', 'الإعدادات')}</button>
      </nav>
      <div className="sidebar-note"><span className="mini-label">{tx('THE REVIEW LOOP', 'دورة المراجعة')}</span><div className="loop-line"><span>01</span>{tx('Capture', 'التقاط')}</div><div className="loop-line"><span>02</span>{tx('Inspect', 'فحص')}</div><div className="loop-line"><span>03</span>{tx('Prioritize', 'تحديد الأولوية')}</div></div>
      <div className="sidebar-bottom"><div className="security"><ShieldCheck size={19}/><div><strong>{tx('Local workspace', 'مساحة محلية')}</strong><small>{tx('Reports stored on this device', 'البلاغات محفوظة على هذا الجهاز')}</small></div></div><small className="version">{tx('Capstone · Human reviewed', 'مشروع تخرج · مراجعة بشرية')}</small></div>
    </aside>
    <main className="main">
      <header className="topbar"><div className="breadcrumb">RoadScan <ChevronRight size={14}/><span>{section === 'dashboard' ? tx('Overview', 'نظرة عامة') : section === 'reports' ? tx('Review queue', 'قائمة المراجعة') : section === 'live' ? tx('Live recognition', 'التعرف المباشر') : section === 'learning' ? tx('Learning', 'التعلّم') : tx('Settings', 'الإعدادات')}</span></div><div className="top-right"><button className="motion-toggle" aria-pressed={playing} aria-label={playing ? tx("Reduce animations", "تقليل الحركة") : tx("Enable animations", "تشغيل الحركة")} title={tx("Animations across the workspace", "الحركة في جميع أقسام مساحة العمل")} onClick={toggleMotion}>{playing ? <Pause size={15}/> : <Play size={15}/>}<span>{playing ? tx("Motion on", "الحركة مفعّلة") : tx("Motion off", "الحركة متوقفة")}</span></button><button className="language-button" onClick={() => setLang(lang === 'en' ? 'ar' : 'en')} aria-label={lang === 'en' ? 'Switch to Arabic' : 'Switch to English'}><Globe2 size={16}/>{lang === 'en' ? 'العربية' : 'English'}</button><span className={'dot ' + (connected ? 'green' : '')}/><span className="connection-label">{connected ? tx('Connected', 'متصل') : tx('Not connected', 'غير متصل')}</span><button className="icon-button" aria-label={tx('Refresh workspace', 'تحديث مساحة العمل')} disabled={!connected || busy} onClick={() => {setError(''); refresh().catch(e => setError(e.message))}}><RefreshCw size={17}/></button></div></header>
      <div className="content" key={section} data-screen={section}>
        {health?.demo && <p className="info">{tx('Presentation workspace · Synthetic reports · Connects automatically. Your real reports are in the separate workspace on port 8000.','مساحة عرض · بلاغات تجريبية · اتصال تلقائي. بلاغاتك الفعلية في مساحة منفصلة على المنفذ 8000.')}</p>}
        {pendingReport && <div className="alert unsaved-review-alert" role="alert"><span>{tx('You have unsaved review changes. Keep editing or discard them before opening another report.','لديك تعديلات غير محفوظة. تابع التحرير أو تجاهلها قبل فتح بلاغ آخر.')}</span><button onClick={()=>setPendingReport(null)}>{tx('Keep editing','متابعة التحرير')}</button><button disabled={busy || batchRunning.current} onClick={()=>void chooseReport(pendingReport,sessionGeneration.current,true)}>{tx('Discard and open','تجاهل وفتح')}</button></div>}
        {batchRunning.current && <div className="info batch-running" role="status"><span>{batchStop.current ? tx('Finishing the current photo, then stopping…', 'جارٍ إكمال الصورة الحالية ثم التوقف…') : tx('Photo batch is running one image at a time.', 'تُعالج مجموعة الصور صورة تلو الأخرى.')}</span><button onClick={() => setSection('dashboard')}>{tx('Show progress', 'عرض التقدم')}</button><button disabled={batchStop.current} onClick={() => {batchStop.current = true; setMessage(tx('Stopping after the current photo is saved or fails.', 'سيتم التوقف بعد حفظ الصورة الحالية أو فشلها.'))}}>{tx('Stop after current photo', 'توقف بعد الصورة الحالية')}</button></div>}
        {error && <div className="alert error" role="alert"><AlertTriangle size={18}/><span>{error}</span><button aria-label={tx('Dismiss error', 'إغلاق الخطأ')} onClick={() => setError('')}><X size={16}/></button></div>}
        {message && <div className="alert success" role="status"><CheckCircle2 size={18}/><span>{message}</span><button aria-label={tx('Dismiss notification', 'إغلاق التنبيه')} onClick={() => setMessage('')}><X size={16}/></button></div>}
        {!connected && <section className="connect"><div className="connect-icon"><LockKeyhole size={24}/></div><div><h2>{tx('Connect your workspace', 'اتصل بمساحة العمل')}</h2><p>{tx('Use your existing RoadScan access token to open your reports.', 'استخدم رمز الوصول الحالي لعرض بلاغات RoadScan.')}</p></div><div className="connect-row"><input aria-label={tx('Access token', 'رمز الوصول')} type="password" autoComplete="off" placeholder={tx('Paste your access token', 'الصق رمز الوصول')} value={draftToken} onChange={e => setDraftToken(e.target.value)} onKeyDown={e => e.key === 'Enter' && connect()}/><button className="primary" disabled={busy} onClick={connect}>{tx('Connect', 'اتصال')}<ArrowUpRight size={16}/></button></div><small>{tx('Kept for this browser session. Sent only to your local RoadScan server.', 'محفوظ لجلسة المتصفح الحالية ويرسل إلى خادم RoadScan المحلي فقط.')}</small></section>}
        {section === 'live' && <LiveRecognition lang={lang} connected={connected} ready={ready} sessionKey={token} autoStart={autoStartLive} request={request} onCapture={frame => {acceptFile(frame); setSection('dashboard'); setMessage(tx('Frame selected. Create a report when you are ready.', 'تم اختيار الإطار. أنشئ البلاغ عندما تكون جاهزًا.'))}}/>}
        {section === 'dashboard' && <>
          <section className="hero showcase-hero">
            <div className="hero-copy">
              <div className="eyebrow"><span className="hero-signal" aria-hidden="true"/>{tx('THE ROAD AHEAD', 'الطريق إلى الأمام')}</div>
              <h1>{tx('See the damage.', 'ارصد الضرر.')}<br/><span>{tx('Drive the change.', 'واصنع التغيير.')}</span></h1>
              <p>{tx('From a single frame to a better-informed decision. AI detection and human judgment, in one clear view.', 'من إطار واحد إلى قرار أوضح. كشف بالذكاء الاصطناعي ومراجعة بشرية في رؤية واحدة.')}</p>
              <div className="hero-actions"><button className="primary" disabled={!connected} onClick={() => setSection('live')}>{tx('Start live recognition', 'ابدأ التعرف المباشر')}<ArrowUpRight size={19}/></button><button className="secondary" disabled={!connected} onClick={() => setSection('reports')}>{tx('Open review queue', 'فتح قائمة المراجعة')}<ChevronRight size={17}/></button></div>
              <div className="hero-footnote"><ShieldCheck size={14}/>{tx('Stored locally. Reviewed by people.', 'محفوظ محلياً. يراجعه الإنسان.')}</div>
            </div>
            <RoadScene lang={lang} playing={playing} onToggle={toggleMotion}/>
          </section>
          <div className="stats"><div className="stat" style={{'--stagger': 1} as CSSProperties}><span>{tx('Total reports', 'إجمالي البلاغات')}</span><strong>{connected ? stats?.total ?? '—' : '—'}</strong><small>{tx('Across your workspace', 'في مساحة العمل')}</small><FileImage className="stat-icon" size={22}/></div><div className="stat" style={{'--stagger': 2} as CSSProperties}><span>{tx('Needs review', 'بانتظار المراجعة')}</span><strong>{connected ? stats?.needs_review ?? '—' : '—'}</strong><small>{tx('Ready for a human decision', 'جاهزة لقرار المراجع')}</small><ClipboardList className="stat-icon" size={22}/></div><div className="stat" style={{'--stagger': 3} as CSSProperties}><span>{tx('High priority', 'أولوية عالية')}</span><strong>{connected ? stats?.high_priority ?? '—' : '—'}</strong><small>{tx('Draft score ≥ 65 / 100', 'درجة مبدئية ≥ 65 / 100')}</small><Activity className="stat-icon" size={22}/></div></div>
          <div className="columns"><section className="panel capture-panel" style={{'--stagger': 4} as CSSProperties}><div className="panel-heading"><div><div className="mini-label">01 / {tx('CAPTURE', 'التقاط')}</div><h2>{tx('New inspection', 'فحص جديد')}</h2><p>{tx('A clear photo is the starting point.', 'صورة واضحة هي نقطة البداية.')}</p></div><span className={'pill ' + (ready ? 'ready' : '')}><span className="dot"/>{ready ? tx('Model ready', 'النموذج جاهز') : tx('Manual review', 'مراجعة يدوية')}</span></div>
            <input ref={input} aria-label={tx('Upload road photo', 'رفع صورة الطريق')} type="file" accept="image/jpeg,image/png,image/webp" multiple hidden onChange={e => {acceptFiles(Array.from(e.target.files || [])); e.target.value = ''}}/>
            {batch.length > 0 ? <BatchUpload items={batch} lang={lang} busy={busy || batchRunning.current} connected={connected} maxMb={health?.max_upload_mb ?? 50} start={uploadBatch} clear={() => {if (!busy && !batchRunning.current) setBatch([])}} open={id => void chooseReport(id)} review={() => setSection('reports')}/> : cameraOpen ? <div className="camera-view"><video ref={video} playsInline muted autoPlay/><div className="camera-controls"><button onClick={() => openCamera(facing === 'environment' ? 'user' : 'environment')}><SwitchCamera size={17}/>{tx('Switch', 'تبديل')}</button><button className="primary" onClick={capture}><Camera size={17}/>{tx('Capture', 'التقاط')}</button><button onClick={stopCamera}><Square size={16}/>{tx('Stop', 'إيقاف')}</button></div></div> : preview ? <div className="photo-preview"><img src={preview} alt={tx('Selected road photo', 'صورة الطريق المحددة')}/><button onClick={() => {setFile(null);setLatitude('');setLongitude('');setLocationSource('manual')}}><X size={16}/>{tx('Remove photo', 'إزالة الصورة')}</button></div> : <div className="dropzone" onDragOver={e => e.preventDefault()} onDrop={e => {e.preventDefault(); acceptFiles(Array.from(e.dataTransfer.files))}}><div className="upload-icon"><CloudUpload size={30}/></div><strong>{tx('Your next inspection starts here', 'فحصك التالي يبدأ هنا')}</strong><span>{tx('Drop up to 20 photos · JPEG, PNG or WebP · ', 'اسحب حتى 20 صورة · JPEG أو PNG أو WebP · ')}{health?.max_upload_mb ?? 50} MB · 25 MP · 4K ✓</span><div className="capture-buttons"><button disabled={busy} onClick={() => input.current?.click()}><Upload size={16}/>{tx('Browse files', 'اختيار صور')}</button><button disabled={busy || !connected} onClick={() => {setAutoStartLive(true); setSection('live')}}><Camera size={16}/>{tx('Open camera', 'فتح الكاميرا')}</button><button disabled={busy} onClick={() => openCamera()}>{tx('Photo only', 'صورة فقط')}</button></div></div>}
            {file && <><details className="location-fields"><summary><MapPin size={14}/>{tx('Add location (optional)', 'إضافة موقع (اختياري)')}</summary><div className="field-grid"><label>{tx('Latitude', 'خط العرض')}<input aria-label={tx('Latitude', 'خط العرض')} type="number" min="-90" max="90" step="any" value={latitude} onChange={e => setLatitude(e.target.value)}/></label><label>{tx('Longitude', 'خط الطول')}<input aria-label={tx('Longitude', 'خط الطول')} type="number" min="-180" max="180" step="any" value={longitude} onChange={e => setLongitude(e.target.value)}/></label><label>{tx('Location source', 'مصدر الموقع')}<select aria-label={tx('Location source', 'مصدر الموقع')} value={locationSource} onChange={e => setLocationSource(e.target.value)}><option value="manual">{tx('Manual', 'يدوي')}</option><option value="simulated">{tx('Simulated demo', 'محاكاة للعرض')}</option></select></label></div></details><button disabled={!connected || busy} className="primary submit" onClick={upload}>{busy ? tx('Saving…', 'جارٍ الحفظ…') : ready ? tx('Analyze & create report', 'تحليل وإنشاء بلاغ') : tx('Create report for review', 'إنشاء بلاغ للمراجعة')}<ArrowUpRight size={17}/></button></>}
            <div className="privacy"><ShieldCheck size={14}/>{tx('EXIF removed on upload. Crop or blur faces and plates before submitting.', 'تزال بيانات EXIF عند الرفع. أخفِ الوجوه ولوحات المركبات قبل الإرسال.')}</div>
          </section><section className="panel activity-panel" style={{'--stagger': 5} as CSSProperties}><div className="panel-heading"><div><div className="mini-label">02 / {tx('REVIEW', 'مراجعة')}</div><h2>{tx('Recent activity', 'آخر النشاط')}</h2><p>{tx('The latest from your workspace.', 'أحدث البلاغات في مساحة العمل.')}</p></div><button className="text-button" onClick={() => setSection('reports')}>{tx('View all', 'عرض الكل')}<ArrowUpRight size={16}/></button></div>{!recent.length ? <div className="empty"><ImageIcon size={32}/><strong>{tx('A clean slate', 'بداية جديدة')}</strong><span>{tx('Your first inspection will appear here.', 'سيظهر الفحص الأول هنا.')}</span></div> : <div className="recent">{recent.map(r => <button key={r.id} disabled={busy} onClick={() => chooseReport(r.id)}><span className="report-avatar"><FileImage size={19}/></span><span><strong>{tx('Inspection', 'فحص')} {initials(r.id)}</strong><small>{displayDate(r.created_at, lang)}</small></span><span className={'status-chip status-' + r.status.replaceAll(' ', '-').toLowerCase()}>{labelStatus(r.status)}</span></button>)}</div>}<div className="model-note"><ScanLine size={17}/><span>{ready ? tx('Model outputs still require human review.', 'مخرجات النموذج تحتاج مراجعة بشرية.') : tx('No trained detector installed. Reports and manual annotations are available.', 'لم يثبت نموذج مدرب. البلاغات والتحديد اليدوي متاحان.')}</span></div></section></div>
        </>}
        {section === 'reports' && <>
          <div className="heading view-heading"><div><div className="eyebrow">02 / {tx('HUMAN REVIEW', 'المراجعة البشرية')}</div><h1>{tx('Every detail matters.', 'كل تفصيل مهم.')}</h1><p>{tx('Inspect the image. Record the evidence. Make the next step clear.', 'افحص الصورة ووثّق الأدلة وحدد الخطوة التالية.')}</p></div><span className="date-tag"><ShieldCheck size={16}/>{tx('Human in the loop', 'الإنسان في قلب القرار')}</span></div>
          <div className="review-layout"><section className="panel report-list" style={{'--stagger': 1} as CSSProperties}><div className="panel-heading"><h2>{tx('Reports', 'البلاغات')}<span className="count">{total}</span></h2></div><form className="search-row" onSubmit={e => {e.preventDefault(); setPage(1); setSearch(searchDraft.trim())}}><input aria-label={tx('Search reports', 'البحث في البلاغات')} placeholder={tx('Report ID or note…', 'رقم البلاغ أو الملاحظة…')} value={searchDraft} onChange={e => setSearchDraft(e.target.value)}/><button className="icon-button" aria-label={tx('Search', 'بحث')} disabled={busy}><Search size={17}/></button></form><select aria-label={tx('Filter reports by status', 'تصفية البلاغات حسب الحالة')} value={filter} disabled={busy} onChange={e => {setFilter(e.target.value); setPage(1)}}><option value="">{tx('All statuses', 'كل الحالات')}</option>{reviewStatuses.map(s => <option key={s} value={s}>{labelStatus(s)}</option>)}</select>
            {reports.length === 0 ? <div className="empty"><ClipboardList size={28}/><strong>{tx('No matching reports', 'لا توجد بلاغات مطابقة')}</strong><span>{tx('Try another filter or create an inspection.', 'جرّب تصفية أخرى أو أنشئ فحصًا.')}</span></div> : reports.map(r => <button key={r.id} disabled={busy} className={'report-item ' + (selected?.id === r.id ? 'chosen' : '')} onClick={() => chooseReport(r.id)}><span className="report-avatar"><FileImage size={17}/></span><span className="report-summary"><strong>{tx('Report', 'بلاغ')} {initials(r.id)}</strong><small>{labelStatus(r.status)}</small></span><span className="score">{r.score === null ? '—' : Math.round(r.score)}</span></button>)}
            <div className="pagination"><button className="icon-button" aria-label={tx('Previous page', 'الصفحة السابقة')} disabled={busy || page <= 1} onClick={() => setPage(p => p - 1)}><ChevronLeft size={17}/></button><span>{tx('Page', 'صفحة')} {page} / {Math.max(1, Math.ceil(total / 20))}</span><button className="icon-button" aria-label={tx('Next page', 'الصفحة التالية')} disabled={busy || page * 20 >= total} onClick={() => setPage(p => p + 1)}><ChevronRight size={17}/></button></div>
          </section><section className="panel detail" style={{'--stagger': 2} as CSSProperties}>{!selected ? <div className="empty selection-empty"><ScanLine size={44}/><strong>{tx('Take a closer look', 'ألقِ نظرة أدق')}</strong><span>{tx('Select a report to review its image, annotations and history.', 'اختر بلاغًا لمراجعة الصورة والتحديدات والسجل.')}</span></div> : <>
            <div className="panel-heading"><div><div className="mini-label">{tx('INSPECTION', 'فحص')} / {initials(selected.id)}</div><h2>{tx('Report details', 'تفاصيل البلاغ')}</h2><p>{displayDate(selected.created_at, lang)}</p></div><span className={'status-chip status-' + selected.status.replaceAll(' ', '-').toLowerCase()}>{labelStatus(selected.status)}</span></div>
            <div className="report-metadata"><span><ScanLine size={14}/>{selected.model_version === 'manual' ? tx('Human annotations', 'تحديدات بشرية') : selected.inference_state === 'not_configured' ? tx('Detector not configured', 'النموذج غير مهيأ') : selected.inference_state}</span><span>{tx('Draft priority', 'أولوية مبدئية')} <strong dir="ltr">{scoreValue === null || scoreValue === undefined ? '—' : Math.round(scoreValue) + ' / 100'}</strong></span></div>
            <div className="image-compare"><span>{showAnnotations ? tx('Annotated image', 'الصورة مع التحديدات') : tx('Original image', 'الصورة الأصلية')}</span><button className="secondary" aria-pressed={showAnnotations} disabled={!imageSrc || busy} onClick={()=>{setShowAnnotations(v=>!v);setDrawMode(false);setDragStart(null);setDragEnd(null)}}>{showAnnotations ? tx('Compare original', 'مقارنة بالأصل') : tx('Show annotations', 'عرض التحديدات')}</button></div><div className={'image-area ' + (drawMode ? 'drawing' : '')}>{imageSrc ? <div className="annotation-stage"><img src={imageSrc} alt={tx('Road report', 'صورة بلاغ الطريق')} id="report-image" onLoad={e => setDimensions([e.currentTarget.naturalWidth, e.currentTarget.naturalHeight])}/>{dimensions[0] > 0 && <svg style={{opacity:showAnnotations?1:0,pointerEvents:showAnnotations?'auto':'none'}} aria-hidden={!showAnnotations} aria-label={tx('Image annotations', 'تحديدات الصورة')} viewBox={`0 0 ${dimensions[0]} ${dimensions[1]}`} onPointerDown={e => {if (!drawMode || busy) return; e.currentTarget.setPointerCapture(e.pointerId); setDragStart(point(e)); setDragEnd(point(e))}} onPointerMove={e => {if (dragStart) setDragEnd(point(e))}} onPointerUp={e => {if (dragStart) {const b = dragBox(dragStart, point(e), dimensions[0], dimensions[1]); if (b && boxes.length < 100) addBox(b)} setDragStart(null); setDragEnd(null)}} onPointerCancel={() => {setDragStart(null); setDragEnd(null)}}>{boxes.map((d, i) => <g key={i}><rect x={d.box[0]} y={d.box[1]} width={Math.max(0, d.box[2] - d.box[0])} height={Math.max(0, d.box[3] - d.box[1])} className={'damage-box box-' + d.class_id}/><text x={d.box[0] + 4} y={Math.max(16, d.box[1] - 6)} fontSize={Math.max(12, dimensions[0] / 50)} fill="#e6f397" paintOrder="stroke" stroke="#0c181b" strokeWidth="2">{i + 1} · {d.class_id}</text></g>)}{drag && <rect x={drag[0]} y={drag[1]} width={drag[2] - drag[0]} height={drag[3] - drag[1]} className="damage-box pending-box"/>}</svg>}</div> : <span>{tx('Loading image…', 'جارٍ تحميل الصورة…')}</span>}</div>
            <div className="detail-section"><div className="section-title"><h3>{tx('Damage annotations', 'تحديدات الضرر')}<span className="count">{boxes.length}</span></h3><span className="unsaved">{edited ? tx('Unsaved changes', 'تغييرات غير محفوظة') : ''}</span></div><p className="muted">{tx('Draw on the image or enter pixel coordinates. New boxes are human annotations, not model predictions.', 'ارسم على الصورة أو أدخل إحداثيات البكسل. المربعات الجديدة تحديدات بشرية وليست تنبؤات النموذج.')}</p><div className="annotation-toolbar"><select aria-label={tx('New damage class', 'نوع الضرر الجديد')} value={damageClass} onChange={e => setDamageClass(e.target.value)}>{Object.entries(names).map(([id, values]) => <option key={id} value={id}>{id} · {tx(...values)}</option>)}</select><button className={drawMode ? 'secondary active-tool' : 'secondary'} disabled={busy || !dimensions[0]} onClick={() => {setShowAnnotations(true);setDrawMode(v => !v)}}><Pencil size={15}/>{drawMode ? tx('Finish drawing', 'إنهاء الرسم') : tx('Draw boxes', 'رسم المربعات')}</button><button className="secondary" disabled={busy || !dimensions[0] || boxes.length >= 100} onClick={() => addBox([Math.round(dimensions[0] * .25), Math.round(dimensions[1] * .25), Math.round(dimensions[0] * .75), Math.round(dimensions[1] * .75)])}><Plus size={15}/>{tx('Add box', 'إضافة مربع')}</button></div>
              {boxes.length === 0 && <p className="muted empty-annotations">{tx('No detections yet. Mark visible damage manually, or save a review note.', 'لا توجد تحديدات. حدد الضرر يدويًا أو احفظ ملاحظة المراجعة.')}</p>}
              {boxes.map((d, i) => <div className="annotation-row" key={i}><div className="annotation-row-heading"><strong><span className="class-tag">{i + 1}</span></strong><select aria-label={tx('Damage class', 'نوع الضرر') + ' ' + (i + 1)} disabled={busy} value={d.class_id} onChange={e => updateBox(i, {class_id: e.target.value})}>{Object.entries(names).map(([id, values]) => <option key={id} value={id}>{id} · {tx(...values)}</option>)}</select><button className="icon-button" disabled={busy} aria-label={tx('Remove annotation', 'حذف التحديد') + ' ' + (i + 1)} onClick={() => {setBoxes(b => b.filter((_, j) => i !== j)); setEdited(true)}}><Trash2 size={15}/></button></div><div className="coordinate-inputs">{['x1', 'y1', 'x2', 'y2'].map((axis, n) => <label key={axis}>{axis}<input aria-label={`${tx('Annotation', 'تحديد')} ${i + 1} ${axis}`} type="number" min="0" max={dimensions[n % 2]} step="1" disabled={busy} value={d.box[n]} onChange={e => {const b = [...d.box]; b[n] = Number(e.target.value); updateBox(i, {box: b})}}/></label>)}<label>{tx('Weight', 'الوزن')}<input aria-label={tx('Annotation weight', 'وزن التحديد') + ' ' + (i + 1)} type="number" min="0" max="1" step=".01" disabled={busy} value={d.confidence} onChange={e => updateBox(i, {confidence: Number(e.target.value)})}/></label></div></div>)}
              {edited && !validAnnotations(boxes, dimensions[0], dimensions[1]) && <p className="inline-error" role="alert">{tx('Boxes must stay inside the image. x2 > x1, y2 > y1; weight 0–1.', 'يجب أن تبقى المربعات داخل الصورة وأن يكون x2 > x1 و y2 > y1 والوزن بين 0 و1.')}</p>}<small className="muted">{tx('Priority uses a draft rule and annotation weights. It is not a validated severity assessment.', 'الأولوية تعتمد قاعدة مبدئية وأوزان التحديدات وليست تقييمًا معتمدًا للشدة.')}</small>
            </div>
            <DuplicateSearch key={"duplicates-"+selected.id+selected.revision} lang={lang} reportId={selected.id} revision={selected.revision} edited={edited} hasGps={selected.latitude!=null&&selected.longitude!=null} hasBoxes={selected.detections.length>0} request={request}/><PriorityExplanation key={selected.id+selected.revision} lang={lang} reportId={selected.id} edited={edited} request={request}/>{selected.source_metadata?.initial_prediction?.elapsed_ms!=null&&<p className="muted">{tx('CPU inference for this image','زمن التحليل على المعالج لهذه الصورة')}: <span dir="ltr">{selected.source_metadata.initial_prediction.elapsed_ms.toFixed(0)} ms</span></p>}<div className="detail-section"><h3>{tx('Possible duplicates', 'التكرارات المحتملة')}</h3>{selected.duplicates.length ? selected.duplicates.map(d => <div key={d.report_id} className="duplicate-row"><code>{initials(d.report_id)}</code><span>{Math.round(d.similarity * 100)}% {tx('image similarity', 'تشابه الصورة')}</span></div>) : <p className="muted">{tx('No duplicate suggestions.', 'لا توجد اقتراحات تكرار.')}</p>}<small className="muted">{tx('Unvalidated image similarity suggestions. A reviewer decides whether reports describe the same damage.', 'اقتراحات تشابه غير معتمدة. يقرر المراجع إن كانت البلاغات تصف الضرر نفسه.')}</small>{selected.latitude != null && <p className="location-note"><MapPin size={14}/><span dir="ltr">{selected.latitude}, {selected.longitude}</span> · {selected.location_source === 'simulated' ? tx('Simulated', 'محاكاة') : tx('Manually entered', 'إدخال يدوي')}</p>}{mapUrl && <div className="map-action"><a className="secondary" href={mapUrl} target="_blank" rel="noopener noreferrer"><MapPin size={16}/>{tx('Open in Google Maps', 'فتح في خرائط Google')}<ArrowUpRight size={15}/></a><small>{tx('Opens an external map with these coordinates.', 'يفتح خريطة خارجية بهذه الإحداثيات.')}</small></div>}</div>
            <div className="review-trail" aria-label={tx('Human review workflow','سير المراجعة البشرية')}><div><small>{tx('Model proposal','اقتراح النموذج')}</small><strong>{selected.source_metadata?.initial_prediction?.detections?.length??'—'} {tx('boxes','تحديدات')}</strong></div><span aria-hidden="true">→</span><div><small>{tx('Human review','مراجعة بشرية')}</small><strong>{boxes.length} {tx('current boxes','تحديدات حالية')}</strong></div><span aria-hidden="true">→</span><div><small>{tx('Next version','النسخة القادمة')}</small><strong>{tx('Approve below','اعتمد أدناه')}</strong></div></div>
            <ModelVote reviewBusy={busy} key={'vote-'+selected.id+'-'+token} lang={lang} reportId={selected.id} revision={selected.revision} imageSrc={imageSrc} dirty={edited || status!==selected.status || note!==(selected.note || '')} request={request} onApply={value=>{setBoxes(value);setEdited(true);setMessage(tx('Model result copied into the draft. Check every box, then save your review.','تم نسخ نتيجة النموذج للمسودة. تحقق من كل تحديد ثم احفظ المراجعة.'))}}/>
            <div className="detail-section decision-section"><h3>{tx('Review decision', 'قرار المراجعة')}</h3><label className="field-label" htmlFor="review-status">{tx('Status', 'الحالة')}</label><select id="review-status" aria-label={tx('Review status', 'حالة المراجعة')} disabled={busy} value={status} onChange={e => setStatus(e.target.value)}>{reviewStatuses.map(s => <option key={s} value={s} disabled={!canReviewTransition(selected.status, s)}>{labelStatus(s)}</option>)}</select><p className="muted">{tx('Confirm before assigning or resolving. Reopen a resolved report with Needs Review. Assigned records a workflow status; it does not dispatch a repair team.', 'أكد البلاغ قبل الإسناد أو الإغلاق. أعد فتح البلاغ المغلق باختيار بانتظار المراجعة. الإسناد حالة في النظام ولا يرسل فريق إصلاح.')}</p><label className="field-label" htmlFor="inspector-note">{tx('Inspector note', 'ملاحظة المراجع')}</label><textarea id="inspector-note" aria-label={tx('Inspector note', 'ملاحظة المراجع')} disabled={busy} maxLength={2000} value={note} onChange={e => setNote(e.target.value)} placeholder={tx('Findings, assignment details or reason for duplication…', 'النتائج أو تفاصيل الإسناد أو سبب التكرار…')} rows={3}/><div className="save-row"><span className="muted">{note.length} / 2000</span><button className="primary" disabled={!connected || busy || !canReviewTransition(selected.status, status) || (edited && !validAnnotations(boxes, dimensions[0], dimensions[1]))} onClick={save}>{busy ? tx('Saving…', 'جارٍ الحفظ…') : tx('Save review', 'حفظ المراجعة')}<CheckCircle2 size={17}/></button></div></div>
            <TrainingApproval key={'training-'+selected.id+'-'+selected.status+'-'+token} lang={lang} reportId={selected.id} revision={selected.revision} dirty={edited || status!==selected.status || note!==(selected.note || '')} empty={boxes.length===0} request={request}/>
            <details className="detail-section history-panel" open><summary><History size={16}/>{tx('Review history', 'سجل المراجعة')}<span className="count">{selected.history?.length ?? 0}</span></summary><ol className="timeline">{selected.history?.map((h, i) => <li key={i}><strong>{labelStatus(h.to)}</strong><small>{h.actor} · {displayDate(h.at, lang)}</small></li>)}</ol><details><summary>{tx('Audit events', 'أحداث التدقيق')}<span className="count">{audit.length}</span></summary>{audit.map((a, i) => <div className="audit-event" key={i}><code>{a.action}</code><span>{a.actor}{a.details.manual_detections ? tx(' · annotations updated', ' · تحديث التحديدات') : ''}</span><small>{displayDate(a.at, lang)}</small></div>)}</details></details>
          </>}</section></div>
        </>}
        {section === 'learning' && <Learning key={token} lang={lang} connected={connected} sessionKey={token} request={request}/>}
        {section === 'settings' && <><div className="heading view-heading"><div><div className="eyebrow">03 / {tx('CONFIGURATION', 'الإعدادات')}</div><h1>{tx('Your workspace, ready.', 'مساحة عملك جاهزة.')}</h1><p>{tx('Know what is configured before you rely on it.', 'تحقق مما هو مهيأ قبل الاعتماد عليه.')}</p></div></div><section className="panel settings-panel" style={{'--stagger': 1} as CSSProperties}><div className="setting-row"><div className="setting-icon"><ScanLine size={23}/></div><div><h2>{tx('Road damage detector', 'نموذج كشف ضرر الطريق')}</h2><p>{ready ? tx('A compatible local detector is loaded. Validate it on held-out images before reporting accuracy.', 'تم تحميل نموذج كشف محلي. اختبره على صور مستقلة قبل إعلان الدقة.') : tx('No trained detector is loaded. Upload, manual annotation and report review remain available.', 'لم يحمل نموذج كشف مدرب. الرفع والتحديد اليدوي والمراجعة متاحة.')}</p><small>D00 · D10 · D20 · D40 · OTHER (optional)</small></div><span className={'status-chip ' + (ready ? 'ready' : '')}>{ready ? tx('Loaded', 'محمل') : tx('Not installed', 'غير مثبت')}</span></div><ModelLibrary lang={lang} connected={connected} sessionKey={token} request={request} onChanged={async () => {const value=await fetch('/api/health').then(response => response.json());setHealth(value)}}/><div className="setting-row"><div className="setting-icon"><LockKeyhole size={22}/></div><div><h2>{tx('Workspace access', 'الوصول لمساحة العمل')}</h2><p>{tx('Your existing local access token protects reports. Shared role keys are supported; named local accounts are optional.', 'رمز الوصول المحلي يحمي البلاغات. مفاتيح الأدوار المشتركة مدعومة والحسابات المسماة اختيارية.')}</p></div></div><div className="team-credit"><strong>{tx('RoadScan · OLO AIEP · Track A','RoadScan · أكاديمية OLO · المسار A')}</strong><p dir="ltr">Feras Alyamani · Ahmed Salamah · Ahmed Alhejaili</p></div><button className="secondary" onClick={disconnect}><LogOut size={16}/>{tx('Disconnect', 'قطع الاتصال')}</button></section></>}
        <footer><span>{tx('RoadScan · A capstone prototype. All decisions require human review.', 'RoadScan · نموذج مشروع تخرج. جميع القرارات تتطلب مراجعة بشرية.')}</span><span>{tx('Observe. Review. Improve.', 'راقب. راجع. حسّن.')}</span></footer>
      </div>
    </main>
  </div>;
}
