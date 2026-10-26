from sqlalchemy import create_engine, text
from roadscan.core import BASE
from roadscan.db_roundtrip import probe_engine, main


def test_probe_rolls_back(tmp_path):
    engine = create_engine(f'sqlite:///{tmp_path / "test.db"}')
    BASE.metadata.create_all(engine)
    result = probe_engine(engine)
    assert result['ok'] and result['rolled_back']
    assert result['transactional_reads'] == {'reports': 1, 'audit_events': 1, 'status_history': 1}
    with engine.connect() as conn:
        for table in ('reports', 'audit_events', 'status_history'):
            assert conn.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar_one() == 0
    engine.dispose()


def test_probe_incomplete_schema(tmp_path):
    engine = create_engine(f'sqlite:///{tmp_path / "empty.db"}')
    assert probe_engine(engine)['reason'] == 'schema_incomplete'
    engine.dispose()


def test_requires_opt_in():
    import pytest
    with pytest.raises(SystemExit):
        main(['--database-url', 'sqlite:///:memory:'])
