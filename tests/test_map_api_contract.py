"""Synthetic API checks for the coordinate view; no map accuracy claims."""
import io
import pytest
from PIL import Image
from test_review_api import review_client


@pytest.mark.parametrize('source', ['manual', 'device_gps', 'simulated', 'not_provided'])
def test_map_list_keeps_location_provenance_and_protected_image(review_client, source):
    client, headers, _ = review_client
    image = io.BytesIO()
    Image.new('RGB', (120, 80), 'gray').save(image, 'PNG')
    data = {'location_source': source}
    if source != 'not_provided':
        data.update(latitude='24.7', longitude='46.7')
    saved = client.post('/api/reports', headers=headers, data=data,
                        files={'photo': ('synthetic-map.png', image.getvalue(), 'image/png')})
    assert saved.status_code == 201
    rid = saved.json()['id']
    listed = client.get('/api/reports?size=20&page=1', headers=headers).json()
    report = next(row for row in listed['items'] if row['id'] == rid)
    assert report['location_source'] == source
    assert (report['latitude'], report['longitude']) == ((None, None) if source == 'not_provided' else (24.7, 46.7))
    assert isinstance(report['detections'], list)
    assert client.get(f'/api/reports/{rid}/image', headers=headers).status_code == 200
    assert client.get(f'/api/reports/{rid}/image').status_code in (401, 403)


@pytest.mark.parametrize('data', [
    {'latitude':'0','longitude':'0'},
    {'latitude':'24.7','location_source':'manual'},
    {'latitude':'91','longitude':'46.7','location_source':'manual'},
])
def test_invalid_or_ambiguous_new_locations_never_create_a_report(review_client, data):
    client, headers, _ = review_client
    before = client.get('/api/reports', headers=headers).json()['total']
    response = client.post('/api/reports', headers=headers, data=data,
                           files={'photo': ('invalid.png', b'invalid', 'image/png')})
    assert response.status_code == 422
    assert client.get('/api/reports', headers=headers).json()['total'] == before
