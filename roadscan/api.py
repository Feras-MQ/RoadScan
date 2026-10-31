import os, json, uuid, hashlib, math
import time
import tempfile
import shutil
import importlib.util
import zipfile
import threading
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Header, Query, Request
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .core import *
from .inference import LocalDetector
from .review import validate_detections
from .workflow import validate_transition
from functools import lru_cache
from sqlalchemy import or_, func, update as sql_update
from starlette.concurrency import run_in_threadpool
from .imaging import decode_image, pillow_open
from .model_library import ModelLibrary, ModelRuntime, MAX_IMPORT
from .training_data import TrainingApproval, current_approval, approve, training_summary, export_dataset

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield
app=FastAPI(title='RoadScan local MVP',version='0.1.0',lifespan=lifespan)
from .security import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)
ROOT=Path(__file__).resolve().parent.parent
app.mount('/static',StaticFiles(directory=str(ROOT/'static')),name='static')

from .access import read_access, review_access, admin_access, identity

def db():
    s=Session()
    try: yield s
    finally:s.close()

@app.get('/')
def home():
    ui = ROOT / 'frontend' / 'dist' / 'index.html'
    return FileResponse(ui if ui.exists() else ROOT/'static'/'index.html')

@app.get('/assets/{asset_name}')
def react_asset(asset_name: str):
    # No arbitrary path traversal; only files inside Vite's asset directory.
    if '/' in asset_name or '\\' in asset_name or asset_name.startswith('.'):
        raise HTTPException(404,'Not found')
    path=ROOT/'frontend'/'dist'/'assets'/asset_name
    if not path.is_file():raise HTTPException(404,'Not found')
    return FileResponse(path)

@app.get('/manifest.webmanifest')
def manifest():return FileResponse(ROOT/'static'/'manifest.webmanifest')
_instance_lock=threading.RLock()

@lru_cache(maxsize=1)
def _library_instance():
    return ModelLibrary(os.getenv('ROADSCAN_MODEL_LIBRARY', str(STORAGE.resolve().parent/'model_library')))

@lru_cache(maxsize=1)
def _detector_instance(): return ModelRuntime(model_library())

def model_library():
    with _instance_lock:return _library_instance()

def detector():
    # lru_cache alone can construct duplicate instances on simultaneous first requests.
    with _instance_lock:return _detector_instance()

@app.get('/api/health')
def health():
    current=detector()
    demo=(os.getenv('ROADSCAN_DEMO_MODE')=='1' and os.getenv('ROADSCAN_API_KEY')=='roadscan-live-qa-local-only' and not os.getenv('ROADSCAN_ACCOUNTS_FILE'))
    return {'status':'ok','model':'configured' if current.model is not None else 'not_configured',
            'model_reason':current.error,'model_version':getattr(current,'version','not_configured'),
            'active_model_id':getattr(current,'active_id',None),'model_warning':getattr(current,'warning',None),
            'duplicate_method':'dhash_unvalidated','mode':'local','demo':demo,
            'demo_token':'roadscan-live-qa-local-only' if demo else None,
            'max_upload_mb':int(os.getenv('ROADSCAN_MAX_UPLOAD_MB','50')), 'max_image_pixels':25_000_000}

async def read_bounded(request,limit):
    raw=bytearray()
    async for block in request.stream():
        if len(raw)+len(block)>limit:raise HTTPException(413,'Preview frames must be under 2 MB')
        raw.extend(block)
    return bytes(raw)

def model_support_available():
    return importlib.util.find_spec('ultralytics') is not None

@app.get('/api/models')
def models(actor:str=Depends(read_access),who:dict=Depends(identity)):
    current=detector()
    try: items=model_library().list()
    except (OSError,ValueError): raise HTTPException(503,'Model library could not be read; existing files are preserved')
    return {'items':items,'active_id':getattr(current,'active_id','baseline'),
            'model_version':getattr(current,'version','not_configured'),
            'can_manage':who['role']=='admin','available':model_support_available(),
            'warning':getattr(current,'warning',None)}

