from pathlib import Path
import pytest
from roadscan.db_migrate import migration_files, apply_postgres_schema

def test_migration_files_exist_and_cover_models():
    paths = migration_files()
    assert all(path.is_file() for path in paths)
    sql = paths[0].read_text()
    for table in ('reports', 'audit_events', 'status_history'):
        assert f'CREATE TABLE IF NOT EXISTS {table}' in sql
    assert 'ix_reports_status_created' in sql

def test_migration_rejects_sqlite():
    with pytest.raises(ValueError, match='PostgreSQL'):
        apply_postgres_schema('sqlite:///test.db')
