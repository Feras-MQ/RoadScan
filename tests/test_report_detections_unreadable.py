"""Malformed stored detections on /api/reports list/detail/PATCH; isolated synthetic DB only."""
import hashlib
import io
import json
from PIL import Image
from roadscan import api
from test_review_api import review_client  # noqa: F401  (fixture)

VALID = {'d40': '[{"class_id": "D40", "box": [1, 1, 5, 5], "confidence": 0.9}]', 'empty': '[]',
         'legacy': '[{"class_id": "D00", "box": [1, 2, 30, 40]}]'}
MALFORMED = ['null', '1', '{broken', '[{}]', '[null]', '{"D40": true}', '[{"class_id": "LEGACY"}]',
             '[{"class_id": "D40"}, {"class_id": 7}]', '"[]"', None]


def stored(client, headers, raw):
    image = io.BytesIO()
    Image.new('RGB', (120, 80), 'gray').save(image, 'PNG')
    rid = client.post('/api/reports', headers=headers, files={'photo': ('d.png', image.getvalue(), 'image/png')}).json()['id']
    with api.Session() as session:  # write the raw value as a legacy row would hold it
        session.query(api.Report).filter_by(id=rid).update({'detections': raw})
        session.commit()
    return rid


def old_revision(rid):
    with api.Session() as session:
        r = session.get(api.Report, rid)
        data = {'id': r.id, 'image_sha': r.image_sha, 'detections': json.loads(r.detections),
                'status': r.status, 'updated_at': r.updated_at.isoformat() if r.updated_at else None}
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def test_list_and_detail_mark_malformed_detections_unreadable(review_client):
    client, headers, _ = review_client
    valid = {name: stored(client, headers, raw) for name, raw in VALID.items()}
    bad = {stored(client, headers, raw): raw for raw in MALFORMED}
    listed = client.get('/api/reports?size=100', headers=headers)
    assert listed.status_code == 200  # one malformed row no longer fails the whole page
    rows = {row['id']: row for row in listed.json()['items']}
    for name, rid in valid.items():
        assert rows[rid]['detections'] == json.loads(VALID[name]) and rows[rid]['detections_readable'] is True
        assert rows[rid]['revision'] == old_revision(rid)  # unchanged for readable records
    assert rows[valid['empty']]['detections'] == []  # a genuine empty list stays zero detections
    for rid in bad:
        assert rows[rid]['detections'] is None and rows[rid]['detections_readable'] is False, bad[rid]
        detail = client.get(f'/api/reports/{rid}', headers=headers)
        assert detail.status_code == 200 and detail.json()['detections'] is None, bad[rid]
        assert detail.json()['detections_readable'] is False and len(detail.json()['revision']) == 64
    assert len({rows[rid]['revision'] for rid in bad}) == len(bad)


def test_patch_keeps_unreadable_raw_value_unless_boxes_are_redrawn(review_client):
    client, headers, _ = review_client
    rid = stored(client, headers, '{broken')
    revision = client.get(f'/api/reports/{rid}', headers=headers).json()['revision']
    saved = client.patch(f'/api/reports/{rid}', headers=headers,
                         json={'revision': revision, 'reviewer': 'Reviewer', 'status': 'Confirmed', 'action': 'confirm', 'note': 'checked'})
    assert saved.status_code == 200 and saved.json()['detections'] is None and saved.json()['note'] == 'checked'
    with api.Session() as session:
        assert session.get(api.Report, rid).detections == '{broken'  # status/note save never rewrites it to []
    redraw = client.patch(f'/api/reports/{rid}', headers=headers,
                          json={'revision': saved.json()['revision'], 'reviewer': 'Reviewer', 'status': 'Confirmed', 'action': 'review',
                                'detections': [{'class_id': 'D40', 'box': [1, 1, 5, 5], 'confidence': 1}]})
    assert redraw.status_code == 200, redraw.text
    assert redraw.json()['detections_readable'] is True and redraw.json()['detections'][0]['class_id'] == 'D40'
    with api.Session() as session:
        audit = [json.loads(a.details) for a in session.query(api.Audit).filter_by(report_id=rid).all()]
    replaced = [d for d in audit if d.get('manual_detections')]
    assert replaced and replaced[-1]['previous_detections'] is None and replaced[-1]['previous_detections_unreadable'] is True
