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


def test_sampled_frames_and_detail_resolution(setup):
    client,headers,raw,_,calls=setup
    # 12 fps clip, 6 analyzed frames per second -> every 2nd of the 4 frames
    meta=client.post('/api/video-analysis?filename=clip.avi&sample=6&mode=detail',content=raw,headers=headers).json()
    assert meta['sample']==6 and meta['total_frames'] is None
    for index in range(2):
        frame=client.post(f"/api/video-analysis/{meta['id']}/next",headers=headers).json()
        assert frame['frame_index']==index and frame['source_frame']==index*2
        assert (frame['width'],frame['height'])==(1280,720)
    final=client.post(f"/api/video-analysis/{meta['id']}/next",headers=headers).json()
    assert final['state']=='finished' and final['complete'] is True and len(calls)==2
    assert [abs(value-expected)<=4 for value,expected in zip([v[1] for v in calls],[30,110])]==[True,True]


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
        original(session); session.total=7; session.source_total=7
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
        original(session); session.total=None; session.source_total=None
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


def test_m4v_extension_reaches_decoder_without_claiming_codec_support(setup, monkeypatch):
    client, headers, raw, *_ = setup
    opened = []
    monkeypatch.setattr(video, '_open', lambda session: opened.append(session))
    response = client.post('/api/video-analysis?filename=clip.M4V', content=raw, headers=headers)
    assert response.status_code == 200 and len(opened) == 1
    # Extension contract only; this deliberately does not claim HEVC/M4V decoding.


class FakeCapture:
    def __init__(self, timestamps, fps):
        self.timestamps, self.fps, self.index = timestamps, fps, -1
        self.grabs = self.retrieves = 0
        self.fail_retrieve_at = None
    def isOpened(self): return True
    def release(self): pass
    def get(self, prop):
        return {cv2.CAP_PROP_FRAME_WIDTH: 4, cv2.CAP_PROP_FRAME_HEIGHT: 4,
                cv2.CAP_PROP_FRAME_COUNT: len(self.timestamps), cv2.CAP_PROP_FPS: self.fps,
                cv2.CAP_PROP_POS_MSEC: self.timestamps[max(0, self.index)]}.get(prop, 0)
    def grab(self):
        self.index += 1; self.grabs += 1
        return self.index < len(self.timestamps)
    def retrieve(self):
        self.retrieves += 1
        return (False, None) if self.index == self.fail_retrieve_at else (True, np.zeros((4, 4, 3), dtype=np.uint8))


def sample_fixture(monkeypatch, timestamps, fps, rate, capture=None):
    capture = capture or FakeCapture(timestamps, fps)
    monkeypatch.setattr(cv2, 'VideoCapture', lambda *args: capture)
    session = video.VideoSession('fixture', 'balanced', 'fixture')
    session.path.write_bytes(b'RIFF0000AVI ')
    session.sample = rate
    detector = SimpleNamespace(version='fixture', predict=lambda *a, **k: dict(state='completed', model_version='fixture', detections=[]))
    frames = []
    try:
        video._open(session)
        while True:
            result = video._next(session, detector)
            if result['state'] == 'finished':
                return frames, result
            frames.append(result)
    finally:
        session.close()


@pytest.mark.parametrize('fps,count,rate,expected', [
    (25, 25, 10, [0,3,5,8,10,13,15,18,20,23]),
    (29.97, 300, 10, None), (5, 5, 10, [0,1,2,3,4]),
])
def test_fractional_sampling_no_rounded_stride(monkeypatch, fps, count, rate, expected):
    frames, final = sample_fixture(monkeypatch, [i*1000/fps for i in range(count)], fps, rate)
    assert final['complete'] is True
    assert len(frames) == (100 if expected is None else len(expected))
    if expected is not None:
        assert [f['source_frame'] for f in frames] == expected
    assert final['total_frames'] == len(frames)


def test_variable_rate_uses_timestamps_not_frame_stride(monkeypatch):
    frames, final = sample_fixture(monkeypatch, [0,10,20,110,115,230,250,310,490,510], 25, 10)
    assert [f['source_frame'] for f in frames] == [0,3,5,7,8,9]
    assert all(f['sampling_timing'] == 'timestamps' for f in frames)
    assert final['complete'] is True


@pytest.mark.parametrize('bad', [0, float('nan'), -1])
def test_bad_timestamps_fall_back_without_stalling(monkeypatch, bad):
    frames, final = sample_fixture(monkeypatch, [0]+[bad]*24, 25, 10)
    assert len(frames) == 10 and final['complete']
    assert frames[-1]['sampling_timing'] == 'nominal_fps_fallback'
    assert [f['source_frame'] for f in frames] == [0,3,5,8,10,13,15,18,20,23]


@pytest.mark.parametrize('fps', [0, -1, float('nan'), float('inf')])
def test_missing_fps_rejects_sampling_but_all_frames_still_work(monkeypatch, fps):
    with pytest.raises(video.HTTPException) as exc:
        sample_fixture(monkeypatch, [0,40,80], fps, 10)
    assert exc.value.status_code == 422
    frames, final = sample_fixture(monkeypatch, [0,40,80], fps, 0)
    assert len(frames) == 3 and final['complete']


