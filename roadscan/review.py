"""Strict manual detection validation for human-reviewed reports."""
import math
from .core import CLASSES

def validate_detections(items, width, height):
    if len(items)>100:
        raise ValueError('Too many detections (max 100)')
    cleaned=[]
    for d in items:
        if not isinstance(d,dict) or set(d)!={'class_id','box','confidence'} or d['class_id'] not in CLASSES:
            raise ValueError('Detection requires class_id, box, confidence')
        box=d['box']; conf=d['confidence']
        if not isinstance(box,list) or len(box)!=4 or any(type(v) not in (float,int) or not math.isfinite(v) for v in box):
            raise ValueError('Invalid detection box')
        x1,y1,x2,y2=box
        if not (0<=x1<x2<=width and 0<=y1<y2<=height):
            raise ValueError('Box outside image')
        if type(conf) not in (int,float) or not math.isfinite(conf) or not 0<=conf<=1:
            raise ValueError('Invalid confidence')
        cleaned.append({'class_id':d['class_id'],'box':box,'confidence':conf})
    return cleaned
