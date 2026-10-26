"""Read-only dataset split leakage audit. Never uses local-test for tuning.

CSV columns: image_path,split,country,group,sha256,phash. Hashes are optional;
missing fields are explicitly reported as unverified, not silently cleared.
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

SPLITS = {'train', 'val', 'heldout_country', 'local_test'}

def audit(rows, heldout_country=None, max_hamming=4):
    rows = list(rows)
    issues = []
    unknown = {'group': 0, 'sha256': 0, 'phash': 0, 'country': 0}
    groups = defaultdict(set)
    hashes = defaultdict(set)
    phashes = []
    for i, row in enumerate(rows, 2):
        split = (row.get('split') or '').strip()
        country = (row.get('country') or '').strip()
        if split not in SPLITS:
            issues.append(f'row {i}: invalid split {split!r}')
        if split == 'local_test' and (row.get('use_for_training') or '').strip().lower() in {'yes','true','1'}:
            issues.append(f'row {i}: local_test marked for training')
        if heldout_country and country == heldout_country and split in {'train', 'val'}:
            issues.append(f'row {i}: held-out country present in {split}')
        if heldout_country and split == 'heldout_country' and country != heldout_country:
            issues.append(f'row {i}: unexpected country in heldout_country split')
        for key in unknown:
            if not (row.get(key) or '').strip():
                unknown[key] += 1
        group = (row.get('group') or '').strip()
        if group: groups[(country, group)].add(split)
        sha = (row.get('sha256') or '').strip().lower()
        if sha: hashes[sha].add(split)
        ph = (row.get('phash') or '').strip().lower()
        if ph:
            try: phashes.append((int(ph, 16), split, i))
            except ValueError: issues.append(f'row {i}: invalid phash')
    for group, splits in groups.items():
        if len(splits) > 1: issues.append(f'group crosses splits: {group!r}: {sorted(splits)}')
    for sha, splits in hashes.items():
        if len(splits) > 1: issues.append(f'exact duplicate crosses splits: {sha}: {sorted(splits)}')
    # Quadratic near-duplicate check; suitable for manageable subsets, not large corpora.
    for a, (h1, s1, r1) in enumerate(phashes):
        for h2, s2, r2 in phashes[a+1:]:
            if s1 != s2 and (h1 ^ h2).bit_count() <= max_hamming:
                issues.append(f'near duplicate across splits: rows {r1},{r2} ({s1}/{s2})')
    return {'passed': not issues, 'rows': len(rows), 'issues': issues,
            'missing_metadata_counts': unknown,
            'note': 'PASS is not proof of no leakage when metadata or hashes are missing; pHash is heuristic.'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--heldout-country', required=True)
    parser.add_argument('--max-hamming', type=int, default=4)
    args = parser.parse_args()
    if not 0 <= args.max_hamming <= 64: parser.error('max-hamming must be 0..64')
    with args.manifest.open(newline='', encoding='utf-8') as f:
        result = audit(csv.DictReader(f), args.heldout_country, args.max_hamming)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['passed'] else 1)

if __name__ == '__main__': main()
