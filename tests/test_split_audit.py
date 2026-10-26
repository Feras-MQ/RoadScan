from roadscan.split_audit import audit

def row(split, country='Japan', group='g1', sha256='', phash=''):
    return dict(split=split, country=country, group=group, sha256=sha256, phash=phash)

def test_clean_split():
    result=audit([row('train',group='g1'),row('val',group='g2'),row('heldout_country',country='India',group='g3')], 'India')
    assert result['passed']
    assert result['missing_metadata_counts']['phash']==3

def test_group_leakage():
    assert not audit([row('train'),row('val')])['passed']

def test_country_leakage():
    assert not audit([row('train',country='India')], 'India')['passed']

def test_hash_leakage():
    assert any('exact duplicate' in x for x in audit([row('train',group='a',sha256='abc'),row('val',group='b',sha256='abc')])['issues'])

def test_near_duplicate_leakage():
    result=audit([row('train',group='a',phash='0000000000000000'),row('val',group='b',phash='0000000000000001')])
    assert any('near duplicate' in x for x in result['issues'])

def test_local_test_training_flag():
    assert not audit([dict(row('local_test'),use_for_training='true')])['passed']
