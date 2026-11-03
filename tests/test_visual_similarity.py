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
    assert result['threshold']==.8 and result['threshold_validated'] is False and 'not a confirmed duplicate' in result['note']
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
    before={rid:client.get('/api/reports/'+rid,headers=headers).json() for rid in (query,same,different,unreadable)}
    result=search(query,'visual')
    assert result.status_code==200,result.text
    body=result.json()
    assert body['mode']=='visual' and body['threshold_validated'] is False
    assert [(m['report_id'],m['distance_m']) for m in body['matches']]==[(same,None)]
    assert body['candidate_reports']==2  # unreadable candidate skipped, not compared as "no damage"
    for rid,saved in before.items():
        after=client.get('/api/reports/'+rid,headers=headers).json()
        assert (after['status'],after['duplicates'],after['revision'])==(saved['status'],saved['duplicates'],saved['revision'])
    assert search(query).status_code==422  # default stays nearby, which needs coordinates
    assert search(query,'nearby').status_code==422
    assert search(query,'everywhere').status_code==422
    assert search(unreadable,'visual').status_code==422


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
