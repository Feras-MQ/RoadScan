"""Persistent, content-addressed model library. Existing checkpoints are never overwritten."""
import csv
import gc
import hashlib
import io
import json
import math
import os
import re
import shutil
import tempfile
import threading
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from PIL import Image
from .checkpoints import inspect_checkpoint
from .inference import LocalDetector, validate_confidence_profile

MAX_MODEL = 700 * 1024 * 1024
MAX_IMPORT = 1600 * 1024 * 1024
MAX_EXPANDED = 1800 * 1024 * 1024
ID_PATTERN = re.compile(r'^[a-f0-9]{64}$')

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def atomic_json(path, value):
    temp = path.with_suffix('.json.tmp')
    try:
        temp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)

class ModelLibrary:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self._lock = threading.Lock()

    def _items(self):
        path = self.root/'catalog.json'
        if not path.exists(): return []
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or not isinstance(data.get('items'), list):
            raise ValueError('Model catalog is invalid; existing model files are preserved')
        items = data['items']
        if any(not ID_PATTERN.fullmatch(str(item.get('id',''))) for item in items):
            raise ValueError('Model catalog identifiers are invalid')
        return items

    def baseline(self):
        path = Path(os.getenv('ROADSCAN_YOLO_WEIGHTS',''))
        digest = os.getenv('ROADSCAN_YOLO_SHA256','').strip().lower()
        if not path.is_file() or not ID_PATTERN.fullmatch(digest): return None
        return {'id':'baseline','name':'RoadScan original YOLO11n baseline','file':path.name,
                'sha256':digest,'bytes':path.stat().st_size,'family':'yolo','imgsz':640,
                'classes':{'0':'D00','1':'D10','2':'D20','3':'D40'},
                'metrics_source':'See original evaluation report; imported model scores use different data and classes',
                'reported_metrics':{},'origin':'original','checked':'Original baseline; see evaluation report'}

    def list(self):
        with self._lock:
            base = self.baseline()
            return ([base] if base else []) + self._items()

    def find(self, ident):
        if ident == 'baseline':
            item = self.baseline()
            if not item: raise ValueError('Original baseline is not available')
            return item, Path(os.environ['ROADSCAN_YOLO_WEIGHTS'])
        if not ID_PATTERN.fullmatch(ident): raise ValueError('Unknown model identifier')
        with self._lock:
            item = next((item for item in self._items() if item['id']==ident), None)
        if item is None: raise ValueError('Model is not in the local library')
        path = self.root/ident/'model.pt'
        if path.is_symlink() or not path.is_file() or path.resolve().parent != self.root/ident:
            raise ValueError('Model file is missing or unsafe')
        return item, path

    def selected(self):
        with self._lock:
            path = self.root/'active.json'
            if not path.exists(): return 'baseline'
            value = json.loads(path.read_text(encoding='utf-8')).get('id','')
        if value != 'baseline' and not ID_PATTERN.fullmatch(value):
            raise ValueError('Invalid active model record')
        return value

    def save_selected(self, ident):
        self.root.mkdir(parents=True,exist_ok=True)
        with self._lock:
            atomic_json(self.root/'active.json',{'id':ident,'selected_at':datetime.now(timezone.utc).isoformat()})

    def import_file(self, source, filename):
        """Validate metadata without inference. Importing never changes the active model."""
        self.root.mkdir(parents=True, exist_ok=True)
        if Path(source).stat().st_size > MAX_IMPORT: raise ValueError('Model package exceeds the 1600 MB limit')
        with self._lock, tempfile.TemporaryDirectory(prefix='.import-',dir=self.root) as scratch:
            temp = Path(scratch)
            candidates, index = [], {}
            if filename.lower().endswith('.zip'):
                with zipfile.ZipFile(source) as archive:
                    infos = archive.infolist()
                    if len(infos)>1000 or sum(i.file_size for i in infos)>MAX_EXPANDED:
                        raise ValueError('Archive is too large or contains too many files')
                    for info in infos:
                        path = PurePosixPath(info.filename.replace('\\','/'))
                        if path.is_absolute() or '..' in path.parts or (info.external_attr>>16)&0o170000==0o120000:
                            raise ValueError('Unsafe archive entry')
                        if path.name == 'MODEL_INDEX.csv' and info.file_size<=200_000:
                            text = archive.read(info).decode('utf-8-sig').replace('\r\r\n','\n')
                            index = {row.get('File'):row for row in csv.DictReader(io.StringIO(text))}
                        if info.is_dir() or path.suffix.lower()!='.pt': continue
                        if len(candidates)>=16 or not 0<info.file_size<=MAX_MODEL:
                            raise ValueError('Archive accepts up to 16 checkpoints, each under 700 MB')
                        dest = temp/('checkpoint-'+str(len(candidates))+'.pt')
                        with archive.open(info) as inp, dest.open('xb') as out:
                            self._copy_bounded(inp,out,MAX_MODEL)
                        candidates.append((dest,path.name,str(path)))
            elif filename.lower().endswith('.pt'):
                if not 0<Path(source).stat().st_size<=MAX_MODEL:
                    raise ValueError('Checkpoint must be between 1 byte and 700 MB')
                candidates=[(Path(source),Path(filename).name,Path(filename).name)]
            else: raise ValueError('Choose a trusted Ultralytics .pt checkpoint or .zip package')
            if not candidates: raise ValueError('No .pt checkpoints found in this package')
            items=self._items(); known={item['id'] for item in items}
            added, duplicates, rejected=[],[],[]
            for source,name,relative in candidates:
                digest=sha(source)
                if digest in known:
                    duplicates.append(name); continue
                try:
                    metadata=inspect_checkpoint(source)
                except Exception as exc:
                    message=str(exc) if isinstance(exc,ValueError) else 'Incompatible checkpoint ('+type(exc).__name__+')'
                    rejected.append({'file':name,'reason':message}); continue
                unique_name=sum(candidate[1]==name for candidate in candidates)==1
                row=index.get(relative,index.get(name,{}) if unique_name else {})
                thresholds = {key: row.get('Threshold_'+key, '') for key in ('D00', 'D10', 'D20', 'D40')}
                if any(value != '' for value in thresholds.values()):
                    try:
                        if row.get('SHA256', '').lower() != digest:
                            raise ValueError('Confidence profile must match the checkpoint SHA-256')
                        metadata['confidence_profile'] = validate_confidence_profile({key: float(value) for key, value in thresholds.items()})
                        metadata['threshold_source'] = str(row.get('Threshold_scope', 'Supplied validation thresholds'))[:500]
                    except (TypeError, ValueError) as exc:
                        rejected.append({'file': name, 'reason': str(exc)})
                        continue
                supplied={}
                for key,col in [('mAP50','Best_mAP50'),('mAP50_95','Best_mAP50_95')]:
                    try:
                        value=float(row[col])
                        if math.isfinite(value) and 0<=value<=1: supplied[key]=value
                    except (KeyError,ValueError,TypeError): pass
                if supplied:
                    metadata['reported_metrics']=supplied
                    metadata['metrics_source']='Supplied MODEL_INDEX.csv validation scores; not independently verified by RoadScan'
                    if row.get('Metric_scope') and row.get('SHA256', '').lower() == digest:
                        metadata['metrics_source']=str(row['Metric_scope'])[:500]+'; team supplied, not independently reproduced'
                display=relative if not unique_name else name
                display=re.sub(r'[^\w. ()-]','_',display)[:180]
                name=re.sub(r'[^\w. ()-]','_',name)[:180]
                dest=self.root/digest
                if dest.is_symlink():raise ValueError('Unsafe model directory')
                dest.mkdir(exist_ok=True)
                checkpoint=dest/'model.pt'
                if checkpoint.is_symlink():raise ValueError('Unsafe model file')
                if not checkpoint.exists():
                    staging=dest/'model.pt.tmp'
                    try:
                        shutil.copyfile(source,staging)
                        os.replace(staging,checkpoint)
                    finally: staging.unlink(missing_ok=True)
                if sha(checkpoint)!=digest: raise ValueError('Stored model hash mismatch')
                item={'id':digest,'name':display.removesuffix('.pt'),'file':name,'sha256':digest,
                      'bytes':checkpoint.stat().st_size,'origin':'imported','imported_at':datetime.now(timezone.utc).isoformat(),
                      'checked':'Labels and restricted checkpoint metadata checked; inference checked on activation',**metadata}
                items.append(item); known.add(digest); added.append(item)
                gc.collect()
            if not added and not duplicates:
                raise ValueError('No compatible checkpoints: '+rejected[0]['reason'])
            atomic_json(self.root/'catalog.json',{'version':1,'items':items})
            return {'imported':added,'duplicates':duplicates,'rejected':rejected,'active_changed':False}

    @staticmethod
    def _copy_bounded(inp,out,limit):
        size=0
        while block:=inp.read(1024*1024):
            size+=len(block)
            if size>limit: raise ValueError('Expanded checkpoint exceeds its size limit')
            out.write(block)

