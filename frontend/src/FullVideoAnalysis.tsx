import {modelName} from './modelName';
import type {CSSProperties} from 'react';
import {useCallback, useEffect, useRef, useState} from 'react';
import {validRecognition} from './liveFrames';
import type {Recognition} from './liveFrames';

type Props={lang:string; connected:boolean; ready:boolean; sessionKey:string;
  request:(path:string,options?:RequestInit)=>Promise<any>; onCapture:(file:File)=>void; onBack:()=>void};
type Frame=Recognition & {jpeg_base64:string; frame_index:number; timestamp_ms:number|null; processed_count:number; total_frames:number|null};
export default function FullVideoAnalysis(props:Props) {
  const tx=(en:string,ar:string)=>props.lang==='ar'?ar:en;
  const [file,setFile]=useState<File|null>(null),[quality,setQuality]=useState('balanced');
  const [running,setRunning]=useState(false),[message,setMessage]=useState(''),[error,setError]=useState('');
  const [frame,setFrame]=useState<Frame|null>(null),[count,setCount]=useState(0),[total,setTotal]=useState<number|null>(null);
  const task=useRef<AbortController|null>(null),session=useRef<string|null>(null),pending=useRef(false);
  const latest=useRef(props);latest.current=props;
  const stop=useCallback(()=>{
    task.current?.abort();task.current=null;
    const id=session.current;session.current=null;
    if(id)void latest.current.request(`/api/video-analysis/${id}`,{method:'DELETE'}).catch(()=>{});
    setRunning(false);
  },[]);
  useEffect(()=>{stop();return stop},[props.sessionKey,props.connected,stop]);
  useEffect(()=>{const hidden=()=>{if(document.hidden){stop();setMessage(latest.current.lang==='ar'?'توقف التحليل عند إخفاء الصفحة؛ النتيجة جزئية.':'Stopped when the page was hidden; analysis is partial.')}};document.addEventListener('visibilitychange',hidden);return()=>document.removeEventListener('visibilitychange',hidden)},[stop]);
  async function start(){
    if(!file||pending.current||!props.connected||!props.ready)return;
    stop();pending.current=true;const controller=new AbortController();task.current=controller;
    setRunning(true);setError('');setFrame(null);setCount(0);setTotal(null);setMessage(tx('Uploading to your local RoadScan server…','جارٍ الرفع إلى خادم RoadScan المحلي…'));
    let id:string|null=null;
    try{
      const opened=await props.request(`/api/video-analysis?filename=${encodeURIComponent(file.name)}&mode=${quality}`,{method:'POST',body:file,signal:controller.signal,headers:{'Content-Type':'application/octet-stream'}});
      id=opened.id;
      if(controller.signal.aborted)return;
      session.current=id;setTotal(opened.total_frames);setMessage(tx('Processing every decoded frame in order. Playback speed does not skip frames.','جارٍ تحليل كل إطار مفكوك الترميز بالترتيب دون تخطي بسبب سرعة التشغيل.'));
      let expected=0;
      while(!controller.signal.aborted){
        const data=await props.request(`/api/video-analysis/${id}/next`,{method:'POST',signal:controller.signal});
        if(controller.signal.aborted)return;
        if(data.state==='busy'){
          setMessage(tx('Detector busy — the same frame is waiting.','النموذج مشغول — ينتظر الإطار نفسه.'));
          await new Promise<void>(resolve=>setTimeout(resolve,800));continue;
        }
        if(data.state==='finished'){
          if(data.processed_count!==expected)throw Error(tx('Frame count mismatch. Analysis is incomplete.','عدد الإطارات غير متطابق. التحليل غير مكتمل.'));
          setMessage(data.complete?tx(`Complete: ${expected} frames analyzed.`,`اكتمل التحليل: ${expected} إطارًا.`):tx(`Incomplete: ${expected} frames analyzed. ${data.reason||'The decoder stopped early.'}`,`تحليل جزئي: ${expected} إطارًا. ${data.reason||'توقف فك الترميز مبكرًا.'}`));
          break;
        }
        if(!validRecognition(data,data.width,data.height)||data.frame_index!==expected||typeof data.jpeg_base64!=='string')throw Error(tx('Analysis stopped without skipping the failed frame. Start again after checking the model/video.','توقف التحليل دون تخطي الإطار المتعذر. تحقق من النموذج والفيديو ثم أعد البدء.'));
        expected++;setCount(expected);setFrame(data);setMessage(tx('Analyzing every decoded frame…','جارٍ تحليل كل إطار مفكوك الترميز…'));
      }
    }catch(reason){if(!controller.signal.aborted)setError(reason instanceof Error?reason.message:String(reason))}
    finally{
      if(id)await props.request(`/api/video-analysis/${id}`,{method:'DELETE'}).catch(()=>{});
      if(task.current===controller){session.current=null;task.current=null;setRunning(false)}
      pending.current=false;
    }
  }
  function useFrame(){
    if(!frame)return;stop();
    const bytes=Uint8Array.from(atob(frame.jpeg_base64),c=>c.charCodeAt(0));
    props.onCapture(new File([bytes],`video-frame-${frame.frame_index+1}.jpg`,{type:'image/jpeg'}));
  }
  return <section className="panel full-video-panel" style={{'--stagger': 1} as CSSProperties}>
    <div className="heading full-video-heading"><div><div className="eyebrow">{tx('THOROUGH VIDEO ANALYSIS','تحليل الفيديو الكامل')}</div><h1>{tx('Every frame. At your pace.','كل إطار. بالسرعة المناسبة.')}</h1></div><button className="secondary" onClick={()=>{stop();props.onBack()}}>{tx('Back to live camera','العودة للكاميرا المباشرة')}</button></div>
    <p>{tx('Choose a recording, then analyze every frame in order. This can take longer than playback. Reviewing every frame does not guarantee every defect is detected.','اختر تسجيلًا ثم حلل كل إطار بالترتيب. قد يستغرق ذلك أطول من تشغيل الفيديو. تحليل كل إطار لا يضمن اكتشاف كل ضرر.')}</p>
    <div className="live-control-fields"><label>{tx('Video file · MP4 / WebM · up to 200 MiB','ملف فيديو · MP4 / WebM · حتى 200 MiB')}<input aria-label={tx('Thorough analysis video','فيديو التحليل الكامل')} type="file" accept=".mp4,.webm" disabled={running} onChange={event=>{const f=event.target.files?.[0];setError('');setFrame(null);setCount(0);setMessage('');if(f&&f.size>200*1024*1024){setFile(null);setError(tx('Choose a video under 200 MiB.','اختر فيديو أصغر من 200 MiB.'))}else setFile(f||null)}}/></label>
    <label>{tx('Quality','الجودة')}<select aria-label={tx('Video analysis quality','جودة تحليل الفيديو')} disabled={running} value={quality} onChange={e=>setQuality(e.target.value)}><option value="balanced">{tx('Balanced','متوازن')}</option><option value="detail">{tx('Detail','تفاصيل')}</option></select></label></div>
    <div className="live-actions"><button className={"primary"+(running?" is-busy":"")} disabled={running||!file||!props.connected||!props.ready} onClick={()=>void start()}>{tx('Analyze every frame','تحليل كل إطار')}</button><button className="secondary" disabled={!running} onClick={()=>{stop();setMessage(tx('Stopped. Only the completed frames were analyzed.','توقف التحليل. تم تحليل الإطارات المكتملة فقط.'))}}>{tx('Stop analysis','إيقاف التحليل')}</button></div>
    <p role="status" className={running?"is-busy":""}>{message}</p>{error&&<p role="alert" className="inline-error">{error}</p>}
    <div className="live-telemetry"><div><strong>{count}</strong><span>{tx('Frames analyzed','إطارات محللة')}</span></div><div><strong>{total??'—'}</strong><span>{tx('Expected frames (video metadata)','الإطارات المتوقعة (بيانات الفيديو)')}</span></div><div><strong>{frame?.timestamp_ms!=null?(frame.timestamp_ms/1000).toFixed(2):'—'} s</strong><span>{tx('Video position','موضع الفيديو')}</span></div></div>
    {frame&&<><div className="annotation-stage live-result"><img src={'data:image/jpeg;base64,'+frame.jpeg_base64} alt={tx('Sequentially analyzed video frame','إطار فيديو محلل بالترتيب')}/><svg viewBox={`0 0 ${frame.width} ${frame.height}`}>{frame.detections.map((d,i)=><g key={i}><rect className={'damage-box box-'+d.class_id} x={d.box[0]} y={d.box[1]} width={d.box[2]-d.box[0]} height={d.box[3]-d.box[1]}/><text x={d.box[0]+4} y={Math.max(20,d.box[1]-5)} fill="white" stroke="black" strokeWidth="1" paintOrder="stroke" fontSize="20">{d.class_id} · {Math.round(d.confidence*100)}%</text></g>)}</svg></div><p><span title={frame.model_version}>{modelName(frame.model_version)}</span> · {frame.detections.length} {tx('boxes','تحديدات')}</p><button className="secondary" onClick={useFrame}>{tx('Stop and use this frame for a report','إيقاف واستخدام هذا الإطار لبلاغ')}</button></>}
    <p className="muted">{tx('Local temporary video only; removed after completion or cancellation. Idle sessions expire. No reports or frame collection are saved automatically. Maximum 50,000 frames per run. Frames are resized to at most 960 pixels before inference. Damaged or unsupported video can end incompletely. Keep this tab visible.','الفيديو مؤقت ومحلي ويُحذف بعد الاكتمال أو الإلغاء. تنتهي الجلسات الخاملة. لا تُحفظ البلاغات أو مجموعة الإطارات تلقائيًا. الحد 50,000 إطار للتشغيل. تُصغّر الإطارات إلى 960 بكسل كحد أقصى قبل التحليل. قد لا يكتمل الفيديو التالف أو غير المدعوم. أبقِ التبويب ظاهرًا.')}</p>
  </section>;
}
