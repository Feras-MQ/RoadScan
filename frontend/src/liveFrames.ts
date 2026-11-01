import {validAnnotations} from './annotations.ts';
import type {Detection} from './annotations';

export type Recognition = {
  state: 'completed' | 'busy' | 'failed' | 'not_configured'; reason: string | null;
  detections: Detection[]; model_version: string; width: number; height: number;
  elapsed_ms: number; confidence_threshold: number | null; persisted: false; inference_size?:number;
};

export function frameSize(width: number, height: number, edge = 960): [number, number] {
  if (![width, height, edge].every(n => Number.isFinite(n) && n > 0)) throw Error('Invalid frame dimensions');
  const scale = Math.min(1, edge / width, edge / height);
  return [Math.max(1, Math.round(width * scale)), Math.max(1, Math.round(height * scale))];
}

export function validRecognition(value: Recognition, width: number, height: number): boolean {
  return value?.state === 'completed' && value.width === width && value.height === height &&
    Number.isFinite(value.elapsed_ms) && value.elapsed_ms >= 0 && value.persisted === false &&
    typeof value.model_version === 'string' && value.model_version.length > 0 &&
    Array.isArray(value.detections) && validAnnotations(value.detections, width, height);
}

// Restarts wait for the previous request to settle, even if its source ignores abort.
export function frameLoop(step: (signal: AbortSignal) => Promise<void>, onError: (error: unknown) => void, intervalMs = 1000, timeoutMs = 60000) {
  let generation = 0;
  let active = false;
  let timer: ReturnType<typeof setTimeout> | null = null;
  let controller: AbortController | null = null;
  let pending = Promise.resolve();
  const current = (id: number) => active && generation === id;
  function queue(id: number) {
    pending = pending.then(async () => {
      if (!current(id)) return;
      const request = new AbortController(); controller = request;
      const deadline = setTimeout(() => request.abort(), timeoutMs);
      try {await step(request.signal)} catch (error) {if (current(id)) onError(error)}
      finally {
        clearTimeout(deadline);
        if (controller === request) controller = null;
        if (current(id)) timer = setTimeout(() => queue(id), intervalMs);
      }
    });
  }
  function stop() {
    active = false; ++generation;
    if (timer !== null) clearTimeout(timer);
    timer = null; controller?.abort();
  }
  return {start() {stop(); active = true; queue(++generation)}, stop};
}

export type HitFrame = {frame_index: number; timestamp_ms: number | null; detections: Detection[]};
export type DamageEvent<F extends HitFrame> = {first: number; last: number; classes: string[]; best: F; confidence: number};
export const MAX_EVENTS = 200; // shortcut: later damage is counted but not listed past 200 events; page if long surveys need it

// Consecutive damage frames (one empty frame allowed between them) are one event, so a crack seen in 30 frames is listed once, with its most confident frame.
export function addDamageEvent<F extends HitFrame>(events: DamageEvent<F>[], frame: F): DamageEvent<F>[] {
  if (!frame.detections.length) return events;
  const confidence = Math.max(...frame.detections.map(d => d.confidence));
  const classes = [...new Set(frame.detections.map(d => d.class_id))];
  const last = events[events.length - 1];
  if (last && frame.frame_index - last.last <= 2) {
    const merged = {...last, last: frame.frame_index, classes: [...new Set([...last.classes, ...classes])].sort()};
    return [...events.slice(0, -1), confidence > last.confidence ? {...merged, best: frame, confidence} : merged];
  }
  if (events.length >= MAX_EVENTS) return events;
  return [...events, {first: frame.frame_index, last: frame.frame_index, classes: classes.sort(), best: frame, confidence}];
}
