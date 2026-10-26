from sqlalchemy import create_engine, text
from roadscan.core import BASE
from roadscan.db_verify import verify_engine, REQUIRED


def test_complete_sqlite_schema():
    engine = create_engine('sqlite:///:memory:')
    BASE.metadata.create_all(engine)
    result = verify_engine(engine)
    assert result['ok']
    assert set(result['tables']) == set(REQUIRED)
    engine.dispose()


def test_missing_columns_fail_closed():
    engine = create_engine('sqlite:///:memory:')
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE reports (id TEXT PRIMARY KEY)'))
    result = verify_engine(engine)
    assert not result['ok']
    assert 'image_ref' in result['tables']['reports']['missing_columns']
    assert not result['tables']['audit_events']['present']
    engine.dispose()


def test_postgis_requirement_rejects_sqlite():
    engine = create_engine('sqlite:///:memory:')
    BASE.metadata.create_all(engine)
    result = verify_engine(engine, require_postgis=True)
    assert not result['ok']
    assert result['postgis'] == 'requires_postgresql'
    engine.dispose()
