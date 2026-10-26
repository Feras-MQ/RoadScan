import io, os, tempfile
from pathlib import Path
os.environ['DATABASE_URL']='sqlite:///'+str(Path(tempfile.gettempdir()) / ('roadscan_test_'+str(os.getpid())+'.db'))
os.environ['ROADSCAN_STORAGE']=str(Path(tempfile.gettempdir()) / ('roadscan_test_uploads_'+str(os.getpid())))
os.environ['ROADSCAN_API_KEY']='test-secret-only'
from fastapi.testclient import TestClient
from PIL import Image
from roadscan.api import app
from roadscan.core import score

def test_synthetic_pipeline_smoke():
    # SYNTHETIC SOFTWARE FIXTURE — NOT DETECTOR PERFORMANCE EVIDENCE.
    with TestClient(app) as client:
        key={'X-API-Key':'test-secret-only'}
        b=io.BytesIO();Image.new('RGB',(120,80),'gray').save(b,'PNG')
        r=client.post('/api/reports',files={'photo':('synthetic.png',b.getvalue(),'image/png')},headers=key)
        assert r.status_code==201,r.text
        d=r.json();assert d['inference_state']=='not_configured' and d['score'] is None and d['detections']==[]
        rid=d['id'];assert client.get('/api/reports/'+rid,headers=key).status_code==200
        assert client.get('/api/reports/'+rid+'/image',headers=key).status_code==200
        assert client.patch('/api/reports/'+rid,headers=key,json={'revision':d['revision'],'reviewer':'Test reviewer','status':'Confirmed','action':'confirm'}).status_code==200
        assert client.get('/api/reports',headers=key).json()['total']==1
        assert client.get('/api/mock/government/'+rid,headers=key).json()['sent'] is False
        assert client.delete('/api/reports/'+rid,headers=key).status_code==204

def test_score_manual_only():
    result,parts=score([{'class_id':'D40','box':[0,0,10,10],'confidence':1}],100,100)
    assert result is not None and parts['area']==.01