@app.post('/api/models/import')
async def import_models(request:Request,filename:str=Query(...,min_length=1,max_length=200),actor:str=Depends(admin_access)):
    if not model_support_available():raise HTTPException(503,'This workspace needs the detector-enabled RoadScan build')
    if '/' in filename or '\\' in filename or not filename.lower().endswith(('.pt','.zip')):
        raise HTTPException(422,'Choose a trusted .pt checkpoint or .zip package')
    library=model_library(); library.root.mkdir(parents=True,exist_ok=True)
    temp_path=None
    try:
        with tempfile.NamedTemporaryFile(prefix='.upload-',suffix=Path(filename).suffix,dir=library.root,delete=False) as output:
            temp_path=Path(output.name); size=0
            async for block in request.stream():
                size+=len(block)
                if size>MAX_IMPORT:raise HTTPException(413,'Model package exceeds the 1600 MB limit')
                if shutil.disk_usage(library.root).free < len(block)+64*1024*1024:
                    raise HTTPException(507,'Not enough free space to import models')
                output.write(block)
        result=await run_in_threadpool(library.import_file,temp_path,filename)
        return result
    except (ValueError,zipfile.BadZipFile) as exc:
        raise HTTPException(422,str(exc)) from exc
    except OSError as exc:
        raise HTTPException(507,'Model files could not be stored; existing models are preserved') from exc
    finally:
        if temp_path:temp_path.unlink(missing_ok=True)

@app.post('/api/models/{ident}/activate')
async def activate_model(ident:str,actor:str=Depends(admin_access)):
    try:return await run_in_threadpool(detector().activate,ident)
    except ValueError as exc:raise HTTPException(409,str(exc)) from exc

@app.post('/api/recognize')
async def recognize(request:Request, mode:str=Query('balanced',pattern='^(balanced|detail)$'), actor:str=Depends(review_access)):
    """Temporary live-frame recognition: no reports, files or audit rows are created."""
    raw=await read_bounded(request,2*1024*1024)
    image=decode_image(raw,max_pixels=2_000_000)
    started=time.perf_counter()
    try:
        prediction=await run_in_threadpool(lambda: detector().predict(image,wait=False,live_mode=mode))
        return {**prediction,'width':image.width,'height':image.height,
                'elapsed_ms':round((time.perf_counter()-started)*1000,2),
                'confidence_threshold':prediction.get('confidence_threshold',getattr(detector(),'confidence',None)),
                'persisted':False}
    finally:
        image.close()

@app.post('/api/reports',status_code=201)
async def upload(photo:UploadFile=File(...),latitude:float|None=Form(None),longitude:float|None=Form(None),location_source:str=Form('not_provided'),actor:str=Depends(review_access),session=Depends(db)):
    if latitude is not None and (not math.isfinite(latitude) or not -90<=latitude<=90):raise HTTPException(422,'Invalid latitude')
    if longitude is not None and (not math.isfinite(longitude) or not -180<=longitude<=180):raise HTTPException(422,'Invalid longitude')
    if (latitude is None)!=(longitude is None):raise HTTPException(422,'Provide both coordinates')
    if location_source not in {'not_provided','manual','simulated','device_gps'}:raise HTTPException(422,'Invalid location source')
    if latitude is not None and location_source=='not_provided':raise HTTPException(422,'Choose a location source when providing coordinates')
    if latitude is None:location_source='not_provided'
    limit=int(os.getenv('ROADSCAN_MAX_UPLOAD_MB','50'))*1024*1024
    raw=await photo.read(limit+1)
    if len(raw)>limit:raise HTTPException(413,'Image exceeds the configured upload limit')
    im=decode_image(raw)
    rid=str(uuid.uuid4()); ref=rid+'.jpg'; path=STORAGE/ref
    # Re-encoding strips EXIF including GPS; uploaded originals are not retained.
    im.save(path,'JPEG',quality=88)
    prediction=await run_in_threadpool(detector().predict,im)
    value,parts=score(prediction['detections'],im.width,im.height) if prediction['state']=='completed' else (None,{})
    r=Report(id=rid,image_ref=ref,image_sha=hashlib.sha256(path.read_bytes()).hexdigest(),image_phash=phash(im),latitude=latitude,longitude=longitude,location_source=location_source,status='Needs Review',inference_state=prediction['state'],model_version=prediction['model_version'],detections=json.dumps(prediction['detections']),score=value,score_parts=json.dumps(parts))
    # Preserve the initial prediction separately from human annotation edits.
    r.source_metadata=json.dumps({'initial_prediction':prediction})
    session.add(r);session.flush();r.duplicates=json.dumps(similar(session,r.image_phash,rid));session.add(Audit(report_id=rid,actor=actor,action='upload',details=json.dumps({'inference_state':prediction['state'],'reason':prediction['reason']})));session.add(History(report_id=rid,to_status='Needs Review',actor=actor));session.commit();im.close();return serialize(r)

