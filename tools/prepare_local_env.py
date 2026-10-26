"""Prepare a local CPU workspace without overwriting existing access settings."""
import hashlib
import json
import math
import os
from pathlib import Path
import secrets


def prepare(root):
    root = Path(root)
    destination = root / '.env'
    if destination.exists():
        return 'Existing .env preserved.'
    values = {'ROADSCAN_API_KEY': secrets.token_urlsafe(32), 'ROADSCAN_WITH_DETECTOR': '1'}
    record_path = root / 'models/roadscan_model.json'
    if record_path.is_file():
        record = json.loads(record_path.read_text(encoding='utf-8-sig'))
        with (root / 'models/roadscan_best.pt').open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != record['sha256']:
            raise ValueError('Checkpoint hash does not match its model record.')
        confidence = float(record['confidence'])
        if not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError('Model confidence must be between 0 and 1.')
        values.update(ROADSCAN_YOLO_SHA256=digest, ROADSCAN_CONFIDENCE=str(confidence))
    # Exclusive creation prevents replacing settings created by another launcher.
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w', encoding='ascii', newline='\n') as stream:
        stream.write(''.join(f'{key}={value}\n' for key, value in values.items()))
    return 'Local .env created. Keep it private; the access token is not printed.'


if __name__ == '__main__':
    print(prepare(Path.cwd()))
