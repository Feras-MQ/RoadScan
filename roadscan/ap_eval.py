"""Offline confidence-ranked detector AP50 and AP50:95 (101-point interpolation).

This is a transparent reference evaluator, not a COCOeval replacement: it does
not implement crowd/ignore flags, area ranges, or max detections per image.
"""
import argparse
import json
from pathlib import Path
from .detection_eval import CLASSES, _read, iou

IOU_THRESHOLDS = tuple(round(0.50 + 0.05 * i, 2) for i in range(10))


def average_precision(truth, predictions, cls, threshold):
    """Return None for classes with no ground truth; otherwise 101-point AP."""
    targets = {(image_id, j): box['box']
               for image_id, boxes in truth.items()
               for j, box in enumerate(boxes) if box['class_id'] == cls}
    if not targets:
        return None
    candidates = [(box['confidence'], image_id, j, box['box'])
                  for image_id, boxes in predictions.items()
                  for j, box in enumerate(boxes) if box['class_id'] == cls]
    candidates.sort(key=lambda row: (-row[0], row[1], row[2]))
    matched = set()
    tp = fp = 0
    points = []
    for _, image_id, _, pred_box in candidates:
        choices = [(iou(pred_box, gt_box), j)
                   for (img, j), gt_box in targets.items()
                   if img == image_id and (img, j) not in matched]
        overlap, j = max(choices, default=(0.0, -1))
        if overlap >= threshold:
            tp += 1
            matched.add((image_id, j))
        else:
            fp += 1
        points.append((tp / len(targets), tp / (tp + fp)))
    return sum(max((precision for recall, precision in points if recall >= k / 100), default=0.0)
               for k in range(101)) / 101


def evaluate_ap(truth, predictions):
    if set(truth) != set(predictions):
        raise ValueError('ground truth and predictions must contain identical image ids')
    results = {}
    for cls in CLASSES:
        scores = [average_precision(truth, predictions, cls, threshold)
                  for threshold in IOU_THRESHOLDS]
        results[cls] = {'ap50': scores[0],
                        'ap50_95': sum(scores) / len(scores) if scores[0] is not None else None,
                        'ground_truth_boxes': sum(b['class_id'] == cls for boxes in truth.values() for b in boxes)}
    valid = [v for v in results.values() if v['ap50'] is not None]
    return {'images': len(truth), 'per_class': results,
            'map50': sum(v['ap50'] for v in valid) / len(valid) if valid else None,
            'map50_95': sum(v['ap50_95'] for v in valid) / len(valid) if valid else None,
            'included_classes': len(valid),
            'method': '101-point interpolated AP, IoU 0.50:0.05:0.95; classes without ground truth excluded',
            'limitations': 'Not COCOeval: no crowd/ignore handling, area ranges, or max-detection caps.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ground-truth', type=Path, required=True)
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = evaluate_ap(_read(args.ground_truth), _read(args.predictions, prediction=True))
        payload = json.dumps(result, indent=2) + '\n'
        if args.output:
            with args.output.open('x', encoding='utf-8') as handle:
                handle.write(payload)
        print(payload, end='')
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
