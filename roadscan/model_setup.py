"""Install a locally supplied four-class YOLO checkpoint for the Windows starter.

No network access, pickle inspection, or model loading occurs in this command.
Only load checkpoints from a source you trust: PyTorch .pt files can execute code.
"""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

CLASSES = ('D00', 'D10', 'D20', 'D40')
CONFIG_NAME = 'local_model.json'


def install(source, root, *, overwrite=False):
    root = Path(root).resolve()
    source = Path(source).resolve(strict=True)
    if not source.is_file() or source.suffix.lower() != '.pt':
        raise ValueError('Select a local Ultralytics YOLO .pt file')
    if source.is_symlink():
        raise ValueError('Checkpoint symlinks are not accepted')
    if source.stat().st_size == 0:
        raise ValueError('Checkpoint is empty')
    models = root / 'models'
    models.mkdir(parents=True, exist_ok=True)
    target = models / 'roadscan_best.pt'
    config = root / CONFIG_NAME
    if not overwrite and (target.exists() or config.exists()):
        raise FileExistsError('Model already installed; use --replace to replace it intentionally')
    if source != target:
        staging = models / 'roadscan_best.pt.tmp'
        try:
            with source.open('rb') as inp, staging.open('wb') as out:
                shutil.copyfileobj(inp, out)
            os.replace(staging, target)
        finally:
            staging.unlink(missing_ok=True)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    payload = {'format': 'ultralytics_yolo_pt', 'checkpoint': 'models/roadscan_best.pt',
               'sha256': digest, 'expected_classes': list(CLASSES),
               'validation': 'class names verified at server load, not during installation'}
    tmp = root / (CONFIG_NAME + '.tmp')
    try:
        tmp.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
        os.replace(tmp, config)
    finally:
        tmp.unlink(missing_ok=True)
    return payload


def configured_checkpoint(root):
    root = Path(root).resolve()
    config = root / CONFIG_NAME
    if not config.exists():
        return None
    data = json.loads(config.read_text(encoding='utf-8'))
    if data.get('format') != 'ultralytics_yolo_pt' or data.get('expected_classes') != list(CLASSES):
        raise ValueError('Invalid local model configuration')
    if data.get('checkpoint') != 'models/roadscan_best.pt':
        raise ValueError('Model path must remain inside the project models directory')
    target = root / 'models' / 'roadscan_best.pt'
    if not target.is_file() or target.is_symlink():
        raise ValueError('Configured model checkpoint is missing or unsafe')
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    if digest != data.get('sha256'):
        raise ValueError('Model checkpoint hash changed; reinstall a trusted checkpoint')
    return str(target)


def main(argv=None):
    p = argparse.ArgumentParser(description='Install a trusted, locally exported YOLO .pt checkpoint')
    p.add_argument('--weights', required=True, help='Path to the trained best.pt file')
    p.add_argument('--replace', action='store_true')
    args = p.parse_args(argv)
    root = Path(__file__).resolve().parent.parent
    try:
        result = install(args.weights, root, overwrite=args.replace)
    except (ValueError, OSError) as exc:
        p.error(str(exc))
    print('Installed local checkpoint; restart RoadScan. SHA-256:', result['sha256'])
    print('Class mapping and model compatibility are checked when RoadScan starts.')
    print('WARNING: Only load checkpoints from trusted sources; .pt files can execute code.')


if __name__ == '__main__':
    main()
