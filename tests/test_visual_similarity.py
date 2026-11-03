"""Visual-similarity mode: DINOv2 crops compared without requiring coordinates. Embeddings are mocked here."""
import io
import json
import pytest
from PIL import Image
from roadscan import api, duplicate_finder
from roadscan.duplicate_finder import DuplicateFinder
from test_review_api import review_client  # noqa: F401  (fixture)

MATCH, OTHER = [1.]+[0.]*383, [0., 1.]+[0.]*382
REAL_FINDER = duplicate_finder.configured_finder


class Fake:
    """Vector chosen by image colour: grey crops match each other, white crops are orthogonal."""
    def __init__(self):self.calls=0
    def encode(self,path,box):
        self.calls+=1
        with Image.open(path) as im:return OTHER if im.getpixel((0,0))[0]>200 else MATCH


def image(tmp_path,name,colour):
    path=tmp_path/name;Image.new('RGB',(10,10),colour).save(path);return str(path)


def test_visual_mode_ignores_location_and_never_invents_distance(tmp_path):
    (tmp_path/'w').write_bytes(b'test-only');finder=DuplicateFinder(tmp_path/'w',tmp_path/'cache',Fake())
    grey,white=image(tmp_path,'grey.png','gray'),image(tmp_path,'white.png','white')
    box=[{'box':[0,0,8,8]}]
    query={'id':'q','status':'Needs Review','gps':(None,None),'location_source':'not_provided','image':grey,'detections':box}
    gallery=[dict(query,id='same-no-gps'),dict(query,id='same-far',gps=(25,46),location_source='manual'),
             dict(query,id='different',image=white),dict(query,id='closed',status='Resolved'),dict(query,id='no-boxes',detections=[])]
    result=finder.search(query,gallery,mode='visual')
    assert result['mode']=='visual' and result['method']=='dinov2_vits14_exact_cosine' and result['radius_m'] is None
    assert result['threshold']==.8 and result['threshold_validated'] is False and 'not confirmation of the same physical damage' in result['note'] and 'not whole-image' in result['note']
    assert result['candidate_reports']==3
    assert [(m['report_id'],m['distance_m']) for m in result['matches']]==[('same-far',None),('same-no-gps',None)]
    assert all(m['similarity']==pytest.approx(1) for m in result['matches'])
    with pytest.raises(ValueError):finder.search(query,gallery)  # nearby still needs coordinates
    with pytest.raises(ValueError):finder.search(query,gallery,mode='anything')


def test_visual_mode_reports_distance_only_for_comparable_coordinates(tmp_path):
    (tmp_path/'w').write_bytes(b'test-only');finder=DuplicateFinder(tmp_path/'w',tmp_path/'cache',Fake())
    query={'id':'q','status':'Needs Review','gps':(24,46),'location_source':'manual','image':image(tmp_path,'g.png','gray'),'detections':[{'box':[0,0,8,8]}]}
    gallery=[dict(query,id='far',gps=(25,46)),dict(query,id='sim',location_source='simulated'),dict(query,id='none',gps=(None,None),location_source='not_provided')]
    matches={m['report_id']:m['distance_m'] for m in finder.search(query,gallery,mode='visual')['matches']}
    assert matches['far']>100000 and matches['sim'] is None and matches['none'] is None


def test_visual_mode_with_empty_gallery_computes_nothing(tmp_path):
    (tmp_path/'w').write_bytes(b'test-only');fake=Fake();finder=DuplicateFinder(tmp_path/'w',tmp_path/'cache',fake)
    query={'id':'q','status':'Needs Review','gps':(None,None),'location_source':None,'image':image(tmp_path,'g.png','gray'),'detections':[{'box':[0,0,8,8]}]}
    result=finder.search(query,[],mode='visual')
    assert result['candidate_reports']==0 and result['matches']==[] and fake.calls==0


