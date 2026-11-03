"""Damage-crop DINOv2 + exact cosine search, nearby (GPS radius) or visual-only (any location); advisory only."""
from pathlib import Path
import hashlib,json,math,os,threading,time
from .feature_embeddings import OfflineEmbedder

OPEN_STATUSES={'New','Needs Review','Confirmed','Assigned'}
PREPROCESS='dinov2-vits14-crop-resize518-imagenet-v1'
MAX_REPORTS=100  # with at most 20 boxes each, this also caps gallery crops at 2000 (about 6 MB of float64 vectors)
LIMITED='Limited search: no match does not rule out similar reports. Repeat the search to continue; finished crops are cached.'

def search_limits():
    """(new-crop budget, seconds) from ROADSCAN_SIMILARITY_NEW_CROPS / ROADSCAN_SIMILARITY_SECONDS."""
    try:new_crops=int(os.getenv('ROADSCAN_SIMILARITY_NEW_CROPS','16'));seconds=float(os.getenv('ROADSCAN_SIMILARITY_SECONDS','20'))
    except ValueError as exc:raise RuntimeError('Invalid similarity search limits') from exc
    if not 1<=new_crops<=500 or not math.isfinite(seconds) or not 1<=seconds<=300:raise RuntimeError('Invalid similarity search limits')
    return new_crops,seconds

class BudgetExhausted(Exception):pass

class Budget:
    """Checked before each uncached embedding. An embedding already running is not interrupted, so a search can overrun `seconds` by about one crop."""
    def __init__(self,new_crops,seconds,clock):
        self.limit,self.seconds,self.clock=new_crops,seconds,clock;self.start=clock();self.used=0;self.reason=None
    def spend(self):
        if self.used>=self.limit:self.reason='new_crop_budget'
        elif self.clock()-self.start>=self.seconds:self.reason='time_budget'
        if self.reason:raise BudgetExhausted
        self.used+=1

def comparable_sources(left,right):
    """Manual and device GPS are both recorded locations; simulated only matches simulated; anything else matches nothing."""
    recorded={'manual','device_gps'}
    return (left in recorded and right in recorded) or left==right=='simulated'