class VoteRequest(BaseModel):
    model_ids:list[str]=Field(min_length=2,max_length=3)
    revision:str=Field(min_length=64,max_length=64)

@app.post('/api/reports/{rid}/vote')
async def vote_report(rid:str, choice:VoteRequest, actor:str=Depends(review_access), session=Depends(db)):
    report=session.get(Report,rid)
    if not report:raise HTTPException(404,'Not found')
    revision=annotation_revision(report)
    if choice.revision!=revision:raise HTTPException(409,'Report changed. Reload before requesting a second opinion')
    path=STORAGE/Path(report.image_ref).name
    try:
        result=await run_in_threadpool(detector().compare,choice.model_ids,path)
    except (ValueError, OSError) as exc:
        detail = str(exc) if isinstance(exc, ValueError) else 'Report image file is missing or unreadable'
        raise HTTPException(409,detail) from exc
    return {**result,'report_id':rid,'revision':revision}

class TrainingChoice(BaseModel):
    revision:str=Field(min_length=64,max_length=64)
    split:str=Field(pattern='^(train|val|test)$')
    capture_group:str=Field(min_length=1,max_length=80)
    rights_confirmed:bool=False
    negative_confirmed:bool=False

@app.get('/api/reports/{rid}/training')
def training_status(rid:str,actor:str=Depends(read_access),session=Depends(db)):
    report=session.get(Report,rid)
    if not report:raise HTTPException(404,'Not found')
    return current_approval(session,report)

@app.put('/api/reports/{rid}/training')
def approve_training(rid:str,choice:TrainingChoice,actor:str=Depends(review_access),session=Depends(db)):
    report=session.get(Report,rid)
    if not report:raise HTTPException(404,'Not found')
    try:return approve(session,report,**choice.model_dump(),actor=actor)
    except ValueError as exc:raise HTTPException(409,str(exc)) from exc

@app.delete('/api/reports/{rid}/training',status_code=204)
def revoke_training(rid:str,actor:str=Depends(review_access),session=Depends(db)):
    if not session.get(Report,rid):raise HTTPException(404,'Not found')
    item=session.get(TrainingApproval,rid)
    if item:
        session.delete(item);session.add(Audit(report_id=rid,actor=actor,action='revoke_training',details='{"weights_changed":false}'));session.commit()

@app.get('/api/training')
def training_overview(actor:str=Depends(read_access),who:dict=Depends(identity),session=Depends(db)):
    return {**training_summary(session),'can_export':who['role']=='admin'}

@app.get('/api/training/export')
def training_export(actor:str=Depends(admin_access),session=Depends(db)):
    try:path,manifest=export_dataset(session,STORAGE)
    except (ValueError,OSError) as exc:
        detail=str(exc) if isinstance(exc,ValueError) else 'Could not read the approved dataset'
        raise HTTPException(409,detail) from exc
    return FileResponse(path,media_type='application/zip',filename='RoadScan-Reviewed-Dataset.zip',
                        headers={'Cache-Control':'no-store'},background=BackgroundTask(path.unlink,missing_ok=True))

