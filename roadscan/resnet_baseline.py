"""Replacement ResNet18 multi-label fine-tuning/evaluation; thresholds use validation only."""
import argparse,json,random,math,os,hashlib
from pathlib import Path
from .classifier_baseline import load_manifest,metrics,CLASSES

def thresholds(truth,scores):
    if not truth or len(truth)!=len(scores):raise ValueError('Nonempty aligned validation labels/scores required')
    if any(len(y)!=4 or len(s)!=4 or any(v not in (0,1) for v in y) or any(not math.isfinite(v) or not 0<=v<=1 for v in s) for y,s in zip(truth,scores)):raise ValueError('Invalid four-class validation labels/scores')
    result=[]
    for j in range(4):
        if not any(row[j] for row in truth) or all(row[j] for row in truth):raise ValueError('Validation needs positive and negative examples for every class')
        best=(-1,.5)
        for i in range(1,100):
            t=i/100;tp=sum(y[j] and s[j]>=t for y,s in zip(truth,scores));fp=sum(not y[j] and s[j]>=t for y,s in zip(truth,scores));fn=sum(y[j] and s[j]<t for y,s in zip(truth,scores))
            value=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0
            if value>best[0]:best=(value,t)
        result.append(best[1])
    return result

def run(manifest,image_root,checkpoint,output,epochs=0,device='cpu',seed=0):
    if epochs<0 or seed<0:raise ValueError('Invalid epochs or seed')
    rows=load_manifest(manifest,image_root);groups={k:[r for r in rows if r[1]==k] for k in ('train','validation','test')}
    if not groups['validation'] or not groups['test'] or (epochs and not groups['train']):raise ValueError('Required train/validation/test split is empty')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
    import torch
    from torchvision.models import resnet18
    from torchvision.transforms import Compose,Resize,ToTensor,Normalize
    from PIL import Image
    random.seed(seed);torch.manual_seed(seed);torch.use_deterministic_algorithms(True)
    state=torch.load(checkpoint,map_location='cpu',weights_only=True)
    if not isinstance(state,dict) or not isinstance(state.get('state_dict'),dict):raise ValueError('Checkpoint must contain a state_dict and class metadata')
    if state.get('classes') not in ([0,1,2,4],list(CLASSES)):raise ValueError('Checkpoint must declare D00,D10,D20,D40 in that order')
    size=state.get('image_size',512);mean=state.get('mean',[.485,.456,.406]);std=state.get('std',[.229,.224,.225])
    if type(size) is not int or not 32<=size<=1024:raise ValueError('Unsupported classifier image size')
    prep=Compose([Resize((size,size)),ToTensor(),Normalize(mean,std)])
    model=resnet18(weights=None);model.fc=torch.nn.Linear(model.fc.in_features,4);model.load_state_dict(state['state_dict'],strict=True);model.to(device)
    class Data(torch.utils.data.Dataset):
        def __init__(self,items):self.items=items
        def __len__(self):return len(self.items)
        def __getitem__(self,i):
            path,_,label=self.items[i]
            with Image.open(path) as image:tensor=prep(image.convert('RGB'))
            return tensor,torch.tensor(label,dtype=torch.float32)
    loaders={k:torch.utils.data.DataLoader(Data(v),batch_size=8,shuffle=(k=='train' and bool(v)),num_workers=0) for k,v in groups.items()}
    def infer(split):
        model.eval();truth=[];scores=[]
        with torch.inference_mode():
            for x,y in loaders[split]:truth.extend(y.tolist());scores.extend(torch.sigmoid(model(x.to(device))).cpu().tolist())
        return truth,scores
    if epochs:
        optimizer=torch.optim.Adam(model.parameters(),lr=1e-4);loss_fn=torch.nn.BCEWithLogitsLoss();best=float('inf')
        for epoch in range(epochs):
            model.train()
            for x,y in loaders['train']:
                optimizer.zero_grad();loss=loss_fn(model(x.to(device)),y.to(device));loss.backward();optimizer.step()
            y,scores=infer('validation');loss=torch.nn.functional.binary_cross_entropy(torch.tensor(scores),torch.tensor(y)).item()
            if loss<best:
                best=loss;torch.save({**state,'state_dict':{k:v.detach().cpu() for k,v in model.state_dict().items()},'epoch':epoch+1,'seed':seed},output/'best.pt')
        model.load_state_dict(torch.load(output/'best.pt',map_location='cpu',weights_only=True)['state_dict'])
    val_truth,val_scores=infer('validation');cutoffs=thresholds(val_truth,val_scores)
    if epochs:
        trained=torch.load(output/'best.pt',map_location='cpu',weights_only=True)
        trained.update(thresholds=cutoffs,replacement_training=True,source_sha256=hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest(),manifest_sha256=hashlib.sha256(Path(manifest).read_bytes()).hexdigest())
        torch.save(trained,output/'best.pt')
    truth,scores=infer('test');predictions=[[int(v>=t) for v,t in zip(row,cutoffs)] for row in scores]
    result={'split':'test','threshold_source':'validation_only','thresholds':dict(zip(CLASSES,cutoffs)),'per_class':metrics(truth,predictions),'any_damage_accuracy':sum(any(y)==any(p) for y,p in zip(truth,predictions))/len(truth),'images':len(truth),'preprocessing':{'resize':[size,size],'mean':mean,'std':std},'replacement_not_original_training_code':True}
    (output/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','image-root','checkpoint','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--epochs',type=int,default=0);p.add_argument('--device',default='cpu');p.add_argument('--seed',type=int,default=0);a=p.parse_args()
    print(json.dumps(run(a.manifest,a.image_root,a.checkpoint,a.output,a.epochs,a.device,a.seed),indent=2))
if __name__=='__main__':main()
