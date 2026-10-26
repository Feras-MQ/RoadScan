"""Synthetic live-preview contracts: no real camera images or live databases."""
import io
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import roadscan.api as api
from roadscan.core import BASE
from roadscan.inference import LocalDetector


def photo(size=(120, 80), kind='PNG'):
    output=io.BytesIO(); Image.new('RGB',size,'gray').save(output,kind); return output.getvalue()


@pytest.fixture
def preview(tmp_path, monkeypatch):
    engine=create_engine('sqlite:///'+str(tmp_path/'preview.db'),connect_args={'check_same_thread':False})
    BASE.metadata.create_all(engine)
    storage=tmp_path/'uploads'; storage.mkdir()
    calls=[]
    def predict(image, *, wait=True, live_mode=None):
        calls.append((image.size,wait))
        return {'state':'completed','reason':None,'model_version':'synthetic-fixture',
                'detections':[{'class_id':'D00','box':[10,10,100,70],'confidence':.7}]}
    fake=SimpleNamespace(confidence=.25,predict=predict)
    monkeypatch.setattr(api,'init_db',lambda:None)
    monkeypatch.setattr(api,'Session',sessionmaker(bind=engine))
    monkeypatch.setattr(api,'STORAGE',storage)
    monkeypatch.setattr(api,'detector',lambda:fake)
    monkeypatch.setenv('ROADSCAN_API_KEY','live-preview-fixture')
    monkeypatch.setenv('ROADSCAN_VIEWER_KEY','live-viewer-fixture')
    monkeypatch.delenv('ROADSCAN_ACCOUNTS_FILE',raising=False)
    monkeypatch.delenv('ROADSCAN_REVIEWER_KEY',raising=False)
    with TestClient(api.app) as client:
        yield client,{'X-API-Key':'live-preview-fixture'},fake,calls,engine,storage
    engine.dispose()


def test_recognition_returns_frame_boxes_without_persisting_anything(preview):
    client,headers,_,calls,engine,storage=preview
    response=client.post('/api/recognize',headers=headers,content=photo())
    assert response.status_code==200
    result=response.json()
    assert result['state']=='completed' and result['persisted'] is False
    assert (result['width'],result['height'])==(120,80)
    assert result['detections'][0]['class_id']=='D00'
    assert result['confidence_threshold']==.25 and result['elapsed_ms']>=0
    assert calls==[((120,80),False)] and list(storage.iterdir())==[]
    with engine.connect() as db:
        for table in ('reports','status_history','audit_events'):
            assert db.execute(text('select count(*) from '+table)).scalar()==0


@pytest.mark.parametrize('headers,code', [({},401),({'X-API-Key':'wrong-fixture'},401),({'X-API-Key':'live-viewer-fixture'},403)])
def test_recognition_requires_review_permission(preview,headers,code):
    client,_,_,calls,_,_=preview
    assert client.post('/api/recognize',headers=headers,content=photo()).status_code==code
    assert calls==[]


@pytest.mark.parametrize('payload,code',[(b'not-an-image',415),(b'x'*(2*1024*1024+1),413),(photo((2001,1000)),415),(photo(kind='GIF'),415)], ids=['not-image', 'oversized-bytes', 'oversized-dims', 'gif'])
def test_rejected_frames_never_reach_the_detector(preview,payload,code):
    client,headers,_,calls,_,storage=preview
    assert client.post('/api/recognize',headers=headers,content=payload).status_code==code
    assert calls==[] and list(storage.iterdir())==[]


@pytest.mark.parametrize('state,reason',[('busy','inference_busy'),('not_configured','checkpoint_missing'),('failed','inference_fixture')])
def test_non_success_states_are_not_disguised_as_a_clean_road(preview,state,reason):
    client,headers,fake,_,_,storage=preview
    fake.predict=lambda image,**kw:dict(state=state,reason=reason,detections=[],model_version='fixture')
    data=client.post('/api/recognize',headers=headers,content=photo()).json()
    assert data['state']==state and data['reason']==reason and data['persisted'] is False
    assert list(storage.iterdir())==[]


def test_preview_does_not_overlap_an_active_model_call(monkeypatch):
    monkeypatch.delenv('ROADSCAN_YOLO_WEIGHTS',raising=False)
    detector=LocalDetector(); entered=threading.Event(); release=threading.Event()
    class FakeModel:
        def predict(self,**kwargs):
            entered.set(); assert release.wait(3); return []
    detector.model=FakeModel(); detector.version='synthetic-lock'; detector.confidence=.25
    with ThreadPoolExecutor(max_workers=1) as pool:
        active=pool.submit(detector.predict,Image.new('RGB',(120,80)))
        try:
            assert entered.wait(3)
            assert detector.predict(Image.new('RGB',(120,80)),wait=False)['state']=='busy'
        finally: release.set()
        assert active.result(timeout=3)['state']=='completed'
    assert detector.predict(Image.new('RGB',(120,80)),wait=False)['state']=='completed'

def test_rtdetr_border_crossing_does_not_reject_the_whole_frame(monkeypatch):
    monkeypatch.delenv('ROADSCAN_YOLO_WEIGHTS',raising=False)
    detector=LocalDetector();detector.confidence=.25;detector.mapping={0:'D40'}
    def fake_box(coords):
        return SimpleNamespace(xyxy=[SimpleNamespace(tolist=lambda:coords)],cls=[0],conf=[.8])
    detector.model=SimpleNamespace(predict=lambda **kwargs:[SimpleNamespace(boxes=[
        fake_box([-5,10,130,90]),fake_box([130,10,140,20]),fake_box([20,20,40,50])])])
    result=detector.predict(Image.new('RGB',(120,80)))
    assert result['state']=='completed'
    assert [d['box'] for d in result['detections']]==[[0,10,120,80],[20,20,40,50]]
