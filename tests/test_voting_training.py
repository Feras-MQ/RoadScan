"""Synthetic voting, data leakage and human-approval contracts; no accuracy claims."""
import io
import json
import os
import zipfile
from types import SimpleNamespace
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import roadscan.api as api
from roadscan.core import BASE
from roadscan.voting import fuse_votes


def box(kind='D40',coords=None,confidence=.8):
    return {'class_id':kind,'box':coords or [10,10,80,70],'confidence':confidence}

def output(ident,boxes=None,state='completed',classes=None):
    return {'id':ident,'state':state,'detections':boxes if boxes is not None else [box()],
            'classes':classes or ['D00','D10','D20','D40','OTHER']}

def test_two_models_need_two_votes_and_coordinates_are_fused():
    result=fuse_votes([output('a'),output('b',[box(coords=[12,10,82,70])])],120,80)
    assert result['consensus']==[box(coords=[11,10,81,70])]
    assert result['agreements'][0]['votes']==2 and result['disagreements']==[]

def test_three_models_can_disagree_without_hiding_the_disagreement():
    result=fuse_votes([output('a'),output('b'),output('c',[box('D00')])],120,80)
    assert len(result['consensus'])==1 and result['consensus'][0]['class_id']=='D40'
    assert result['disagreements'][0]['detection']['class_id']=='D00'

def test_duplicate_boxes_from_one_model_cannot_manufacture_a_majority():
    result=fuse_votes([output('a',[box(),box(),box()]),output('b',[])],120,80)
    assert result['consensus']==[]
    assert all(v['votes']==1 for v in result['disagreements'])

def test_different_locations_of_the_same_class_do_not_agree():
    result=fuse_votes([output('a',[box(coords=[1,1,20,20])]),output('b',[box(coords=[90,50,110,70])])],120,80)
    assert result['consensus']==[] and len(result['disagreements'])==2

def test_other_class_needs_two_capable_models_and_four_class_model_abstains():
    four=['D00','D10','D20','D40']
    single=fuse_votes([output('a',[box('OTHER')]),output('b',[],classes=four)],120,80)
    assert single['consensus']==[] and single['disagreements'][0]['eligible_models']==1
    paired=fuse_votes([output('a',[box('OTHER')]),output('b',[box('OTHER')]),output('c',[],classes=four)],120,80)
    assert len(paired['consensus'])==1 and paired['agreements'][0]['eligible_models']==2

def test_failure_is_not_silently_counted_as_a_negative_or_reduced_quorum():
    result=fuse_votes([output('a'),output('b'),output('c',[],state='failed')],120,80)
    assert result['state']=='partial' and result['consensus']==[]

def test_same_checkpoint_cannot_vote_twice():
    with pytest.raises(ValueError):fuse_votes([output('a'),output('a')],120,80)

def image_bytes(color='gray',size=(120,80)):
    stream=io.BytesIO();Image.new('RGB',size,color).save(stream,'PNG');return stream.getvalue()

@pytest.fixture
def workspace(tmp_path,monkeypatch):
    engine=create_engine('sqlite:///'+str(tmp_path/'fixture.db'),connect_args={'check_same_thread':False})
    BASE.metadata.create_all(engine);storage=tmp_path/'images';storage.mkdir()
    monkeypatch.setattr(api,'init_db',lambda:None);monkeypatch.setattr(api,'Session',sessionmaker(bind=engine));monkeypatch.setattr(api,'STORAGE',storage)
    fake=SimpleNamespace(model=object(),error=None,version='synthetic-model',confidence=.25)
    fake.predict=lambda image,**kw:dict(state='completed',reason=None,model_version='synthetic-model',detections=[])
    fake.compare=lambda ids,path:dict(state='completed',consensus=[box()],agreements=[],disagreements=[],models=[],width=120,height=80,annotations_changed=False,active_model_changed=False)
    monkeypatch.setattr(api,'detector',lambda:fake)
    monkeypatch.setenv('ROADSCAN_API_KEY','training-admin-fixture');monkeypatch.setenv('ROADSCAN_VIEWER_KEY','training-viewer-fixture')
    monkeypatch.delenv('ROADSCAN_ACCOUNTS_FILE',raising=False);monkeypatch.delenv('ROADSCAN_REVIEWER_KEY',raising=False);monkeypatch.delenv('ROADSCAN_MAX_UPLOAD_MB',raising=False)
    with TestClient(api.app) as client:
        yield client,{'X-API-Key':'training-admin-fixture'},storage,engine
    engine.dispose()

