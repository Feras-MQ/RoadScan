"""Local YOLO evaluation with explicitly scoped metrics; no dataset downloads."""
import argparse,json,math,hashlib
from pathlib import Path
from .model_classes import class_mapping

def select_thresholds(x,precision,recall,classes):
    result={}
    if len(precision)!=len(classes) or len(recall)!=len(classes):raise ValueError('Curve class mismatch')
    for cls,ps,rs in zip(classes,precision,recall):
        if cls not in {'D00','D10','D20','D40'}:continue
        if len(ps)!=len(x) or len(rs)!=len(x) or not len(x):raise ValueError('Curve length mismatch')
        beta2=4 if cls=='D40' else 1;scores=[]
        for t,p,r in zip(x,ps,rs):
            if not all(math.isfinite(float(v)) and 0<=v<=1 for v in (t,p,r)):raise ValueError('Invalid validation curve')
            scores.append((1+beta2)*p*r/(beta2*p+r) if beta2*p+r else 0)
        if max(scores)>0:result[cls]=float(x[max(range(len(x)),key=lambda i:scores[i])])
    return result

def evaluate(checkpoint,dataset,output,split='test',imgsz=640,device='cpu'):
    import yaml
    if split not in {'val','test'} or imgsz<32:raise ValueError('Invalid evaluation settings')
    config=yaml.safe_load(Path(dataset).read_text())
    if not isinstance(config,dict) or set(config)-{'path','train','val','test','names','nc'}:raise ValueError('Only local dataset paths and class names are allowed; download scripts are forbidden')
    root=(Path(dataset).resolve().parent/str(config.get('path','.'))).resolve(strict=True)
    for key in ('train','val','test'):
        if key not in config:continue
        if not isinstance(config[key],str):raise ValueError('Use one local directory per split')
        path=(root/config[key]).resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_dir():raise ValueError('Split directory escapes dataset root')
        config[key]=str(path)
    if split not in config:raise ValueError('Requested split is missing')
    config['path']=str(root)
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    safe=output/'dataset.yaml';safe.write_text(yaml.safe_dump(config))
    from .checkpoints import load_detector
    model,_=load_detector(Path(checkpoint));mapping=class_mapping(model.names)
    names=config['names'];data_mapping=class_mapping(dict(enumerate(names)) if isinstance(names,list) else names)
    if mapping!=data_mapping:raise ValueError('Checkpoint and dataset class order differ; remap labels explicitly')
    measured=model.val(data=str(safe.resolve()),split=split,imgsz=imgsz,device=device,conf=.001,plots=True,project=str(output.resolve()),name='evaluation',exist_ok=True)
    box=measured.box;per_class={}
    for i,raw in enumerate(box.ap_class_index):
        cls=mapping[int(raw)]
        if cls=='OTHER':continue
        per_class[cls]={'ap50':float(box.ap50[i]),'ap50_95':float(box.ap[i]),'precision':float(box.p[i]),'recall':float(box.r[i]),'f1':float(box.f1[i])}
    result={'split':'validation' if split=='val' else 'test','checkpoint_sha256':hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest(),'image_size':imgsz,'per_class':per_class,'missing_classes':sorted({'D00','D10','D20','D40'}-per_class.keys()),'mAP50':sum(v['ap50'] for v in per_class.values())/len(per_class) if per_class else None,'mAP50_95':sum(v['ap50_95'] for v in per_class.values())/len(per_class) if per_class else None,'scope':'Four damage classes present in this split; OTHER excluded; dataset leakage requires a separate split audit'}
    if split=='val':
        result['confidence_profile']=select_thresholds(box.px,box.p_curve,box.r_curve,[mapping[int(i)] for i in box.ap_class_index])
        result['threshold_scope']='Validation only; F1 cracks / F2 potholes; valid only for this checkpoint, preprocessing and image size'
    (output/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False));return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('checkpoint','dataset','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--split',choices=['val','test'],default='test');p.add_argument('--imgsz',type=int,default=640);p.add_argument('--device',default='cpu');a=p.parse_args()
    print(json.dumps(evaluate(a.checkpoint,a.dataset,a.output,a.split,a.imgsz,a.device),indent=2))
if __name__=='__main__':main()
