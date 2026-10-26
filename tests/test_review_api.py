"""Synthetic lifecycle checks; no real reports or model metrics are used."""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import roadscan.api as api
from roadscan.core import BASE


def save_review(client, headers, rid, payload):
    revision = client.get('/api/reports/' + rid, headers=headers).json()['revision']
    return client.patch('/api/reports/' + rid, headers=headers, json={'revision': revision, **payload})


@pytest.fixture
def review_client(tmp_path, monkeypatch):
    engine = create_engine('sqlite:///' + str(tmp_path / 'review.db'), connect_args={'check_same_thread': False})
    BASE.metadata.create_all(engine)
    storage = tmp_path / 'uploads'
    storage.mkdir()
    monkeypatch.setattr(api, 'Session', sessionmaker(bind=engine))
    monkeypatch.setattr(api, 'STORAGE', storage)
    monkeypatch.setenv('ROADSCAN_API_KEY', 'review-lifecycle-fixture')
    for name in ('ROADSCAN_ACCOUNTS_FILE', 'ROADSCAN_VIEWER_KEY', 'ROADSCAN_REVIEWER_KEY'):
        monkeypatch.delenv(name, raising=False)
    with TestClient(api.app) as client:
        image = io.BytesIO()
        Image.new('RGB', (120, 80), 'gray').save(image, 'PNG')
        headers = {'X-API-Key': 'review-lifecycle-fixture'}
        result = client.post('/api/reports', headers=headers, files={'photo': ('synthetic.png', image.getvalue(), 'image/png')})
        assert result.status_code == 201
        yield client, headers, result.json()['id']
    engine.dispose()


def test_complete_review_lifecycle_persists_notes_history_and_actor(review_client):
    client, headers, rid = review_client
    for status, action in [('Confirmed', 'confirm'), ('Assigned', 'assign'), ('Resolved', 'resolve'), ('Needs Review', 'review'), ('Duplicate', 'duplicate')]:
        result = save_review(client, headers, rid, {'status': status, 'action': action, 'note': 'Reviewed: ' + status})
        assert result.status_code == 200, result.text
        saved = client.get('/api/reports/' + rid, headers=headers).json()
        assert saved['status'] == status
        assert saved['note'] == 'Reviewed: ' + status
        assert saved['reviewer'] == 'admin'
        assert saved['history'][-1]['to'] == status
    audit = client.get('/api/reports/' + rid + '/audit', headers=headers).json()['items']
    assert [event['action'] for event in audit] == ['upload', 'confirm', 'assign', 'resolve', 'review', 'duplicate']


def test_rejected_review_does_not_change_report_or_audit(review_client):
    client, headers, rid = review_client
    for payload, code in [({'status': 'Confirmed'}, 422), ({'status': 'Assigned', 'action': 'assign'}, 409), ({'status': 'Resolved', 'action': 'resolve'}, 409)]:
        result = save_review(client, headers, rid, dict(payload, note='Must not persist'))
        assert result.status_code == code
    saved = client.get('/api/reports/' + rid, headers=headers).json()
    assert saved['status'] == 'Needs Review' and saved['note'] == ''
    assert len(saved['history']) == 1
    assert len(client.get('/api/reports/' + rid + '/audit', headers=headers).json()['items']) == 1


def test_search_statistics_and_pagination_use_all_reports(review_client):
    client, headers, rid = review_client
    image = io.BytesIO()
    Image.new('RGB', (120, 80), 'white').save(image, 'PNG')
    other = client.post('/api/reports', headers=headers, files={'photo': ('other.png', image.getvalue(), 'image/png')}).json()['id']
    save_review(client, headers, rid, {'status': 'Confirmed', 'action': 'confirm', 'note': 'Sector 50%_road'})
    assert client.get('/api/stats').status_code == 401
    stats = client.get('/api/stats', headers=headers).json()
    assert stats['total'] == 2 and stats['needs_review'] == 1
    assert stats['by_status']['Confirmed'] == 1
    first = client.get('/api/reports?size=1', headers=headers).json()
    second = client.get('/api/reports?size=1&page=2', headers=headers).json()
    assert first['total'] == second['total'] == 2
    assert first['items'][0]['id'] != second['items'][0]['id']
    filtered = client.get('/api/reports', params={'status': 'Confirmed', 'search': '50%_road'}, headers=headers).json()
    assert filtered['total'] == 1 and filtered['items'][0]['id'] == rid
    assert client.get('/api/reports', params={'search': '%'}, headers=headers).json()['total'] == 1
    assert client.get('/api/reports', params={'search': other[:8]}, headers=headers).json()['total'] == 1


def test_manual_annotations_persist_and_recalculate_draft_score(review_client):
    client, headers, rid = review_client
    boxes = [{'class_id': 'D40', 'box': [10, 10, 110, 70], 'confidence': 1}]
    result = save_review(client, headers, rid, {'detections': boxes, 'note': 'Synthetic manual annotation'})
    assert result.status_code == 200
    saved = client.get('/api/reports/' + rid, headers=headers).json()
    assert saved['detections'] == boxes and saved['inference_state'] == 'manual_review'
    assert saved['model_version'] == 'manual' and saved['score'] == 74.63
    assert client.get('/api/stats', headers=headers).json()['high_priority'] == 1
    rejected = save_review(client, headers, rid, {'detections': [{'class_id': 'D40', 'box': [0, 0, 121, 80], 'confidence': 1}]})
    assert rejected.status_code == 422
    assert client.get('/api/reports/' + rid, headers=headers).json()['detections'] == boxes

