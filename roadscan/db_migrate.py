"""Explicit PostgreSQL migration runner; no implicit production schema creation."""
import os
from pathlib import Path
from sqlalchemy import create_engine, text

MIGRATIONS = Path(__file__).resolve().parent.parent / 'migrations'

def migration_files():
    return [MIGRATIONS / '000_postgres_schema.sql', MIGRATIONS / '001_postgis.sql']

def apply_postgres_schema(database_url=None, *, with_postgis=False):
    url = database_url or os.getenv('DATABASE_URL', '')
    if not url.startswith(('postgresql://', 'postgresql+psycopg://')):
        raise ValueError('A PostgreSQL DATABASE_URL is required; SQLite cannot run these migrations')
    engine = create_engine(url, pool_pre_ping=True)
    try:
        paths = migration_files() if with_postgis else migration_files()[:1]
        for path in paths:
            # SQLAlchemy/psycopg supports PostgreSQL multi-statement SQL via exec_driver_sql.
            with engine.begin() as connection:
                connection.exec_driver_sql(path.read_text(encoding='utf-8'))
    finally:
        engine.dispose()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-postgis', action='store_true', help='Requires approved PostGIS extension permissions')
    args = parser.parse_args()
    apply_postgres_schema(with_postgis=args.with_postgis)
    print('PostgreSQL schema applied. No data imported.')
