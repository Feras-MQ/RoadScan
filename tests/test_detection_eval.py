import pytest
from roadscan.detection_eval import evaluate, iou


def box(cls='D00', coords=None, confidence=0.9):
    return {'class_id': cls, 'box': coords or [0, 0, 10, 10], 'confidence': confidence}


def test_iou():
    assert iou([0, 0, 10, 10], [0, 0, 10, 10]) == 1
    assert iou([0, 0, 10, 10], [20, 20, 30, 30]) == 0


def test_one_to_one_matching_and_false_positive():
    result = evaluate({'a': [box()]}, {'a': [box(), box()]})
    assert result['per_class']['D00']['tp'] == 1
    assert result['per_class']['D00']['fp'] == 1
    assert result['per_class']['D00']['fn'] == 0


def test_missed_and_empty_class():
    result = evaluate({'a': [box('D10')]}, {'a': []})
    assert result['per_class']['D10']['fn'] == 1
    assert result['per_class']['D20']['recall'] is None


def test_confidence_filter():
    result = evaluate({'a': [box()]}, {'a': [box(confidence=0.1)]})
    assert result['per_class']['D00']['fn'] == 1
    assert result['per_class']['D00']['fp'] == 0


def test_mismatched_image_ids_rejected():
    with pytest.raises(ValueError, match='identical'):
        evaluate({'a': []}, {'b': []})


def test_invalid_threshold_rejected():
    with pytest.raises(ValueError):
        evaluate({'a': []}, {'a': []}, threshold=float('nan'))


def test_invalid_input_rejected(tmp_path):
    from roadscan.detection_eval import _read
    import json
    p = tmp_path / 'bad.json'
    p.write_text(json.dumps({'images': [{'id': 'x', 'boxes': [{'class_id': 'D00', 'box': [0, 0, 0, 5]}]}]}))
    with pytest.raises(ValueError, match='extent'):
        _read(p)