def test_annotation_history_retains_initial_prediction_and_each_edit(review_client):
    client, headers, rid = review_client
    initial = client.get('/api/reports/' + rid, headers=headers).json()['source_metadata']['initial_prediction']
    first = [{'class_id': 'D00', 'box': [10, 10, 50, 60], 'confidence': 1}]
    second = [{'class_id': 'D40', 'box': [20, 20, 100, 70], 'confidence': 1}]
    for boxes in (first, second, []):
        assert save_review(client, headers, rid, {'detections': boxes}).status_code == 200
        assert client.get('/api/reports/' + rid, headers=headers).json()['source_metadata']['initial_prediction'] == initial
    events = client.get('/api/reports/' + rid + '/audit', headers=headers).json()['items'][1:]
    assert events[0]['details']['previous_detections'] == initial['detections']
    assert events[0]['details']['detections'] == first
    assert events[1]['details']['previous_detections'] == first
    assert events[1]['details']['detections'] == second
    assert events[2]['details']['previous_detections'] == second
    assert events[2]['details']['detections'] == []


def test_stale_review_cannot_overwrite_newer_edits(review_client):
    client, headers, rid = review_client
    endpoint = '/api/reports/' + rid
    before = client.get(endpoint, headers=headers).json()
    payload = {'revision': before['revision'], 'note': 'First saved edit', 'detections': [
        {'class_id': 'D40', 'box': [10, 10, 60, 60], 'confidence': 1}]}
    first = client.patch(endpoint, headers=headers, json=payload)
    assert first.status_code == 200
    assert first.json()['revision'] != before['revision']
    assert client.patch(endpoint, headers=headers, json={**payload, 'note': 'Stale edit', 'detections': []}).status_code == 409
    assert client.patch(endpoint, headers=headers, json={'note': 'Missing revision'}).status_code == 422
    assert client.get(endpoint, headers=headers).json()['note'] == 'First saved edit'
    assert len(client.get(endpoint + '/audit', headers=headers).json()['items']) == 2


def test_conditional_write_rejects_change_committed_after_revision_check(review_client, monkeypatch):
    from sqlalchemy import event, update
    from roadscan.core import Report
    client, headers, rid = review_client
    endpoint = '/api/reports/' + rid
    before = client.get(endpoint, headers=headers).json()
    engine = api.Session.kw['bind']
    triggered = False
    def competing_save(conn, cursor, statement, parameters, context, executemany):
        nonlocal triggered
        if triggered or not statement.lstrip().upper().startswith('UPDATE REPORTS'):
            return
        triggered = True
        # Commit an independent edit immediately before the guarded UPDATE executes.
        with engine.begin() as other:
            other.execute(update(Report).where(Report.id == rid).values(status='Confirmed', note='Competing edit'))
    event.listen(engine, 'before_cursor_execute', competing_save)
    try:
        result = client.patch(endpoint, headers=headers, json={'revision': before['revision'], 'note': 'Must not persist'})
    finally:
        event.remove(engine, 'before_cursor_execute', competing_save)
    assert triggered and result.status_code == 409
    assert client.get(endpoint, headers=headers).json()['note'] == 'Competing edit'
    assert len(client.get(endpoint + '/audit', headers=headers).json()['items']) == 1


def test_missing_image_gives_structured_errors_without_saving(review_client, monkeypatch):
    client, headers, rid = review_client
    endpoint = '/api/reports/' + rid
    before = client.get(endpoint, headers=headers).json()
    next(api.STORAGE.iterdir()).unlink()
    def fail_if_open(*args, **kwargs):
        raise AssertionError('Missing files must be checked before optional image decoders')
    monkeypatch.setattr(api, 'pillow_open', fail_if_open)
    assert client.get(endpoint + '/image', headers=headers).status_code == 404
    assert client.get(endpoint + '/sensitivity', headers=headers).status_code == 404
    assert client.patch(endpoint, headers=headers, json={'revision': before['revision'], 'detections': []}).status_code == 404
    assert client.get(endpoint, headers=headers).json()['revision'] == before['revision']


def test_corrupt_image_is_reported_without_optional_detector_decoders(review_client, monkeypatch):
    client, headers, rid = review_client
    endpoint = '/api/reports/' + rid
    before = client.get(endpoint, headers=headers).json()
    next(api.STORAGE.iterdir()).write_bytes(b'corrupt synthetic fixture')
    def detector_fallback(*args, **kwargs):
        raise ModuleNotFoundError('pi_heif')
    monkeypatch.setattr(Image, 'open', detector_fallback)
    assert client.get(endpoint + '/sensitivity', headers=headers).status_code == 409
    assert client.patch(endpoint, headers=headers, json={'revision': before['revision'], 'detections': []}).status_code == 409
    assert client.get(endpoint, headers=headers).json()['revision'] == before['revision']
