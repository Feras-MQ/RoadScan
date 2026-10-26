import csv
from pathlib import Path
import pytest
from PIL import Image
from roadscan.classifier_baseline import load_manifest, metrics, CLASSES


def prepare(tmp_path, entries):
    root = tmp_path / 'images'
    root.mkdir()
    for name, color in {'a.png': 'red', 'b.png': 'blue', 'c.png': 'green'}.items():
        Image.new('RGB', (12, 12), color).save(root / name)
    manifest = tmp_path / 'labels.csv'
    with manifest.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['image', 'split', *CLASSES])
        writer.writerows(entries)
    return root, manifest


def test_valid_manifest(tmp_path):
    root, csvfile = prepare(tmp_path, [['a.png', 'train', 1, 0, 0, 0], ['b.png', 'validation', 0, 1, 0, 0]])
    assert len(load_manifest(csvfile, root)) == 2


def test_duplicate_path_rejected(tmp_path):
    root, csvfile = prepare(tmp_path, [['a.png', 'train', 1, 0, 0, 0], ['a.png', 'test', 1, 0, 0, 0]])
    with pytest.raises(ValueError, match='Duplicate'):
        load_manifest(csvfile, root)


def test_unsafe_path_rejected(tmp_path):
    root, csvfile = prepare(tmp_path, [['../bad.png', 'train', 1, 0, 0, 0]])
    with pytest.raises(ValueError, match='Unsafe'):
        load_manifest(csvfile, root)


def test_invalid_label_rejected(tmp_path):
    root, csvfile = prepare(tmp_path, [['a.png', 'train', 2, 0, 0, 0]])
    with pytest.raises(ValueError, match='Invalid D00'):
        load_manifest(csvfile, root)


def test_metrics():
    m = metrics([[1, 0, 0, 0], [0, 1, 0, 0]], [[1, 1, 0, 0], [0, 0, 0, 0]])
    assert m['D00']['f1'] == 1
    assert m['D10']['f1'] == 0
    assert m['D20']['f1'] is None


def test_train_and_predict(tmp_path):
    pytest.importorskip('numpy')
    pytest.importorskip('sklearn')
    from roadscan.classifier_baseline import train, predict
    root, csvfile = prepare(tmp_path, [['a.png', 'train', 1, 0, 0, 0], ['b.png', 'train', 0, 1, 0, 0], ['c.png', 'validation', 0, 0, 0, 0]])
    model = train(load_manifest(csvfile, root))
    prediction = predict(model, [root / 'c.png'])
    assert len(prediction) == 1 and len(prediction[0]) == 4
    assert prediction[0][2:] == [0, 0]
