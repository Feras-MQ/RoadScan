"""Run a reviewed local experiment plan; dry-run by default, no cloud provisioning."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULES={'detector_train','retrieval_eval','duplicate_eval','ap_eval','classifier_baseline','resnet_baseline','priority','accuracy_report'}

def input_fingerprint(command):
    digest=hashlib.sha256()
    for index,argument in enumerate(command[:-1]):
        if argument not in {'--dataset-root','--weights','--checkpoint','--dataset','--manifest','--image-root','--queries','--gallery','--input'}:continue
        path=(ROOT/command[index+1]).resolve(strict=True)
        if argument=='--dataset':
            import yaml
            config=yaml.safe_load(path.read_text());path=(path.parent/str(config.get('path','.'))).resolve(strict=True)
        files=sorted(p for p in path.rglob('*') if p.is_file() and p.suffix!='.cache') if path.is_dir() else [path]
        for file in files:
            digest.update(str(file).encode())
            with file.open('rb') as stream:digest.update(hashlib.file_digest(stream,'sha256').digest())
    return digest.hexdigest()

def commands(plan):
    if not isinstance(plan,list) or not plan:raise ValueError('Plan must contain at least one experiment')
    seen=set();result=[]
    for job in plan:
        name=job.get('name','');module=job.get('module');args=job.get('args',[])
        if not name or len(name)>80 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name) or name in seen:raise ValueError('Use unique safe experiment names')
        if module not in MODULES or not isinstance(args,list) or not all(isinstance(v,str) for v in args):raise ValueError('Unsupported module or arguments')
        seen.add(name);result.append((name,[sys.executable,'-m','roadscan.'+module,*args]))
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
    raw=a.plan.read_bytes();jobs=commands(json.loads(raw));fingerprint=hashlib.sha256(raw).hexdigest()
    if not a.execute:
        print(json.dumps({'status':'dry_run_no_training','plan_sha256':fingerprint,'jobs':[{'name':n,'command':c} for n,c in jobs]},indent=2));return
    a.output.mkdir(parents=True,exist_ok=True)
    saved=a.output/'plan.json'
    if saved.exists() and saved.read_bytes()!=raw:raise ValueError('Output belongs to a different plan; choose another output folder')
    if not saved.exists():saved.write_bytes(raw)
    code=hashlib.sha256()
    for source in sorted((ROOT/'roadscan').glob('*.py'))+[Path(__file__)]:code.update(source.read_bytes())
    code_hash=code.hexdigest()
    summary=[]
    for name,command in jobs:
        inputs=input_fingerprint(command)
        done=a.output/(name+'.completed.json')
        if done.exists():
            record=json.loads(done.read_text())
            if any(record.get(k)!=v for k,v in {'plan_sha256':fingerprint,'code_sha256':code_hash,'inputs_sha256':inputs}.items()):raise ValueError('Completed experiment inputs/code changed; choose a new output folder')
            summary.append(record);continue
        env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join([str(ROOT),str(ROOT/'third_party'),env.get('PYTHONPATH','')])
        with (a.output/(name+'.log')).open('a',encoding='utf-8') as log:
            result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:raise RuntimeError(f'{name} failed; inspect its log before rerunning. Existing model outputs are not overwritten.')
        record={'name':name,'plan_sha256':fingerprint,'code_sha256':code_hash,'inputs_sha256':inputs,'exit_code':0,'command':command};done.write_text(json.dumps(record,indent=2));summary.append(record)
        (a.output/'summary.json').write_text(json.dumps(summary,indent=2))
        print(name+': completed',flush=True)
if __name__=='__main__':main()
