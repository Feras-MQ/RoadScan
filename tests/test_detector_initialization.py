import hashlib
import sys
import types
import pytest
from PIL import Image
from roadscan.inference import LocalDetector

def test_inference_initialization_mapping_error(tmp_path, monkeypatch):
    # 1. Create a tiny fake checkpoint file and compute its actual SHA256
    fake_pt = tmp_path / "fake.pt"
    fake_data = b"fake weights data"
    fake_pt.write_bytes(fake_data)
    actual_sha256 = hashlib.sha256(fake_data).hexdigest()

    # 2. Set environment variables, including the mandatory hash matching
    monkeypatch.setenv('ROADSCAN_YOLO_WEIGHTS', str(fake_pt))
    monkeypatch.setenv('ROADSCAN_YOLO_SHA256', actual_sha256)
    monkeypatch.setenv('ROADSCAN_CONFIDENCE', '0.25')
    monkeypatch.setenv('ROADSCAN_INFERENCE_THREADS', '2')

    # 3. Inject fake torch module into sys.modules
    fake_torch = types.ModuleType("torch")
    fake_torch.set_num_threads = lambda threads: None
    monkeypatch.setitem(sys.modules, 'torch', fake_torch)

    # 4. Inject fake ultralytics module and YOLO class into sys.modules
    class FakeYOLO:
        def __init__(self, path):
            # Invalid integer key to trigger ValueError during int(i) casting
            self.names = {'invalid_key': 'D00'}
            
        def predict(self, *args, **kwargs):
            raise RuntimeError("Inference should not be executed")

    fake_ultralytics = types.ModuleType("ultralytics")
    fake_ultralytics.settings = {}
    fake_ultralytics.YOLO = FakeYOLO
    monkeypatch.setitem(sys.modules, 'ultralytics', fake_ultralytics)
    monkeypatch.setattr('roadscan.inference.load_detector', lambda path: (FakeYOLO(path), 'yolo'))

    # 5. Initialize the detector
    detector = LocalDetector()

    # 6. Assert model is None and error is correctly captured
    assert detector.model is None
    assert detector.error == 'load_failed_ValueError'

    # 7. Assert predict handles the unconfigured state safely without executing inference
    result = detector.predict(None)
    assert result['state'] == 'not_configured'
    assert result['reason'] == 'load_failed_ValueError'
    assert result['model_version'] == 'not_configured'
    assert result['detections'] == []


@pytest.mark.parametrize('configured_threads', [None, '3'])
def test_cpu_thread_limit_survives_predictor_setup(tmp_path, monkeypatch, configured_threads):
    checkpoint = tmp_path / 'synthetic.pt'
    checkpoint.write_bytes(b'synthetic checkpoint; no real model is loaded')
    monkeypatch.setenv('ROADSCAN_YOLO_WEIGHTS', str(checkpoint))
    monkeypatch.setenv('ROADSCAN_YOLO_SHA256', hashlib.sha256(checkpoint.read_bytes()).hexdigest())
    monkeypatch.setenv('ROADSCAN_CONFIDENCE', '0.25')
    if configured_threads is None:
        monkeypatch.delenv('ROADSCAN_INFERENCE_THREADS', raising=False)
    else:
        monkeypatch.setenv('ROADSCAN_INFERENCE_THREADS', configured_threads)
    expected_threads = int(configured_threads or '2')
    state = types.SimpleNamespace(threads=None, warmup=[], forward=[])
    fake_torch = types.ModuleType('torch')
    fake_torch.set_num_threads = lambda threads: setattr(state, 'threads', threads)
    monkeypatch.setitem(sys.modules, 'torch', fake_torch)

    class FakeYOLO:
        def __init__(self, path):
            self.names = dict(enumerate(('D00', 'D10', 'D20', 'D40')))
            self.callbacks = {}
            self.initialized = False

        def add_callback(self, event, callback):
            self.callbacks.setdefault(event, []).append(callback)

        def predict(self, **kwargs):
            first_call = not self.initialized
            if first_call:
                # Ultralytics selects its device lazily and resets Torch threads here.
                fake_torch.set_num_threads(7)
                self.initialized = True
            for callback in self.callbacks.get('on_predict_start', []):
                callback(self)
            if first_call:
                state.warmup.append(state.threads)
            state.forward.append(state.threads)
            return []

    fake_ultralytics = types.ModuleType('ultralytics')
    fake_ultralytics.settings = {}
    fake_ultralytics.YOLO = FakeYOLO
    monkeypatch.setitem(sys.modules, 'ultralytics', fake_ultralytics)
    monkeypatch.setattr('roadscan.inference.load_detector', lambda path: (FakeYOLO(path), 'yolo'))
    detector = LocalDetector()
    assert detector.error is None
    image = Image.new('RGB', (16, 16))
    assert detector.predict(image)['state'] == 'completed'
    # A later prediction must also reapply the configured limit if another user changed it.
    fake_torch.set_num_threads(9)
    assert detector.predict(image)['state'] == 'completed'
    assert state.warmup == [expected_threads]
    assert state.forward == [expected_threads, expected_threads]
