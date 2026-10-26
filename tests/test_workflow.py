import pytest
from fastapi import HTTPException
from roadscan.workflow import validate_transition

@pytest.mark.parametrize('old,target,action,code', [
    ('Needs Review','Assigned','assign',409),
    ('Needs Review','Resolved','resolve',409),
    ('Needs Review','Confirmed','assign',422),
    ('Confirmed','Assigned','confirm',422),
    ('Resolved','Assigned','assign',409),
])
def test_invalid_transitions(old,target,action,code):
    with pytest.raises(HTTPException) as err:
        validate_transition(old,target,action)
    assert err.value.status_code == code

def test_valid_review_path():
    for old,target,action in [('Needs Review','Confirmed','confirm'),('Confirmed','Assigned','assign'),('Assigned','Resolved','resolve'),('Resolved','Needs Review','review')]:
        validate_transition(old,target,action)
