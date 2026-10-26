import {useEffect, useRef, useState} from 'react';

type Analysis = {baseline:number|null;variations:{component:string;multiplier:number;score:number|null;difference:number|null}[]};
type Props = {lang:string;reportId:string;edited:boolean;request:(path:string,options?:RequestInit)=>Promise<any>};

export default function PriorityExplanation({lang,reportId,edited,request}:Props) {
  const tx=(en:string,ar:string)=>lang==='ar'?ar:en;
  const [analysis,setAnalysis]=useState<Analysis|null>(null);
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  const controller=useRef<AbortController|null>(null);
  useEffect(()=>()=>controller.current?.abort(),[]);
  async function compare(){
    controller.current?.abort();const task=new AbortController();controller.current=task;
    setBusy(true);setError('');
    try{const result=await request(`/api/reports/${reportId}/sensitivity`,{signal:task.signal});if(!task.signal.aborted)setAnalysis(result.analysis)}
    catch(reason){if(!task.signal.aborted)setError(reason instanceof Error?reason.message:String(reason))}
    finally{if(!task.signal.aborted)setBusy(false)}
  }
  const labels:Record<string,string>={type:tx('Damage type','نوع الضرر'),area:tx('Relative area','المساحة النسبية'),count:tx('Number of boxes','عدد التحديدات'),confidence:tx('Confidence / review weight','الثقة / وزن المراجعة')};
  return <details className="priority-explanation">
    <summary>{tx('How is this priority score calculated?','كيف تُحسب درجة الأولوية؟')}</summary>
    <p>{tx('A transparent 0–100 repair-priority rule: damage type 40%, relative box area 25%, number of boxes 20%, and average confidence/review weight 15%.','قاعدة واضحة لأولوية الإصلاح من 0 إلى 100: نوع الضرر 40٪، مساحة التحديد النسبية 25٪، عدد التحديدات 20٪، ومتوسط الثقة أو وزن المراجعة 15٪.')}</p>
    <p>{tx('Type has the largest weight because potholes and alligator cracks usually warrant more attention. Area measures visible coverage, not physical depth; the count contribution stops growing after five boxes. Review weights become human inputs when you edit boxes.','نوع الضرر له أكبر وزن لأن الحفر والتشققات التمساحية تستحق عادة اهتمامًا أكبر. المساحة تعبّر عن الجزء الظاهر لا عن العمق الفعلي، وتتوقف مساهمة العدد عن الزيادة بعد خمسة تحديدات. عند تعديل التحديدات تصبح أوزان المراجعة مدخلات بشرية.')}</p>
    <small>{tx('This is an estimate for human review, not a validated engineering severity rating. No detections means unscored, not a confirmed safe road.','هذا تقدير للمراجعة البشرية وليس تصنيفًا هندسيًا معتمدًا للشدة. عدم وجود تحديدات يعني غياب الدرجة، لا تأكيد سلامة الطريق.')}</small>
    {edited&&<p className="info">{tx('Save your changes to recalculate the score and sensitivity. The displayed score belongs to the saved report.','احفظ التغييرات لإعادة حساب الدرجة والحساسية. الدرجة المعروضة تخص البلاغ المحفوظ.')}</p>}
    <button className="secondary" disabled={busy||edited} onClick={compare}>{busy?tx('Comparing…','جارٍ المقارنة…'):tx('Check sensitivity: change each weight ±20%','فحص الحساسية: تغيير كل وزن ±20٪')}</button>
    {error&&<p role="alert" className="inline-error">{error}</p>}
    {analysis&&!edited&&<><p>{tx('Each weight changes separately and the total is normalized back to 100%. This checks one saved report; ranking across a dataset is reported separately.','يتغير كل وزن منفردًا ثم يُعاد تطبيع المجموع إلى 100٪. هذا الفحص لبلاغ محفوظ واحد؛ أما ترتيب مجموعة بيانات فيُعرض منفصلًا.')}</p><div className="priority-variations">{analysis.variations.map(row=><div key={row.component+row.multiplier}><span>{labels[row.component]} {row.multiplier<1?'−20%':'+20%'}</span><strong dir="ltr">{row.score==null?'—':row.score.toFixed(1)} / 100</strong><small dir="ltr">Δ {row.difference==null?'—':row.difference>0?'+'+row.difference:row.difference}</small></div>)}</div></>}
  </details>;
}
