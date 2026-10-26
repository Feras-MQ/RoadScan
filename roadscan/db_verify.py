"""Read-only schema checks for a configured RoadScan database.

Does not migrate, insert records, or prove operational deployment readiness.
"""
import argparse
import json
import os
from sqlalchemy import create_engine, inspect, text

REQUIRED = {
    'reports': {'id', 'image_ref', 'image_sha', 'image_phash', 'created_at',
                'updated_at', 'status', 'reviewer', 'source', 'source_metadata',
                'latitude', 'longitude', 'location_source', 'model_version',
                'inference_state', 'detections', 'score', 'score_parts',
                'duplicates', 'note'},
    'audit_events': {'id', 'report_id', 'actor', 'action', 'details', 'created_at'},
    'status_history': {'id', 'report_id', 'from_status', 'to_status', 'actor', 'created_at'},
}


def verify_engine(engine, *, require_postgis=False):
    """Return structured findings; only issue metadata queries and SELECT statements."""
    dialect = engine.dialect.name
    findings = {'dialect': dialect, 'tables': {}, 'postgis': 'not_checked', 'ok': True}
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    for table, required in REQUIRED.items():
        missing = sorted(required - {col['name'] for col in inspector.get_columns(table)}) if table in existing else sorted(required)
        findings['tables'][table] = {'present': table in existing, 'missing_columns': missing}
        if missing:
            findings['ok'] = False
    if require_postgis:
        if dialect != 'postgresql':
            findings['postgis'] = 'requires_postgresql'
            findings['ok'] = False
        else:
            with engine.connect() as connection:
                installed = connection.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='postgis')")).scalar()
            geom = 'geom' in {col['name'] for col in inspector.get_columns('reports')} if 'reports' in existing else False
            findings['postgis'] = {'extension_installed': bool(installed), 'geometry_column': geom}
            if not installed or not geom:
                findings['ok'] = False
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database-url', default=None, help='Defaults to DATABASE_URL; do not put credentials in logs')
    parser.add_argument('--require-postgis', action='store_true')
    args = parser.parse_args(argv)
    url = args.database_url or os.getenv('DATABASE_URL')
    if not url:
        parser.error('DATABASE_URL or --database-url is required (no implicit SQLite fallback)')
    engine = create_engine(url, pool_pre_ping=True)
    try:
        findings = verify_engine(engine, require_postgis=args.require_postgis)
    finally:
        engine.dispose()
    print(json.dumps(findings, indent=2, sort_keys=True))
    return 0 if findings['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
