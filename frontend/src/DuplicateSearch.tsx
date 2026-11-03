import {useEffect,useRef,useState} from 'react';
import {useNavigationWork} from './navigationWork';

type Mode='nearby'|'visual';
type Result={mode:Mode;candidate_reports:number;threshold:number;matches:{report_id:string;similarity:number;distance_m:number|null}[]};
type Props={lang:string;reportId:string;revision:string;edited:boolean;hasGps:boolean;hasBoxes:boolean;request:(path:string,options?:RequestInit)=>Promise<any>};
export default function DuplicateSearch({lang,reportId,revision,edited,hasGps,hasBoxes,request}:Props){
  const tx=(en:string,ar:string)=>lang==='ar'?ar:en;
  const [result,setResult]=useState<Result|null>(null),[busy,setBusy]=useState<Mode|null>(null),[error,setError]=useState('');
  useNavigationWork('analysis', false, busy!==null);
  const controller=useRef<AbortController|null>(null);
  useEffect(()=>()=>controller.current?.abort(),[]);
  async function search(mode:Mode){
    const task=new AbortController();controller.current=task;setBusy(mode);setError('');setResult(null);
    try{const value=await request(`/api/reports/${reportId}/duplicates/search`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision,mode}),signal:task.signal});if(!task.signal.aborted)setResult(value)}
    catch(reason){if(!task.signal.aborted)setError(reason instanceof Error?reason.message:String(reason))}
    finally{if(!task.signal.aborted)setBusy(null)}
  }
  const blocked=busy!==null||edited||!hasBoxes;
  return <section className="priority-explanation" aria-label={tx('Similar damage search','البحث عن أضرار مشابهة')}>
    <h3>{tx('Same damage, another report?','نفس الضرر في بلاغ آخر؟')}</h3>
    <p className="muted">{tx('Compare damage crops with DINOv2 among open reports: anywhere by appearance alone, or only within 50 m when this report has coordinates. Runs when you ask; the first search may take longer.','قارن مناطق الضرر باستخدام DINOv2 مع البلاغات المفتوحة: في أي مكان حسب المظهر فقط، أو ضمن 50 مترًا فقط عندما يكون للبلاغ إحداثيات. يعمل عند الطلب؛ قد يستغرق البحث الأول وقتًا أطول.')}</p>
    <div className="similarity-actions"><button className="secondary" disabled={blocked} onClick={()=>search('visual')}>{busy==='visual'?tx('Comparing damage appearance…','جارٍ مقارنة مظهر الضرر…'):tx('Find visually similar damage (any location)','البحث عن أضرار مشابهة بصريًا (أي موقع)')}</button>
    <button className="secondary" disabled={blocked||!hasGps} onClick={()=>search('nearby')}>{busy==='nearby'?tx('Comparing nearby damage…','جارٍ مقارنة الأضرار القريبة…'):tx('Find nearby matches (50 m)','البحث عن تطابقات قريبة (50 م)')}</button></div>
    {(edited||!hasBoxes)?<p className="muted">{edited?tx('Save your changes first.','احفظ التغييرات أولًا.'):tx('Save at least one damage box first.','احفظ تحديد ضرر واحدًا على الأقل أولًا.')}</p>:!hasGps&&<p className="muted">{tx('No coordinates on this report, so only the visual search is available. No location is assumed.','لا توجد إحداثيات لهذا البلاغ، لذا يتاح البحث البصري فقط. لا يُفترض أي موقع.')}</p>}
    {error&&<p role="alert">{error}</p>}
    {result&&<div role="status"><p>{result.candidate_reports} {result.mode==='visual'?tx('open reports compared by appearance only','بلاغات مفتوحة قورنت حسب المظهر فقط'):tx('nearby open reports checked','بلاغات مفتوحة قريبة تم فحصها')}</p>{result.mode==='visual'&&<p className="muted">{tx('Visually similar is not a confirmed duplicate: location was not used. Open both reports and decide.','التشابه البصري ليس تكرارًا مؤكدًا: لم يُستخدم الموقع. افتح البلاغين وقرّر.')}</p>}{result.matches.map(m=><p key={m.report_id}><code>{m.report_id.slice(0,8)}</code> · {(m.similarity*100).toFixed(1)}% {tx('crop similarity','تشابه مناطق الضرر')}{m.distance_m!=null&&<> · <span dir="ltr">{m.distance_m} m</span></>}</p>)}{!result.matches.length&&<p>{tx('No matches above the experimental threshold. This does not prove that no duplicate exists.','لا توجد تطابقات تتجاوز الحد التجريبي. هذا لا يثبت عدم وجود تكرار.')}</p>}</div>}
    <small className="muted">{tx('Experimental similarity threshold 0.80, not calibrated on your local roads. Suggestions never merge or relabel reports; distances appear only between real locations or between simulated ones.','حد التشابه التجريبي 0.80 غير معاير على طرقكم المحلية. الاقتراحات لا تدمج البلاغات ولا تعيد تصنيفها؛ تظهر المسافات فقط بين مواقع حقيقية أو بين مواقع محاكاة.')}</small>
  </section>
}
