import {useEffect,useRef,useState} from 'react';

type Result={candidate_reports:number;threshold:number;matches:{report_id:string;similarity:number;distance_m:number}[]};
type Props={lang:string;reportId:string;revision:string;edited:boolean;hasGps:boolean;hasBoxes:boolean;request:(path:string,options?:RequestInit)=>Promise<any>};
export default function DuplicateSearch({lang,reportId,revision,edited,hasGps,hasBoxes,request}:Props){
  const tx=(en:string,ar:string)=>lang==='ar'?ar:en;
  const [result,setResult]=useState<Result|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const controller=useRef<AbortController|null>(null);
  useEffect(()=>()=>controller.current?.abort(),[]);
  async function search(){
    const task=new AbortController();controller.current=task;setBusy(true);setError('');setResult(null);
    try{const value=await request(`/api/reports/${reportId}/duplicates/search`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision}),signal:task.signal});if(!task.signal.aborted)setResult(value)}
    catch(reason){if(!task.signal.aborted)setError(reason instanceof Error?reason.message:String(reason))}
    finally{if(!task.signal.aborted)setBusy(false)}
  }
  return <section className="priority-explanation" aria-label={tx('Nearby damage search','البحث عن أضرار قريبة')}>
    <h3>{tx('Same damage, another report?','نفس الضرر في بلاغ آخر؟')}</h3>
    <p className="muted">{tx('Compare damage crops with DINOv2 among open reports within 50 m. Runs when you ask; the first search may take longer.','قارن مناطق الضرر باستخدام DINOv2 مع البلاغات المفتوحة ضمن 50 مترًا. يعمل عند الطلب؛ قد يستغرق البحث الأول وقتًا أطول.')}</p>
    <button className="secondary" disabled={busy||edited||!hasGps||!hasBoxes} onClick={search}>{busy?tx('Comparing nearby damage…','جارٍ مقارنة الأضرار القريبة…'):tx('Find nearby matches','البحث عن تطابقات قريبة')}</button>
    {(edited||!hasGps||!hasBoxes)&&<p className="muted">{edited?tx('Save your changes first.','احفظ التغييرات أولًا.'):!hasGps?tx('This report needs coordinates; add them when uploading a location-enabled photo.','يحتاج البلاغ إلى إحداثيات؛ أضفها عند رفع صورة مع موقع.'):tx('Save at least one damage box first.','احفظ تحديد ضرر واحدًا على الأقل أولًا.')}</p>}
    {error&&<p role="alert">{error}</p>}
    {result&&<div role="status"><p>{result.candidate_reports} {tx('nearby open reports checked','بلاغات مفتوحة قريبة تم فحصها')}</p>{result.matches.map(m=><p key={m.report_id}><code>{m.report_id.slice(0,8)}</code> · {(m.similarity*100).toFixed(1)}% {tx('crop similarity','تشابه مناطق الضرر')} · {m.distance_m} m</p>)}{!result.matches.length&&<p>{tx('No matches above the experimental threshold. This does not prove that no duplicate exists.','لا توجد تطابقات تتجاوز الحد التجريبي. هذا لا يثبت عدم وجود تكرار.')}</p>}</div>}
    <small className="muted">{tx('Experimental similarity threshold 0.80, not calibrated on your local roads. Suggestions never merge reports automatically; simulated and real locations are compared separately.','حد التشابه التجريبي 0.80 غير معاير على طرقكم المحلية. الاقتراحات لا تدمج البلاغات تلقائيًا؛ تُقارن المواقع الحقيقية والمحاكاة بشكل منفصل.')}</small>
  </section>
}
