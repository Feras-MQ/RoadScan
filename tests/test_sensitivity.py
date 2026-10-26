from roadscan.sensitivity import scenarios

def test_sensitivity_synthetic_fixture():
    # Synthetic fixture tests arithmetic only, not ML performance.
    ds = [{'class_id':'D40','box':[0,0,50,50],'confidence':0.9}]
    result = scenarios(ds, 100, 100)
    assert len(result['variations']) == 8
    assert all(abs(sum(v['weights'].values())-1)<1e-10 for v in result['variations'])
    assert all(0 <= v['score'] <= 100 for v in result['variations'])

def test_empty_detection_not_scored():
    assert scenarios([], 100, 100)['baseline'] is None
