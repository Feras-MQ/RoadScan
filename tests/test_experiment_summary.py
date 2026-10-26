import json
import pytest
from roadscan.experiment_summary import summarize


def fixture(tmp_path, split='val'):
    d = tmp_path / 'e2'
    d.mkdir()
    box = {'class_id': 'D40', 'box': [0, 0, 10, 10]}
    (d / 'truth.json').write_text(json.dumps({'images': [{'id': 'one', 'boxes': [box]}]}))
    (d / 'predictions.json').write_text(json.dumps({'images': [{'id': 'one', 'boxes': [dict(box, confidence=.9)]}]}))
    (d / 'audit.json').write_text(json.dumps({'split': split}))
    m = tmp_path / 'manifest.json'
    m.write_text(json.dumps({'split': 'val', 'experiments': [{'id': 'E2', 'export_dir': 'e2'}]}))
    return m, tmp_path / 'result.json'


def test_summary_success(tmp_path):
    m, out = fixture(tmp_path)
    result = summarize(m, out)
    assert result['experiments'][0]['metrics']['map50'] == pytest.approx(1)
    assert out.exists()


def test_no_overwrite(tmp_path):
    m, out = fixture(tmp_path)
    out.write_text('existing')
    with pytest.raises(ValueError, match='overwrite'):
        summarize(m, out)
    assert out.read_text() == 'existing'


def test_reject_test_exports(tmp_path):
    m, out = fixture(tmp_path, 'test')
    with pytest.raises(ValueError, match='non-validation'):
        summarize(m, out)


def test_reject_duplicate_ids(tmp_path):
    m, out = fixture(tmp_path)
    obj = json.loads(m.read_text())
    obj['experiments'].append(obj['experiments'][0])
    m.write_text(json.dumps(obj))
    with pytest.raises(ValueError, match='duplicate'):
        summarize(m, out)