@pytest.mark.parametrize('timestamps,fps,rate', [
    ([i*40 for i in range(25)], 25, 10), ([i*1000/29.97 for i in range(300)], 29.97, 10),
    ([0,10,20,110,115,230,250,310,490,510], 25, 10), ([0]+[float('nan')]*24, 25, 10),
    ([i*40 for i in range(25)], 25, 0), ([i*1000/120 for i in range(240)], 120, 1),
])
def test_only_analyzed_frames_are_retrieved(monkeypatch, timestamps, fps, rate):
    capture = FakeCapture(timestamps, fps)
    frames, final = sample_fixture(monkeypatch, timestamps, fps, rate, capture)
    assert final['complete'] is True and final['reason'] == 'decoder_eof'
    assert capture.retrieves == len(frames) and capture.grabs == len(timestamps) + 1


def test_retrieve_failure_ends_like_a_failed_read(monkeypatch):
    capture = FakeCapture([i*40 for i in range(25)], 25)
    capture.fail_retrieve_at = 5
    frames, final = sample_fixture(monkeypatch, [], 25, 0, capture)
    assert len(frames) == 5 and final['processed_count'] == 5
    assert final['complete'] is False and final['reason'] == 'metadata_mismatch_coverage_unverified'


def test_cancel_between_frames_retrieves_nothing_more(monkeypatch):
    capture = FakeCapture([i*40 for i in range(25)], 25)
    monkeypatch.setattr(cv2, 'VideoCapture', lambda *args: capture)
    session = video.VideoSession('fixture', 'balanced', 'fixture')
    session.path.write_bytes(b'RIFF0000AVI ')
    session.sample = 10
    detector = SimpleNamespace(version='fixture', predict=lambda *a, **k: dict(state='completed', model_version='fixture', detections=[]))
    video._open(session)
    assert video._next(session, detector)['source_frame'] == 0
    session.cancelled.set()
    assert video._next(session, detector)['reason'] == 'cancelled'
    assert capture.retrieves == 1 and capture.grabs == 1


def test_low_disk_removes_partial_file_and_frees_slot(setup, monkeypatch):
    paths = []
    original = video.VideoSession
    def tracked(*args):
        session = original(*args); paths.append(session.path); return session
    monkeypatch.setattr(video, 'VideoSession', tracked)
    disk_usage = video.shutil.disk_usage
    monkeypatch.setattr(video.shutil, 'disk_usage', lambda path: SimpleNamespace(free=video.TEMP_RESERVE))
    for _ in range(3):
        assert start(setup).status_code == 507
        assert not paths[-1].parent.exists()
    monkeypatch.setattr(video.shutil, 'disk_usage', disk_usage)
    assert start(setup).status_code == 200


def test_interrupted_and_slow_uploads_release_files_and_slots(monkeypatch):
    import asyncio
    from starlette.requests import Request, ClientDisconnect
    paths = []
    original = video.VideoSession
    def tracked(*args):
        session = original(*args); paths.append(session.path); return session
    monkeypatch.setattr(video, 'VideoSession', tracked)
    monkeypatch.setattr(video, 'UPLOAD_IDLE_TIMEOUT', .01)
    router = video.create_video_router(lambda: SimpleNamespace(version='fixture'))
    upload = next(r.endpoint for r in router.routes if r.path == '/api/video-analysis')
    async def run():
        async with router.lifespan_context(FastAPI()):
            for kind in ['disconnect', 'slow', 'disconnect']:
                calls = 0
                async def receive():
                    nonlocal calls
                    calls += 1
                    if calls == 1:
                        return {'type':'http.request', 'body':b'partial', 'more_body':True}
                    if kind == 'slow':
                        await asyncio.sleep(1)
                    return {'type':'http.disconnect'}
                request = Request({'type':'http', 'method':'POST', 'headers':[]}, receive)
                with pytest.raises((ClientDisconnect, video.HTTPException)) as exc:
                    await upload(request, filename='x.avi', mode='balanced', sample=0, actor='fixture')
                if kind == 'slow': assert exc.value.status_code == 408
                assert not paths[-1].parent.exists()
    asyncio.run(run())


def test_concurrent_uploads_respect_two_slot_limit_and_release_on_cancel(monkeypatch):
    import asyncio
    from starlette.requests import Request
    paths = []
    original = video.VideoSession
    def tracked(*args):
        session = original(*args); paths.append(session.path); return session
    monkeypatch.setattr(video, 'VideoSession', tracked)
    router = video.create_video_router(lambda: SimpleNamespace(version='fixture'))
    upload = next(r.endpoint for r in router.routes if r.path == '/api/video-analysis')
    async def run():
        async with router.lifespan_context(FastAPI()):
            entered = asyncio.Queue()
            async def receive():
                entered.put_nowait(True)
                await asyncio.Event().wait()
            def request(): return Request({'type':'http','method':'POST','headers':[]},receive)
            tasks = [asyncio.create_task(upload(request(),filename='x.avi',mode='balanced',sample=0,actor='fixture')) for _ in range(2)]
            await asyncio.wait_for(entered.get(),1); await asyncio.wait_for(entered.get(),1)
            try:
                with pytest.raises(video.HTTPException) as exc:
                    await upload(request(),filename='x.avi',mode='balanced',sample=0,actor='fixture')
                assert exc.value.status_code == 429
            finally:
                for task in tasks: task.cancel()
                await asyncio.gather(*tasks,return_exceptions=True)
            assert all(not path.parent.exists() for path in paths)
    asyncio.run(run())
