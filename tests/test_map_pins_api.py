"""Synthetic contract checks for GET /api/reports/map; isolated DB, no real reports or coordinates."""
import io
import json
from datetime import datetime
from PIL import Image
from roadscan import api
from test_review_api import review_client  # noqa: F401  (fixture)


def make(client, headers, **row):
    image = io.BytesIO()
    Image.new('RGB', (120, 80), 'gray').save(image, 'PNG')
    rid = client.post('/api/reports', headers=headers, data={'latitude': '24.7', 'longitude': '46.7', 'location_source': 'manual'},
                      files={'photo': ('pin.png', image.getvalue(), 'image/png')}).json()['id']
    if 'raw_detections' in row:
        row['detections'] = row.pop('raw_detections')  # stored as-is, like a legacy row
    elif 'detections' in row:
        row['detections'] = json.dumps([{'class_id': c, 'box': [1, 1, 5, 5], 'confidence': .9} for c in row['detections']])
    with api.Session() as session:  # set provenance, coordinates and times directly, as legacy rows could hold them
        session.query(api.Report).filter_by(id=rid).update(row)
        session.commit()
    return rid


def pins(client, headers, query):
    response = client.get('/api/reports/map?' + query, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_map_pins_contract(review_client):
    client, headers, _ = review_client
    t = lambda h: datetime(2026, 11, 2, h)
    r1 = make(client, headers, detections=['D40', 'D00', 'D40'], status='Needs Review', score=72.5, created_at=t(9))
    r2 = make(client, headers, latitude=0.0, longitude=0.0, location_source='device_gps', detections=[], created_at=t(8))
    r3 = make(client, headers, latitude=90.0, longitude=180.0, detections=['D10'], status='Confirmed', created_at=t(8))
    r9 = make(client, headers, latitude=-90.0, longitude=-180.0, detections=['OTHER'], created_at=None)
    sim = make(client, headers, location_source='simulated', detections=['D20'], created_at=t(10))
    excluded = [make(client, headers, **change) for change in (
        {'latitude': 91.0}, {'longitude': -180.5}, {'longitude': None}, {'location_source': None},
        {'location_source': 'gps_guess'}, {'location_source': 'not_provided'})]

    body = pins(client, headers, 'location=recorded')
    ids = [p['id'] for p in body['items']]
    assert ids == [r1, *sorted([r2, r3]), r9]  # created_at desc, id asc tie-break, null created_at last
    assert not set(excluded) & set(ids) and sim not in ids
    assert body['total'] == body['returned'] == 4 and body['limit'] == 2000 and body['truncated'] is False and body['unreadable'] == 0
    first = body['items'][0]
    assert set(first) == {'id', 'latitude', 'longitude', 'location_source', 'status', 'score', 'classes', 'created_at'}
    assert first['classes'] == ['D00', 'D40'] and first['score'] == 72.5 and first['created_at'] == '2026-11-02T09:00:00'
    zero = next(p for p in body['items'] if p['id'] == r2)
    assert (zero['latitude'], zero['longitude'], zero['classes'], zero['location_source']) == (0.0, 0.0, [], 'device_gps')
    assert body['items'][-1]['created_at'] is None

    assert [p['id'] for p in pins(client, headers, 'location=simulated')['items']] == [sim]
    for query, expected in [('damage=D40', [r1]), ('damage=none', [r2]), ('damage=OTHER', [r9]),
                            ('status=Confirmed', [r3]), ('status=Confirmed&damage=D10', [r3]),
                            ('status=Confirmed&damage=D40', []), ('damage=D20', [])]:
        result = pins(client, headers, 'location=recorded&' + query)
        assert [p['id'] for p in result['items']] == expected, query
        assert result['total'] == len(expected) and result['truncated'] is False

    capped = pins(client, headers, 'location=recorded&limit=2')
    assert [p['id'] for p in capped['items']] == ids[:2]
    assert (capped['total'], capped['returned'], capped['limit'], capped['truncated']) == (4, 2, 2, True)
    assert pins(client, headers, 'location=recorded&limit=2') == capped  # stable under the cap
    assert pins(client, headers, 'location=recorded&limit=4')['truncated'] is False
    filtered_cap = pins(client, headers, 'location=recorded&status=Needs Review&limit=1')
    assert filtered_cap['total'] == 3 and filtered_cap['returned'] == 1 and filtered_cap['truncated'] is True

    # The static route is not captured by /api/reports/{rid}, and report-ID routes still work.
    assert client.get(f'/api/reports/{r1}', headers=headers).json()['id'] == r1
    assert client.get('/api/reports?size=5', headers=headers).json()['size'] == 5


def test_map_pins_rejects_bad_parameters_and_requires_auth(review_client):
    client, headers, _ = review_client
    for query in ['', 'location=none', 'location=all', 'location=recorded&damage=d40', 'location=recorded&damage=D30',
                  'location=recorded&status=Bogus', 'location=recorded&limit=0', 'location=recorded&limit=2001']:
        assert client.get('/api/reports/map?' + query, headers=headers).status_code == 422, query
    assert client.get('/api/reports/map?location=recorded').status_code in (401, 403)


def test_malformed_legacy_detections_are_unreadable_not_zero(review_client):
    client, headers, _ = review_client
    t = lambda m: datetime(2026, 11, 2, 9, m)
    valid = make(client, headers, detections=['D40'], created_at=t(59))
    empty = make(client, headers, detections=[], created_at=t(58))
    raws = ['null', '1', '{broken', '[{}]', '[null]', '{"D40": true}', '[{"class_id": "LEGACY"}]',
            '[{"class_id": "D40"}, {"class_id": 7}]', '"[]"', None, '[{"class_id": []}]', '[{"class_id": {}}]',
            '[{"class_id": "D40", "box": [1, 1, 5, 5], "confidence": NaN}]',
            '[{"class_id": "D40", "box": [1, 1, 5, 5], "confidence": Infinity}]',
            '[{"class_id": "D40", "box": [1, 1, 5, 5], "confidence": -Infinity}]']
    bad = [make(client, headers, raw_detections=raw, created_at=t(m)) for m, raw in enumerate(raws)]
    first = pins(client, headers, 'location=recorded&limit=1')  # older malformed rows must not break a capped request
    assert [p['id'] for p in first['items']] == [valid] and first['total'] == 2 + len(raws) and first['unreadable'] == len(raws)
    body = pins(client, headers, 'location=recorded')
    unreadable = {p['id'] for p in body['items'] if p['classes'] is None}
    assert unreadable == set(bad) and body['unreadable'] == len(raws)
    assert [p['id'] for p in pins(client, headers, 'location=recorded&damage=none')['items']] == [empty]
    d40 = pins(client, headers, 'location=recorded&damage=D40')
    assert [p['id'] for p in d40['items']] == [valid] and d40['unreadable'] == 0
    assert pins(client, headers, 'location=recorded&damage=OTHER')['total'] == 0
