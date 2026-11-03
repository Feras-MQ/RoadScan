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
    assert [(m['report_id'],m['distance_m']) for m in body['matches']]==[(same,None)]
    assert body['candidate_reports']==2 and body['skipped_reports']==1  # unreadable never reaches the finder; box-less legacy row skipped and counted
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


@pytest.mark.parametrize('mode',['nearby','visual'])
def test_more_than_100_candidates_is_refused_before_any_embedding(tmp_path,mode):
    finder,embedder=finder_with(tmp_path,{'g.png':MATCH})
    query=row(tmp_path,'q','g.png',gps=(24,46),location_source='manual')
    with pytest.raises(ValueError,match='More than 100'):finder.search(query,[dict(query,id=f'r{i}') for i in range(101)],mode=mode)
    assert embedder.calls==0
