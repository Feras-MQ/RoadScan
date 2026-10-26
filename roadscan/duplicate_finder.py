"""Damage-crop DINOv2 + exact FAISS search inside a GPS radius; advisory only."""
from pathlib import Path
import hashlib,json,math,os,threading
from .feature_embeddings import OfflineEmbedder

OPEN_STATUSES={'New','Needs Review','Confirmed','Assigned'}
PREPROCESS='dinov2-vits14-crop-resize518-imagenet-v1'

def distance_m(left,right):
    for point in (left,right):
        if len(point)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in point):raise ValueError('Both reports need GPS coordinates')
        if not -90<=point[0]<=90 or not -180<=point[1]<=180:raise ValueError('GPS coordinates out of range')
    lat1,lon1,lat2,lon2=map(math.radians,(*left,*right))
    h=math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 6371000*2*math.asin(math.sqrt(min(1,max(0,h))))

class DuplicateFinder:
    def __init__(self,checkpoint,cache_dir,embedder=None):
        path=Path(checkpoint)
        self.fingerprint=hashlib.sha256(path.read_bytes()).hexdigest()
        self.cache=Path(cache_dir);self.cache.mkdir(parents=True,exist_ok=True)
        self.embedder=embedder or OfflineEmbedder('dinov2_vits14',path)
        self.lock=threading.Lock()

    def features(self,report):
        boxes=[d['box'] for d in report['detections']]
        if not boxes:raise ValueError('Save at least one damage box before comparing crops')
        if len(boxes)>20:raise ValueError('Duplicate search supports at most 20 damage boxes per report')
        path=Path(report['image']);image_hash=hashlib.sha256(path.read_bytes()).hexdigest()
        vectors=[]
        for box in boxes:
            key=hashlib.sha256(json.dumps([self.fingerprint,PREPROCESS,image_hash,box],allow_nan=False).encode()).hexdigest()
            cache=self.cache/(key+'.json');vector=None
            try:
                candidate=json.loads(cache.read_text())
                if isinstance(candidate,list) and len(candidate)==384 and all(type(v) in (int,float) and math.isfinite(v) for v in candidate) and sum(v*v for v in candidate)>0:vector=candidate
            except (OSError,ValueError):pass
            if vector is None:
                vector=self.embedder.encode(path,box)
                if len(vector)!=384 or not all(math.isfinite(v) for v in vector) or sum(v*v for v in vector)<=0:raise ValueError('Invalid DINOv2 embedding')
                temporary=cache.with_suffix('.tmp')
                temporary.write_text(json.dumps(vector,allow_nan=False));temporary.replace(cache)
            vectors.append(vector)
        return vectors

    def search(self,query,reports,radius=50,threshold=.80):
        if not math.isfinite(radius) or not 1<=radius<=500:raise ValueError('Radius must be 1–500 metres')
        if not math.isfinite(threshold) or not -1<=threshold<=1:raise ValueError('Invalid similarity threshold')
        if not self.lock.acquire(blocking=False):raise RuntimeError('Another duplicate search is running; try again shortly')
        try:
            distance_m(query['gps'],query['gps'])
            if not query['detections']:raise ValueError('Save at least one damage box before comparing crops')
            candidates=[]
            for row in reports:
                if row['id']==query['id'] or row['status'] not in OPEN_STATUSES or not row['detections']:continue
                if row.get('location_source')!=query.get('location_source'):continue
                if any(v is None for v in row['gps']):continue
                distance=distance_m(query['gps'],row['gps'])
                if distance<=radius:candidates.append((row,distance))
            if len(candidates)>100:raise ValueError('More than 100 nearby reports; narrow the search radius')
            result={'method':'dinov2_vits14_faiss_gps','preprocessing':PREPROCESS,'radius_m':radius,'threshold':threshold,'threshold_validated':False,'candidate_reports':len(candidates),'matches':[],'note':'Experimental threshold; inspect the images. No automatic merge. Simulated and real location sources are kept separate.'}
            if not candidates:return result
            import numpy as np
            import faiss
            vectors=[];owners=[]
            for row,distance in candidates:
                for vector in self.features(row):vectors.append(vector);owners.append((row['id'],distance))
            gallery=np.asarray(vectors,dtype='float32');queries=np.asarray(self.features(query),dtype='float32')
            if not np.isfinite(gallery).all() or not np.isfinite(queries).all():raise ValueError('Embedding exceeds numeric range')
            faiss.normalize_L2(gallery);faiss.normalize_L2(queries)
            index=faiss.IndexFlatIP(gallery.shape[1]);index.add(gallery)
            scores,indices=index.search(queries,len(owners));best={}
            for row_scores,row_indices in zip(scores,indices):
                for similarity,position in zip(row_scores,row_indices):
                    if not 0<=int(position)<len(owners) or not math.isfinite(float(similarity)):continue
                    ident,distance=owners[int(position)];similarity=float(max(-1,min(1,similarity)))
                    if similarity>=threshold and similarity>best.get(ident,{}).get('similarity',-2):best[ident]={'report_id':ident,'similarity':similarity,'distance_m':round(distance,1)}
            result['matches']=sorted(best.values(),key=lambda x:(-x['similarity'],x['report_id']))[:5]
            return result
        finally:self.lock.release()

_instance=None
_lock=threading.Lock()
def configured_finder():
    global _instance
    with _lock:
        if _instance is None:
            path=Path(os.getenv('ROADSCAN_DINO_WEIGHTS','/opt/roadscan-models/dinov2_vits14_pretrain.pth'))
            if not path.is_file():raise RuntimeError('DINOv2 is not installed; use the detector-enabled build')
            _instance=DuplicateFinder(path,Path(os.getenv('ROADSCAN_STORAGE','./private_uploads')).parent/'embedding_cache')
        return _instance
