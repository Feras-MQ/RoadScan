"""SYNTHETIC software tests; not ML performance measurements."""
from roadscan.inference import LocalDetector
from roadscan.core import score
import hashlib
import threading
from types import SimpleNamespace
from PIL import Image

def test_missing_checkpoint_is_honest(monkeypatch):
    monkeypatch.delenv('ROADSCAN_YOLO_WEIGHTS', raising=False)
    model=LocalDetector()
    result=model.predict(None)
    assert result['state']=='not_configured'
    assert result['detections']==[]

def test_nonexistent_checkpoint_is_honest(monkeypatch):
    monkeypatch.setenv('ROADSCAN_YOLO_WEIGHTS','/missing/roadscan.pt')
    assert LocalDetector().error=='checkpoint_missing'

def test_draft_score_is_bounded():
    v, parts=score([{'class_id':'D40','box':[0,0,50,50],'confidence':0.8}],100,100)
    assert 0<=v<=100 and parts['type']==1

def test_mismatched_hash_rejects_checkpoint_before_loading(monkeypatch, tmp_path):
    checkpoint = tmp_path / 'synthetic.pt'
    checkpoint.write_bytes(b'not a serialized model')
    monkeypatch.setenv('ROADSCAN_YOLO_WEIGHTS', str(checkpoint))
    monkeypatch.setenv('ROADSCAN_YOLO_SHA256', '0' * 64)
    assert LocalDetector().error == 'checkpoint_hash_mismatch'

def test_checkpoint_without_expected_hash_is_not_deserialized(monkeypatch, tmp_path):
    checkpoint = tmp_path / 'unverified.pt'
    checkpoint.write_bytes(b'not a serialized model')
    monkeypatch.setenv('ROADSCAN_YOLO_WEIGHTS', str(checkpoint))
    monkeypatch.delenv('ROADSCAN_YOLO_SHA256', raising=False)
    assert LocalDetector().error == 'checkpoint_hash_required'

def test_invalid_confidence_rejects_before_loading(monkeypatch, tmp_path):
    checkpoint = tmp_path / 'synthetic.pt'
    checkpoint.write_bytes(b'not a serialized model')
    monkeypatch.setenv('ROADSCAN_YOLO_WEIGHTS', str(checkpoint))
    monkeypatch.setenv('ROADSCAN_YOLO_SHA256', hashlib.sha256(checkpoint.read_bytes()).hexdigest())
    monkeypatch.setenv('ROADSCAN_CONFIDENCE', 'nan')
    assert LocalDetector().error == 'invalid_confidence'

class Array:
    def __init__(self, values): self.values = values
    def tolist(self): return self.values

def test_prediction_uses_cpu_clips_border_boxes_and_rejects_nonfinite_geometry():
    calls = []
    def predict(**kwargs):
        calls.append(kwargs)
        return [SimpleNamespace(boxes=[SimpleNamespace(xyxy=[Array([-1, 0, 50, 50])], cls=[3], conf=[0.8])])]
    adapter = LocalDetector.__new__(LocalDetector)
    adapter._inference_lock = threading.Lock()
    adapter.imgsz = 640
    adapter.model = SimpleNamespace(predict=predict)
    adapter.mapping = {3: 'D40'}
    adapter.confidence = 0.25
    adapter.version = 'synthetic.pt@synthetic'
    result = adapter.predict(Image.new('RGB', (100, 100)))
    assert result['state'] == 'completed' and result['detections'][0]['box'] == [0,0,50,50]
    assert calls[0]['device'] == 'cpu' and calls[0]['max_det'] == 100 and calls[0]['imgsz'] == 640
    adapter.model.predict=lambda **kwargs:[SimpleNamespace(boxes=[SimpleNamespace(xyxy=[Array([float('nan'),0,50,50])],cls=[3],conf=[.8])])]
    result=adapter.predict(Image.new('RGB',(100,100)))
    assert result['state']=='failed' and result['detections']==[]


def test_class_thresholds_keep_low_confidence_potholes_and_filter_other():
    from roadscan.inference import validate_confidence_profile
    import pytest
    profile={'D00':.173,'D10':.166,'D20':.195,'D40':.056}
    assert validate_confidence_profile(profile)==profile
    for invalid in [dict(profile,D40=float('nan')),{'D40':.056},dict(profile,D40=True)]:
        with pytest.raises(ValueError): validate_confidence_profile(invalid)
    calls=[]
    def predict(**kwargs):
        calls.append(kwargs)
        return [SimpleNamespace(boxes=[SimpleNamespace(xyxy=[Array([1,1,20,20])],cls=[kind],conf=[confidence]) for kind,confidence in [(0,.17),(0,.18),(4,.06),(4,.05),(3,.99)]])]
    adapter=LocalDetector.__new__(LocalDetector)
    adapter._inference_lock=threading.Lock();adapter.imgsz=1024
    adapter.model=SimpleNamespace(predict=predict);adapter.mapping={0:'D00',3:'OTHER',4:'D40'}
    adapter.confidence=.056;adapter.confidence_profile=profile;adapter.version='synthetic'
    with Image.new('RGB',(100,100)) as image: result=adapter.predict(image)
    assert result['state']=='completed'
    assert [(d['class_id'],d['confidence']) for d in result['detections']]==[('D00',.18),('D40',.06)]
    assert calls[0]['conf']==.056 and calls[0]['imgsz']==1024