@app.get('/api/reports')
def reports(status:str|None=None,search:str=Query('',max_length=200),page:int=Query(1,ge=1),size:int=Query(20,ge=1,le=100),actor:str=Depends(read_access),session=Depends(db)):
    q=session.query(Report)
    if status:
        if status not in STATUSES:raise HTTPException(422,'Invalid status')
        q=q.filter(Report.status==status)
    if search.strip():
        term=search.strip()
        q=q.filter(or_(Report.id.contains(term,autoescape=True), Report.note.contains(term,autoescape=True)))
    total=q.count();items=q.order_by(Report.created_at.desc()).offset((page-1)*size).limit(size).all()
    return {'items':[serialize(r) for r in items],'page':page,'size':size,'total':total}

@app.get('/api/stats')
def stats(actor:str=Depends(read_access),session=Depends(db)):
    counts=dict(session.query(Report.status,func.count(Report.id)).group_by(Report.status).all())
    return {'total':sum(counts.values()),'needs_review':counts.get('Needs Review',0),
            'high_priority':session.query(Report).filter(Report.score>=65).count(),
            'by_status':counts}
@app.get('/api/reports/{rid}')
def detail(rid:str,actor:str=Depends(read_access),session=Depends(db)):
    r=session.get(Report,rid)
    if not r:raise HTTPException(404,'Not found')
    d=serialize(r);d['history']=[{'from':h.from_status,'to':h.to_status,'actor':h.actor,'at':h.created_at.isoformat()} for h in session.query(History).filter_by(report_id=rid).order_by(History.id).all()]
    return d
@app.get('/api/reports/{rid}/image')
def image(rid:str,actor:str=Depends(read_access),session=Depends(db)):
    r=session.get(Report,rid)
    if not r:raise HTTPException(404,'Not found')
    path=STORAGE/Path(r.image_ref).name
    if not path.is_file():raise HTTPException(404,'Report image file is missing')
    return FileResponse(path,media_type='image/jpeg',headers={'Cache-Control':'no-store'})

def report_image_size(report):
    path=STORAGE/Path(report.image_ref).name
    if not path.is_file():raise HTTPException(404,'Report image file is missing')
    try:
        with pillow_open(path, formats=('JPEG', 'PNG', 'WEBP')) as image:
            return image.size
    except FileNotFoundError as exc:
        raise HTTPException(404,'Report image file is missing') from exc
    except OSError as exc:
        raise HTTPException(409,'Report image file is unreadable') from exc

class Change(BaseModel):
    revision:str=Field(min_length=64,max_length=64)
    status:str|None=None
    reviewer:str|None=None
    note:str=Field(default='',max_length=2000)
    detections:list[dict]|None=None
    action:str='review'
@app.patch('/api/reports/{rid}')
def update(rid:str,change:Change,actor:str=Depends(review_access),session=Depends(db)):
    r=session.get(Report,rid)
    if not r:raise HTTPException(404,'Not found')
    if change.revision!=annotation_revision(r):
        raise HTTPException(409,'Report changed. Reload before saving your review')
    if change.status and change.status not in STATUSES:raise HTTPException(422,'Invalid status')
    validate_transition(r.status, change.status, change.action)
    annotation_audit={}
    values={'status':change.status or r.status,'reviewer':actor,'note':change.note,
            'updated_at':datetime.now(timezone.utc)}
    if change.detections is not None:
        width,height=report_image_size(r)
        try:
            validate_detections(change.detections,width,height)
        except ValueError as exc:
            raise HTTPException(422,str(exc)) from exc
        annotation_audit={'previous_detections':json.loads(r.detections), 'detections':change.detections,
                          'previous_inference_state':r.inference_state, 'previous_model_version':r.model_version}
        value,rparts=score(change.detections,width,height)
        values.update(detections=json.dumps(change.detections),score=value,score_parts=json.dumps(rparts),
                      inference_state='manual_review',model_version='manual')
    old=r.status
    # Match every persisted revision input in the write itself. A second request
    # can commit after the check above; its changes must not be overwritten.
    changed=session.execute(sql_update(Report).where(
        Report.id==rid,Report.image_sha==r.image_sha,Report.detections==r.detections,
        Report.status==r.status,Report.updated_at==r.updated_at
    ).values(**values).execution_options(synchronize_session=False))
    if changed.rowcount!=1:
        session.rollback()
        raise HTTPException(409,'Report changed. Reload before saving your review')
    if old!=values['status']:session.add(History(report_id=rid,from_status=old,to_status=values['status'],actor=actor))
    session.add(Audit(report_id=rid,actor=actor,action=change.action,details=json.dumps({'from':old,'to':values['status'],'manual_detections':change.detections is not None,**annotation_audit})))
    session.commit();return serialize(r)
