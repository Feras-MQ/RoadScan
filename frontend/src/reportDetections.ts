import type {ReviewDetection} from './annotations';

export type StoredAnnotations = {detections:unknown[]|null; detections_readable?:boolean};
export type AnnotationState = {kind:'ready'|'legacy'|'unreadable'|'not_displayable'; boxes:ReviewDetection[]|null};

/** API readability does not guarantee valid geometry or a legacy confidence value. */
export function inspectAnnotations(report:StoredAnnotations):AnnotationState {
  if (report.detections_readable === false || !Array.isArray(report.detections)) return {kind:'unreadable',boxes:null};
  const boxes:ReviewDetection[]=[];
  for (const raw of report.detections) {
    if (!raw || typeof raw !== 'object') return {kind:'not_displayable',boxes:null};
    const value=raw as Record<string,unknown>, box=value.box;
    if (typeof value.class_id!=='string' || !['D00','D10','D20','D40','OTHER'].includes(value.class_id) || !Array.isArray(box) || box.length!==4 ||
        !box.every(n=>typeof n==='number'&&Number.isFinite(n)) || box[0]<0 || box[1]<0 || box[2]<=box[0] || box[3]<=box[1] ||
        (value.confidence!==undefined && (typeof value.confidence!=='number' || !Number.isFinite(value.confidence) || value.confidence<0 || value.confidence>1))) return {kind:'not_displayable',boxes:null};
    boxes.push({...value,class_id:value.class_id as string,box:[...box],confidence:value.confidence as number|undefined});
  }
  return {kind:boxes.some(box=>box.confidence===undefined)?'legacy':'ready',boxes};
}

export function annotationSummary(report:StoredAnnotations,lang:string):string {
  const state=inspectAnnotations(report), ar=lang==='ar';
  if(state.kind==='unreadable') return ar?'التحديدات غير قابلة للقراءة':'Annotations unreadable';
  if(state.kind==='not_displayable') return ar?'التحديدات غير قابلة للعرض':'Annotations not displayable';
  return `${state.boxes!.length} ${ar?'تحديدات':'annotations'}`+(state.kind==='legacy'?(ar?' · الثقة غير مسجلة':' · confidence not recorded'):'');
}

export function reportPriority(report:StoredAnnotations & {score:number|null}):number|null {
  return inspectAnnotations(report).kind==='ready' && typeof report.score==='number' && Number.isFinite(report.score) ? report.score : null;
}
