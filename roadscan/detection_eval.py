"""Offline four-class detector evaluation at a fixed IoU threshold.

JSON inputs: {"images": [{"id": "image-id", "boxes": [{"class_id": "D00",
"box": [x1,y1,x2,y2], "confidence": 0.8}]}]}. Ground truth boxes
omit confidence. All coordinates are pixels in the same original image space.
No training, model loading, image access, or downloads occur here.
"""
import argparse
import json
import math
from pathlib import Path

CLASSES = ('D00', 'D10', 'D20', 'D40')


def _read(path, prediction=False):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('images'), list):
        raise ValueError('expected an object with images list')
    images = {}
    for item in data['images']:
        if not isinstance(item, dict) or not isinstance(item.get('id'), str) or not item['id'] or item['id'] in images:
            raise ValueError('missing or duplicate image id')
        boxes = item.get('boxes')
        if not isinstance(boxes, list):
            raise ValueError('boxes must be a list')
        clean = []
        for b in boxes:
            if not isinstance(b, dict) or b.get('class_id') not in CLASSES:
                raise ValueError('invalid class id')
            xy = b.get('box')
            if not isinstance(xy, list) or len(xy) != 4 or any(type(v) not in (int, float) or not math.isfinite(v) for v in xy):
                raise ValueError('invalid box coordinates')
            x1, y1, x2, y2 = xy
            if x1 < 0 or y1 < 0 or x2 <= x1 or y2 <= y1:
                raise ValueError('invalid box extent')
            conf = b.get('confidence', 1)
            if prediction and (type(conf) not in (int, float) or not math.isfinite(conf) or not 0 <= conf <= 1):
                raise ValueError('invalid confidence')
            clean.append({'class_id': b['class_id'], 'box': xy, 'confidence': float(conf) if prediction else 1.0})
        images[item['id']] = clean
    return images


def iou(a, b):
    left, top = max(a[0], b[0]), max(a[1], b[1])
    right, bottom = min(a[2], b[2]), min(a[3], b[3])
    intersection = max(0, right-left) * max(0, bottom-top)
    union = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - intersection
    return intersection / union


def evaluate(ground_truth, predictions, threshold=0.5, confidence=0.25):
    if not (0 < threshold <= 1 and 0 <= confidence <= 1):
        raise ValueError('threshold and confidence outside valid range')
    if set(ground_truth) != set(predictions):
        raise ValueError('ground truth and predictions must contain identical image ids')
    counts = {c: {'tp': 0, 'fp': 0, 'fn': 0} for c in CLASSES}
    for image_id, truth in ground_truth.items():
        pred = predictions[image_id]
        for cls in CLASSES:
            gt_boxes = [b['box'] for b in truth if b['class_id'] == cls]
            candidates = sorted((b for b in pred if b['class_id'] == cls and b['confidence'] >= confidence), key=lambda b: -b['confidence'])
            matched = set()
            for candidate in candidates:
                options = [(iou(candidate['box'], gt), j) for j, gt in enumerate(gt_boxes) if j not in matched]
                best_iou, best_j = max(options, default=(0, -1))
                if best_iou >= threshold:
                    matched.add(best_j)
                    counts[cls]['tp'] += 1
                else:
                    counts[cls]['fp'] += 1
            counts[cls]['fn'] += len(gt_boxes) - len(matched)
    result = {}
    for cls, c in counts.items():
        tp, fp, fn = c['tp'], c['fp'], c['fn']
        result[cls] = {**c, 'precision': tp/(tp+fp) if tp+fp else None,
                       'recall': tp/(tp+fn) if tp+fn else None,
                       'f1': 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}
    return {'images': len(ground_truth), 'iou_threshold': threshold, 'confidence_threshold': confidence,
            'per_class': result, 'note': 'Fixed-threshold detection precision/recall/F1, NOT AP or mAP. Empty denominators are null.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ground-truth', required=True, type=Path)
    p.add_argument('--predictions', required=True, type=Path)
    p.add_argument('--iou', type=float, default=0.5)
    p.add_argument('--confidence', type=float, default=0.25)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    try:
        result = evaluate(_read(args.ground_truth), _read(args.predictions, True), args.iou, args.confidence)
        payload = json.dumps(result, indent=2)
        if args.output:
            if args.output.exists():
                raise ValueError('refusing to overwrite existing evaluation')
            args.output.write_text(payload + '\n', encoding='utf-8')
        print(payload)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        p.error(str(exc))


if __name__ == '__main__':
    main()