def create(workspace,color='gray',confirmed=True,boxes=None):
    client,headers,_,_=workspace
    report=client.post('/api/reports',headers=headers,files={'photo':('fixture.png',image_bytes(color),'image/png')}).json()
    if confirmed:
        report=client.patch('/api/reports/'+report['id'],headers=headers,json={'revision':report['revision'],'status':'Confirmed','action':'confirm','detections':boxes if boxes is not None else [box()]}).json()
    return report

def approval(workspace,report,**changes):
    client,headers,_,_=workspace
    value=dict(revision=report['revision'],split='train',capture_group='synthetic-run-1',rights_confirmed=True,negative_confirmed=False)
    value.update(changes)
    return client.put('/api/reports/'+report['id']+'/training',headers=headers,json=value)

def test_review_does_not_automatically_approve_or_change_any_model(workspace):
    client,headers,_,_=workspace;report=create(workspace)
    state=client.get('/api/reports/'+report['id']+'/training',headers=headers).json()
    assert state['approved'] is False and state['weights_changed'] is False
    assert client.get('/api/training/export',headers=headers).status_code==409

def test_approval_requires_confirmed_review_permission_and_current_revision(workspace):
    report=create(workspace,confirmed=False)
    assert approval(workspace,report).status_code==409
    report=create(workspace,'white')
    assert approval(workspace,report,rights_confirmed=False).status_code==409
    assert approval(workspace,report,revision='0'*64).status_code==409
    assert approval(workspace,report,capture_group='../route').status_code==409

def test_valid_export_has_yolo_labels_metadata_and_original_model_provenance(workspace):
    client,headers,_,_=workspace;report=create(workspace)
    assert approval(workspace,report).json()['approved'] is True
    response=client.get('/api/training/export',headers=headers);assert response.status_code==200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        meta=json.loads(archive.read('manifest.json'));example=meta['examples'][0]
        assert meta['weights_changed'] is False and example['initial_model_version']=='synthetic-model'
        labels=archive.read('labels/train/'+example['image_sha256']+'.txt').decode().split()
        assert labels[0]=='3' and [float(x) for x in labels[1:]]==pytest.approx([.375,.5,70/120,.75])
        assert '4: OTHER' in archive.read('data.yaml').decode()
        assert not any('.env' in name or name.endswith('.db') for name in archive.namelist())
    assert client.get('/api/training',headers=headers).json()['counts']['train']==1

def test_negative_examples_need_explicit_approval_and_export_empty_label_file(workspace):
    client,headers,_,_=workspace;report=create(workspace,boxes=[])
    assert approval(workspace,report).status_code==409
    assert approval(workspace,report,negative_confirmed=True).status_code==200
    with zipfile.ZipFile(io.BytesIO(client.get('/api/training/export',headers=headers).content)) as archive:
        example=json.loads(archive.read('manifest.json'))['examples'][0]
        assert example['reviewed_negative'] and archive.read('labels/train/'+example['image_sha256']+'.txt')==b''

@pytest.mark.parametrize('change',[{'detections':[box('D00')]},{'status':'Needs Review','action':'review'}])
def test_changed_annotations_or_reopened_review_are_excluded_until_reapproved(workspace,change):
    client,headers,_,_=workspace;report=create(workspace);assert approval(workspace,report).status_code==200
    assert client.patch('/api/reports/'+report['id'],headers=headers,json={'revision':report['revision'],**change}).status_code==200
    state=client.get('/api/reports/'+report['id']+'/training',headers=headers).json()
    assert state['stale'] and not state['approved']
    assert client.get('/api/training/export',headers=headers).status_code==409

def test_capture_group_cannot_leak_between_training_and_test(workspace):
    first=create(workspace);second=create(workspace,'white')
    assert approval(workspace,first).status_code==200
    assert approval(workspace,second,split='test').status_code==409
    assert approval(workspace,second,split='test',capture_group='different-run').status_code==200

def test_exact_duplicate_image_is_not_approved_twice_even_in_different_groups(workspace):
    first=create(workspace);second=create(workspace)
    assert approval(workspace,first).status_code==200
    assert approval(workspace,second,capture_group='other',split='test').status_code==409

