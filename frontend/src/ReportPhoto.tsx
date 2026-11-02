import {useEffect, useState} from 'react';
import {FileImage, RefreshCw} from 'lucide-react';

/** Authenticated same-origin report photo; aborts stale loads and revokes object URLs. Key it by report and session. */
export default function ReportPhoto({id, sessionKey, lang}:{id:string; sessionKey:string; lang:string}) {
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
