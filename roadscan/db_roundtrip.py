"""Explicit transactional persistence probe for a prepared RoadScan database.

Temporarily INSERTs linked report/audit/history rows and SELECTs them in the
same transaction, then always rolls back. Use only on authorized test databases.
"""
import argparse
import json
import os
import uuid
from sqlalchemy import create_engine, text
from roadscan.db_verify import verify_engine


def probe_engine(engine):
    """Test insert/read/FK integration; rollback even on errors."""
    schema = verify_engine(engine)
    if not schema['ok']:
        return {'ok': False, 'reason': 'schema_incomplete', 'schema': schema}
    marker = 'roadscan-probe-' + uuid.uuid4().hex
    conn = engine.connect()
    tx = conn.begin()
    try:
        conn.execute(text('INSERT INTO reports (id, image_ref, status, source_metadata, detections, score_parts, duplicates) '
                          'VALUES (:id, :image_ref, :status, :metadata, :detections, :parts, :duplicates)'),
                     {'id': marker, 'image_ref': 'probe-not-an-image', 'status': 'New',
                      'metadata': '{}', 'detections': '[]', 'parts': '{}', 'duplicates': '[]'})
        conn.execute(text('INSERT INTO audit_events (report_id, actor, action, details) '
                          'VALUES (:id, :actor, :action, :details)'),
                     {'id': marker, 'actor': 'db_probe', 'action': 'probe', 'details': '{}'})
        conn.execute(text('INSERT INTO status_history (report_id, from_status, to_status, actor) '
                          'VALUES (:id, :from_status, :to_status, :actor)'),
                     {'id': marker, 'from_status': 'New', 'to_status': 'Needs Review', 'actor': 'db_probe'})
        counts = {}
        for table in ('reports', 'audit_events', 'status_history'):
            key = 'id' if table == 'reports' else 'report_id'
            counts[table] = conn.execute(text(f'SELECT COUNT(*) FROM {table} WHERE {key}=:id'), {'id': marker}).scalar_one()
        success = all(value == 1 for value in counts.values())
        return {'ok': success, 'dialect': engine.dialect.name, 'transactional_reads': counts,
                'rolled_back': True}
    finally:
        tx.rollback()
        conn.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database-url', default=None)
    parser.add_argument('--allow-write-test', action='store_true',
                        help='Required acknowledgment: temporary inserts will be attempted then rolled back')
    args = parser.parse_args(argv)
    if not args.allow_write_test:
        parser.error('Pass --allow-write-test only for an authorized test database')
    url = args.database_url or os.getenv('DATABASE_URL')
    if not url:
        parser.error('Supply DATABASE_URL or --database-url; no implicit SQLite fallback')
    engine = create_engine(url, pool_pre_ping=True)
    try:
        result = probe_engine(engine)
    finally:
        engine.dispose()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