def make(client,headers,colour,detections=None,**row):
    data=io.BytesIO();Image.new('RGB',(120,80),colour).save(data,'PNG')
    rid=client.post('/api/reports',headers=headers,files={'photo':('synthetic.png',data.getvalue(),'image/png')}).json()['id']
    row['detections']=detections if detections is not None else json.dumps([{'class_id':'D40','box':[0,0,8,8],'confidence':.9}])
    with api.Session() as session:
        session.query(api.Report).filter_by(id=rid).update(row);session.commit()
    return rid


@pytest.fixture
def searcher(review_client,tmp_path,monkeypatch):
    client,headers,_=review_client
    (tmp_path/'w').write_bytes(b'test-only');fake=Fake()
    finder=DuplicateFinder(tmp_path/'w',tmp_path/'cache',fake)
    monkeypatch.setattr(duplicate_finder,'configured_finder',lambda:finder)
    def search(rid,mode=None,key=headers):
        revision=client.get('/api/reports/'+rid,headers=headers).json()['revision']
        return client.post(f'/api/reports/{rid}/duplicates/search',headers=key,json={'revision':revision} if mode is None else {'revision':revision,'mode':mode})
    return client,headers,search,fake,monkeypatch


def test_api_visual_search_works_without_coordinates_and_changes_nothing(searcher):
    client,headers,search,_,_=searcher
    query,same,different=make(client,headers,'gray'),make(client,headers,'gray'),make(client,headers,'white')
    unreadable=make(client,headers,'gray',detections='{not json')
    no_box=make(client,headers,'gray',detections=json.dumps([{'class_id':'D40','confidence':.9}]))  # readable legacy row without a box
    before={rid:client.get('/api/reports/'+rid,headers=headers).json() for rid in (query,same,different,unreadable)}
    result=search(query,'visual')
    assert result.status_code==200,result.text
    body=result.json()
    assert body['mode']=='visual' and body['threshold_validated'] is False
    assert body['partial_search'] is False and body['partial_reasons']==[] and body['eligible_reports']==4 and body['examined_reports']==2 and body['not_examined_reports']==0 and body['new_crop_budget']==16
    assert [(m['report_id'],m['distance_m']) for m in body['matches']]==[(same,None)]
    assert body['candidate_reports']==2 and body['skipped_reports']==2  # unreadable and box-less legacy rows are both counted, never dropped silently
    for rid,saved in before.items():
        after=client.get('/api/reports/'+rid,headers=headers).json()
        assert (after['status'],after['duplicates'],after['revision'])==(saved['status'],saved['duplicates'],saved['revision'])
    assert search(query).status_code==422  # default stays nearby, which needs coordinates
    assert search(query,'nearby').status_code==422
    assert search(query,'everywhere').status_code==422
    assert search(unreadable,'visual').status_code==422
    assert search(no_box,'visual').status_code==422


def test_api_nearby_mode_unchanged(searcher):
    client,headers,search,_,_=searcher
    query=make(client,headers,'gray',latitude=24.7,longitude=46.7,location_source='manual')
    near=make(client,headers,'gray',latitude=24.7001,longitude=46.7,location_source='manual')
    make(client,headers,'gray')  # no coordinates: excluded from nearby
    body=search(query).json()
    assert body['mode']=='nearby' and body['candidate_reports']==1 and body['matches'][0]['report_id']==near and body['matches'][0]['distance_m']<20


