import {modelName} from './modelName';
import {useEffect, useRef, useState} from 'react';
import {Upload, CheckCircle2, ScanLine, RefreshCw} from 'lucide-react';
import './models.css';

type ModelItem = {id:string;name:string;file:string;sha256:string;bytes:number;family:string;imgsz:number;classes:Record<string,string>;reported_metrics:Record<string,number>;metrics_source:string;checked:string;confidence_profile?:Record<string,number>;threshold_source?:string};
type Catalog = {items:ModelItem[];active_id:string;can_manage:boolean;available:boolean;warning:string|null;model_version:string};
type Props = {lang:string;connected:boolean;sessionKey:string;request:(path:string,options?:RequestInit)=>Promise<unknown>;onChanged:()=>Promise<void>};
const maxBytes=1600*1024*1024;

export default function ModelLibrary(props:Props) {
  const latest=useRef(props);latest.current=props;
  const tx=(en:string,ar:string)=>props.lang==='ar'?ar:en;
  const [catalog,setCatalog]=useState<Catalog|null>(null);
  const [busy,setBusy]=useState(false);
  const [notice,setNotice]=useState('');
  const [error,setError]=useState('');
  const [dragging,setDragging]=useState(false);
  const input=useRef<HTMLInputElement>(null);
  const generation=useRef(0);
  const controller=useRef<AbortController|null>(null);
  const current=(id:number)=>generation.current===id;
  async function refresh(signal?:AbortSignal) {
    const value=await latest.current.request('/api/models',{signal}) as Catalog;
    return value;
  }
  useEffect(()=>{
    const id=++generation.current;
    controller.current?.abort();controller.current=new AbortController();
    setCatalog(null);setBusy(false);setError('');setNotice('');
    if(props.connected) refresh(controller.current.signal).then(value=>{if(current(id))setCatalog(value)}).catch(reason=>{if(current(id) && !controller.current?.signal.aborted)setError(String(reason.message||reason))});
    return ()=>{++generation.current;controller.current?.abort()};
  },[props.sessionKey,props.connected]);
  async function act(operation:(signal:AbortSignal)=>Promise<string>) {
    if(busy || !catalog?.can_manage || !props.connected)return;
    const id=++generation.current;controller.current?.abort();
    const active=new AbortController();controller.current=active;
    setBusy(true);setError('');setNotice('');
    try {
      const message=await operation(active.signal);
      if(!current(id))return;
      const updated=await refresh(active.signal);if(!current(id))return;
      setCatalog(updated);setNotice(message);
      await latest.current.onChanged();
    } catch(reason) {
      if(current(id) && !active.signal.aborted)setError(reason instanceof Error?reason.message:String(reason));
    } finally {if(current(id))setBusy(false)}
  }
  function importFile(file:File|null) {
    if(!file)return;
    if(!/\.(pt|zip)$/i.test(file.name)){setError(tx('Choose a .pt model or a ZIP of models.','اختر نموذج .pt أو حزمة ZIP للنماذج.'));return}
    if(!file.size || file.size>maxBytes){setError(tx('Choose a non-empty package under 1600 MB.','اختر حزمة غير فارغة أصغر من 1600 ميجابايت.'));return}
    void act(async signal=>{
      const result=await latest.current.request('/api/models/import?'+new URLSearchParams({filename:file.name}),{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file,signal}) as {imported:ModelItem[];duplicates:string[];rejected:{file:string;reason:string}[]};
      const text=latest.current.lang==='ar'
        ? `تم استيراد ${result.imported.length} نموذج؛ ${result.duplicates.length} موجود مسبقًا و${result.rejected.length} غير متوافق. اختر «استخدام النموذج» للتفعيل.`
        : `Imported ${result.imported.length}; ${result.duplicates.length} already present; ${result.rejected.length} incompatible. Choose Use model to activate.`;
      return text+(result.rejected.length?' '+result.rejected.map(r=>r.file+': '+r.reason).join('; '):'');
    });
  }
  function activate(item:ModelItem) {
    void act(async signal=>{
      await latest.current.request('/api/models/'+encodeURIComponent(item.id)+'/activate',{method:'POST',signal});
      return latest.current.lang==='ar'?'النموذج النشط: '+item.name+' — جاهز دون إعادة تشغيل.':'Active model: '+item.name+' — ready without restarting.';
    });
  }
  const manage=props.connected && catalog?.can_manage && catalog.available;
  const ordered=[...(catalog?.items||[])].sort((a,b)=>Number(b.id===catalog?.active_id)-Number(a.id===catalog?.active_id));
  return <section className="model-library" aria-labelledby="model-library-title">
    <div className="panel-heading"><div><h2 id="model-library-title"><ScanLine size={20}/>{tx('Your model library','مكتبة النماذج')}</h2><p>{tx('Drop a checkpoint or a model ZIP, then choose Use model. No renaming, settings files or restart.','اسحب نموذجًا أو حزمة ZIP ثم اختر استخدام النموذج. دون إعادة تسمية أو تعديل ملفات أو إعادة تشغيل.')}</p></div></div>
    <p className="muted">{tx('Import checkpoints only from people you trust. Files stay on this RoadScan server. The previous model remains available, and a failed switch keeps it active.','استورد النماذج من مصادر موثوقة فقط. تبقى الملفات على خادم RoadScan. يظل النموذج السابق متاحًا وفعالًا إذا فشل التبديل.')}</p>
    {error && <p className="alert error" role="alert">{error}</p>}
    {notice && <p className="alert success" role="status">{notice}</p>}
    {catalog?.warning && <p className="info" role="status">{catalog.warning}</p>}
    {!props.connected && <p className="info">{tx('Connect your workspace to manage models.','اتصل بمساحة العمل لإدارة النماذج.')}</p>}
    {catalog && !catalog.can_manage && <p className="info">{tx('An administrator token is required to import or switch models.','يتطلب الاستيراد والتبديل رمز مسؤول.')}</p>}
    {catalog && !catalog.available && <p className="info">{tx('Open the real detector-enabled workspace to import models. The presentation workspace supports manual review.','افتح مساحة العمل الفعلية التي تدعم النموذج للاستيراد. مساحة العرض تدعم المراجعة اليدوية.')}</p>}
    <div className={'dropzone model-drop '+(dragging?'dragging':'')} onDragOver={event=>{event.preventDefault();if(manage && !busy)setDragging(true)}} onDragLeave={()=>setDragging(false)} onDrop={event=>{event.preventDefault();setDragging(false);if(manage && !busy)importFile(event.dataTransfer.files[0]||null)}}>
      <Upload size={27}/><strong>{busy?tx('Preparing models… Please keep this view open.','جارٍ تجهيز النماذج… أبقِ هذه الشاشة مفتوحة.'):tx('Drop your .pt model or .zip package here','اسحب نموذج .pt أو حزمة .zip هنا')}</strong>
      <span>{tx('YOLO / RT-DETR · Up to 700 MB per checkpoint · 1600 MB per package','YOLO / RT-DETR · حتى 700 ميجابايت للنموذج و1600 للحزمة')}</span>
      <input ref={input} type="file" accept=".pt,.zip" aria-label={tx('Model file','ملف النموذج')} hidden onChange={event=>{importFile(event.target.files?.[0]||null);event.target.value=''}}/>
      <button className="primary" disabled={!manage || busy} onClick={()=>input.current?.click()}><Upload size={16}/>{tx('Browse models','اختيار النماذج')}</button>
    </div>
    {busy && <p className="muted" role="status"><RefreshCw size={14}/>{tx('Large packages can take a few minutes. Camera analysis pauses while a model switches.','قد تستغرق الحزم الكبيرة دقائق. يتوقف التحليل مؤقتًا أثناء تبديل النموذج.')}</p>}
    <div className="model-cards">{ordered.map(item=><article key={item.id} className={'model-card '+(catalog?.active_id===item.id?'selected-model':'')}><div className="model-card-title"><h3 title={item.name}>{modelName(item.name,item.imgsz)}</h3>{catalog?.active_id===item.id && <span className="pill ready"><CheckCircle2 size={14}/>{tx('Active','نشط')}</span>}</div><p className="model-facts">{item.family.toUpperCase()} · {item.imgsz}px · {(item.bytes/1024/1024).toFixed(1)} MB</p><p className="model-classes">{Object.values(item.classes).join(' · ')}</p>{Object.keys(item.reported_metrics).length>0 && <p className="model-scores">{item.reported_metrics.mAP50!==undefined && <span>mAP50 <strong>{(item.reported_metrics.mAP50*100).toFixed(2)}%</strong></span>}{item.reported_metrics.mAP50_95!==undefined && <span>mAP50–95 <strong>{(item.reported_metrics.mAP50_95*100).toFixed(2)}%</strong></span>}</p>}<p className="muted model-score-source">{item.metrics_source}</p>{item.confidence_profile&&<p className="model-thresholds"><strong>{tx('Class thresholds','حدود الثقة لكل فئة')}</strong> · <span dir="ltr">{Object.entries(item.confidence_profile).map(([label,value])=>`${label} ${value.toFixed(3)}`).join(' · ')}</span><br/>{item.threshold_source}</p>}<details className="model-provenance"><summary>{tx("Checkpoint details","تفاصيل ملف النموذج")}</summary><p>{item.name}</p><p>{item.file}</p></details><small className="model-hash">SHA-256 {item.sha256.slice(0,12)}…</small><button className="secondary" disabled={!manage || busy || catalog?.active_id===item.id} onClick={()=>activate(item)}>{catalog?.active_id===item.id?tx('Currently in use','مستخدم حاليًا'):tx('Use model','استخدام النموذج')}</button></article>)}</div>
    <p className="info">{tx('Scores supplied with a checkpoint are reported results, not a new RoadScan accuracy test. Different datasets, splits and class counts prevent a fair direct comparison. mAP is not the percentage of images classified correctly. Every model still needs human review.','الدرجات المرفقة نتائج مقدمة وليست اختبار دقة جديدًا من RoadScan. اختلاف البيانات والتقسيم وعدد الفئات يمنع المقارنة المباشرة. mAP ليست نسبة الصور المصنفة صحيـحًا. تتطلب كل النماذج مراجعة بشرية.')}</p>
  </section>;
}

