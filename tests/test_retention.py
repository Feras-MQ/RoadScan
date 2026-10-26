from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session as DBSession
from roadscan.core import BASE, Report
from roadscan.retention import purge, expired_reports


def test_retention_dry_run_does_not_delete(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path / 'test.db'))
    BASE.metadata.create_all(engine)
    with DBSession(engine) as s:
        s.add(Report(id='old', image_ref='old.jpg', created_at=datetime.now(timezone.utc)-timedelta(days=60)))
        s.add(Report(id='new', image_ref='new.jpg', created_at=datetime.now(timezone.utc)))
        s.commit()
        result = purge(s, 30)
        assert result['mode'] == 'dry_run'
        assert result['report_ids'] == ['old']
        assert s.query(Report).count() == 2


def test_retention_rejects_invalid_days(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path / 'test.db'))
    BASE.metadata.create_all(engine)
    with DBSession(engine) as s:
        try:
            expired_reports(s, 0)
            assert False
        except ValueError:
            pass
