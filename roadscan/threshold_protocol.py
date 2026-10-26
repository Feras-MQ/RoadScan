"""E5 pHash pair threshold selection on validation and frozen test evaluation.

Validation CSV must have left,right,same,split columns. Test mode never optimizes.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from .duplicate_eval import evaluate


def read_pairs(path, split):
    with path.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        if not {'left', 'right', 'same', 'split'}.issubset(reader.fieldnames or []):
            raise ValueError('CSV requires left,right,same,split')
        rows = list(reader)
    if any(r['split'] not in ('validation', 'test') for r in rows):
        raise ValueError('Only validation and test splits are supported')
    selected = [r for r in rows if r['split'] == split]
    if not selected:
        raise ValueError(f'No {split} pairs available')
    if any(r['same'] not in ('0', '1') for r in selected):
        raise ValueError('Labels must be 0 or 1')
    return selected


def select_threshold(rows, root):
    """Maximize validation F1; tie-break toward higher threshold (fewer false alerts)."""
    if not any(r['same'] == '1' for r in rows) or not any(r['same'] == '0' for r in rows):
        raise ValueError('Validation needs both positive and negative pairs')
    best = None
    for step in range(65):
        threshold = step / 64
        result = evaluate(rows, root, threshold)
        p, r = result['precision'] or 0, result['recall'] or 0
        f1 = 2 * p * r / (p + r) if p + r else 0
        if best is None or (f1, threshold) > (best['f1'], best['threshold']):
            best = {**result, 'f1': f1}
    return best


def freeze(rows, root, source_path):
    best = select_threshold(rows, root)
    return {'protocol': 'roadscan-e5-phash-pairs-v1', 'selection_split': 'validation',
            'selection_metric': 'f1', 'threshold': best['threshold'],
            'validation': best, 'validation_csv_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest()}


def test_frozen(rows, root, frozen):
    if frozen.get('protocol') != 'roadscan-e5-phash-pairs-v1' or frozen.get('selection_split') != 'validation':
        raise ValueError('Invalid frozen validation protocol')
    threshold = frozen.get('threshold')
    if type(threshold) not in (float, int) or not 0 <= threshold <= 1:
        raise ValueError('Invalid frozen threshold')
    result = evaluate(rows, root, threshold)
    return {'protocol': frozen['protocol'], 'selection_split': 'validation', 'evaluation_split': 'test',
            'validation_csv_sha256': frozen.get('validation_csv_sha256'), 'test': result}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    for name in ('freeze', 'test'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--pairs', required=True, type=Path)
        cmd.add_argument('--image-root', required=True, type=Path)
        if name == 'freeze':
            cmd.add_argument('--output', required=True, type=Path)
        else:
            cmd.add_argument('--frozen', required=True, type=Path)
    args = p.parse_args()
    if args.command == 'freeze':
        result = freeze(read_pairs(args.pairs, 'validation'), args.image_root, args.pairs)
        if args.output.exists():
            p.error('Output exists: refusing to overwrite frozen protocol')
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    else:
        frozen = json.loads(args.frozen.read_text(encoding='utf-8'))
        result = test_frozen(read_pairs(args.pairs, 'test'), args.image_root, frozen)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
