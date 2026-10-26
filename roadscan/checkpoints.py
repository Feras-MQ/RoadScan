"""Restricted deserialization for supported local Ultralytics checkpoints."""
import importlib
import os
import math

# Force torch.load to use its restricted unpickler, including inside Ultralytics.
os.environ['TORCH_FORCE_WEIGHTS_ONLY_LOAD'] = '1'

def supported_globals(path):
    import torch
    permitted = (
        'torch.nn.modules.',
        'ultralytics.nn.modules.',
    )
    exact = {
        'ultralytics.nn.tasks.DetectionModel',
        'ultralytics.nn.tasks.RTDETRDetectionModel',
        'ultralytics.utils.IterableSimpleNamespace',
    }
    symbols = torch.serialization.get_unsafe_globals_in_checkpoint(path)
    allowed = []
    for name in symbols:
        if name not in exact and not name.startswith(permitted):
            raise ValueError('Checkpoint contains unsupported serialized types')
        module, attr = name.rsplit('.', 1)
        value = getattr(importlib.import_module(module), attr)
        if not isinstance(value, type):
            raise ValueError('Checkpoint contains unsupported serialized functions')
        allowed.append(value)
    family = 'rtdetr' if 'ultralytics.nn.tasks.RTDETRDetectionModel' in symbols else 'yolo'
    return allowed, family

def inspect_checkpoint(path):
    """Read metadata with restricted, memory-mapped loading; never run inference."""
    import torch
    from .model_classes import class_mapping
    allowed, family = supported_globals(path)
    with torch.serialization.safe_globals(allowed):
        checkpoint = torch.load(path, map_location='cpu', weights_only=True, mmap=True)
    model = checkpoint.get('ema') or checkpoint.get('model')
    if not isinstance(model, torch.nn.Module):
        raise ValueError('No supported detector in this checkpoint')
    mapped = class_mapping(model.names)
    args = checkpoint.get('train_args') or {}
    imgsz = args.get('imgsz', 640)
    if type(imgsz) is not int or not 320 <= imgsz <= 1280 or imgsz % 32:
        imgsz = 640
    # The labels/arguments are checkpoint metadata, not independently measured accuracy.
    metrics = checkpoint.get('train_metrics') or {}
    reported = {}
    for output, key in [('mAP50','metrics/mAP50(B)'),('mAP50_95','metrics/mAP50-95(B)')]:
        value = metrics.get(key)
        if type(value) in (int,float) and math.isfinite(value) and 0 <= value <= 1:
            reported[output] = value
    return {'family': family, 'classes': {str(i): c for i,c in mapped.items()},
            'original_classes': {str(i): str(c) for i,c in model.names.items()},
            'imgsz': imgsz, 'checkpoint_epoch': checkpoint.get('epoch') if type(checkpoint.get('epoch')) is int else None,
            'reported_metrics': reported, 'metrics_source': 'Checkpoint training metadata; not independently verified by RoadScan'}

def load_detector(path):
    import torch
    from ultralytics import YOLO
    allowed, family = supported_globals(path)
    if family == 'rtdetr':
        from ultralytics import RTDETR
        wrapper = RTDETR
    else:
        wrapper = YOLO
    with torch.serialization.safe_globals(allowed):
        model = wrapper(str(path))
    # Inference does not use optimizer/EMA/training tensors kept in the checkpoint
    # dictionary. Retain the loaded inference model, release that training payload.
    model.ckpt = None
    return model, family

