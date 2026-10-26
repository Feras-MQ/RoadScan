import pytest
from roadscan.threshold_protocol import read_pairs, select_threshold, test_frozen as evaluate_frozen


def test_selection_requires_both_classes(tmp_path):
    with pytest.raises(ValueError, match='both'):
        select_threshold([{'left': 'a.png', 'right': 'b.png', 'same': '1'}], tmp_path)


def test_frozen_rejects_invalid_protocol(tmp_path):
    with pytest.raises(ValueError, match='protocol'):
        evaluate_frozen([], tmp_path, {'protocol': 'unknown', 'selection_split': 'validation'})


def test_frozen_rejects_bad_threshold(tmp_path):
    with pytest.raises(ValueError, match='threshold'):
        evaluate_frozen([], tmp_path, {'protocol': 'roadscan-e5-phash-pairs-v1', 'selection_split': 'validation', 'threshold': 2})


def test_read_pairs_separates_splits(tmp_path):
    path = tmp_path / 'pairs.csv'
    path.write_text('left,right,same,split\na,b,1,validation\nc,d,0,test\n')
    assert len(read_pairs(path, 'validation')) == 1
    assert len(read_pairs(path, 'test')) == 1


def test_read_pairs_rejects_unknown_split(tmp_path):
    path = tmp_path / 'pairs.csv'
    path.write_text('left,right,same,split\na,b,1,training\n')
    with pytest.raises(ValueError, match='splits'):
        read_pairs(path, 'validation')
