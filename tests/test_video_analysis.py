"""Synthetic AVI evidence only; no physical camera or ML accuracy claims."""
from types import SimpleNamespace
import base64
import io
import cv2
import numpy as np
import pytest
from PIL import Image
from fastapi import FastAPI
from fastapi.testclient import TestClient
from roadscan import video_analysis as video

@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv('ROADSCAN_API_KEY', 'synthetic-admin')
    monkeypatch.setenv('ROADSCAN_REVIEWER_KEY', 'synthetic-reviewer')
    monkeypatch.setenv('ROADSCAN_VIEWER_KEY', 'synthetic-viewer')
    monkeypatch.delenv('ROADSCAN_ACCOUNTS_FILE', raising=False)
    path = tmp_path/'clip.avi'
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'MJPG'), 12, (1280, 720))
    assert writer.isOpened()
    for index in range(4):
        writer.write(np.full((720,1280,3), 30+index*40, dtype=np.uint8))
    writer.release()
    calls=[]
    def predict(image, **kw):
        calls.append((image.size, image.getpixel((0,0))[0], kw))
        return dict(state='completed',detections=[],model_version='fixture')
    detector = SimpleNamespace(version='fixture',predict=predict)
    app=FastAPI(); app.include_router(video.create_video_router(lambda:detector))
    with TestClient(app) as client:
        yield client, {'X-API-Key':'synthetic-admin'}, path.read_bytes(), detector, calls


def start(setup, **kw):
    client,headers,raw,*_=setup
    return client.post('/api/video-analysis?filename=clip.avi',content=raw,headers=headers,**kw)


def test_every_frame_and_honest_eof(setup):
    client,headers,_,_,calls=setup
    result=start(setup); assert result.status_code==200
    meta=result.json(); assert meta['total_frames']==4
    ident=meta['id']
    for index in range(4):
        frame=client.post(f'/api/video-analysis/{ident}/next',headers=headers).json()
        assert frame['state']=='completed' and frame['frame_index']==index
        assert frame['processed_count']==index+1 and frame['persisted'] is False
        assert (frame['width'],frame['height'])==(960,540)
        with Image.open(io.BytesIO(base64.b64decode(frame['jpeg_base64']))) as image:
            assert image.size==(960,540)
    final=client.post(f'/api/video-analysis/{ident}/next',headers=headers).json()
    assert final['state']=='finished' and final['complete'] is True
    assert final['processed_count']==4 and len(calls)==4
    assert [v[1] for v in calls]==sorted(v[1] for v in calls)


def test_busy_retains_frame_and_model_change_aborts(setup):
    client,headers,_,detector,calls=setup
    ident=start(setup).json()['id']; original=detector.predict
    detector.predict=lambda image,**kw:dict(state='busy',detections=[],model_version='fixture')
    assert client.post(f'/api/video-analysis/{ident}/next',headers=headers).json()['state']=='busy'
    detector.predict=original
    frame=client.post(f'/api/video-analysis/{ident}/next',headers=headers).json()
    assert frame['frame_index']==0 and calls[0][1]<40
    detector.version='other'
    result=client.post(f'/api/video-analysis/{ident}/next',headers=headers).json()
    assert not result['complete'] and result['reason']=='model_changed' and len(calls)==1


def test_auth_owner_limit_and_cancellation(setup):
    client,headers,raw,*_=setup
    for auth,status in [({},401),({'X-API-Key':'synthetic-viewer'},403)]:
        assert client.post('/api/video-analysis?filename=x.avi',headers=auth,content=raw).status_code==status
    ident=start(setup).json()['id']
    assert client.post(f'/api/video-analysis/{ident}/next',headers={'X-API-Key':'synthetic-reviewer'}).status_code==404
    assert start(setup).status_code==200
    assert start(setup).status_code==429
    assert client.delete(f'/api/video-analysis/{ident}',headers=headers).status_code==200
    assert client.post(f'/api/video-analysis/{ident}/next',headers=headers).status_code==404
    assert start(setup).status_code==200


