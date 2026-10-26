import pytest
from roadscan.review import validate_detections

def test_manual_boxes_reject_nan_and_boolean():
    for value in (float('nan'),True,float('inf')):
        with pytest.raises(ValueError):
            validate_detections([{'class_id':'D40','box':[0,0,value,20],'confidence':.8}],100,100)

def test_manual_detection_valid():
    d={'class_id':'D00','box':[1,2,20,30],'confidence':.9}
    assert validate_detections([d],100,100)==[d]
