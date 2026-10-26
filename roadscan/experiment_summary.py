"""Summarize frozen validation detector exports without training or touching test data.

Manifest JSON: {"split":"val","experiments":[{"id":"E2","export_dir":"..."}, ...]}
Each export directory must contain truth.json, predictions.json, audit.json.
"""
import argparse
import hashlib
import json
from pathlib import Path
from .ap_eval import evaluate_ap
from .detection_eval import _read


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(manifest_path, output_path):
    manifest_path = Path(manifest_path).resolve(strict=True)
    output_path = Path(output_path).resolve()
    if output_path.exists():
        raise ValueError('Refusing to overwrite an existing summary')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if not isinstance(manifest, dict) or manifest.get('split') != 'val':
        raise ValueError('Only explicit validation manifests are supported')
    experiments = manifest.get('experiments')
    if not isinstance(experiments, list) or not experiments:
        raise ValueError('Provide a nonempty experiments list')
    rows, ids, reference_truth = [], set(), None
    for entry in experiments:
        if not isinstance(entry, dict) or set(entry) != {'id', 'export_dir'}:
            raise ValueError('Each experiment needs id and export_dir only')
        name = entry['id']
        if not isinstance(name, str) or not name or name in ids or any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-' for c in name):
            raise ValueError('Invalid or duplicate experiment id')
        ids.add(name)
        directory = (manifest_path.parent / entry['export_dir']).resolve(strict=True)
        if not directory.is_dir():
            raise ValueError('Export path must be a directory')
        truth_path, pred_path, audit_path = (directory / p for p in ('truth.json', 'predictions.json', 'audit.json'))
        audit = json.loads(audit_path.read_text(encoding='utf-8'))
        if audit.get('split') != 'val':
            raise ValueError('Refusing a non-validation export')
        truth_hash = _digest(truth_path)
        if reference_truth is None:
            reference_truth = truth_hash
        elif reference_truth != truth_hash:
            raise ValueError('Experiments must use byte-identical validation ground truth')
        metrics = evaluate_ap(_read(truth_path), _read(pred_path, prediction=True))
        rows.append({'id': name, 'metrics': metrics, 'truth_sha256': truth_hash,
                     'predictions_sha256': _digest(pred_path), 'audit_sha256': _digest(audit_path)})
    result = {'split': 'val', 'manifest_sha256': _digest(manifest_path), 'experiments': rows,
              'note': 'Validation-only reference AP. No trained-model performance claimed without actual exports.'}
    with output_path.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        result = summarize(args.manifest, args.output)
        print(json.dumps({'split': result['split'], 'experiments': len(result['experiments']), 'output': args.output}))
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
