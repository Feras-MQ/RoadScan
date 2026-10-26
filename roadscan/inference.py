"""Optional local-only YOLO checkpoint adapter. Never downloads model weights."""
import hashlib
import math
import os
import threading
from pathlib import Path
from .review import validate_detections
from .model_classes import class_mapping
from .checkpoints import load_detector

CLASS_IDS = {'D00', 'D10', 'D20', 'D40'}

def validate_confidence_profile(values):
    if not isinstance(values, dict) or set(values) != {'D00', 'D10', 'D20', 'D40'}:
        raise ValueError('A confidence profile must contain all four damage classes')
    if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in values.values()):
        raise ValueError('Class confidence thresholds must be finite numbers from 0 to 1')
    return dict(values)


class LocalDetector:
    def __init__(self, path=None, sha256=None, imgsz=640, confidence=None, confidence_profile=None):
        self.confidence_profile = validate_confidence_profile(confidence_profile) if confidence_profile is not None else None
        self._inference_lock = threading.Lock()
        self.path = str(path) if path is not None else os.getenv('ROADSCAN_YOLO_WEIGHTS', '').strip()
        self.imgsz = imgsz
        self.family = None
        self.model = None
        self.version = 'not_configured'
        self.error = 'checkpoint_not_configured'
        if not self.path:
            return
        if not Path(self.path).is_file():
            self.error = 'checkpoint_missing'
            return
        try:
            checkpoint = Path(self.path)
            if checkpoint.suffix.lower() != '.pt':
                self.error = 'unsupported_checkpoint_format'
                return
            with checkpoint.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            expected = str(sha256).lower() if sha256 is not None else os.getenv('ROADSCAN_YOLO_SHA256', '').strip().lower()
            if not expected:
                self.error = 'checkpoint_hash_required'
                return
            if expected != digest:
                self.error = 'checkpoint_hash_mismatch'
                return
            self.confidence = float(confidence if confidence is not None else os.getenv('ROADSCAN_CONFIDENCE', '0.25'))
            if not math.isfinite(self.confidence) or not 0 <= self.confidence <= 1:
                self.error = 'invalid_confidence'
                return
            if self.confidence_profile:
                self.confidence = min(self.confidence_profile.values())
            import torch
            threads = int(os.getenv('ROADSCAN_INFERENCE_THREADS', '2'))
            if not 1 <= threads <= 16:
                self.error = 'invalid_inference_threads'
                return
            torch.set_num_threads(threads)
            from ultralytics import settings
            settings.update({key: False for key in ('sync', 'wandb', 'mlflow', 'clearml', 'comet', 'neptune', 'hub', 'tensorboard') if key in settings})
            self.model, self.family = load_detector(self.path)
            names = self.model.names
            mapped = class_mapping(names)
            def apply_cpu_thread_limit(_predictor):
                # Device setup resets Torch threads; this runs afterward, before warmup/forward.
                torch.set_num_threads(threads)
            self.model.add_callback('on_predict_start', apply_cpu_thread_limit)
            self.mapping = mapped
            self.version = checkpoint.name + '@' + digest[:12]
            self.error = None
        except Exception as exc:
            self.model = None
            self.error = 'load_failed_' + type(exc).__name__

    def predict(self, image, *, wait=True, imgsz=None):
        if self.model is None:
            return {'state':'not_configured', 'reason':self.error, 'detections':[], 'model_version':'not_configured'}
        if not self._inference_lock.acquire(blocking=wait):
            return {'state':'busy', 'reason':'inference_busy', 'detections':[], 'model_version':self.version}
        try:
            results = self.model.predict(source=image, device='cpu', verbose=False, conf=self.confidence, imgsz=imgsz or self.imgsz, max_det=100)
            detections=[]
            for result in results:
                for box in result.boxes:
                    class_id = self.mapping[int(box.cls[0])]
                    confidence = float(box.conf[0])
                    profile = getattr(self, 'confidence_profile', None)
                    if profile and (class_id not in profile or confidence < profile[class_id]):
                        continue
                    raw = [float(v) for v in box.xyxy[0].tolist()]
                    if len(raw)!=4 or not all(math.isfinite(v) for v in raw):
                        raise ValueError('Non-finite model coordinates')
                    # RT-DETR can predict across the image border. Clip to the
                    # observed image before strict review validation, as YOLO does.
                    coords = [round(min(max(value,0),bound),2) for value,bound in
                              zip(raw,(image.width,image.height,image.width,image.height))]
                    if coords[0]>=coords[2] or coords[1]>=coords[3]: continue
                    detections.append({'class_id':class_id, 'box':coords, 'confidence':round(confidence,5)})
            detections = validate_detections(detections, image.width, image.height)
            return {'state':'completed', 'reason':None, 'detections':detections, 'model_version':self.version}
        except Exception as exc:
            return {'state':'failed', 'reason':'inference_' + type(exc).__name__, 'detections':[], 'model_version':self.version}
        finally:
            # Ultralytics retains the previous source and result tensors in its
            # predictor. A live session needs only the plain boxes returned above.
            predictor = getattr(self.model, 'predictor', None)
            if predictor is not None:
                for field in ('batch', 'results', 'plotted_img', 'dataset'):
                    if hasattr(predictor, field): setattr(predictor, field, None)
            self._inference_lock.release()