def test_api_unavailable_dino_and_backend_failures_are_honest(searcher,tmp_path):
    client,headers,search,fake,monkeypatch=searcher
    query=make(client,headers,'gray');make(client,headers,'gray')
    monkeypatch.setattr(duplicate_finder,'configured_finder',REAL_FINDER)  # real loader, pointed at a missing checkpoint
    monkeypatch.setattr(duplicate_finder,'_instance',None)
    monkeypatch.setenv('ROADSCAN_DINO_WEIGHTS',str(tmp_path/'missing.pth'))
    response=search(query,'visual')
    assert response.status_code==503 and 'DINOv2' in response.json()['detail']
    monkeypatch.setattr(duplicate_finder,'configured_finder',lambda:DuplicateFinder(tmp_path/'w',tmp_path/'cache',fake))
    monkeypatch.setenv('ROADSCAN_SIMILARITY_NEW_CROPS','0')  # misconfigured limits are an honest 503, never an unbounded search
    assert search(query,'visual').status_code==503 and fake.calls==0
    monkeypatch.delenv('ROADSCAN_SIMILARITY_NEW_CROPS')
    def no_torch():raise RuntimeError('Install compatible torch and torchvision offline')
    monkeypatch.setattr(duplicate_finder,'configured_finder',no_torch)
    assert search(query,'visual').status_code==503
    (tmp_path/'w2').write_bytes(b'test-only')
    class Broken:
        def encode(self,path,box):raise OSError('disk failure')
    monkeypatch.setattr(duplicate_finder,'configured_finder',lambda:DuplicateFinder(tmp_path/'w2',tmp_path/'cache2',Broken()))
    assert search(query,'visual').status_code==503
    class Invalid:
        def encode(self,path,box):return [0.]*384
    monkeypatch.setattr(duplicate_finder,'configured_finder',lambda:DuplicateFinder(tmp_path/'w2',tmp_path/'cache3',Invalid()))
    response=search(query,'visual')
    assert response.status_code==422 and 'embedding' in response.json()['detail']


def test_api_visual_search_requires_reviewer(searcher):
    client,headers,search,fake,monkeypatch=searcher
    query=make(client,headers,'gray');make(client,headers,'gray')
    monkeypatch.setenv('ROADSCAN_VIEWER_KEY','viewer-visual-fixture')
    assert search(query,'visual',key={}).status_code==401
    assert search(query,'visual',key={'X-API-Key':'wrong'}).status_code==401
    assert search(query,'visual',key={'X-API-Key':'viewer-visual-fixture'}).status_code==403
    assert fake.calls==0


class ByName:
    """Returns a fixed vector per image file name, to pin exact cosine values."""
    def __init__(self,vectors):self.vectors=vectors;self.calls=0
    def encode(self,path,box):self.calls+=1;return self.vectors[path.name]


def finder_with(tmp_path,vectors):
    (tmp_path/'w').write_bytes(b'test-only');embedder=ByName(vectors)
    for i,name in enumerate(vectors):Image.new('RGB',(10,10),(i,i,i)).save(tmp_path/name)  # distinct content: the cache is keyed by image hash
    return DuplicateFinder(tmp_path/'w',tmp_path/'cache',embedder),embedder


def row(tmp_path,ident,name,**extra):
    return {'id':ident,'status':'Needs Review','gps':(None,None),'location_source':None,'image':str(tmp_path/name),'detections':[{'box':[0,0,8,8]}],**extra}


def test_cosine_is_normalised_and_threshold_is_inclusive(tmp_path):
    finder,_=finder_with(tmp_path,{'q.png':[2.]+[0.]*383,'c.png':[3.,4.]+[0.]*382})  # unnormalised; cosine is exactly 3/5
    query,gallery=row(tmp_path,'q','q.png'),[row(tmp_path,'c','c.png')]
    assert finder.search(query,gallery,threshold=.6,mode='visual')['matches'][0]['similarity']==pytest.approx(.6,abs=1e-12)
    assert finder.search(query,gallery,threshold=.6+1e-9,mode='visual')['matches']==[]
    assert len(finder.search(query,gallery,threshold=-1,mode='visual')['matches'])==1
    for bad in (float('nan'),1.01,-1.01):
        with pytest.raises(ValueError):finder.search(query,gallery,threshold=bad,mode='visual')


def test_ties_are_ordered_by_report_id_and_capped_at_five(tmp_path):
    finder,_=finder_with(tmp_path,{f'{i}.png':MATCH for i in range(8)})
    gallery=[row(tmp_path,f'r{i}',f'{i}.png') for i in (6,2,7,4,1,5,3)]
    first=finder.search(row(tmp_path,'q','0.png'),gallery,mode='visual')['matches']
    assert [m['report_id'] for m in first]==['r1','r2','r3','r4','r5']
    assert first==finder.search(row(tmp_path,'q','0.png'),list(reversed(gallery)),mode='visual')['matches']


