"""Bounded local video sessions: every decoded frame, at inference speed.

Video metadata is advisory. EOF with a discrepant advertised frame count is
reported as incomplete, never silently called successful full coverage.
"""
import base64
import io
import math
from pathlib import Path
import tempfile
import threading
import time
import uuid
from contextlib import asynccontextmanager
import importlib
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from PIL import Image
from starlette.concurrency import run_in_threadpool
from .access import review_access

MAX_UPLOAD = 200 * 1024 * 1024
MAX_FRAMES = 50_000
MAX_SESSIONS = 2
SESSION_TTL = 15 * 60
MAX_PIXELS = 25_000_000


class VideoSession:
    def __init__(self, owner, mode, version):
        self.id = uuid.uuid4().hex
        self.owner, self.mode, self.version = owner, mode, version
        self.lock = threading.Lock()
        self.touched = time.monotonic()
        self.directory = tempfile.TemporaryDirectory(prefix='roadscan-video-')
        self.path = Path(self.directory.name) / 'upload.video'
        self.capture = None
        self.pending = None
        self.processed = 0
        self.total = None
        self.fps = None
        self.terminal = None
        self.cancelled = threading.Event()

    def close(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        if self.pending is not None:
            self.pending.close()
            self.pending = None
        self.directory.cleanup()

    def finish(self, complete, reason):
        self.terminal = dict(state='finished', complete=complete, reason=reason,
                             processed_count=self.processed, total_frames=self.total,
                             persisted=False)
        self.close()
        return self.terminal


def _container_allowed(header):
    # Reject playlist/text inputs; only local media containers are passed to FFmpeg.
    return (len(header) >= 12 and header[4:8] == b'ftyp') or (
        header[:4] == b'RIFF' and header[8:12] == b'AVI ') or header[:4] == b'\x1aE\xdf\xa3'


def _cv2():
    try:
        return importlib.import_module("cv2")
    except ImportError as exc:
        raise HTTPException(503, "Video analysis requires the detector-enabled build") from exc


def _open(session):
    cv2 = _cv2()
    with session.path.open('rb') as stream:
        if not _container_allowed(stream.read(32)):
            raise HTTPException(415, 'Choose an MP4, MOV, AVI, MKV or WebM video')
    session.capture = cv2.VideoCapture(str(session.path), cv2.CAP_FFMPEG)
    cap = session.capture
    if not cap.isOpened():
        raise HTTPException(415, 'Video codec could not be decoded locally')
    width, height = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    if not all(math.isfinite(v) and v > 0 for v in (width, height)) or width * height > MAX_PIXELS:
        raise HTTPException(413, 'Video dimensions exceed the 25 megapixel limit')
    total, fps = cap.get(cv2.CAP_PROP_FRAME_COUNT), cap.get(cv2.CAP_PROP_FPS)
    session.total = int(total) if math.isfinite(total) and total > 0 else None
    session.fps = fps if math.isfinite(fps) and fps > 0 else None
    if session.total and session.total > MAX_FRAMES:
        raise HTTPException(413, 'Video exceeds the 50,000 frame limit; split it into shorter clips')


def _next(session, detector):
    cv2 = _cv2()
    if session.terminal is not None:
        return session.terminal
    if detector.version != session.version:
        return session.finish(False, 'model_changed')
    if session.pending is None:
        ok, frame = session.capture.read()
        if not ok:
            complete = session.processed > 0 and (session.total is not None and session.processed == session.total)
            reason = 'decoder_eof' if complete else ('decoder_end_coverage_unverified' if session.total is None else 'metadata_mismatch_coverage_unverified')
            return session.finish(complete, reason)
        if session.processed >= MAX_FRAMES:
            return session.finish(False, 'frame_limit_reached')
        if frame.ndim != 3 or frame.shape[0] * frame.shape[1] > MAX_PIXELS:
            return session.finish(False, 'invalid_frame_dimensions')
        height, width = frame.shape[:2]
        factor = min(1., 960 / max(width, height))
        if factor < 1:
            frame = cv2.resize(frame, (max(1, round(width * factor)), max(1, round(height * factor))), interpolation=cv2.INTER_AREA)
        session.pending = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        stamp = session.capture.get(cv2.CAP_PROP_POS_MSEC)
        session.timestamp = stamp if math.isfinite(stamp) and stamp >= 0 else None
    started = time.perf_counter()
    prediction = detector.predict(session.pending, wait=False, live_mode=session.mode)
    # A switch can occur between the pre-check and acquiring the runtime lock.
    if prediction.get('state') != 'busy' and prediction.get('model_version') != session.version:
        return session.finish(False, 'model_changed')
    if prediction.get('state') != 'completed':
        return {**prediction, 'processed_count': session.processed, 'total_frames': session.total,
                'persisted': False, 'frame_index': session.processed}
    image = session.pending
    output = io.BytesIO()
    image.save(output, 'JPEG', quality=88)
    result = {**prediction, 'jpeg_base64': base64.b64encode(output.getvalue()).decode('ascii'),
              'width': image.width, 'height': image.height, 'frame_index': session.processed,
              'timestamp_ms': session.timestamp, 'total_frames': session.total,
              'processed_count': session.processed + 1, 'persisted': False,
              'elapsed_ms': round((time.perf_counter() - started) * 1000, 2)}
    session.processed += 1
    session.pending.close()
    session.pending = None
    return result


def create_video_router(detector_getter):
    sessions = {}
    lock = threading.Lock()
    stop = threading.Event()
    janitor = None

    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            stop.set()
            with lock:
                remaining = list(sessions.values())
                sessions.clear()
            for session in remaining:
                session.cancelled.set()
                def release(item=session):
                    with item.lock:
                        item.close()
                await run_in_threadpool(release)

    router = APIRouter(prefix='/api/video-analysis', lifespan=lifespan)

    def purge():
        with lock:
            for ident, session in list(sessions.items()):
                if time.monotonic() - session.touched > SESSION_TTL and session.lock.acquire(False):
                    try:
                        session.close()
                        sessions.pop(ident, None)
                    finally:
                        session.lock.release()

    def reap():
        while not stop.wait(30):
            purge()

    def lookup(ident, actor):
        purge()
        with lock:
            session = sessions.get(ident)
            if session is None or session.owner != actor:
                raise HTTPException(404, 'Video session expired or not found')
            if not session.lock.acquire(False):
                raise HTTPException(409, 'Video session has a request in progress')
            session.touched = time.monotonic()
            return session

    @router.post('')
    async def upload(request: Request, filename: str = Query(..., min_length=1, max_length=200),
                     mode: str = Query('balanced', pattern='^(balanced|detail)$'), actor: str = Depends(review_access)):
        nonlocal janitor
        if Path(filename).suffix.lower() not in {'.mp4', '.mov', '.avi', '.webm', '.mkv'}:
            raise HTTPException(415, 'Choose an MP4, MOV, AVI, MKV or WebM video')
        _cv2()
        purge()
        with lock:
            if len(sessions) >= MAX_SESSIONS:
                raise HTTPException(429, 'Two video sessions are already open; stop one first')
            session = VideoSession(actor, mode, detector_getter().version)
            session.lock.acquire()
            sessions[session.id] = session
            if janitor is None:
                janitor = threading.Thread(target=reap, daemon=True)
                janitor.start()
        try:
            size = 0
            with session.path.open('wb') as output:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > MAX_UPLOAD:
                        raise HTTPException(413, 'Video exceeds the 200 MiB upload limit')
                    output.write(chunk)
            await run_in_threadpool(_open, session)
            return dict(id=session.id, state='ready', total_frames=session.total, fps=session.fps)
        except BaseException:
            session.close()
            with lock:
                sessions.pop(session.id, None)
            raise
        finally:
            session.touched = time.monotonic()
            session.lock.release()

    @router.post('/{ident}/next')
    def next_frame(ident: str, actor: str = Depends(review_access)):
        session = lookup(ident, actor)
        try:
            try:
                result = _next(session, detector_getter())
                return {'state': 'cancelled'} if session.cancelled.is_set() else result
            except Exception:
                return session.finish(False, 'decode_or_inference_failed')
        finally:
            session.touched = time.monotonic()
            if session.cancelled.is_set():
                session.close()
                with lock:
                    sessions.pop(ident, None)
            session.lock.release()

    @router.delete('/{ident}')
    def cancel(ident: str, actor: str = Depends(review_access)):
        with lock:
            session = sessions.get(ident)
            if session is None or session.owner != actor:
                raise HTTPException(404, 'Video session expired or not found')
            session.cancelled.set()
            acquired = session.lock.acquire(False)
            if acquired:
                sessions.pop(ident, None)
        if acquired:
            try:
                session.close()
            finally:
                session.lock.release()
        # In-flight inference cannot be interrupted safely. Its finally block
        # releases this session immediately on return; it cannot decode again.
        return {'state': 'cancelled'}

    return router
