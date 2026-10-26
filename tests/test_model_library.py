"""Synthetic library tests. Fixture bytes/boxes are not model accuracy evidence."""
import hashlib
import io
import json
import sys
import types
import time
from concurrent.futures import ThreadPoolExecutor
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
import roadscan.api as api
import roadscan.model_library as library_module
from roadscan.model_library import ModelLibrary, ModelRuntime
from roadscan.model_classes import class_mapping
from roadscan.checkpoints import supported_globals

FIVE = dict(enumerate(('Longitudinal_Crack','Transverse_Crack','Alligator_Crack','Other_Corruption','Pothole')))

def test_fifth_class_preserves_pothole_identity_and_explicit_aliases():
    mapped=class_mapping(FIVE)
    assert mapped[3]=='OTHER' and mapped[4]=='D40'
    assert class_mapping(dict(enumerate(('D00_Longitudinal_Crack','D10_Transverse_Crack','D20_Alligator_Crack','D40_Pothole'))))=={0:'D00',1:'D10',2:'D20',3:'D40'}

@pytest.mark.parametrize('names',[
    {0:'D00',1:'D10',2:'D20',3:'unknown'},
    {0:'D00',1:'D10',2:'D20',3:'D40',4:'Pothole'},
    {0:'D00',1:'D10',2:'D20',4:'D40'},
])
def test_unknown_duplicate_or_missing_label_mapping_is_rejected(names):
    with pytest.raises(ValueError):class_mapping(names)

def test_checkpoint_scanner_blocks_unapproved_serialized_code(monkeypatch):
    fake=types.ModuleType('torch')
    fake.serialization=SimpleNamespace(get_unsafe_globals_in_checkpoint=lambda _:['os.system'])
    monkeypatch.setitem(sys.modules,'torch',fake)
    with pytest.raises(ValueError,match='unsupported serialized types'):supported_globals('fixture.pt')

def test_simultaneous_first_requests_create_only_one_runtime(monkeypatch):
    created=[]
    def constructor(library):
        created.append(object());time.sleep(.02);return created[-1]
    monkeypatch.setattr(api,'ModelRuntime',constructor)
    monkeypatch.setattr(api,'model_library',lambda:object())
    api._detector_instance.cache_clear()
    try:
        with ThreadPoolExecutor(max_workers=6) as pool:
            values=list(pool.map(lambda _:api.detector(),range(6)))
        assert len(created)==1 and all(value is values[0] for value in values)
    finally:api._detector_instance.cache_clear()

@pytest.fixture
def library(tmp_path,monkeypatch):
    def inspect(path):
        if path.read_bytes()==b'invalid-fixture':raise ValueError('Unsupported class label')
        return dict(family='yolo',classes={'0':'D00','1':'D10','2':'D20','3':'D40'},imgsz=640,reported_metrics={},metrics_source='Synthetic metadata fixture')
    monkeypatch.setattr(library_module,'inspect_checkpoint',inspect)
    return ModelLibrary(tmp_path/'library')

def package(path,entries):
    with zipfile.ZipFile(path,'w') as z:
        for name,value in entries.items():z.writestr(name,value)
    return path

def test_import_deduplicates_and_does_not_activate(library,tmp_path):
    source=tmp_path/'first.pt';source.write_bytes(b'synthetic-model')
    first=library.import_file(source,'first.pt')
    assert len(first['imported'])==1 and first['active_changed'] is False
    assert library.selected()=='baseline'
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    item,path=library.find(digest)
    assert path.read_bytes()==source.read_bytes() and item['id']==digest
    assert library.import_file(source,'renamed.pt')['duplicates']==['renamed.pt']
    assert len(library.list())==1

def test_zip_import_ignores_documents_and_labels_supplied_metrics(library,tmp_path):
    source=package(tmp_path/'models.zip',{'models/a.pt':b'first-fixture','b.pt':b'invalid-fixture','README.txt':b'not executable',
        'MODEL_INDEX.csv':'File,Best_mAP50,Best_mAP50_95\na.pt,0.6,0.3\n'})
    result=library.import_file(source,'models.zip')
    assert len(result['imported'])==1 and len(result['rejected'])==1
    assert result['imported'][0]['reported_metrics']=={'mAP50':.6,'mAP50_95':.3}
    assert 'not independently verified' in result['imported'][0]['metrics_source']
    assert not (library.root/'README.txt').exists()