def test_revocation_and_image_integrity_prevent_unapproved_export(workspace):
    client,headers,storage,_=workspace;report=create(workspace);assert approval(workspace,report).status_code==200
    path=next(storage.iterdir());original=path.read_bytes();path.write_bytes(original+b'changed')
    assert client.get('/api/training/export',headers=headers).status_code==409
    path.write_bytes(original)
    assert client.delete('/api/reports/'+report['id']+'/training',headers=headers).status_code==204
    assert client.get('/api/training/export',headers=headers).status_code==409

def test_viewers_cannot_approve_vote_or_export(workspace):
    client,_,_,_=workspace;report=create(workspace);viewer={'X-API-Key':'training-viewer-fixture'}
    assert client.get('/api/training/export',headers=viewer).status_code==403
    assert client.delete('/api/reports/'+report['id']+'/training',headers=viewer).status_code==403
    assert client.post('/api/reports/'+report['id']+'/vote',headers=viewer,json={'model_ids':['a','b'],'revision':report['revision']}).status_code==403
    assert client.get('/api/training/export').status_code==401

def test_vote_is_bound_to_the_report_revision_and_does_not_edit_report(workspace):
    client,headers,_,_=workspace;report=create(workspace)
    endpoint='/api/reports/'+report['id'];before=client.get(endpoint,headers=headers).json()
    assert client.post(endpoint+'/vote',headers=headers,json={'model_ids':['a','b'],'revision':'0'*64}).status_code==409
    result=client.post(endpoint+'/vote',headers=headers,json={'model_ids':['a','b'],'revision':report['revision']}).json()
    assert result['annotations_changed'] is False and result['active_model_changed'] is False
    assert client.get(endpoint,headers=headers).json()==before

def test_4k_png_larger_than_10mb_is_accepted_without_resizing(workspace):
    client,headers,storage,_=workspace;stream=io.BytesIO()
    image=Image.frombytes('RGB',(3840,2160),os.urandom(3840*2160*3));image.save(stream,'PNG');image.close()
    assert len(stream.getvalue())>10*1024*1024
    response=client.post('/api/reports',headers=headers,files={'photo':('4k.png',stream.getvalue(),'image/png')})
    assert response.status_code==201
    with Image.open(next(storage.iterdir())) as saved:assert saved.size==(3840,2160)
    assert client.get('/api/health').json()['max_upload_mb']==50

def test_configured_upload_byte_limit_remains_enforced(workspace,monkeypatch):
    client,headers,storage,_=workspace;monkeypatch.setenv('ROADSCAN_MAX_UPLOAD_MB','1')
    response=client.post('/api/reports',headers=headers,files={'photo':('large.png',b'x'*(1024*1024+1),'image/png')})
    assert response.status_code==413 and list(storage.iterdir())==[]


def test_missing_vote_image_returns_structured_error(workspace,monkeypatch):
    client,headers,storage,_=workspace;report=create(workspace)
    def missing(*args):raise FileNotFoundError('private-path-must-not-leak')
    monkeypatch.setattr(api.detector(),'compare',missing)
    response=client.post('/api/reports/'+report['id']+'/vote',headers=headers,json={'revision':report['revision'],'model_ids':['a','b']})
    assert response.status_code==409
    assert response.json()['detail']=='Report image file is missing or unreadable'


def test_vote_worker_is_independent_of_launch_directory(tmp_path,monkeypatch):
    import roadscan.voting as voting
    def fake_run(command,**options):
        job=json.loads(options['input'])
        root=str(__import__('pathlib').Path(voting.__file__).resolve().parent.parent)
        assert options['cwd']==root and options['env']['PYTHONPATH']==root
        assert 'ROADSCAN_API_KEY' not in options['env']
        __import__('pathlib').Path(job['output']).write_text(json.dumps({'state':'completed','reason':None,'detections':[]}),encoding='utf-8')
        return SimpleNamespace(returncode=0)
    monkeypatch.chdir(tmp_path);monkeypatch.setattr(voting.subprocess,'run',fake_run)
    monkeypatch.setenv('ROADSCAN_API_KEY','must-not-forward')
    item={'sha256':'a'*64,'name':'fixture','classes':{'0':'D40'},'file':'fixture.pt','imgsz':640}
    assert voting.run_model(item,tmp_path/'fixture.pt',tmp_path/'fixture.jpg')['state']=='completed'
