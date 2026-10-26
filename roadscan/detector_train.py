"""Validate a local YOLO dataset and optionally train an offline detector.

Directory layout: root/{train,val}/{images,labels}/stem.{jpg,png,...|txt}.
Test images must never appear in this training root. Training requires a
locally supplied YOLO model checkpoint and an optional Ultralytics install.
"""
import argparse
import hashlib
import json
from pathlib import Path

CLASSES = ('D00', 'D10', 'D20', 'D40')
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}


def inspect_dataset(root):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Dataset root must be a directory')
    if (root / 'test').exists():
        raise ValueError('Keep final test images outside the training dataset root')
    counts = {}
    seen_hashes = {}
    for split in ('train', 'val'):
        images_dir = root / split / 'images'
        labels_dir = root / split / 'labels'
        if not images_dir.is_dir() or not labels_dir.is_dir():
            raise ValueError(f'Missing {split}/images or {split}/labels')
        images = sorted(p for p in images_dir.iterdir() if p.suffix.lower() in EXTENSIONS)
        if not images:
            raise ValueError(f'No images in {split}')
        stems = set()
        for image in images:
            if image.is_symlink() or not image.is_file() or image.stem in stems:
                raise ValueError(f'Unsafe or ambiguous image: {image}')
            stems.add(image.stem)
            label = labels_dir / (image.stem + '.txt')
            if label.is_symlink() or not label.is_file():
                raise ValueError(f'Missing label file: {label}')
            digest = hashlib.sha256(image.read_bytes()).hexdigest()
            if digest in seen_hashes and seen_hashes[digest] != split:
                raise ValueError('Exact duplicate image across train and val')
            seen_hashes[digest] = split
            for line_number, line in enumerate(label.read_text(encoding='utf-8').splitlines(), 1):
                if not line.strip():
                    continue
                tokens = line.split()
                if len(tokens) != 5:
                    raise ValueError(f'Invalid YOLO annotation: {label}:{line_number}')
                try:
                    class_id = int(tokens[0])
                    coords = [float(value) for value in tokens[1:]]
                except ValueError as exc:
                    raise ValueError(f'Invalid YOLO annotation: {label}:{line_number}') from exc
                import math
                if not 0 <= class_id < 4 or not all(math.isfinite(x) for x in coords):
                    raise ValueError(f'Invalid class or nonfinite coordinate: {label}:{line_number}')
                cx, cy, w, h = coords
                # Decimal serialization can put a boundary a few floating-point ULPs outside 0/1.
                tolerance = 1e-9
                if not (0 < w <= 1 and 0 < h <= 1 and -tolerance <= cx-w/2 and cx+w/2 <= 1+tolerance and -tolerance <= cy-h/2 and cy+h/2 <= 1+tolerance):
                    raise ValueError(f'Out-of-bounds box: {label}:{line_number}')
        extra_labels = {p.stem for p in labels_dir.glob('*.txt')} - stems
        if extra_labels:
            raise ValueError(f'Orphan labels in {split}: {sorted(extra_labels)[0]}')
        counts[split] = len(images)
    return {'root': str(root), 'classes': list(CLASSES), 'image_counts': counts,
            'warning': 'Exact hashes only; separately audit sequence, country, and near-duplicate leakage.'}


def run_training(root, weights, epochs, imgsz, project, name, device='cpu', seed=0, augmentation='standard'):
    if epochs < 1 or imgsz < 32:
        raise ValueError('epochs must be >= 1 and imgsz >= 32')
    if augmentation not in {'standard','none','vertical_flip'} or seed<0:raise ValueError('Invalid augmentation or seed')
    info = inspect_dataset(root)
    checkpoint = Path(weights).resolve(strict=True)
    if not checkpoint.is_file() or checkpoint.suffix.lower() != '.pt':
        raise ValueError('Supply a local .pt checkpoint; no automatic downloads')
    destination = Path(project).resolve()
    if (destination / name).exists():
        raise ValueError('Refusing to overwrite an existing experiment directory')
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError('Install optional ultralytics after reviewing its license') from exc
    # Use an absolute dataset YAML written inside the experiment directory.
    destination.mkdir(parents=True, exist_ok=True)
    experiment = destination / name
    experiment.mkdir(exist_ok=False)
    yaml_path = experiment / 'dataset.yaml'
    yaml_path.write_text('path: ' + json.dumps(info['root']) + '\ntrain: train/images\nval: val/images\nnames:\n' +
                         ''.join(f'  {i}: {cls}\n' for i, cls in enumerate(CLASSES)), encoding='utf-8')
    (experiment / 'dataset_audit.json').write_text(json.dumps(info, indent=2) + '\n', encoding='utf-8')
    model = YOLO(str(checkpoint))
    augment={}
    if augmentation=='none':augment=dict(hsv_h=0,hsv_s=0,hsv_v=0,degrees=0,translate=0,scale=0,shear=0,perspective=0,flipud=0,fliplr=0,mosaic=0,mixup=0,copy_paste=0)
    elif augmentation=='vertical_flip':augment={'flipud':.5}
    model.train(data=str(yaml_path), epochs=epochs, imgsz=imgsz, device=device,seed=seed,deterministic=True,
                project=str(destination), name=name, exist_ok=True,**augment)
    metrics=model.val(data=str(yaml_path),split='val',imgsz=imgsz,device=device)
    (experiment/'validation_metrics.json').write_text(json.dumps({'split':'validation_not_test','metrics':{k:float(v) for k,v in metrics.results_dict.items()}},indent=2))
    return info


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-root', required=True)
    parser.add_argument('--weights', help='Existing local YOLO .pt checkpoint; required for --train')
    parser.add_argument('--train', action='store_true', help='Run optional CPU training after audit')
    parser.add_argument('--epochs', type=int, default=30)
    parser.add_argument('--imgsz', type=int, default=640)
    parser.add_argument('--project', default='experiments/detector_runs')
    parser.add_argument('--name', default='e2_local')
    parser.add_argument('--device',default='cpu')
    parser.add_argument('--seed',type=int,default=0)
    parser.add_argument('--augmentation',choices=['standard','none','vertical_flip'],default='standard')
    args = parser.parse_args(argv)
    try:
        if args.train:
            if not args.weights:
                parser.error('--train requires --weights')
            result = run_training(args.dataset_root, args.weights, args.epochs, args.imgsz, args.project, args.name,args.device,args.seed,args.augmentation)
        else:
            result = inspect_dataset(args.dataset_root)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, RuntimeError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
