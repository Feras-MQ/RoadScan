"""Reproducible priority and dataset-ranking sensitivity using the app's formula."""
import argparse,json,math
from pathlib import Path
from .core import score,WEIGHTS
from .review import validate_detections
from .sensitivity import scenarios

def analyze(records):
    seen=set();items=[]
    for r in records:
        if not isinstance(r.get('id'),str) or not r['id'] or r['id'] in seen:raise ValueError('Report IDs must be unique nonempty strings')
        seen.add(r['id'])
        if any(type(r[k]) is not int or r[k]<=0 for k in ('width','height')):raise ValueError('Image dimensions must be positive integers')
        ds=validate_detections(r['detections'],r['width'],r['height'])
        items.append({'id':r['id'],'analysis':scenarios(ds,r['width'],r['height'])})
    ranked=sorted([r for r in items if r['analysis']['baseline'] is not None],key=lambda r:(-r['analysis']['baseline'],r['id']))
    baseline=[r['id'] for r in ranked];positions={v:i for i,v in enumerate(baseline)};checks=[]
    for index in range(8):
        order=sorted(ranked,key=lambda r:(-r['analysis']['variations'][index]['score'],r['id']))
        ids=[r['id'] for r in order];n=len(ids);k=min(50,n)
        shifts=[abs(positions[ident]-i) for i,ident in enumerate(ids)]
        variation=items[0]['analysis']['variations'][index] if items else {}
        checks.append({'component':variation.get('component'),'multiplier':variation.get('multiplier'),'ranking':ids,'top_k':k,'top_k_overlap':len(set(ids[:k])&set(baseline[:k]))/k if k else None,'maximum_rank_shift':max(shifts,default=0)})
    return {'formula':'app-v1','weights':WEIGHTS,'status':'heuristic_not_engineering_severity','tie_policy':'score descending, then report ID; equal scores are not distinct severity judgments','reports':items,'baseline_ranking':baseline,'ranking_sensitivity':checks}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=analyze(json.loads(a.input.read_text()))
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,allow_nan=False)
if __name__=='__main__':main()