class ModelRuntime:
    """One model/inference/switch at a time; a failed switch retains the old detector."""
    def __init__(self, library):
        self.library=library
        self._lock=threading.Lock()
        self._current=LocalDetector()
        self.active_id='baseline'
        self.warning=None
        try:
            selected=library.selected()
            if selected!='baseline': self.activate(selected,persist=False)
        except Exception:
            self.warning='Saved model could not load; original baseline retained. Select a model in Settings.'

    @property
    def model(self): return self._current.model
    @property
    def error(self): return self._current.error
    @property
    def confidence(self): return getattr(self._current,'confidence',None)
    @property
    def version(self): return self._current.version

    def predict(self,image,*,wait=True,live_mode=None):
        if not self._lock.acquire(blocking=wait):
            return dict(state='busy',reason='inference_busy',detections=[],model_version=self.version)
        try:
            current=self._current
            size = min(getattr(current, 'imgsz', 640), 640) if live_mode == 'balanced' else None
            started = time.perf_counter()
            result=current.predict(image, imgsz=size) if size else current.predict(image)
            result['elapsed_ms']=round((time.perf_counter()-started)*1000, 2)
            result['confidence_threshold']=getattr(current,'confidence',None)
            result['confidence_profile']=getattr(current,'confidence_profile',None)
            result['inference_size']=size or getattr(current,'imgsz',640)
            return result
        finally: self._lock.release()

    def compare(self, identifiers, image_path):
        from .voting import run_model, fuse_votes
        if len(identifiers) not in (2,3) or len(set(identifiers)) != len(identifiers):
            raise ValueError('Choose two or three different models')
        if not self._lock.acquire(blocking=False):
            raise ValueError('Detector is busy. Stop live recognition and try voting again')
        try:
            candidates = [self.library.find(ident) for ident in identifiers]
            if len({item['sha256'] for item, _ in candidates}) != len(candidates):
                raise ValueError('A checkpoint cannot vote twice under different names')
            # Workers run sequentially. Live requests receive busy while this lock
            # is held. Neither the selected model nor its active record changes.
            gc.collect()
            outputs = [run_model(item, path, image_path) for item, path in candidates]
            with Image.open(image_path) as image: width, height = image.size
            return {**fuse_votes(outputs, width, height), 'models': outputs, 'width': width, 'height': height,
                    'iou_threshold': .5, 'method': 'class-aware majority, one vote per checkpoint',
                    'confidence_note': 'Mean of agreeing detection scores; not probability of correctness',
                    'active_model_changed': False, 'annotations_changed': False}
        finally:
            self._lock.release()

    def activate(self, ident, *, persist=True):
        if not self._lock.acquire(blocking=False):
            raise ValueError('Detector is busy. Stop recognition and try again.')
        try:
            item,path=self.library.find(ident)
            options = {'confidence_profile': item['confidence_profile']} if item.get('confidence_profile') else {}
            candidate=LocalDetector(path=path,sha256=item['sha256'],imgsz=item['imgsz'],**options)
            if candidate.model is None:
                raise ValueError('Model could not load: '+str(candidate.error))
            started=time.perf_counter()
            with Image.new('RGB',(640,480),'gray') as image:
                result=candidate.predict(image)
            if result['state']!='completed': raise ValueError('Model inference check failed; previous model is still active')
            if persist: self.library.save_selected(ident)
            # Keep a readable model identity; the immutable SHA distinguishes all checkpoints.
            candidate.version=item['file']+'@'+item['sha256'][:12]
            self._current=candidate; self.active_id=ident; self.warning=None
            gc.collect()
            return {'active_id':ident,'model_version':candidate.version,
                    'synthetic_check_ms':round((time.perf_counter()-started)*1000,2),
                    'note':'Synthetic inference check, not an accuracy measurement'}
        finally: self._lock.release()

