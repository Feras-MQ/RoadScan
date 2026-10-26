"""Explicit local retention maintenance; never runs automatically."""
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from .core import Session, Report, History, Audit, STORAGE, init_db


def expired_reports(session, days, now=None):
    if days < 1:
        raise ValueError('Retention days must be >= 1')
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    return session.query(Report).filter(Report.created_at < cutoff).order_by(Report.created_at).all()


def purge(session, days, execute=False, now=None):
    candidates = expired_reports(session, days, now)
    ids = [r.id for r in candidates]
    if not execute:
        return {'mode': 'dry_run', 'count': len(ids), 'report_ids': ids}
    # Remove DB rows first; files are removed after commit. An interrupted process
    # can leave orphaned media, which should be reconciled during maintenance.
    files = [STORAGE / Path(r.image_ref).name for r in candidates]
    for r in candidates:
        session.query(History).filter_by(report_id=r.id).delete()
        session.query(Audit).filter_by(report_id=r.id).delete()
        session.delete(r)
    session.commit()
    for path in files:
        path.unlink(missing_ok=True)
    return {'mode': 'executed', 'count': len(ids), 'report_ids': ids}


def main():
    parser = argparse.ArgumentParser(description='RoadScan local retention (explicit operation)')
    parser.add_argument('--days', type=int, default=None, help='Age threshold in days')
    parser.add_argument('--execute', action='store_true', help='Actually delete; omit for dry run')
    args = parser.parse_args()
    import os, json
    days = args.days if args.days is not None else int(os.getenv('ROADSCAN_RETENTION_DAYS', '30'))
    init_db()
    with Session() as session:
        print(json.dumps(purge(session, days, args.execute), indent=2))

if __name__ == '__main__':
    main()
