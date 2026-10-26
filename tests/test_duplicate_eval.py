from PIL import Image
import pytest
from roadscan.duplicate_eval import phash, similarity, evaluate


def test_identical_images_and_pair_metrics(tmp_path):
    Image.new('RGB', (32, 32), 'gray').save(tmp_path / 'a.png')
    Image.new('RGB', (32, 32), 'gray').save(tmp_path / 'b.png')
    assert similarity(phash(tmp_path / 'a.png'), phash(tmp_path / 'b.png')) == 1
    result = evaluate([{'left': 'a.png', 'right': 'b.png', 'same': '1'}], tmp_path, 0.9)
    assert result['tp'] == 1 and result['recall'] == 1
    assert result['recall_at_1'] is None


def test_rejects_path_traversal(tmp_path):
    with pytest.raises(ValueError):
        evaluate([{'left': '../private.jpg', 'right': 'x.png', 'same': '1'}], tmp_path, 0.9)


def test_rejects_unknown_labels(tmp_path):
    with pytest.raises(ValueError):
        evaluate([{'left': 'a.png', 'right': 'b.png', 'same': 'yes'}], tmp_path, 0.9)
