"""Internal voting worker; reads a bounded job from its parent, never a web request."""
import json
import sys
from pathlib import Path
from PIL import Image
from .inference import LocalDetector


def main():
    job = json.loads(sys.stdin.read(16000))
    options = {'confidence_profile': job['confidence_profile']} if job.get('confidence_profile') else {}
    detector = LocalDetector(path=job['path'], sha256=job['sha256'], imgsz=job['imgsz'], **options)
    with Image.open(job['image']) as image:
        result = detector.predict(image.convert('RGB'))
    Path(job['output']).write_text(json.dumps(result, allow_nan=False), encoding='utf-8')


if __name__ == '__main__':
    main()
