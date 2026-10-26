"""Trainable, offline image-level multilabel baseline (not a damage detector).

CSV: image,split,D00,D10,D20,D40. Split must be train/validation/test;
labels are 0/1. Never train or select using test images.
Requires numpy and scikit-learn as explicitly installed optional dependencies.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from PIL import Image

CLASSES = ('D00', 'D10', 'D20', 'D40')
SPLITS = ('train', 'validation', 'test')


def load_manifest(path, image_root):
    root = Path(image_root).resolve(strict=True)
    with open(path, newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not {'image', 'split', *CLASSES}.issubset(reader.fieldnames):
            raise ValueError('Expected CSV columns: image,split,D00,D10,D20,D40')
        rows = []
        seen_paths = set()
        seen_hashes = {}
        for line, row in enumerate(reader, 2):
            rel = Path(row['image'] or '')
            if not rel.parts or rel.is_absolute() or '..' in rel.parts:
                raise ValueError(f'Unsafe image path at line {line}')
            full = (root / rel).resolve(strict=True)
            if not full.is_relative_to(root) or not full.is_file():
                raise ValueError(f'Image outside approved root at line {line}')
            split = row['split']
            if split not in SPLITS:
                raise ValueError(f'Invalid split at line {line}')
            if full in seen_paths:
                raise ValueError(f'Duplicate image path at line {line}')
            seen_paths.add(full)
            labels = []
            for cls in CLASSES:
                if row[cls] not in ('0', '1'):
                    raise ValueError(f'Invalid {cls} label at line {line}')
                labels.append(int(row[cls]))
            digest = hashlib.sha256(full.read_bytes()).hexdigest()
            if digest in seen_hashes and seen_hashes[digest] != split:
                raise ValueError('Exact duplicate image across splits')
            seen_hashes[digest] = split
            rows.append((full, split, labels))
    if not rows:
        raise ValueError('Empty manifest')
    return rows


def image_features(path):
    """Fixed RGB histogram + small spatial mean features, independent of image size."""
    import numpy as np
    with Image.open(path) as im:
        arr = np.asarray(im.convert('RGB').resize((32, 32)), dtype=np.float32) / 255.0
    hist = [np.histogram(arr[:, :, c], bins=8, range=(0, 1))[0] / 1024.0 for c in range(3)]
    spatial = [arr[y:y+8, x:x+8].mean(axis=(0, 1)) for y in range(0, 32, 8) for x in range(0, 32, 8)]
    return np.concatenate([*hist, *spatial]).astype(float).tolist()


def metrics(y_true, y_pred):
    results = {}
    for j, cls in enumerate(CLASSES):
        tp = sum(a[j] == 1 and b[j] == 1 for a, b in zip(y_true, y_pred))
        fp = sum(a[j] == 0 and b[j] == 1 for a, b in zip(y_true, y_pred))
        fn = sum(a[j] == 1 and b[j] == 0 for a, b in zip(y_true, y_pred))
        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None
        results[cls] = dict(tp=tp, fp=fp, fn=fn, precision=precision, recall=recall, f1=f1)
    return results


def train(rows):
    """Train per-class logistic regression; constant-label classes use constant predictors."""
    try:
        import numpy as np
        from sklearn.linear_model import LogisticRegression
    except ImportError as exc:
        raise RuntimeError('Install optional numpy and scikit-learn to train baseline') from exc
    training = [(p, y) for p, s, y in rows if s == 'train']
    if not training:
        raise ValueError('At least one train image is required')
    x = np.asarray([image_features(p) for p, _ in training])
    labels = np.asarray([y for _, y in training])
    models = []
    for i in range(len(CLASSES)):
        if len(set(labels[:, i])) == 1:
            models.append({'constant': int(labels[0, i])})
        else:
            model = LogisticRegression(random_state=42, max_iter=1000, solver='liblinear')
            model.fit(x, labels[:, i])
            models.append({'coef': model.coef_[0].tolist(), 'intercept': float(model.intercept_[0])})
    return {'classes': list(CLASSES), 'features': 'rgb_hist8_spatial4x4_v1', 'models': models, 'threshold': 0.5}


def predict(model, paths):
    import math
    if model.get('classes') != list(CLASSES) or model.get('features') != 'rgb_hist8_spatial4x4_v1':
        raise ValueError('Unsupported baseline model format')
    result = []
    for path in paths:
        x = image_features(path)
        predictions = []
        for entry in model['models']:
            if 'constant' in entry:
                predictions.append(int(entry['constant']))
            else:
                z = sum(a*b for a, b in zip(x, entry['coef'])) + entry['intercept']
                prob = 1 / (1 + math.exp(-max(-700, min(700, z))))
                predictions.append(int(prob >= model['threshold']))
        result.append(predictions)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--image-root', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    output = Path(args.output)
    if output.exists():
        parser.error('Refusing to overwrite existing output')
    rows = load_manifest(args.manifest, args.image_root)
    model = train(rows)
    validation = [(p, y) for p, s, y in rows if s == 'validation']
    result = {'model': model, 'train_count': sum(s == 'train' for _, s, _ in rows),
              'validation_count': len(validation), 'validation_metrics': None,
              'test_count_not_evaluated': sum(s == 'test' for _, s, _ in rows)}
    if validation:
        result['validation_metrics'] = metrics([y for _, y in validation], predict(model, [p for p, _ in validation]))
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'train_count': result['train_count'], 'validation_count': len(validation), 'output': str(output)}))


if __name__ == '__main__':
    main()