@pytest.mark.parametrize('vector',[[0.]*384,[float('nan')]+[0.]*383,[float('inf')]+[0.]*383,[1.]*383,[1e200]*384])
def test_zero_nonfinite_wrong_size_and_overflowing_embeddings_are_rejected(tmp_path,vector):
    finder,_=finder_with(tmp_path,{'q.png':MATCH,'c.png':vector})
    with pytest.raises(ValueError):finder.search(row(tmp_path,'q','q.png'),[row(tmp_path,'c','c.png')],mode='visual')


def test_bad_boxes_reject_the_query_and_skip_candidates(tmp_path):
    finder,embedder=finder_with(tmp_path,{'q.png':MATCH,'c.png':MATCH})
    good=row(tmp_path,'good','c.png')
    bad=[[0,0,11,8],[5,0,5,8],[-1,0,8,8],[0,0,8],[0,0,8,float('nan')],[0,0,True,8],None]
    for box in bad:
        with pytest.raises(ValueError):finder.search(row(tmp_path,'q','q.png',detections=[{'box':box}]),[good],mode='visual')
    with pytest.raises(ValueError):finder.search(row(tmp_path,'q','q.png',detections=[{'box':[0,0,8,8]}]*21),[good],mode='visual')
    assert embedder.calls==0
    gallery=[good]+[row(tmp_path,f'bad{i}','c.png',detections=[{'box':box}]) for i,box in enumerate(bad)]
    gallery+=[row(tmp_path,'many','c.png',detections=[{'box':[0,0,8,8]}]*21),row(tmp_path,'missing-image','gone.png')]
    result=finder.search(row(tmp_path,'q','q.png'),gallery,mode='visual')
    assert result['candidate_reports']==1 and result['skipped_reports']==len(bad)+2 and [m['report_id'] for m in result['matches']]==['good']


def test_nearby_radius_and_source_rules_are_unchanged_while_visual_crosses_them(tmp_path):
    finder,_=finder_with(tmp_path,{'g.png':MATCH})
    metre=1/111195  # degrees of latitude per metre on the 6371 km haversine sphere
    query=row(tmp_path,'q','g.png',gps=(24,46),location_source='manual')
    gallery=[row(tmp_path,'in-49m','g.png',gps=(24+49*metre,46),location_source='manual'),
             row(tmp_path,'out-51m','g.png',gps=(24+51*metre,46),location_source='manual'),
             row(tmp_path,'device-10m','g.png',gps=(24+10*metre,46),location_source='device_gps'),
             row(tmp_path,'simulated-10m','g.png',gps=(24+10*metre,46),location_source='simulated'),
             row(tmp_path,'unknown-10m','g.png',gps=(24+10*metre,46),location_source=None),
             row(tmp_path,'no-gps','g.png',location_source='not_provided')]
    nearby=finder.search(query,gallery)
    assert nearby['mode']=='nearby' and nearby['radius_m']==50 and nearby['candidate_reports']==2
    assert {m['report_id'] for m in nearby['matches']}=={'in-49m','device-10m'}
    for radius in (0,501,float('nan')):
        with pytest.raises(ValueError):finder.search(query,gallery,radius=radius)
    visual=finder.search(query,gallery,mode='visual')
    assert visual['candidate_reports']==6
    distance={m['report_id']:m['distance_m'] for m in visual['matches']}  # top five of six equal scores, by id
    assert distance['in-49m']==pytest.approx(49,abs=.2) and distance['device-10m']==pytest.approx(10,abs=.2)
    assert all(distance.get(k) is None for k in ('simulated-10m','unknown-10m','no-gps'))  # never a cross-source distance


class Clock:
    """Fake monotonic clock; each embedding takes `step` seconds."""
    def __init__(self):self.now=0.
    def __call__(self):return self.now


