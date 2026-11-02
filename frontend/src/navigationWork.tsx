import {createContext, useContext, useId, useLayoutEffect} from 'react';

export type WorkKind = 'vote' | 'training' | 'live' | 'video' | 'models' | 'export' | 'analysis';
export type NavigationWork = {kind:WorkKind; dirty?:boolean; running?:boolean; blocking?:boolean};
export type WorkRegistry = Map<string, NavigationWork>;
export const NavigationWorkContext = createContext<WorkRegistry | null>(null);

/** Only mounted tools register loss/interruption; a clean screen registers nothing. */
export function useNavigationWork(kind:WorkKind, dirty=false, running=false, blocking=false) {
  const registry=useContext(NavigationWorkContext), id=useId();
  useLayoutEffect(() => {
    if (dirty || running) registry?.set(id,{kind,dirty,running,blocking});
    else registry?.delete(id);
    return () => {registry?.delete(id);};
  },[registry,id,kind,dirty,running,blocking]);
}

export function workWarning(work:NavigationWork[], lang:string):string|null {
  if (!work.some(item=>item.dirty || item.running)) return null;
  const tx=(en:string,ar:string)=>lang==='ar'?ar:en;
  const labels:Record<WorkKind,string>={
    vote:tx('model choices, comparison results or a running model vote','اختيارات النماذج أو نتائج المقارنة أو تصويت جارٍ'),
    training:tx('unsaved training settings','إعدادات التدريب غير المحفوظة'),
    live:tx('the selected video, captured frame or live session','الفيديو المختار أو الإطار الملتقط أو الجلسة المباشرة'),
    video:tx('the selected video or analysis results','الفيديو المختار أو نتائج التحليل'),
    models:tx('a model update','تحديث النموذج'),
    export:tx('the dataset download','تنزيل بيانات التدريب'),
    analysis:tx('the report analysis','تحليل البلاغ'),
  };
  const names=[...new Set(work.filter(item=>item.dirty || item.running).map(item=>labels[item.kind]))].join(lang==='ar'?'، ':', ');
  return tx('Leaving this screen will discard unfinished work or stop ongoing work: ','مغادرة هذه الشاشة ستفقد العمل غير المحفوظ أو توقف العمل الجاري: ')+names+tx('. Continue?', '. هل تريد المتابعة؟');
}
