import {modelName} from './modelName';
import type {CSSProperties} from 'react';
import {useEffect, useRef, useState} from 'react';
import {GitCompareArrows, CheckCircle2} from 'lucide-react';
import type {Detection} from './annotations';
import {validAnnotations} from './annotations';
import './learning.css';

type Item = {id:string; name:string; sha256:string; family:string};
type Vote = {detection:Detection; votes:number; eligible_models:number; required_votes:number; model_ids:string[]};
type Result = {state:string; revision:string; width:number; height:number; consensus:Detection[]; agreements:Vote[]; disagreements:Vote[];
  models:{id:string; name:string; state:string; reason:string|null; detections:Detection[]; elapsed_ms:number}[]; reason:string|null};
type Props = {lang:string; reportId:string; revision:string; imageSrc:string|null; dirty:boolean; reviewBusy?:boolean;
  request:(path:string, options?:RequestInit)=>Promise<any>; onApply:(boxes:Detection[])=>void};

function validVoteBoxes(boxes:Detection[],width:number,height:number):boolean {
  if(!Number.isFinite(width)||!Number.isFinite(height)||width<=0||height<=0||!Array.isArray(boxes))return false;
  try{return validAnnotations(boxes,width,height)}catch{return false}
}

export default function ModelVote(props:Props) {
  const tx=(en:string,ar:string)=>props.lang==='ar'?ar:en;
  const [items,setItems]=useState<Item[]>([]); const [chosen,setChosen]=useState<string[]>([]);
  const [busy,setBusy]=useState(false); const [error,setError]=useState(''); const [result,setResult]=useState<Result|null>(null);
  const [showDisagreements,setShowDisagreements]=useState(true);
  const [emptyConfirmed,setEmptyConfirmed]=useState<Record<string,boolean>>({});
  const task=useRef<AbortController|null>(null);
  useEffect(()=>{
    const controller=new AbortController();task.current?.abort();task.current=null;setBusy(false);setResult(null);setError('');setEmptyConfirmed({});
    props.request('/api/models',{signal:controller.signal}).then(data=>{
      if(controller.signal.aborted)return;
      const unique:Item[]=data.items.filter((item:Item,index:number,array:Item[])=>array.findIndex(x=>x.sha256===item.sha256)===index);
      setItems(unique);
      const recommended=unique.filter(item=>/^(RTDETR_L_RDD2022|YOLO11s_RDD2022|YOLOv8m_RDD2022)/.test(item.name));
      setChosen((recommended.length>=2?recommended:unique).slice(0,3).map(item=>item.id));
    }).catch(reason=>{if(!controller.signal.aborted)setError(reason.message)});
    return ()=>{controller.abort();task.current?.abort();task.current=null};
  },[props.reportId,props.revision,props.request]);
  async function run() {
    if(busy||props.reviewBusy||props.dirty||chosen.length<2)return;
    const controller=new AbortController();task.current?.abort();task.current=controller;
    setBusy(true);setError('');setResult(null);setEmptyConfirmed({});
    const deadline=setTimeout(()=>controller.abort(),285000);
    try {
      const data=await props.request(`/api/reports/${props.reportId}/vote`,{method:'POST',signal:controller.signal,
        headers:{'Content-Type':'application/json'},body:JSON.stringify({model_ids:chosen,revision:props.revision})}) as Result;
      if(controller.signal.aborted)return;
      if(data.revision!==props.revision || !validVoteBoxes(data.consensus,data.width,data.height))throw Error(tx('Invalid vote response. Run the comparison again.','نتيجة التصويت غير صالحة. أعد تشغيل المقارنة.'));
      setResult(data);
    } catch(reason) {if(task.current===controller && !controller.signal.aborted)setError(reason instanceof Error?reason.message:String(reason));
      else if(task.current===controller)setError(tx('Voting took too long. Try two lighter models.','استغرق التصويت وقتًا طويلًا. جرّب نموذجين أخف.'));
    } finally {clearTimeout(deadline);if(task.current===controller)setBusy(false)}
  }
  const adoptionBlocked=busy||!!props.reviewBusy||props.dirty||result?.revision!==props.revision;
  function applyBoxes(boxes:Detection[],allowEmpty=false) {
    if(!result||adoptionBlocked||!validVoteBoxes(boxes,result.width,result.height)||(!boxes.length&&!allowEmpty))return;
    props.onApply(boxes.map(box=>({...box,box:[...box.box]})));
    setEmptyConfirmed({});
  }
  return <section className="detail-section vote-panel" style={{'--stagger': 1} as CSSProperties}>
    <div className="panel-heading"><div><div className="mini-label">{tx('SECOND OPINION','رأي ثانٍ')}</div><h3><GitCompareArrows size={20}/> {tx('Model voting','تصويت النماذج')}</h3></div><span className="pill">2–3 {tx('models','نماذج')}</span></div>
    <p className="muted">{tx('Compare the same saved image. Two models need agreement from both; three need two votes for the same damage type and location.','قارن الصورة المحفوظة نفسها. يحتاج نموذجان لاتفاقهما معًا؛ وتحتاج ثلاثة نماذج لصوتين لنوع الضرر وموقعه.')}</p>
    <details className="vote-picker"><summary>{tx('Choose voting models','اختيار نماذج التصويت')} · {chosen.length}/3</summary><div className="vote-options">{items.map(item=><label key={item.id}><input type="checkbox" checked={chosen.includes(item.id)} disabled={busy || (!chosen.includes(item.id)&&chosen.length>=3)} onChange={event=>setChosen(old=>event.target.checked?[...old,item.id]:old.filter(id=>id!==item.id))}/><span title={item.name}>{modelName(item.name)}<small>{item.family.toUpperCase()} · {item.sha256.slice(0,10)}</small></span></label>)}</div></details>
    {props.dirty&&<p className="info">{tx('Save your review before running a new vote.','احفظ المراجعة قبل إجراء تصويت جديد.')}</p>}
    <button className={"secondary"+(busy?" is-busy":"")} onClick={()=>void run()} disabled={busy || props.reviewBusy || props.dirty || chosen.length<2}>{busy?tx('Models are comparing…','جارٍ مقارنة النماذج…'):tx('Run model vote','تشغيل تصويت النماذج')}</button>
    {busy&&<p role="status" className="muted is-busy">{tx('Models run one at a time to limit memory. Keep this report open. Live recognition waits during voting. Each model has a 90-second limit.','تعمل النماذج بالتتابع لتقليل الذاكرة. أبقِ البلاغ مفتوحًا. ينتظر التعرف المباشر أثناء التصويت. الحد الأقصى 90 ثانية لكل نموذج.')}</p>}
    {error&&<p role="alert" className="inline-error">{error}</p>}
    {result&&<div className="vote-results">
      <div className="learning-stats"><div><strong>{result.agreements.length}</strong><span>{tx('Agreed regions','مناطق متفق عليها')}</span></div><div><strong>{result.disagreements.length}</strong><span>{tx('Need another look','تحتاج فحصًا إضافيًا')}</span></div></div>
      {result.state!=='completed'&&<p role="alert" className="info">{tx('One or more models failed. No voting verdict was produced. Inspect the individual results below.','تعذر تشغيل نموذج أو أكثر. لم تُنتج نتيجة تصويت. راجع النتائج الفردية أدناه.')}</p>}
      {result.state==='completed'&&props.imageSrc&&<><label className="check-line"><input type="checkbox" checked={showDisagreements} onChange={event=>setShowDisagreements(event.target.checked)}/>{tx('Show disagreement regions (amber)','إظهار مناطق الاختلاف (كهرماني)')}</label><div className="annotation-stage vote-image"><img src={props.imageSrc} alt={tx('Model vote on saved report','تصويت النماذج على البلاغ المحفوظ')}/><svg viewBox={`0 0 ${result.width} ${result.height}`} aria-label={tx('Model agreement overlay','طبقة اتفاق النماذج')}>{[...result.agreements,...(showDisagreements?result.disagreements:[])].map((entry,index)=><g key={index}><rect className={entry.votes>=entry.required_votes?'vote-agreed':'vote-disagreed'} x={entry.detection.box[0]} y={entry.detection.box[1]} width={entry.detection.box[2]-entry.detection.box[0]} height={entry.detection.box[3]-entry.detection.box[1]}/><text x={entry.detection.box[0]+4} y={Math.max(22,entry.detection.box[1]-6)} fontSize={Math.max(16,result.width/45)} fill="#fff" stroke="#111" strokeWidth="2" paintOrder="stroke">{entry.detection.class_id} · {entry.votes}/{entry.eligible_models} · {tx("need", "المطلوب")} {entry.required_votes}</text></g>)}</svg></div></>}
      <p className="muted">{tx('You can use any completed model, even when the others disagree. Its result replaces all draft boxes. Inspect every box and save your review separately.','يمكنك استخدام أي نموذج مكتمل حتى عند اختلاف النماذج الأخرى. تستبدل نتيجته جميع تحديدات المسودة. افحص كل تحديد ثم احفظ المراجعة بشكل منفصل.')}</p>
      <div className="vote-model-results">{result.models.map(model=>{
        const completed=model.state==='completed';
        const valid=completed&&validVoteBoxes(model.detections,result.width,result.height);
        const empty=valid&&model.detections.length===0;
        return <div key={model.id}><strong title={model.name}>{modelName(model.name)}</strong><span>{completed&&Array.isArray(model.detections)?`${model.detections.length} ${tx('boxes','تحديدات')} · ${(model.elapsed_ms/1000).toFixed(1)}s`:tx('Did not finish','لم يكتمل')}</span>
          {!completed&&<small>{model.reason?.startsWith('worker_timeout_') ? tx('This model exceeded the 90-second limit. You can still choose a completed model below.','تجاوز هذا النموذج حد 90 ثانية. يمكنك اختيار أحد النماذج المكتملة أدناه.') : model.reason}</small>}
          {completed&&!valid&&<p className="inline-error" role="alert">{tx('This model returned invalid boxes. Run the comparison again before using its result.','أعاد هذا النموذج تحديدات غير صالحة. أعد المقارنة قبل استخدام نتيجته.')}</p>}
          {empty&&<label className="check-line"><input type="checkbox" checked={!!emptyConfirmed[model.id]} disabled={adoptionBlocked} onChange={event=>setEmptyConfirmed(old=>({...old,[model.id]:event.target.checked}))}/>{tx('I inspected the image and want to remove all draft boxes. No detections does not prove a clean road.','فحصت الصورة وأريد إزالة جميع تحديدات المسودة. غياب التحديدات لا يثبت سلامة الطريق.')}</label>}
          {completed&&<button className="secondary" disabled={adoptionBlocked||!valid||(empty&&!emptyConfirmed[model.id])} aria-label={tx('Replace draft boxes with the result from ','استبدال تحديدات المسودة بنتيجة ')+modelName(model.name)} onClick={()=>applyBoxes(model.detections,empty&&!!emptyConfirmed[model.id])}><CheckCircle2 size={16}/>{empty?tx('Replace draft with no boxes','إفراغ تحديدات المسودة'):tx('Replace draft with this model','استبدال المسودة بهذا النموذج')}</button>}
        </div>;
      })}</div>
      {result.state==='completed'&&result.consensus.length>0&&<button className="secondary" disabled={adoptionBlocked} onClick={()=>applyBoxes(result.consensus)}><CheckCircle2 size={16}/>{tx('Replace draft boxes with agreement','استبدال تحديدات المسودة بالمناطق المتفق عليها')}</button>}
      <p className="muted">{tx('Agreement can still be wrong. Missing agreement does not prove a clean road. Your saved review is unchanged until you edit and save it. Voting scores are not accuracy.','قد يكون الاتفاق خاطئًا. غياب الاتفاق لا يثبت سلامة الطريق. لا تتغير مراجعتك المحفوظة حتى تعدلها وتحفظها. درجات التصويت ليست قياسًا للدقة.')}</p>
    </div>}
  </section>;
}
