import os, json, hashlib, uuid, time, io
from datetime import datetime, timezone, timedelta
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import create_engine, Column, String, Float, DateTime, ForeignKey, Text, Integer, Index
from sqlalchemy.orm import declarative_base, sessionmaker

BASE = declarative_base()
CLASSES = {'D00':'Longitudinal crack','D10':'Transverse crack','D20':'Alligator crack','D40':'Pothole','OTHER':'Other surface damage'}
TYPE = {'D00':.55,'D10':.45,'D20':.85,'D40':1.0,'OTHER':.55}
WEIGHTS = {'type':.40,'area':.25,'count':.20,'confidence':.15}
STATUSES = {'New','Needs Review','Confirmed','Assigned','Resolved','Duplicate'}
DB_URL = os.getenv('DATABASE_URL','sqlite:///./roadscan.db')
engine = create_engine(DB_URL, connect_args={'check_same_thread':False} if DB_URL.startswith('sqlite') else {}, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
STORAGE = Path(os.getenv('ROADSCAN_STORAGE','./private_uploads'))

class Report(BASE):
    __tablename__='reports'
    id=Column(String,primary_key=True)
    image_ref=Column(String,nullable=False)
    image_sha=Column(String,index=True)
    image_phash=Column(String)
    created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),index=True)
    updated_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    status=Column(String,default='New',index=True)
    reviewer=Column(String)
    source=Column(String,default='upload')
    source_metadata=Column(Text,default='{}')
    latitude=Column(Float)
    longitude=Column(Float)
    location_source=Column(String,default='not_provided')
    model_version=Column(String,default='not_configured')
    inference_state=Column(String,default='not_configured')
    detections=Column(Text,default='[]')
    score=Column(Float)
    score_parts=Column(Text,default='{}')
    duplicates=Column(Text,default='[]')
    note=Column(Text,default='')
Index('ix_reports_status_created','reports.status','reports.created_at')
class Audit(BASE):
    __tablename__='audit_events'
    id=Column(Integer,primary_key=True,autoincrement=True)
    report_id=Column(String,ForeignKey('reports.id'),index=True)
    actor=Column(String)
    action=Column(String)
    details=Column(Text)
    created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class History(BASE):
    __tablename__='status_history'
    id=Column(Integer,primary_key=True,autoincrement=True)
    report_id=Column(String,ForeignKey('reports.id'),index=True)
    from_status=Column(String)
    to_status=Column(String)
    actor=Column(String)
    created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

def init_db():
    STORAGE.mkdir(parents=True,exist_ok=True)
    BASE.metadata.create_all(engine) # local bootstrap; migrations provided separately for PostgreSQL

def score(detections, width, height, weights=None):
    if not detections: return None, {}
    w=weights or WEIGHTS
    area=max(min(((d['box'][2]-d['box'][0])*(d['box'][3]-d['box'][1]))/(width*height),1) for d in detections)
    parts={'type':max(TYPE[d['class_id']] for d in detections),'area':area,'count':min(len(detections)/5,1),'confidence':sum(d['confidence'] for d in detections)/len(detections)}
    return round(100*min(1,max(0,sum(w[k]*parts[k] for k in w))),2),parts

def phash(image):
    # Lightweight 8x8 difference hash; intentionally NOT mislabeled as perceptual DCT pHash.
    gray=ImageOps.grayscale(image).resize((9,8))
    p=list(gray.get_flattened_data() if hasattr(gray,"get_flattened_data") else gray.getdata())
    return ''.join('1' if p[y*9+x]>p[y*9+x+1] else '0' for y in range(8) for x in range(8))

def similar(session, h, current_id, limit=5):
    if not h: return []
    results=[]
    for r in session.query(Report).filter(Report.id!=current_id,Report.status.in_(['New','Needs Review','Confirmed','Assigned'])).all():
        if not r.image_phash: continue
        sim=1-sum(a!=b for a,b in zip(h,r.image_phash))/64
        if sim>=.85: results.append({'report_id':r.id,'similarity':round(sim,4),'method':'dhash','threshold':.85,'threshold_validated':False})
    return sorted(results,key=lambda x:-x['similarity'])[:limit]

def annotation_revision(r):
    data = {'id': r.id, 'image_sha': r.image_sha, 'detections': json.loads(r.detections),
            'status': r.status, 'updated_at': r.updated_at.isoformat() if r.updated_at else None}
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def serialize(r):
    return {'id':r.id,'revision':annotation_revision(r),'created_at':r.created_at.isoformat() if r.created_at else None,'status':r.status,'reviewer':r.reviewer,'image_url':'/api/reports/'+r.id+'/image','source':r.source,'source_metadata':json.loads(r.source_metadata),'latitude':r.latitude,'longitude':r.longitude,'location_source':r.location_source,'model_version':r.model_version,'inference_state':r.inference_state,'detections':json.loads(r.detections),'score':r.score,'score_parts':json.loads(r.score_parts),'duplicates':json.loads(r.duplicates),'note':r.note}