@pytest.mark.parametrize('entry',['../escaped.pt','/absolute.pt','nested/../../outside.pt'])
def test_archive_paths_cannot_escape_library(library,tmp_path,entry):
    source=package(tmp_path/'bad.zip',{entry:b'never loaded'})
    with pytest.raises(ValueError,match='Unsafe archive'):library.import_file(source,'bad.zip')
    assert not (tmp_path/'escaped.pt').exists()

def test_model_path_tampering_and_unknown_identifiers_fail_closed(library,tmp_path):
    with pytest.raises(ValueError):library.find('../file')
    source=tmp_path/'model.pt';source.write_bytes(b'fixture')
    ident=library.import_file(source,'model.pt')['imported'][0]['id']
    library.save_selected(ident)
    assert ModelLibrary(library.root).selected()==ident
    with pytest.raises(ValueError):library.find('a'*64)

def test_duplicate_basenames_do_not_inherit_an_ambiguous_metric(library,tmp_path):
    source=package(tmp_path/'models.zip',{'one/best.pt':b'one','two/best.pt':b'two',
        'MODEL_INDEX.csv':'File,Best_mAP50,Best_mAP50_95\nbest.pt,0.9,0.8\n'})
    items=library.import_file(source,'models.zip')['imported']
    assert {item['name'] for item in items}=={'one_best','two_best'}
    assert all(item['reported_metrics']=={} for item in items)

@pytest.fixture
def runtime(library,tmp_path,monkeypatch):
    baseline=tmp_path/'baseline.pt';baseline.write_bytes(b'baseline')
    monkeypatch.setenv('ROADSCAN_YOLO_WEIGHTS',str(baseline))
    monkeypatch.setenv('ROADSCAN_YOLO_SHA256',hashlib.sha256(baseline.read_bytes()).hexdigest())
    class FakeDetector:
        def __init__(self,path=None,sha256=None,imgsz=640,confidence_profile=None):
            self.model=object();self.version='baseline-fixture';self.error=None;self.confidence=.25
            self.confidence_profile=confidence_profile
            if path is not None and hashlib.sha256(Path(path).read_bytes()).hexdigest()!=sha256:
                self.model=None;self.error='checkpoint_hash_mismatch'
        def predict(self,image):
            return dict(state='completed',reason=None,detections=[],model_version=self.version)
    monkeypatch.setattr(library_module,'LocalDetector',FakeDetector)
    source=tmp_path/'new.pt';source.write_bytes(b'new-fixture')
    ident=library.import_file(source,'new.pt')['imported'][0]['id']
    return ModelRuntime(library),ident,FakeDetector

def test_activation_persists_and_switching_back_needs_no_restart(runtime,library):
    current,ident,_=runtime
    result=current.activate(ident)
    assert result['active_id']==ident and library.selected()==ident
    assert current.version=='new.pt@'+ident[:12]
    assert ModelRuntime(library).active_id==ident
    current.activate('baseline')
    assert current.active_id=='baseline' and library.selected()=='baseline'

def test_failed_switch_keeps_previous_model_and_active_record(runtime,library,monkeypatch):
    current,ident,fake=runtime
    before=current.model
    monkeypatch.setattr(fake,'predict',lambda *args:dict(state='failed'))
    with pytest.raises(ValueError,match='previous model is still active'):current.activate(ident)
    assert current.model is before and current.active_id=='baseline' and library.selected()=='baseline'
    assert not (library.root/'active.json').exists()

def test_changed_model_bytes_cannot_activate(runtime,library):
    current,ident,_=runtime
    _,path=library.find(ident);path.write_bytes(b'tampered')
    before=current.model
    with pytest.raises(ValueError,match='checkpoint_hash_mismatch'):current.activate(ident)
    assert current.model is before and library.selected()=='baseline'

def test_model_switch_and_live_inference_do_not_overlap(runtime):
    current,ident,_=runtime
    with current._lock:
        assert current.predict(None,wait=False)['state']=='busy'
        with pytest.raises(ValueError,match='busy'):current.activate(ident)

