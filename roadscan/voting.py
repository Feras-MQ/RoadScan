"""Transparent class-aware voting. Agreement is not a calibrated probability."""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from .review import validate_detections


def iou(a, b):
    intersection = max(0, min(a[2], b[2])-max(a[0], b[0])) * max(0, min(a[3], b[3])-max(a[1], b[1]))
    union = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - intersection
    return intersection / union if union else 0


def fuse_votes(outputs, width, height, threshold=.5):
    """One vote per distinct checkpoint per cluster, matched to a fixed seed box.

    Two models require both; three require two. Unsupported classes abstain but
    a class always needs two supporting models. Failed models invalidate consensus.
    """
    if len(outputs) not in (2, 3) or len({x['id'] for x in outputs}) != len(outputs):
        raise ValueError('Select two or three different checkpoints')
    if any(x['state'] != 'completed' for x in outputs):
        return {'state': 'partial', 'consensus': [], 'agreements': [], 'disagreements': [],
                'reason': 'A model did not finish; no consensus was produced'}
    candidates = []
    for result in outputs:
        for detection in validate_detections(result['detections'], width, height):
            candidates.append({**detection, 'model_id': result['id']})
    candidates.sort(key=lambda d: (-d['confidence'], d['model_id'], d['box']))
    clusters = []
    for detection in candidates:
        matches = [(iou(detection['box'], c[0]['box']), c) for c in clusters
                   if c[0]['class_id'] == detection['class_id']
                   and detection['model_id'] not in {x['model_id'] for x in c}]
        best = max(matches, key=lambda value: value[0], default=(0, None))
        if best[0] >= threshold:
            best[1].append(detection)
        else:
            clusters.append([detection])
    agreements, disagreements = [], []
    for cluster in clusters:
        class_id = cluster[0]['class_id']
        eligible = sum(class_id in x['classes'] for x in outputs)
        required = max(2, eligible // 2 + 1)
        weights = [max(d['confidence'], .00001) for d in cluster]
        box = [round(sum(d['box'][i]*w for d, w in zip(cluster, weights))/sum(weights), 2) for i in range(4)]
        detection = {'class_id': class_id, 'box': box,
                     'confidence': round(sum(d['confidence'] for d in cluster)/len(cluster), 5)}
        entry = {'detection': detection, 'votes': len(cluster), 'eligible_models': eligible,
                 'required_votes': required, 'model_ids': [d['model_id'] for d in cluster]}
        (agreements if len(cluster) >= required else disagreements).append(entry)
    # With 2-3 inputs and a >=2 quorum there can be at most 150 agreements.
    agreements.sort(key=lambda x: (-x['votes'], -x['detection']['confidence']))
    selected = agreements[:100]
    return {'state': 'completed', 'consensus': [x['detection'] for x in selected],
            'agreements': selected, 'disagreements': disagreements,
            'truncated_agreements': max(0, len(agreements)-100), 'reason': None}


def run_model(item, checkpoint, image_path):
    """A short-lived sequential worker releases all tensor memory on exit.

    This is process/lifetime isolation, not a sandbox for untrusted checkpoints.
    No API keys, database settings or cloud credentials are forwarded to it.
    """
    started = time.perf_counter()
    result = {'id': item['sha256'], 'name': item['name'], 'classes': list(item['classes'].values()),
              'state': 'failed', 'reason': 'worker_failed', 'detections': [], 'model_version': item['file']+'@'+item['sha256'][:12]}
    environment = {k: v for k, v in os.environ.items() if k in {
        'PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PYTHONPATH', 'HOME',
        'YOLO_CONFIG_DIR', 'MPLCONFIGDIR', 'ROADSCAN_INFERENCE_THREADS'}}
    environment.update(YOLO_AUTOINSTALL='false', TORCH_FORCE_WEIGHTS_ONLY_LOAD='1', OMP_NUM_THREADS='2', MALLOC_ARENA_MAX='2')
    app_root = str(Path(__file__).resolve().parent.parent)
    environment['PYTHONPATH'] = app_root
    with tempfile.TemporaryDirectory(prefix='roadscan-vote-') as folder:
        output = Path(folder)/'result.json'
        payload = {'path': str(checkpoint), 'sha256': item['sha256'], 'imgsz': item['imgsz'],
                   'image': str(image_path), 'output': str(output)}
        if item.get('confidence_profile'):
            payload['confidence_profile'] = item['confidence_profile']
        try:
            completed = subprocess.run([sys.executable, '-m', 'roadscan.vote_worker'],
                                       input=json.dumps(payload), text=True, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL, env=environment, cwd=app_root, timeout=90, check=False)
            if completed.returncode == 0 and output.exists():
                data = json.loads(output.read_text(encoding='utf-8'))
                result.update(state=data['state'], reason=data['reason'], detections=data['detections'])
            elif completed.returncode < 0 or completed.returncode in (0xC0000017, 0xC000009A):
                result['reason'] = 'worker_stopped_resource_limit'
        except subprocess.TimeoutExpired:
            result['reason'] = 'worker_timeout_90s'
        except (OSError, ValueError, KeyError):
            result['reason'] = 'worker_unavailable'
    result['elapsed_ms'] = round((time.perf_counter()-started)*1000, 2)
    return result