def budget_finder(tmp_path,count,step=0.,checkpoint=b'test-only'):
    """Query q.png plus candidates c0..c{count-1}, each a distinct image, so every crop is a new embedding until cached."""
    (tmp_path/'w').write_bytes(checkpoint);clock=Clock()
    class Embedder:
        calls=0
        def encode(self,path,box):Embedder.calls+=1;clock.now+=step;return MATCH
    for i,name in enumerate(['q.png']+[f'c{i}.png' for i in range(count)]):Image.new('RGB',(10,10),(i,0,0)).save(tmp_path/name)
    finder=DuplicateFinder(tmp_path/'w',tmp_path/'cache',Embedder());finder.clock=clock
    return finder,Embedder,[row(tmp_path,f'c{i:02d}',f'c{i}.png') for i in range(count)]


def test_new_crop_budget_counts_the_query_and_stops_deterministically(tmp_path):
    finder,embedder,gallery=budget_finder(tmp_path,6)
    query=row(tmp_path,'q','q.png')
    first=finder.search(query,gallery,mode='visual',new_crops=4,seconds=60)
    assert (first['eligible_reports'],first['examined_reports'],first['new_crops_used'],first['new_crop_budget'])==(6,3,4,4)  # query took 1 of 4
    assert first['partial_search'] is True and first['partial_reasons']==['new_crop_budget'] and 'Limited search' in first['note']
    assert [m['report_id'] for m in first['matches']]==['c00','c01','c02']  # fixed order: no distance, then id
    second=finder.search(query,list(reversed(gallery)),mode='visual',new_crops=4,seconds=60)  # warm cache: earlier crops are free
    assert (second['examined_reports'],second['new_crops_used'],second['partial_search'])==(6,3,False)
    assert second['partial_reasons']==[] and 'Limited search' not in second['note'] and embedder.calls==7
    warm=finder.search(query,gallery,mode='visual',new_crops=1,seconds=60)
    assert (warm['examined_reports'],warm['new_crops_used'],warm['partial_search'])==(6,0,False) and embedder.calls==7


def test_budget_boundary_exact_fit_is_exhaustive_and_one_short_is_partial(tmp_path):
    finder,_,gallery=budget_finder(tmp_path,3)
    query=row(tmp_path,'q','q.png')
    short=finder.search(query,gallery,mode='visual',new_crops=3,seconds=60)
    assert (short['examined_reports'],short['partial_search'])==(2,True)
    fresh=tmp_path/'fresh';fresh.mkdir()
    finder2,_,gallery2=budget_finder(fresh,3)
    exact=finder2.search(row(fresh,'q','q.png'),gallery2,mode='visual',new_crops=4,seconds=60)
    assert (exact['examined_reports'],exact['new_crops_used'],exact['partial_search'],exact['partial_reasons'])==(3,4,False,[])


def test_query_crops_alone_can_exhaust_the_budget_without_an_exhaustive_claim(tmp_path):
    finder,embedder,gallery=budget_finder(tmp_path,2)
    query=row(tmp_path,'q','q.png',detections=[{'box':[0,0,8,8]},{'box':[1,1,9,9]},{'box':[2,2,10,10]}])
    result=finder.search(query,gallery,mode='visual',new_crops=2,seconds=60)
    assert (result['examined_reports'],result['eligible_reports'],result['new_crops_used'],result['matches'])==(0,2,2,[])
    assert result['partial_search'] is True and 'no match does not rule out' in result['note']
    again=finder.search(query,gallery,mode='visual',new_crops=2,seconds=60)  # the two finished query crops are cached
    assert (again['examined_reports'],again['new_crops_used'],again['partial_search'])==(1,2,True) and embedder.calls==4


