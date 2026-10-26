import pytest
from roadscan.ap_eval import average_precision, evaluate_ap


def b(cls='D40', xy=None, conf=0.9):
    return {'class_id': cls, 'box': xy or [0, 0, 10, 10], 'confidence': conf}


def test_perfect_detection():
    result = evaluate_ap({'a': [b()]}, {'a': [b()]})
    assert result['map50'] == pytest.approx(1)
    assert result['map50_95'] == pytest.approx(1)
    assert result['included_classes'] == 1
    assert result['per_class']['D00']['ap50'] is None


def test_no_predictions_is_zero_when_truth_exists():
    assert evaluate_ap({'a': [b()]}, {'a': []})['map50'] == 0


def test_empty_ground_truth_has_null_map():
    assert evaluate_ap({'a': []}, {'a': [b()]})['map50'] is None


def test_duplicate_detection_reduces_precision_when_ranked_first():
    truth = {'a': [b()], 'b': [b()]}
    pred = {'a': [b(conf=0.99), b(conf=0.98)], 'b': [b(conf=0.5)]}
    assert 0 < average_precision(truth, pred, 'D40', 0.5) < 1


def test_localization_changes_ap_across_iou_thresholds():
    result = evaluate_ap({'a': [b()]}, {'a': [b(xy=[2, 0, 12, 10])]})
    assert result['map50'] == pytest.approx(1)
    assert result['map50_95'] < 1


def test_mismatched_ids_fail():
    with pytest.raises(ValueError, match='identical'):
        evaluate_ap({'a': []}, {'b': []})


def test_wrong_class_is_not_match():
    assert evaluate_ap({'a': [b()]}, {'a': [b(cls='D00')]})['per_class']['D40']['ap50'] == 0
