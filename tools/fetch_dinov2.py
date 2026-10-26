"""Fetch the official pretrained backbone once; never download during inference."""
from pathlib import Path
import hashlib, json, sys, urllib.request,shutil

def fetch(destination):
    record=json.loads((Path(__file__).resolve().parents[1]/'third_party/dinov2-provenance.json').read_text())
    target=Path(destination);target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest()!=record['weights_sha256']:raise ValueError('Existing DINOv2 checkpoint hash mismatch')
        return
    temporary=target.with_suffix('.download')
    try:
        with urllib.request.urlopen(record['weights_url'],timeout=60) as response,temporary.open('wb') as out:
            shutil.copyfileobj(response,out)
        if hashlib.sha256(temporary.read_bytes()).hexdigest()!=record['weights_sha256']:raise ValueError('Downloaded DINOv2 checkpoint hash mismatch')
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
if __name__=='__main__':fetch(sys.argv[1])