@app.delete('/api/reports/{rid}',status_code=204)
def delete(rid:str,actor:str=Depends(admin_access),session=Depends(db)):
    r=session.get(Report,rid)
    if not r:raise HTTPException(404,'Not found')
    path=STORAGE/Path(r.image_ref).name
    session.query(TrainingApproval).filter_by(report_id=rid).delete()
    session.query(History).filter_by(report_id=rid).delete();session.query(Audit).filter_by(report_id=rid).delete();session.delete(r);session.commit();path.unlink(missing_ok=True)
@app.get('/api/mock/camera')
def camera(actor:str=Depends(read_access)):return {'adapter':'mock_only','camera_id':'SYNTHETIC-CAMERA-001','frame':'not_collected','authorization':'not_granted'}
@app.get('/api/mock/government/{rid}')
def government(rid:str,actor:str=Depends(read_access),session=Depends(db)):
    r=session.get(Report,rid)
    if not r:raise HTTPException(404,'Not found')
    return {'adapter':'mock_only','sent':False,'payload':{'local_report_id':rid,'status':r.status,'priority':r.score,'location_source':r.location_source}}

@app.get('/api/reports/{rid}/sensitivity')
def sensitivity(rid: str, actor: str = Depends(read_access), session=Depends(db)):
    from .sensitivity import scenarios
    r = session.get(Report, rid)
    if not r:
        raise HTTPException(404, 'Not found')
    width, height = report_image_size(r)
    return {'report_id': rid, 'weights_status': 'draft_not_official',
            'analysis': scenarios(json.loads(r.detections), width, height)}

class DuplicateSearch(BaseModel):
    revision:str=Field(min_length=64,max_length=64)

@app.post('/api/reports/{rid}/duplicates/search')
async def search_duplicates(rid:str,choice:DuplicateSearch,actor:str=Depends(review_access),session=Depends(db)):
    from .duplicate_finder import configured_finder,OPEN_STATUSES
    report=session.get(Report,rid)
    if not report:raise HTTPException(404,'Not found')
    if choice.revision!=annotation_revision(report):raise HTTPException(409,'Report changed; reload before searching')
    def record(row):
        return {'id':row.id,'status':row.status,'gps':(row.latitude,row.longitude),'location_source':row.location_source,'image':str(STORAGE/Path(row.image_ref).name),'detections':json.loads(row.detections)}
    query=record(report)
    candidates=[record(row) for row in session.query(Report).filter(Report.id!=rid,Report.status.in_(OPEN_STATUSES),Report.latitude.isnot(None),Report.longitude.isnot(None)).all()]
    try:
        result=await run_in_threadpool(lambda:configured_finder().search(query,candidates))
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    except (RuntimeError,ImportError,OSError):raise HTTPException(503,'Duplicate search unavailable or busy; check the configured DINOv2 runtime and try again')
    session.expire_all()
    current=session.get(Report,rid)
    if not current or choice.revision!=annotation_revision(current):raise HTTPException(409,'Report changed during search; reload and retry')
    eligible={row.id for row in session.query(Report).filter(Report.status.in_(OPEN_STATUSES)).all()}
    result['matches']=[match for match in result['matches'] if match['report_id'] in eligible]
    return result

@app.get('/api/reports/{rid}/audit')
def audit_log(rid: str, actor: str = Depends(read_access), session=Depends(db)):
    if not session.get(Report, rid):
        raise HTTPException(404, 'Not found')
    events = session.query(Audit).filter_by(report_id=rid).order_by(Audit.id).all()
    return {'items': [{'actor': e.actor, 'action': e.action,
                       'details': json.loads(e.details or '{}'),
                       'at': e.created_at.isoformat()} for e in events]}

# Video decoder sessions are temporary and authenticated; no reports are auto-created.
from .video_analysis import create_video_router
app.include_router(create_video_router(lambda: detector()))
