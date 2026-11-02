export type Detection = {class_id: string; box: number[]; confidence: number};
export type ReviewDetection = Omit<Detection, 'confidence'> & {confidence?:number; source?:string};
export function dragBox(start: number[], end: number[], width: number, height: number): number[] | null {
  const x1 = Math.max(0, Math.min(width, Math.min(start[0], end[0])));
  const y1 = Math.max(0, Math.min(height, Math.min(start[1], end[1])));
  const x2 = Math.max(0, Math.min(width, Math.max(start[0], end[0])));
  const y2 = Math.max(0, Math.min(height, Math.max(start[1], end[1])));
  if (x2 - x1 < 3 || y2 - y1 < 3) return null;
  return [x1, y1, x2, y2].map(Math.round);
}
export function validAnnotations(detections: ReviewDetection[], width: number, height: number): boolean {
  return detections.length <= 100 && detections.every(d => {
    const [x1, y1, x2, y2] = d.box;
    return ['D00', 'D10', 'D20', 'D40', 'OTHER'].includes(d.class_id) && d.box.length === 4 &&
      d.box.every(Number.isFinite) && x1 >= 0 && y1 >= 0 && x2 <= width && y2 <= height &&
      x2 > x1 && y2 > y1 && typeof d.confidence === 'number' && Number.isFinite(d.confidence) && d.confidence >= 0 && d.confidence <= 1;
  });
}

/** Box ordering and object key order do not change a review; duplicates still count.
 * Source is compared conservatively if present in a future/legacy response. */
export function sameAnnotations(left: ReviewDetection[], right: ReviewDetection[]): boolean {
  if (left.length !== right.length) return false;
  const remaining = [...right];
  return left.every(a => {
    const index = remaining.findIndex(b => a.class_id === b.class_id && a.confidence === b.confidence &&
      a.source === b.source && a.box.length === b.box.length && a.box.every((value, i) => value === b.box[i]));
    if (index < 0) return false;
    remaining.splice(index, 1);
    return true;
  });
}
