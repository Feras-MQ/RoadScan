"""Offline E5 ranked retrieval with pHash or locally supplied neural checkpoints."""
import argparse
import csv
import json
from pathlib import Path
from .duplicate_eval import phash, similarity
from .feature_embeddings import OfflineEmbedder, cosine_similarity


def read_manifest(path, split):
    with path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not {'image', 'damage_id', 'split'}.issubset(reader.fieldnames or []):
            raise ValueError('Manifest requires image,damage_id,split')
        rows = [r for r in reader if r['split'] == split]
    if not rows:
        raise ValueError('No records in requested split')
    if any(not r['image'].strip() or not r['damage_id'].strip() for r in rows):
        raise ValueError('Blank image or damage_id')
    return rows


def secure_image(root, name):
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Image path outside authorized root')
    root = root.resolve()
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise ValueError('Missing or unauthorized image')
    return candidate


def evaluate_retrieval(queries, gallery, root, method='phash', checkpoint=None, embedder=None):
    """Return Recall@1/5 over eligible queries; never rank the same physical file."""
    if method not in ('phash', 'resnet18', 'dinov2_vits14'):
        raise ValueError('Unsupported retrieval method')
    if method != 'phash' and embedder is None:
        if checkpoint is None:
            raise ValueError('Neural retrieval requires --checkpoint')
        embedder = OfflineEmbedder(method, checkpoint)
    cache = {}
    def get_feature(name):
        path = secure_image(root, name)
        if path not in cache:
            cache[path] = phash(path) if method == 'phash' else embedder.encode(path)
        return path, cache[path]
    indexed = [(r, *get_feature(r['image'])) for r in gallery]
    eligible = hits1 = hits5 = 0
    for q in queries:
        qpath, qfeature = get_feature(q['image'])
        candidates = [(r, similarity(qfeature, feat) if method == 'phash' else cosine_similarity(qfeature, feat))
                      for r, path, feat in indexed if path != qpath]
        if not any(r['damage_id'] == q['damage_id'] for r, _ in candidates):
            continue
        eligible += 1
        ranked = sorted(candidates, key=lambda item: (-item[1], item[0]['image']))
        hits1 += any(r['damage_id'] == q['damage_id'] for r, _ in ranked[:1])
        hits5 += any(r['damage_id'] == q['damage_id'] for r, _ in ranked[:5])
    return {'method': method, 'eligible_queries': eligible, 'total_queries': len(queries),
            'recall_at_1': hits1 / eligible if eligible else None,
            'recall_at_5': hits5 / eligible if eligible else None,
            'note': 'No eligible queries means no retrieval metric; synthetic tests are not performance evidence.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--queries', type=Path, required=True)
    p.add_argument('--gallery', type=Path, required=True)
    p.add_argument('--image-root', type=Path, required=True)
    p.add_argument('--split', choices=['validation', 'test'], required=True)
    p.add_argument('--method', choices=['phash', 'resnet18', 'dinov2_vits14'], default='phash')
    p.add_argument('--checkpoint', type=Path)
    a = p.parse_args()
    if a.method != 'phash' and a.checkpoint is None:
        p.error('--checkpoint is required for neural embedding methods')
    result = evaluate_retrieval(read_manifest(a.queries, a.split), read_manifest(a.gallery, a.split),
                                a.image_root, method=a.method, checkpoint=a.checkpoint)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
