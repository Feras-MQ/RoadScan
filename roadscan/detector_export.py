"""Export local YOLO predictions and ground truth in RoadScan evaluation JSON format.

Uses only the validation split of an audited YOLO dataset. No model downloads.
"""
import argparse
import json
import math
from pathlib import Path
from .detector_train import CLASSES, EXTENSIONS, inspect_dataset


def _boxes_from_label(path, width, height):
    boxes = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        cls, cx, cy, w, h = line.split()
        cx, cy, w, h = map(float, (cx, cy, w, h))
        boxes.append({'class_id': CLASSES[int(cls)], 'box': [
            (cx-w/2)*width, (cy-h/2)*height, (cx+w/2)*width, (cy+h/2)*height]})
    return boxes


def export_validation(dataset_root, weights, output_dir, model_factory=None):
    from PIL import Image
    audit = inspect_dataset(dataset_root)
    checkpoint = Path(weights).resolve(strict=True)
    if not checkpoint.is_file() or checkpoint.suffix.lower() != '.pt':
        raise ValueError('A trusted local .pt checkpoint is required')
    root = Path(audit['root'])
    destination = Path(output_dir).resolve()
    if destination.exists():
        raise ValueError('Refusing to overwrite an existing export directory')
    if model_factory is None:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError('Install optional ultralytics after license review') from exc
        model_factory = YOLO
    model = model_factory(str(checkpoint))
    truth, predictions = [], []
    images = sorted(p for p in (root / 'val' / 'images').iterdir() if p.suffix.lower() in EXTENSIONS)
    for path in images:
        with Image.open(path) as im:
            width, height = im.size
        image_id = path.name
        truth.append({'id': image_id, 'boxes': _boxes_from_label(root / 'val' / 'labels' / (path.stem + '.txt'), width, height)})
        results = model.predict(source=str(path), conf=0.001, verbose=False)
        if len(results) != 1:
            raise ValueError('Expected one prediction result per image')
        boxes = []
        for b in results[0].boxes:
            cls = int(b.cls.item())
            conf = float(b.conf.item())
            coords = [float(v) for v in b.xyxy[0].tolist()]
            if not 0 <= cls < len(CLASSES) or not math.isfinite(conf) or not 0 <= conf <= 1:
                raise ValueError('Invalid predicted class or confidence')
            if len(coords) != 4 or not all(math.isfinite(v) for v in coords):
                raise ValueError('Invalid predicted box')
            x1, y1, x2, y2 = coords
            if x1 < 0 or y1 < 0 or x2 <= x1 or y2 <= y1 or x2 > width + 1 or y2 > height + 1:
                raise ValueError('Predicted box outside image bounds')
            boxes.append({'class_id': CLASSES[cls], 'box': coords, 'confidence': conf})
        predictions.append({'id': image_id, 'boxes': boxes})
    destination.mkdir(parents=True, exist_ok=False)
    try:
        for filename, data in [('truth.json', truth), ('predictions.json', predictions)]:
            (destination / filename).write_text(json.dumps({'images': data}, indent=2) + '\n', encoding='utf-8')
        (destination / 'audit.json').write_text(json.dumps({'dataset': audit, 'checkpoint': str(checkpoint), 'split': 'val', 'confidence_floor': 0.001}, indent=2) + '\n', encoding='utf-8')
    except Exception:
        import shutil
        shutil.rmtree(destination)
        raise
    return {'images': len(images), 'output_dir': str(destination), 'split': 'val'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-root', required=True)
    parser.add_argument('--weights', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(export_validation(args.dataset_root, args.weights, args.output_dir), indent=2))
    except (ValueError, OSError, RuntimeError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