@pytest.fixture
def model_api(library,runtime,monkeypatch):
    current,ident,_=runtime
    monkeypatch.setattr(api,'init_db',lambda:None)
    monkeypatch.setattr(api,'model_library',lambda:library)
    monkeypatch.setattr(api,'detector',lambda:current)
    monkeypatch.setattr(api,'model_support_available',lambda:True)
    monkeypatch.setenv('ROADSCAN_API_KEY','model-admin-fixture')
    monkeypatch.setenv('ROADSCAN_VIEWER_KEY','model-viewer-fixture')
    monkeypatch.delenv('ROADSCAN_REVIEWER_KEY',raising=False)
    monkeypatch.delenv('ROADSCAN_ACCOUNTS_FILE',raising=False)
    with TestClient(api.app) as client:yield client,ident

def test_browser_model_api_import_activate_and_roles(model_api):
    client,ident=model_api
    admin={'X-API-Key':'model-admin-fixture'}
    viewer={'X-API-Key':'model-viewer-fixture'}
    assert client.get('/api/models').status_code==401
    value=client.get('/api/models',headers=viewer).json()
    assert value['can_manage'] is False and value['items'][1]['id']==ident
    assert client.post('/api/models/import?filename=other.pt',headers=viewer,content=b'secret fixture').status_code==403
    response=client.post('/api/models/import?filename=other.pt',headers=admin,content=b'other synthetic')
    assert response.status_code==200 and response.json()['active_changed'] is False
    assert client.post('/api/models/'+ident+'/activate',headers=viewer).status_code==403
    assert client.post('/api/models/'+ident+'/activate',headers=admin).json()['active_id']==ident
    assert client.get('/api/models',headers=admin).json()['active_id']==ident

@pytest.mark.parametrize('name',['../foo.pt','a.exe','sub\\file.pt'])
def test_model_upload_rejects_unsafe_filenames(model_api,name):
    client,_=model_api
    response=client.post('/api/models/import',params={'filename':name},headers={'X-API-Key':'model-admin-fixture'},content=b'fixture')
    assert response.status_code==422

def test_demo_auto_connect_exposes_only_the_fixed_public_demo_key(model_api,monkeypatch):
    client,_=model_api
    monkeypatch.setenv('ROADSCAN_DEMO_MODE','1')
    private=client.get('/api/health').json()
    assert private['demo'] is False and private['demo_token'] is None
    assert 'model-admin-fixture' not in json.dumps(private)
    monkeypatch.setenv('ROADSCAN_API_KEY','roadscan-live-qa-local-only')
    demo=client.get('/api/health').json()
    assert demo['demo'] is True and demo['demo_token']=='roadscan-live-qa-local-only'



@pytest.mark.parametrize('digest_ok,threshold,accepted', [(True,'0.056',True),(False,'0.056',False),(True,'nan',False),(True,'',False)])
def test_team_thresholds_require_exact_checkpoint_and_complete_finite_values(library,tmp_path,digest_ok,threshold,accepted):
    weights=b'team-detector-fixture'
    digest=hashlib.sha256(weights).hexdigest() if digest_ok else '0'*64
    index='File,SHA256,Best_mAP50,Best_mAP50_95,Metric_scope,Threshold_D00,Threshold_D10,Threshold_D20,Threshold_D40,Threshold_scope\n'
    index+=f'main.pt,{digest},0.6304,0.3301,RDD test,0.173,0.166,0.195,{threshold},RDD validation 1024px\n'
    source=package(tmp_path/'team.zip',{'main.pt':weights,'MODEL_INDEX.csv':index,**{f'plots/{i}.txt':'fixture' for i in range(110)}})
    if not accepted:
        with pytest.raises(ValueError, match='No compatible checkpoints'):
            library.import_file(source,'team.zip')
        return
    result=library.import_file(source,'team.zip')
    assert bool(result['imported']) is accepted
    if accepted:
        item=result['imported'][0]
        assert item['confidence_profile']=={'D00':.173,'D10':.166,'D20':.195,'D40':.056}
        assert item['metrics_source'].startswith('RDD test; team supplied')