def test_bad_upload_does_not_leak_session_slot(setup,monkeypatch):
    client,headers,*_=setup
    for _ in range(3):
        assert client.post('/api/video-analysis?filename=x.mp4',headers=headers,content=b'playlist').status_code==415
    monkeypatch.setattr(video,'MAX_UPLOAD',10)
    assert start(setup).status_code==413
    monkeypatch.setattr(video,'MAX_UPLOAD',200*1024*1024)
    assert start(setup).status_code==200


def test_metadata_discrepancy_is_not_full_coverage(setup,monkeypatch):
    client,headers,*_=setup
    original=video._open
    def wrong_metadata(session):
        original(session); session.total=7
    monkeypatch.setattr(video,'_open',wrong_metadata)
    ident=start(setup).json()['id']
    for _ in range(4):
        client.post(f'/api/video-analysis/{ident}/next',headers=headers)
    result=client.post(f'/api/video-analysis/{ident}/next',headers=headers).json()
    assert result['complete'] is False and result['processed_count']==4 and result['total_frames']==7


def test_expired_session_deleted(setup,monkeypatch):
    client,headers,*_=setup
    ident=start(setup).json()['id']
    monkeypatch.setattr(video,'SESSION_TTL',-1)
    assert client.post(f'/api/video-analysis/{ident}/next',headers=headers).status_code==404

def test_missing_optional_decoder_is_actionable_503(setup,monkeypatch):
    original=video.importlib.import_module
    def missing(name):
        if name=='cv2': raise ImportError('fixture')
        return original(name)
    monkeypatch.setattr(video.importlib,'import_module',missing)
    assert start(setup).status_code==503


def test_cancel_during_inference_cleans_up_without_another_frame(setup):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    client,headers,_,detector,calls=setup
    ident=start(setup).json()['id']
    entered=threading.Event(); release=threading.Event(); original=detector.predict
    def slow(image,**kw):
        entered.set(); assert release.wait(5)
        return original(image,**kw)
    detector.predict=slow
    with ThreadPoolExecutor(max_workers=1) as pool:
        request=pool.submit(client.post,f'/api/video-analysis/{ident}/next',headers=headers)
        assert entered.wait(3)
        try:
            response=client.delete(f'/api/video-analysis/{ident}',headers=headers)
            assert response.status_code==200 and response.json()['state']=='cancelled'
        finally:
            release.set()
        assert request.result(timeout=5).json()['state']=='cancelled'
    assert client.post(f'/api/video-analysis/{ident}/next',headers=headers).status_code==404
    assert len(calls)==1

def test_unknown_count_does_not_claim_all_original_frames(setup,monkeypatch):
    client,headers,*_=setup
    original=video._open
    def unknown_metadata(session):
        original(session); session.total=None
    monkeypatch.setattr(video,'_open',unknown_metadata)
    ident=start(setup).json()['id']
    for _ in range(4): client.post(f'/api/video-analysis/{ident}/next',headers=headers)
    result=client.post(f'/api/video-analysis/{ident}/next',headers=headers).json()
    assert result['complete'] is False and result['reason']=='decoder_end_coverage_unverified'


def test_model_switch_race_discards_different_model_result(setup):
    client,headers,_,detector,_=setup
    ident=start(setup).json()['id']
    detector.predict=lambda image,**kw:dict(state='completed',model_version='changed',detections=[])
    result=client.post(f'/api/video-analysis/{ident}/next',headers=headers).json()
    assert result['complete'] is False and result['reason']=='model_changed'
    assert result['processed_count']==0 and 'jpeg_base64' not in result


def test_router_lifespan_releases_temporary_files(setup,monkeypatch):
    client,headers,raw,detector,_=setup
    paths=[]; original=video.VideoSession
    def tracked(*args):
        session=original(*args); paths.append(session.path); return session
    monkeypatch.setattr(video,'VideoSession',tracked)
    app=FastAPI(); app.include_router(video.create_video_router(lambda:detector))
    with TestClient(app) as other:
        response=other.post('/api/video-analysis?filename=x.avi',content=raw,headers=headers)
        assert response.status_code==200 and paths[0].exists()
    assert not paths[0].parent.exists()