def test_time_budget_is_checked_between_embeddings(tmp_path):
    finder,embedder,gallery=budget_finder(tmp_path,6,step=1.)
    result=finder.search(row(tmp_path,'q','q.png'),gallery,mode='visual',new_crops=50,seconds=2.5)
    # Checks at t=0,1,2 pass; the check at t=3 stops. The third embedding ran past 2.5 s: no hard cancellation.
    assert (result['new_crops_used'],result['examined_reports'],result['partial_reasons'])==(3,2,['time_budget']) and embedder.calls==3
    assert result['elapsed_s']==3


def test_cache_is_invalidated_by_box_and_checkpoint_changes(tmp_path):
    finder,embedder,gallery=budget_finder(tmp_path,2)
    query=row(tmp_path,'q','q.png')
    finder.search(query,gallery,mode='visual',new_crops=16,seconds=60);assert embedder.calls==3
    moved=[gallery[0],dict(gallery[1],detections=[{'box':[1,1,9,9]}])]
    assert finder.search(query,moved,mode='visual',new_crops=16,seconds=60)['new_crops_used']==1
    other,other_embedder,_=budget_finder(tmp_path,2,checkpoint=b'other-weights')  # same cache directory, different checkpoint
    assert other.search(query,gallery,mode='visual',new_crops=16,seconds=60)['new_crops_used']==3 and other_embedder.calls==3


@pytest.mark.parametrize('mode',['nearby','visual'])
def test_report_cap_examines_the_first_100_in_fixed_order_and_says_partial(tmp_path,mode):
    finder,embedder=finder_with(tmp_path,{'g.png':MATCH})
    query=row(tmp_path,'q','g.png',gps=(24,46),location_source='manual')
    gallery=[dict(query,id=f'r{i:03d}') for i in range(101)]
    result=finder.search(query,gallery,mode=mode,new_crops=16,seconds=60)
    assert (result['eligible_reports'],result['examined_reports'],result['partial_reasons'])==(101,100,['report_cap'])
    assert embedder.calls==1  # identical crops: cache hits still count toward the 100-report limit
    assert [m['report_id'] for m in result['matches']]==['r000','r001','r002','r003','r004']


def test_skips_and_backend_failures_are_accounted_and_release_the_lock(tmp_path):
    finder,embedder,gallery=budget_finder(tmp_path,2)
    query=row(tmp_path,'q','q.png')
    result=finder.search(query,gallery+[row(tmp_path,'bad','c0.png',detections=[{'box':[0,0,99,99]}])],mode='visual',new_crops=16,seconds=60)
    assert (result['eligible_reports'],result['examined_reports'],result['skipped_reports'],result['partial_search'])==(3,2,1,False)
    class Broken:
        def encode(self,path,box):raise OSError('disk failure')
    finder.embedder=Broken()
    with pytest.raises(OSError):finder.search(query,gallery+[row(tmp_path,'new','c0.png',detections=[{'box':[1,1,9,9]}])],mode='visual',new_crops=16,seconds=60)
    assert finder.lock.acquire(blocking=False);finder.lock.release()


def test_limits_come_from_environment_and_reject_bad_values(monkeypatch):
    for name in ('ROADSCAN_SIMILARITY_NEW_CROPS','ROADSCAN_SIMILARITY_SECONDS'):monkeypatch.delenv(name,raising=False)
    assert duplicate_finder.search_limits()==(16,20.)
    monkeypatch.setenv('ROADSCAN_SIMILARITY_NEW_CROPS','40');monkeypatch.setenv('ROADSCAN_SIMILARITY_SECONDS','45')
    assert duplicate_finder.search_limits()==(40,45.)
    for crops,seconds in (('0','20'),('many','20'),('16','nan'),('16','0.5'),('501','20'),('16','301')):
        monkeypatch.setenv('ROADSCAN_SIMILARITY_NEW_CROPS',crops);monkeypatch.setenv('ROADSCAN_SIMILARITY_SECONDS',seconds)
        with pytest.raises(RuntimeError):duplicate_finder.search_limits()