def crop_boxes(report):
    """The report's 1–20 damage boxes, each a finite rectangle inside its image; ValueError says why it cannot be compared."""
    boxes=[d.get('box') for d in report['detections']]
    if not boxes:raise ValueError('Save at least one damage box before comparing crops')
    if len(boxes)>20:raise ValueError('Duplicate search supports at most 20 damage boxes per report')
    from PIL import Image
    with Image.open(report['image']) as image:width,height=image.size
    for box in boxes:
        if not isinstance(box,list) or len(box)!=4 or any(type(v) not in (int,float) or not math.isfinite(v) for v in box):raise ValueError('Damage boxes must be four finite numbers')
        if not (0<=box[0]<box[2]<=width and 0<=box[1]<box[3]<=height):raise ValueError('A damage box lies outside its image')
    return boxes

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
        self.lock=threading.Lock();self.clock=time.monotonic

    def features(self,report,budget=None):
        boxes=crop_boxes(report)
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
                if budget:budget.spend()
                vector=self.embedder.encode(path,box)
                if len(vector)!=384 or not all(math.isfinite(v) for v in vector) or sum(v*v for v in vector)<=0:raise ValueError('Invalid DINOv2 embedding')
                temporary=cache.with_suffix('.tmp')
                temporary.write_text(json.dumps(vector,allow_nan=False));temporary.replace(cache)
            vectors.append(vector)
        return vectors

    def search(self,query,reports,radius=50,threshold=.80,mode='nearby',new_crops=None,seconds=None):
        """nearby: same location source within `radius`. visual: any open report; location is ignored and never required.
        Candidates are examined in a fixed order (distance, then id) until the new-crop or time budget runs out; the result says whether it was partial."""
        if mode not in ('nearby','visual'):raise ValueError('Unknown search mode')
        if not math.isfinite(radius) or not 1<=radius<=500:raise ValueError('Radius must be 1–500 metres')
        if not math.isfinite(threshold) or not -1<=threshold<=1:raise ValueError('Invalid similarity threshold')
        if new_crops is None or seconds is None:new_crops,seconds=search_limits()
        if not self.lock.acquire(blocking=False):raise RuntimeError('Another duplicate search is running; try again shortly')
        try:
            budget=Budget(new_crops,seconds,self.clock)
            if mode=='nearby':distance_m(query['gps'],query['gps'])
            crop_boxes(query)
            candidates=[];skipped=0
            for row in reports:
                if row['id']==query['id'] or row['status'] not in OPEN_STATUSES or not row['detections']:continue
                try:crop_boxes(row)
                except (ValueError,OSError):skipped+=1;continue  # one bad stored box must not block every search
                comparable=comparable_sources(row.get('location_source'),query.get('location_source'))
                try:distance=distance_m(query['gps'],row['gps']) if comparable else None
                except ValueError:distance=None
                if mode=='visual':candidates.append((row,distance))
                elif distance is not None and distance<=radius:candidates.append((row,distance))
            candidates.sort(key=lambda c:(c[1] is None,c[1] or 0,c[0]['id']))
            if mode=='nearby':
                result={'mode':mode,'method':'dinov2_vits14_exact_cosine_gps','radius_m':radius,'note':'Experimental threshold; inspect the images. No automatic merge. Simulated and real location sources are kept separate.'}
            else:
                result={'mode':mode,'method':'dinov2_vits14_exact_cosine','radius_m':None,'note':'Crop-level visual similarity of saved damage boxes only: not whole-image matching and not confirmation of the same physical damage. Location is not used. Experimental threshold; inspect the images. No automatic merge.'}
            reasons=['report_cap'] if len(candidates)>MAX_REPORTS else []
            vectors=[];owners=[];examined=0
            if candidates:
                try:
                    queries=self.features(query,budget)
                    for row,distance in candidates[:MAX_REPORTS]:
                        for vector in self.features(row,budget):vectors.append(vector);owners.append((row['id'],distance))
                        examined+=1
                except BudgetExhausted:reasons.append(budget.reason)
            result.update(preprocessing=PREPROCESS,threshold=threshold,threshold_validated=False,eligible_reports=len(candidates),examined_reports=examined,
                          candidate_reports=examined,skipped_reports=skipped,new_crops_used=budget.used,new_crop_budget=new_crops,time_budget_s=seconds,
                          partial_search=bool(reasons),partial_reasons=reasons,matches=[])
            if reasons:result['note']+=' '+LIMITED
            if owners:
                import numpy as np
                gallery=np.asarray(vectors,dtype='float64');queries=np.asarray(queries,dtype='float64')
                if not np.isfinite(gallery).all() or not np.isfinite(queries).all():raise ValueError('Embedding exceeds numeric range')
                # Exact cosine over every examined crop (what a flat inner-product index computes).
                norms=[np.linalg.norm(m,axis=1,keepdims=True) for m in (gallery,queries)]
                if not all(np.isfinite(n).all() and (n>0).all() for n in norms):raise ValueError('Embedding exceeds numeric range')
                gallery/=norms[0];queries/=norms[1]
                best={}
                for row_scores in queries@gallery.T:
                    for (ident,distance),similarity in zip(owners,row_scores):
                        similarity=float(max(-1,min(1,similarity)))
                        if similarity>=threshold and similarity>best.get(ident,{}).get('similarity',-2):best[ident]={'report_id':ident,'similarity':similarity,'distance_m':None if distance is None else round(distance,1)}
                result['matches']=sorted(best.values(),key=lambda x:(-x['similarity'],x['report_id']))[:5]
            result['elapsed_s']=round(self.clock()-budget.start,3)
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
