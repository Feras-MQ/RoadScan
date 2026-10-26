"""Offline pHash duplicate-pair evaluation; never tunes on final test pairs.

CSV columns: left,right,same,split. Images must be authorized local files.
ResNet and DINOv2 are deliberately NOT silently substituted for pHash.
"""
import argparse
import csv
import json
import math
from pathlib import Path
from PIL import Image


def phash(path):
    """64-bit DCT perceptual hash (CPU reference implementation)."""
    with Image.open(path) as im:
        im = im.convert('L').resize((32, 32))
        pixels = list(im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata())
    coeffs = []
    for u in range(8):
        for v in range(8):
            total = 0.0
            for x in range(32):
                cx = math.cos((2*x+1)*u*math.pi/64)
                for y in range(32):
                    total += pixels[y*32+x]*cx*math.cos((2*y+1)*v*math.pi/64)
            coeffs.append(total)
    median = sorted(coeffs[1:])[31]
    return sum((1 << i) for i, value in enumerate(coeffs) if value > median)


def similarity(a, b):
    return 1.0 - ((a ^ b).bit_count() / 64.0)


def evaluate(rows, root, threshold):
    cache = {}
    tp = fp = tn = fn = 0
    for row in rows:
        label = str(row['same']).strip()
        if label not in ('0', '1'):
            raise ValueError('same must be 0 or 1')
        images = []
        for key in ('left', 'right'):
            relative = Path(row[key])
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Image paths must stay within the approved dataset root')
            path = (root / relative).resolve()
            if not path.is_relative_to(root.resolve()):
                raise ValueError('Image path escapes dataset root')
            if path not in cache:
                cache[path] = phash(path)
            images.append(cache[path])
        predicted = similarity(*images) >= threshold
        positive = label == '1'
        if predicted and positive: tp += 1
        elif predicted: fp += 1
        elif positive: fn += 1
        else: tn += 1
    return {'pairs': len(rows), 'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn,
            'precision': tp/(tp+fp) if tp+fp else None,
            'recall': tp/(tp+fn) if tp+fn else None,
            'threshold': threshold, 'method': 'phash',
            'recall_at_1': None, 'recall_at_5': None,
            'note': 'Pair classification only; retrieval Recall@K requires a ranked gallery.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pairs', type=Path)
    parser.add_argument('--image-root', type=Path, required=True)
    parser.add_argument('--split', choices=['validation', 'test'], required=True)
    parser.add_argument('--threshold', type=float, required=True,
                        help='Threshold must be frozen on validation before test evaluation')
    args = parser.parse_args()
    if not 0 <= args.threshold <= 1:
        parser.error('threshold must be between 0 and 1')
    with args.pairs.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not {'left', 'right', 'same', 'split'}.issubset(reader.fieldnames or []):
            parser.error('CSV must contain left,right,same,split')
        rows = [row for row in reader if row['split'] == args.split]
    if not rows:
        parser.error('No pairs for selected split; no metrics computed')
    print(json.dumps(evaluate(rows, args.image_root, args.threshold), indent=2))


if __name__ == '__main__':
    main()
