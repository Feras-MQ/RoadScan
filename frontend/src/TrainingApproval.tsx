import {useEffect, useState, useRef} from 'react';
import {GraduationCap, CheckCircle2} from 'lucide-react';
import './learning.css';

type Props={lang:string; reportId:string; revision:string; dirty:boolean; empty:boolean;
  request:(path:string,options?:RequestInit)=>Promise<any>};
type Status={approved:boolean; stale:boolean; eligible:boolean; split:string; capture_group:string; approved_at:string|null};

export default function TrainingApproval(props:Props) {
  const tx=(en:string,ar:string)=>props.lang==='ar'?ar:en;
  const [state,setState]=useState<Status|null>(null);const [group,setGroup]=useState('');const [split,setSplit]=useState('train');
  const [rights,setRights]=useState(false);const [negative,setNegative]=useState(false);const [busy,setBusy]=useState(false);const [error,setError]=useState('');
  const task=useRef<AbortController|null>(null);
  useEffect(()=>{
    const controller=new AbortController();task.current?.abort();task.current=controller;setState(null);setBusy(false);setError('');setRights(false);setNegative(false);
    props.request(`/api/reports/${props.reportId}/training`,{signal:controller.signal}).then(data=>{if(!controller.signal.aborted){setState(data);setGroup(data.capture_group);setSplit(data.split)}}).catch(reason=>{if(!controller.signal.aborted)setError(reason.message)});
    return ()=>controller.abort();
  },[props.reportId,props.revision,props.request]);
  async function save(revoke=false) {
    task.current?.abort();const controller=new AbortController();task.current=controller;setBusy(true);setError('');
    try {
      const data=await props.request(`/api/reports/${props.reportId}/training`,{method:revoke?'DELETE':'PUT',signal:controller.signal,
        ...(revoke?{}:{headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:props.revision,split,capture_group:group.trim(),rights_confirmed:rights,negative_confirmed:negative})})});
      if(controller.signal.aborted)return;
      if(revoke)setState(old=>old?{...old,approved:false,stale:false}:old);else setState(data);
    } catch(reason){if(!controller.signal.aborted)setError(reason instanceof Error?reason.message:String(reason))}
    finally{if(!controller.signal.aborted)setBusy(false)}
  }
  useEffect(()=>()=>task.current?.abort(),[]);
  return <section className="detail-section training-approval"><h3><GraduationCap size={20}/> {tx('Teach the next model','علّم النموذج القادم')}</h3>
    <p className="muted">{tx('Your correction becomes a training example only after approval. Current model weights stay the same. Export approved examples from Learning.','تصبح المراجعة مثالًا للتدريب بعد اعتمادها. تبقى أوزان النموذج الحالي كما هي. صدّر الأمثلة المعتمدة من صفحة التعلّم.')}</p>
    {error&&<p role="alert" className="inline-error">{error}</p>}
    {state?.approved?<div className="training-approved"><CheckCircle2 size={22}/><span>{tx('Approved for','معتمد لـ')} <strong>{state.split}</strong> · {state.capture_group}</span><button disabled={busy} className="text-button" onClick={()=>void save(true)}>{tx('Revoke approval','إلغاء الاعتماد')}</button></div>:<>
      {state?.stale&&<p className="info">{tx('The saved review changed. Check it again before approving this version.','تغيرت المراجعة المحفوظة. تحقق منها قبل اعتماد هذه النسخة.')}</p>}
      {(!state?.eligible||props.dirty)&&<p className="info">{tx('Save a Confirmed review first. Correct every box, including missed damage.','احفظ المراجعة بحالة مؤكد أولًا. صحح كل التحديدات وأضف الضرر الذي فات النموذج.')}</p>}
      <div className="field-grid"><label>{tx('Capture group','مجموعة التصوير')}<input aria-label={tx('Training capture group','مجموعة تصوير التدريب')} value={group} maxLength={80} placeholder="campus-run-01" onChange={event=>setGroup(event.target.value)}/><small>{tx('Use one name per road run/video and keep that group in one split. Use A–Z, numbers, hyphens or underscores.','استخدم اسمًا واحدًا لكل رحلة أو فيديو وفي تقسيم واحد. استخدم أحرفًا إنجليزية وأرقامًا وشرطة أو شرطة سفلية.')}</small></label><label>{tx('Dataset split','تقسيم البيانات')}<select aria-label={tx('Dataset split','تقسيم البيانات')} value={split} onChange={event=>setSplit(event.target.value)}><option value="train">{tx('Train — model can learn here','تدريب — يتعلم منها النموذج')}</option><option value="val">{tx('Validation — choose settings','تحقق — لاختيار الإعدادات')}</option><option value="test">{tx('Protected test — never train here','اختبار محمي — لا يستخدم للتدريب')}</option></select></label></div>
      <label className="check-line"><input type="checkbox" checked={rights} onChange={event=>setRights(event.target.checked)}/>{tx('I checked these labels and have permission to use this image.','تحققت من التحديدات ولدي إذن باستخدام الصورة.')}</label>
      {props.empty&&<label className="check-line"><input type="checkbox" checked={negative} onChange={event=>setNegative(event.target.checked)}/>{tx('I inspected the full image: this is an intentional empty/negative example.','فحصت الصورة كاملة: هذا مثال خالٍ من الضرر المستهدف عن قصد.')}</label>}
      <button className="secondary" disabled={busy||props.dirty||!state?.eligible||!rights||!group.trim()||(props.empty&&!negative)} onClick={()=>void save()}>{busy?tx('Saving…','جارٍ الحفظ…'):tx('Approve this example','اعتماد هذا المثال')}</button>
    </>}
  </section>;
}
