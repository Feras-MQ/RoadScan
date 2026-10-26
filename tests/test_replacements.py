import importlib.util,json
from pathlib import Path
import pytest
from roadscan.priority import analyze
from roadscan.duplicate_finder import DuplicateFinder,distance_m
from roadscan.accuracy_report import select_thresholds
from roadscan.resnet_baseline import thresholds

def test_priority_ranking_preserves_unscored_and_validates_boxes():
    box={'class_id':'D40','box':[1,1,8,8],'confidence':.9}
    rows=[{'id':'a','width':10,'height':10,'detections':[box]},{'id':'b','width':10,'height':10,'detections':[]}]
    result=analyze(rows)
    assert result['baseline_ranking']==['a'] and len(result['ranking_sensitivity'])==8
    assert result['reports'][1]['analysis']['baseline'] is None
    with pytest.raises(ValueError):analyze(rows+rows)
    rows[0]['detections'][0]['box']=[0,0,20,20]
    with pytest.raises(ValueError):analyze(rows)

def test_gps_distance_and_invalid_inputs():
    assert distance_m((24,46),(24,46))==0
    assert 40<distance_m((24,46),(24.0004,46))<50
    assert distance_m((0,179.9999),(0,-179.9999))<25
    for point in [(None,0),(91,0),(0,float('nan'))]:
        with pytest.raises(ValueError):distance_m(point,(0,0))

def test_faiss_crops_exclude_closed_distant_and_simulated_reports(tmp_path):
    pytest.importorskip('faiss')
    from PIL import Image
    image=tmp_path/'image.png';Image.new('RGB',(10,10)).save(image)
    checkpoint=tmp_path/'weights';checkpoint.write_bytes(b'test-only')
    class Fake:
        calls=0
        def encode(self,path,box):self.calls+=1;assert box==[0,0,8,8];return [1.]+[0.]*383
    fake=Fake();finder=DuplicateFinder(checkpoint,tmp_path/'cache',fake)
    query={'id':'q','status':'Needs Review','gps':[24,46],'location_source':'manual','image':str(image),'detections':[{'box':[0,0,8,8]}]}
    gallery=[dict(query,id='near',gps=[24.0001,46]),dict(query,id='closed',status='Resolved'),dict(query,id='far',gps=[25,46]),dict(query,id='sim',location_source='simulated'),dict(query)]
    result=finder.search(query,gallery)
    assert result['candidate_reports']==1 and result['matches'][0]['report_id']=='near'
    assert result['matches'][0]['similarity']==pytest.approx(1) and fake.calls==1
    assert finder.search(query,gallery)['matches']==result['matches'] and fake.calls==1
    with pytest.raises(ValueError):finder.search(dict(query,gps=[None,None]),gallery)

def test_validation_thresholds_and_runner_refuse_bad_plans(tmp_path):
    profile=select_thresholds([.1,.5],[[.5,.9],[.5,.9]],[[.9,.5],[.9,.5]],['D00','D40'])
    assert profile['D40']==.1
    assert select_thresholds([.1],[[0]],[[0]],['D40'])=={}
    with pytest.raises(ValueError):select_thresholds([float('nan')],[[.5]],[[.5]],['D00'])
    assert len(thresholds([[0]*4,[1]*4],[[.1]*4,[.9]*4]))==4
    with pytest.raises(ValueError):thresholds([[1]*4],[[.9]*4])
    path=Path(__file__).resolve().parents[1]/'runpod/run_all.py'
    spec=importlib.util.spec_from_file_location('replacement_runner',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.commands([{'name':'E1','module':'resnet_baseline','args':['--help']}])[0][0]=='E1'
    for plan in [[{'name':'../escape','module':'priority'}],[{'name':'x','module':'os'}],[{'name':'x','module':'priority','args':'--help'}]]:
        with pytest.raises(ValueError):module.commands(plan)
    data=tmp_path/'reports.json';data.write_text('[]');command=['python','--input',str(data)]
    before=module.input_fingerprint(command);data.write_text('[{}]')
    assert before!=module.input_fingerprint(command)
