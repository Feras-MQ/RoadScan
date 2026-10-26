import json
from pathlib import Path
from PIL import Image
import pytest
from roadscan.detector_export import export_validation

class Scalar:
    def __init__(self, v): self.v = v
    def item(self): return self.v

class Coords:
    def __init__(self, v): self.v = v
    def tolist(self): return self.v

class Box:
    cls = Scalar(3)
    conf = Scalar(.9)
    xyxy = [Coords([1., 1., 7., 7.])]

class Result:
    boxes = [Box()]

class Model:
    def __init__(self, checkpoint): pass
    def predict(self, **kwargs): return [Result()]

@pytest.fixture
def dataset(tmp_path):
    for split in ('train', 'val'):
        (tmp_path / split / 'images').mkdir(parents=True)
        (tmp_path / split / 'labels').mkdir()
        Image.new('RGB', (10, 10), 'red' if split == 'train' else 'blue').save(tmp_path / split / 'images' / 'one.png')
        (tmp_path / split / 'labels' / 'one.txt').write_text('3 0.4 0.4 0.6 0.6\n')
    (tmp_path / 'weights.pt').write_bytes(b'fake local checkpoint')
    return tmp_path

def test_export(dataset):
    result = export_validation(dataset, dataset / 'weights.pt', dataset / 'export', Model)
    assert result['images'] == 1
    truth = json.loads((dataset / 'export' / 'truth.json').read_text())
    pred = json.loads((dataset / 'export' / 'predictions.json').read_text())
    assert truth['images'][0]['boxes'][0]['class_id'] == 'D40'
    assert pred['images'][0]['boxes'][0]['confidence'] == .9
    assert pred['images'][0]['id'] == truth['images'][0]['id']

def test_refuse_overwrite(dataset):
    (dataset / 'export').mkdir()
    with pytest.raises(ValueError, match='overwrite'):
        export_validation(dataset, dataset / 'weights.pt', dataset / 'export', Model)

def test_missing_checkpoint(dataset):
    with pytest.raises(FileNotFoundError):
        export_validation(dataset, dataset / 'missing.pt', dataset / 'export', Model)

def test_invalid_prediction(dataset):
    class BadModel(Model):
        def predict(self, **kwargs):
            Box.cls = Scalar(9)
            return [Result()]
    with pytest.raises(ValueError, match='class'):
        export_validation(dataset, dataset / 'weights.pt', dataset / 'export', BadModel)
    assert not (dataset / 'export').exists()
    Box.cls = Scalar(3)
