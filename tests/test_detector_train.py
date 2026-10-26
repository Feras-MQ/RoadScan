from pathlib import Path
import pytest
from roadscan.detector_train import inspect_dataset, run_training


def fixture(root):
    for split in ('train', 'val'):
        for kind in ('images', 'labels'):
            (root / split / kind).mkdir(parents=True)
        (root / split / 'images' / 'a.jpg').write_bytes(split.encode())
        (root / split / 'labels' / 'a.txt').write_text('3 0.5 0.5 0.2 0.2\n')
    return root


def test_valid_dataset(tmp_path):
    assert inspect_dataset(fixture(tmp_path))['image_counts'] == {'train': 1, 'val': 1}


def test_duplicate_bytes_rejected(tmp_path):
    fixture(tmp_path)
    (tmp_path / 'val/images/a.jpg').write_bytes(b'train')
    with pytest.raises(ValueError, match='duplicate'):
        inspect_dataset(tmp_path)


def test_out_of_bounds_box_rejected(tmp_path):
    fixture(tmp_path)
    (tmp_path / 'val/labels/a.txt').write_text('3 0.9 0.5 0.4 0.2')
    with pytest.raises(ValueError, match='Out-of-bounds'):
        inspect_dataset(tmp_path)


def test_serialized_boundary_rounding_is_valid(tmp_path):
    fixture(tmp_path)
    (tmp_path / 'val/labels/a.txt').write_text('3 0.9 0.5 0.20000000000000004 0.2')
    assert inspect_dataset(tmp_path)['image_counts']['val'] == 1


def test_final_test_inside_root_rejected(tmp_path):
    fixture(tmp_path)
    (tmp_path / 'test').mkdir()
    with pytest.raises(ValueError, match='final test'):
        inspect_dataset(tmp_path)


def test_missing_annotation_rejected(tmp_path):
    fixture(tmp_path)
    (tmp_path / 'val/labels/a.txt').unlink()
    with pytest.raises(ValueError, match='Missing label'):
        inspect_dataset(tmp_path)


def test_no_checkpoint_refuses_training(tmp_path):
    fixture(tmp_path)
    with pytest.raises(FileNotFoundError):
        run_training(tmp_path, tmp_path / 'missing.pt', 2, 640, tmp_path / 'runs', 'e2')
    assert not (tmp_path / 'runs').exists()

@pytest.mark.parametrize('mode,expected',[('standard',None),('none',0),('vertical_flip',.5)])
def test_training_options_and_validation_scope(tmp_path,monkeypatch,mode,expected):
    import sys,json
    from types import SimpleNamespace
    fixture(tmp_path);weights=tmp_path/'initial.pt';weights.write_bytes(b'fake-checkpoint-for-mocked-loader')
    called={}
    class Fake:
        def __init__(self,path):pass
        def train(self,**kwargs):called.update(kwargs)
        def val(self,**kwargs):assert kwargs['split']=='val';return SimpleNamespace(results_dict={'mAP50':.5})
    monkeypatch.setitem(sys.modules,'ultralytics',SimpleNamespace(YOLO=Fake))
    run_training(tmp_path,weights,2,640,tmp_path/'runs','e2',device='0',seed=7,augmentation=mode)
    assert called['device']=='0' and called['seed']==7 and called['deterministic']
    assert called.get('flipud')==expected
    if mode=='none':assert called['mosaic']==0 and called['fliplr']==0
    assert json.loads((tmp_path/'runs/e2/validation_metrics.json').read_text())['split']=='validation_not_test'