def test_visual_coverage_does_not_depend_on_coordinates(tmp_path):
    """Review probe 1: a near nonmatch must not take the last budget slot from a farther match because of its distance."""
    finder,_=finder_with(tmp_path,{'q.png':MATCH,'match.png':MATCH,'other.png':OTHER})
    query=row(tmp_path,'q','q.png',gps=(24,46),location_source='manual')
    far_match=row(tmp_path,'a-match','match.png',gps=(25,46),location_source='manual')
    near_other=row(tmp_path,'z-other','other.png',gps=(24.0001,46),location_source='manual')
    with_gps=finder.search(query,[near_other,far_match],mode='visual',new_crops=2,seconds=60)
    (tmp_path/'cache2').mkdir();finder.cache=tmp_path/'cache2'
    strip=lambda r:dict(r,gps=(None,None),location_source='not_provided')
    without=finder.search(strip(query),[strip(near_other),strip(far_match)],mode='visual',new_crops=2,seconds=60)
    for result in (with_gps,without):
        assert [m['report_id'] for m in result['matches']]==['a-match'] and result['partial_reasons']==['new_crop_budget']
    nearby=finder.search(query,[near_other,far_match],new_crops=16,seconds=60)
    assert nearby['eligible_reports']==1  # nearby still filters and orders by distance


def test_report_cap_is_not_advanced_by_repeating_and_says_so(tmp_path):
    """Review probe 2: the only match sorts last of 101; a warm repeat examines the same 100 and must not promise progress."""
    finder,_=finder_with(tmp_path,{'q.png':MATCH,'other.png':OTHER,'match.png':MATCH})
    query=row(tmp_path,'q','q.png')
    gallery=[row(tmp_path,f'r{i:03d}','other.png') for i in range(100)]+[row(tmp_path,'r999','match.png')]
    for _ in range(2):
        result=finder.search(query,gallery,mode='visual',new_crops=16,seconds=60)
        assert (result['examined_reports'],result['not_examined_reports'],result['partial_reasons'],result['matches'])==(100,1,['report_cap'],[])
        assert 'will not reach the rest' in result['note'] and 'continues from cached crops' not in result['note']


class Ticking:
    """Clock that advances `step` seconds every time it is read, standing in for slow cached reads or a slow scan."""
    def __init__(self,step):self.now=0.;self.step=step
    def __call__(self):self.now+=self.step;return self.now


def test_time_budget_applies_to_cached_work_and_scanning(tmp_path):
    """Review probe 3: a fully cached search with slow reads must stop on time, not report a complete search after 90 s."""
    finder,embedder,gallery=budget_finder(tmp_path,6)
    query=row(tmp_path,'q','q.png')
    finder.search(query,gallery,mode='visual',new_crops=16,seconds=60);calls=embedder.calls
    finder.clock=Ticking(1.)
    warm=finder.search(query,gallery,mode='visual',new_crops=16,seconds=5)
    assert warm['partial_reasons']==['time_budget'] and warm['new_crops_used']==0 and embedder.calls==calls
    assert warm['examined_reports']<6 and warm['partial_search'] is True and warm['elapsed_s']<=6
    finder.clock=Ticking(1.)
    scan=finder.search(query,gallery*3,mode='visual',new_crops=16,seconds=4)
    assert scan['unscanned_reports']>0 and scan['examined_reports']==0 and scan['partial_reasons']==['time_budget']
    assert 'Not every open report could be scanned' in scan['note'] and 'continues from cached crops' not in scan['note']


def test_images_are_opened_only_for_reports_reached_in_order(tmp_path):
    finder,_=finder_with(tmp_path,{'q.png':MATCH,'g.png':MATCH})
    query=row(tmp_path,'q','q.png')
    gallery=[row(tmp_path,f'r{i:03d}','g.png') for i in range(100)]+[row(tmp_path,f's{i:03d}','missing.png') for i in range(50)]
    result=finder.search(query,gallery,mode='visual',new_crops=16,seconds=60)
    # Unreached reports with missing images are never opened, so they are "not examined", not "skipped".
    assert (result['eligible_reports'],result['examined_reports'],result['skipped_reports'],result['not_examined_reports'])==(150,100,0,50)
