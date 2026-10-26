import {modelName} from './modelName';
import type {CSSProperties} from 'react';
import {useCallback, useEffect, useRef, useState} from 'react';
import {Camera, Play, Square, ScanLine, FileImage, AlertTriangle, RefreshCw} from 'lucide-react';
import {currentMedia} from './currentTask';
import {frameLoop, frameSize, validRecognition} from './liveFrames';
import FullVideoAnalysis from './FullVideoAnalysis';
import type {Recognition} from './liveFrames';
import './live.css';

type Props = {
  lang: string; connected: boolean; ready: boolean; sessionKey: string; autoStart: boolean;
  request: (path: string, options?: RequestInit) => Promise<unknown>;
  onCapture: (file: File) => void;
};
type Processed = {file: File; url: string; data: Recognition; at: number};
const labels: Record<string, [string,string]> = {
  D00:['Longitudinal crack','شق طولي'], D10:['Transverse crack','شق عرضي'],
  D20:['Alligator crack','تشققات شبكية'], D40:['Pothole','حفرة'], OTHER:['Other surface damage','أضرار سطحية أخرى'],
};

export default function LiveRecognition(props: Props) {
  const latest=useRef(props); latest.current=props;
  const tx=(en: string, ar: string) => props.lang==='ar' ? ar : en;
  const video=useRef<HTMLVideoElement>(null);
  const media=useRef<MediaStream|null>(null);
  const epoch=useRef(0);
  const loop=useRef<ReturnType<typeof frameLoop>|null>(null);
  const [devices,setDevices]=useState<MediaDeviceInfo[]>([]);
  const [deviceId,setDeviceId]=useState('');
  const [opening,setOpening]=useState(false);
  const [running,setRunning]=useState(false);
  const [error,setError]=useState('');
  const [waiting,setWaiting]=useState(false);
  const [processed,setProcessed]=useState<Processed|null>(null);
  const [count,setCount]=useState(0);
  const [sourceMode,setSourceMode]=useState<'camera'|'video'|'thorough'>('camera');
  const [videoURL,setVideoURL]=useState<string|null>(null);
  const [videoName,setVideoName]=useState('');
  const fileInput=useRef<HTMLInputElement>(null);
  const autoStarted=useRef(false);
  const failures=useRef(0);
  const [quality,setQuality]=useState<'balanced'|'detail'>('balanced');
  const [processing,setProcessing]=useState(false);
  const qualityRef=useRef(quality);qualityRef.current=quality;

  const release=useCallback(() => {
    ++epoch.current; loop.current?.stop();
    media.current?.getTracks().forEach(track => track.stop()); media.current=null;
    if(video.current) {video.current.pause(); if(video.current.srcObject)video.current.srcObject=null}
  },[]);
  const stop=useCallback(() => {release(); setRunning(false); setOpening(false); setWaiting(false);setProcessing(false)},[release]);
  useEffect(() => release,[release]);
  useEffect(() => {stop(); return release},[props.sessionKey,props.connected,props.ready,release,stop]);
  useEffect(() => () => {if(processed) URL.revokeObjectURL(processed.url)},[processed]);
  useEffect(() => () => {if(videoURL) URL.revokeObjectURL(videoURL)},[videoURL]);
  useEffect(() => {
    const hidden=() => {if(document.hidden) stop()};
    document.addEventListener('visibilitychange',hidden); window.addEventListener('pagehide',stop);
    return () => {document.removeEventListener('visibilitychange',hidden); window.removeEventListener('pagehide',stop)};
  },[stop]);
  async function refreshDevices() {
    const id=epoch.current;
    try {
      const list=await navigator.mediaDevices?.enumerateDevices();
      if(id===epoch.current && list) {
        const cameras=list.filter(device => device.kind==='videoinput');setDevices(cameras);
        setDeviceId(previous => previous && !cameras.some(device => device.deviceId===previous) ? '' : previous);
      }
    } catch { /* Device labels may stay unavailable until camera permission is granted. */ }
  }
  useEffect(() => {
    const changed=() => {void refreshDevices()};changed();
    navigator.mediaDevices?.addEventListener('devicechange',changed);
    return () => navigator.mediaDevices?.removeEventListener('devicechange',changed);
  },[]);

  async function recognizeFrame(signal: AbortSignal, id: number) {
    const source=video.current;
    if(!source || source.readyState<2 || !source.videoWidth || source.ended || source.paused || signal.aborted) return;
    const [width,height]=frameSize(source.videoWidth,source.videoHeight);
    const canvas=document.createElement('canvas'); canvas.width=width; canvas.height=height;
    const context=canvas.getContext('2d'); if(!context) throw Error('Frame capture unavailable');
    context.drawImage(source,0,0,width,height);
    const blob=await new Promise<Blob|null>(resolve => canvas.toBlob(resolve,'image/jpeg',.85));
    canvas.width=0;canvas.height=0;
    if(signal.aborted || id!==epoch.current) return;
    if(!blob) throw Error('Frame capture unavailable');
    const file=new File([blob],`roadscan-frame-${Date.now()}.jpg`,{type:'image/jpeg'});
    setProcessing(true);
    let data:Recognition;
    try {data=await latest.current.request('/api/recognize?mode='+qualityRef.current,{method:'POST',headers:{'Content-Type':'image/jpeg'},body:file,signal}) as Recognition}
    finally {if(id===epoch.current)setProcessing(false)}
    if(signal.aborted || id!==epoch.current) return;
    if(data?.state==='busy') {setWaiting(true); return}
    if(data?.state!=='completed') throw Error(latest.current.lang==='ar' ? 'لم يكتمل التحليل. تحقق من النموذج ثم حاول مجددًا.' : 'Recognition did not complete. Check the detector and try again.');
    if(!validRecognition(data,width,height)) throw Error('Invalid recognition response');
    failures.current=0;setError('');setWaiting(false); setProcessed({file,url:URL.createObjectURL(file),data,at:Date.now()}); setCount(n => n+1);
  }

  async function start() {
    stop(); failures.current=0;setError(''); setCount(0); setProcessed(null); setOpening(true);
    const id=epoch.current;
    const openingDeadline=setTimeout(() => {
      if(id!==epoch.current)return;
      stop();setError(latest.current.lang==='ar'?'تعذر فتح المصدر في الوقت المحدد. اسمح بوصول الكاميرا في المتصفح أو تحقق من ملف الفيديو ثم حاول مجددًا.':'The source did not open in time. Allow camera access in your browser or check the video file, then try again.');
    },20000);
    try {
      if(!latest.current.connected || !latest.current.ready) throw Error(tx('Connect your workspace and load a detector first.','اتصل بمساحة العمل وحمّل النموذج أولًا.'));
      const source=video.current; if(!source) throw Error('Video element unavailable');
      if(sourceMode==='camera') {
        if(!navigator.mediaDevices?.getUserMedia) throw Error(tx('Camera access requires a supported browser on localhost or HTTPS.','تحتاج الكاميرا متصفحًا مدعومًا على localhost أو HTTPS.'));
        const available=await navigator.mediaDevices.enumerateDevices();
        if(id!==epoch.current) return;
        // Prefer the user's already-installed Iriun camera when its label is available.
        const chosen=(available.some(device => device.kind==='videoinput' && device.deviceId===deviceId) ? deviceId : '') || available.find(device => device.kind==='videoinput' && /iriun/i.test(device.label))?.deviceId;
        const acquired=await currentMedia(() => navigator.mediaDevices.getUserMedia({audio:false,video:{width:{ideal:1280},height:{ideal:720},...(chosen ? {deviceId:{exact:chosen}} : {facingMode:{ideal:'environment'}})}}),() => id===epoch.current);
        if(!acquired.current) return;
        media.current=acquired.value; source.srcObject=acquired.value;
        acquired.value.getVideoTracks().forEach(track => track.addEventListener('ended',() => {
          if(id!==epoch.current)return;
          stop();setError(latest.current.lang==='ar'?'انقطع اتصال الكاميرا. أعد توصيلها ثم ابدأ مجددًا.':'The camera disconnected. Reconnect it, then start again.');
        },{once:true}));
        const activeDevice=acquired.value.getVideoTracks()[0]?.getSettings().deviceId;
        if(activeDevice) setDeviceId(activeDevice);
        void refreshDevices();
      } else {
        if(!videoURL) throw Error(tx('Choose a video file first.','اختر ملف فيديو أولًا.'));
        if(source.ended) source.currentTime=0;
      }
      await source.play();
      if(id!==epoch.current) return;
      setOpening(false); setRunning(true);
      if(!loop.current)loop.current=frameLoop(signal => recognizeFrame(signal,epoch.current),reason => {
        failures.current+=1;
        if(failures.current>=3) {
          stop();setError(latest.current.lang==='ar'?'تعذر التحليل ثلاث مرات. اختر وضع متوازن أو نموذجًا أخف ثم ابدأ مجددًا.':'Recognition failed three times. Choose Balanced mode or a lighter model, then start again.');
        } else {
          setError(latest.current.lang==='ar'?'تأخر التحليل أو تعذر مؤقتًا؛ ستُعاد المحاولة تلقائيًا.':'Recognition was slow or temporarily failed; retrying automatically.');
        }
        void reason;
      });
      loop.current.start();
    } catch(reason) {
      if(id!==epoch.current) return;
      stop(); setError(reason instanceof Error ? reason.message : String(reason));
    } finally {clearTimeout(openingDeadline)}
  }
  useEffect(() => {
    let cancelled=false;
    Promise.resolve().then(() => {
      if(!cancelled && props.autoStart && props.connected && props.ready && !autoStarted.current) {
        autoStarted.current=true; void start();
      }
    });
    return () => {cancelled=true};
  },[props.autoStart,props.connected,props.ready]);
  function chooseVideo(file: File|null) {
    if(!file) return;
    stop(); setError(''); setProcessed(null);
    if(!/\.(mp4|webm)$/i.test(file.name)) {setError(tx('Choose an MP4 or WebM video supported by your browser.','اختر فيديو MP4 أو WebM يدعمه المتصفح.')); return}
    setVideoURL(URL.createObjectURL(file)); setVideoName(file.name);
  }
  const result=processed?.data;
  if(sourceMode==='thorough')return <FullVideoAnalysis lang={props.lang} connected={props.connected} ready={props.ready} sessionKey={props.sessionKey} request={props.request} onCapture={props.onCapture} onBack={()=>setSourceMode('camera')}/>;
  return <>
    <div className="heading live-heading"><div><div className="eyebrow">04 / {tx('LIVE RECOGNITION','التعرف المباشر')}</div><h1>{tx('See. Analyze. Review.','شاهد. حلل. راجع.')}</h1><p>{tx('Frames are analyzed automatically while recognition is running. No Capture button needed.','تُحلل الإطارات تلقائيًا أثناء التشغيل دون الحاجة إلى الضغط على التقاط.')}</p></div><span className={'pill '+(running?'ready':'')}><ScanLine size={15}/>{running ? tx('Analyzing automatically','تحليل تلقائي') : tx('Stopped','متوقف')}</span></div>
    <div className="info live-limits"><AlertTriangle size={18}/><span>{tx('Experimental road-damage recognition can miss defects or draw incorrect boxes. No detections does not mean the road is undamaged. Human review is required.','التعرف على أضرار الطريق تجريبي وقد يفوّت الضرر أو يرسم مربعات خاطئة. عدم وجود تحديدات لا يعني سلامة الطريق. المراجعة البشرية ضرورية.')}</span></div>
    {!props.ready && <p className="inline-error">{tx('A trained detector must be loaded before live recognition can start.','يجب تحميل نموذج مدرب قبل بدء التعرف المباشر.')}</p>}
    {error && <div className="alert error" role="alert">{error}</div>}
    <div className="live-telemetry" aria-label={tx('Recognition metrics','مؤشرات التعرف')}><div style={{'--stagger': 1} as CSSProperties}><strong>{count}</strong><span>{tx('Frames analyzed','إطارات محللة')}</span></div><div style={{'--stagger': 2} as CSSProperties}><strong>{result?result.detections.length:'—'}</strong><span>{tx('Boxes in latest frame','تحديدات آخر إطار')}</span></div><div style={{'--stagger': 3} as CSSProperties}><strong>{result?(result.elapsed_ms/1000).toFixed(2):'—'}<small>s</small></strong><span>{tx('Last processing time','زمن التحليل الأخير')}</span></div><div style={{'--stagger': 4} as CSSProperties}><strong>{result?.inference_size??(quality==='balanced'?'≤640':'—')}<small>px</small></strong><span>{tx('Model input size','حجم دخل النموذج')}</span></div></div>
    <section className="panel live-controls" style={{'--stagger': 1} as CSSProperties}><div className="live-control-fields">
      <label>{tx('Source','المصدر')}<select aria-label={tx('Recognition source','مصدر التعرف')} value={sourceMode} onChange={e => {stop();setProcessed(null);setSourceMode(e.target.value as 'camera'|'video'|'thorough')}}><option value="camera">{tx('Camera / Iriun / USB','كاميرا / Iriun / USB')}</option><option value="video">{tx('Video · real-time preview (samples frames)','فيديو · معاينة مباشرة (إطارات مختارة)')}</option><option value="thorough">{tx('Video · analyze every frame','فيديو · تحليل كل إطار')}</option></select></label>
      {sourceMode==='camera' ? <><label>{tx('Camera','الكاميرا')}<select aria-label={tx('Recognition camera','كاميرا التعرف')} value={deviceId} disabled={opening || running} onChange={e => setDeviceId(e.target.value)}><option value="">{tx('Default camera (prefers Iriun)','الكاميرا الافتراضية (تُفضّل Iriun)')}</option>{devices.map((device,i) => <option key={device.deviceId || i} value={device.deviceId}>{device.label || tx('Camera ','كاميرا ')+(i+1)}</option>)}</select></label><button className="secondary" disabled={opening || running} onClick={() => void refreshDevices()} aria-label={tx('Refresh cameras','تحديث الكاميرات')}><RefreshCw size={16}/></button></> : <><input ref={fileInput} aria-label={tx('Choose recognition video','اختيار فيديو التعرف')} type="file" accept="video/mp4,video/webm,.mp4,.webm" hidden onChange={e => {chooseVideo(e.target.files?.[0] || null);e.target.value=''}}/><button className="secondary" onClick={() => fileInput.current?.click()}><FileImage size={16}/>{tx('Choose video','اختيار فيديو')}</button><small>{videoName || tx('MP4 or WebM; codec support depends on your browser.','MP4 أو WebM حسب دعم المتصفح للترميز.')}</small></>}
    <label className="live-quality">{tx('Live quality','جودة التحليل المباشر')}<select aria-label={tx('Live quality','جودة التحليل المباشر')} value={quality} disabled={running || opening} onChange={event=>setQuality(event.target.value as 'balanced'|'detail')}><option value="balanced">{tx('Balanced · lighter CPU load','متوازن · حمل أخف على المعالج')}</option><option value="detail">{tx('Detail · model resolution','تفاصيل · دقة النموذج')}</option></select></label></div><div className="live-actions"><button className={"primary"+(opening?" is-busy":"")} onClick={() => void start()} disabled={!props.connected || !props.ready || opening || running || (sourceMode==='video' && !videoURL)}><Play size={16}/>{opening ? tx('Starting…','جارٍ البدء…') : tx('Start live recognition','بدء التعرف المباشر')}</button><button className="secondary" onClick={stop} disabled={!running && !opening}><Square size={16}/>{tx('Stop recognition','إيقاف التعرف')}</button><span className="muted">{tx('One frame at a time · Speed depends on the model · Frames are not saved automatically','إطار واحد في كل مرة · تعتمد السرعة على النموذج · لا تُحفظ الإطارات تلقائيًا')}</span></div></section>
    <details className="capture-guide"><summary>{tx("Dashcam or drone footage?", "تسجيل كاميرا سيارة أو طائرة مسيّرة؟")}</summary><p>{tx("For a recording, choose Video · analyze every frame. Use real-time preview for a quick look; it samples frames. Drone photos can be uploaded from Overview. A live drone feed works here only if your computer exposes it as a camera device.", "للتسجيل اختر فيديو · تحليل كل إطار. استخدم المعاينة المباشرة لإلقاء نظرة سريعة؛ فهي تختار بعض الإطارات. ارفع صور الطائرة من النظرة العامة. لا يعمل البث المباشر للطائرة هنا إلا إذا ظهر على الكمبيوتر كجهاز كاميرا.")}</p><small>{tx("Aerial accuracy and drone hardware have not been validated. Review the results; RoadScan does not control the aircraft or attach flight GPS automatically.", "لم تُختبر الدقة الجوية أو أجهزة الطائرات. راجع النتائج؛ لا يتحكم RoadScan بالطائرة ولا يرفق إحداثيات الرحلة تلقائيًا.")}</small></details><div className="live-grid"><section className="panel" style={{'--stagger': 2} as CSSProperties}><div className="panel-heading"><div><h2><Camera size={18}/> {tx('Live source','المصدر المباشر')}</h2><p>{tx('Point your Iriun phone or USB camera at the road.','وجّه هاتف Iriun أو كاميرا USB نحو الطريق.')}</p></div></div><div className={"live-source"+(running?" is-running":"")}><video ref={video} muted playsInline controls={sourceMode==='video'} src={sourceMode==='video' ? videoURL || undefined : undefined} onEnded={stop} onError={() => {stop();setError(tx('The browser could not play this source. Try another MP4/WebM codec or camera.','تعذر تشغيل المصدر. جرّب ترميز MP4/WebM آخر أو كاميرا أخرى.'))}}/>{!running && !opening && <span>{tx('Select your source, then start recognition.','اختر المصدر ثم ابدأ التعرف.')}</span>}</div></section>
    <section className="panel" style={{'--stagger': 3} as CSSProperties}><div className="panel-heading"><div><h2>{tx('Latest processed frame','آخر إطار محلل')}</h2><p>{tx('Boxes belong to this exact still frame, not a later moment in the video.','تخص المربعات هذا الإطار بالتحديد ولا تُنقل إلى لحظة أخرى في الفيديو.')}</p></div></div>{processed ? <><div className="annotation-stage live-result"><img src={processed.url} alt={tx('Analyzed road frame','إطار طريق محلل')}/><svg aria-label={tx('Live damage detections','تحديدات الضرر المباشرة')} viewBox={`0 0 ${processed.data.width} ${processed.data.height}`}>{processed.data.detections.map((d,i) => <g key={i}><rect className={'damage-box box-'+d.class_id} x={d.box[0]} y={d.box[1]} width={d.box[2]-d.box[0]} height={d.box[3]-d.box[1]}/><text x={d.box[0]+4} y={Math.max(18,d.box[1]-6)} fontSize={Math.max(14,processed.data.width/45)} fill="#e6f397" stroke="#0c181b" strokeWidth="2" paintOrder="stroke">{d.class_id} · {Math.round(d.confidence*100)}%</text></g>)}</svg></div><p className="live-metrics" role="status">{count} {tx('frames analyzed','إطارات محللة')} · {processed.data.elapsed_ms.toFixed(0)} ms · {new Date(processed.at).toLocaleTimeString(props.lang==='ar'?'ar-SA':'en-GB')}</p>{processed.data.detections.length ? <ul className="live-detections">{processed.data.detections.map((d,i) => <li key={i}><strong>{d.class_id} · {labels[d.class_id]?.[props.lang==='ar'?1:0] || d.class_id}</strong><span>{tx('Detection score','درجة التحديد')} {Math.round(d.confidence*100)}%</span></li>)}</ul> : <p className="info">{tx('No boxes above the detection threshold. Inspect the frame yourself; this is not a clean-road verdict.','لا توجد مربعات فوق عتبة الكشف. افحص الإطار بنفسك؛ هذه ليست نتيجة تثبت سلامة الطريق.')}</p>}<button className="primary" onClick={() => {stop();latest.current.onCapture(processed.file)}}><FileImage size={16}/>{tx('Use this frame for a report','استخدام هذا الإطار لبلاغ')}</button></> : <div className="empty live-empty"><ScanLine size={38}/><strong>{tx('Waiting for the first analyzed frame','بانتظار أول إطار محلل')}</strong><span>{tx('Analysis starts automatically after the camera opens.','يبدأ التحليل تلقائيًا بعد فتح الكاميرا.')}</span></div>}
    {processing && <p role="status" className="live-processing is-busy">{tx('Processing a frame… Heavy models may take longer; the next frame waits.','جارٍ تحليل إطار… قد تستغرق النماذج الثقيلة وقتًا أطول؛ ينتظر الإطار التالي.')}</p>}
    {waiting && <p className="muted is-busy" role="status">{tx('Detector busy; waiting for the next frame.','النموذج مشغول؛ بانتظار الإطار التالي.')}</p>}
    {result && <p className="muted live-baseline">{tx('Model: ','النموذج: ')}<span title={result.model_version}>{modelName(result.model_version)}</span> · {result.inference_size ?? '—'} px</p>}
    {result?.model_version.endsWith('@2bb146ad53a3') && <p className="muted live-baseline">{tx('Measured baseline: US test mAP50 25.05%; Czech validation mAP50 6.12%. These detection scores are not the percentage of images classified correctly.','نتائج النموذج المرجعي: mAP50 لاختبار أمريكا 25.05% وللتحقق التشيكي 6.12%. هذه درجات كشف وليست نسبة الصور المصنفة بصورة صحيحة.')}</p>}
    </section></div>
    <p className="muted live-footnote">{tx('Preview frames are processed on this RoadScan server without creating reports or saving photographs. Use a chosen frame to create a report through the normal review workflow. Recognition stops when you leave this view or hide the tab.','تُعالج إطارات المعاينة على خادم RoadScan دون إنشاء بلاغات أو حفظ الصور. اختر إطارًا لإنشاء بلاغ عبر المراجعة المعتادة. يتوقف التعرف عند مغادرة هذه الشاشة أو إخفاء التبويب.')}</p>
  </>;
}
