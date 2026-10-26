"""Desktop backend entrypoint; receives a random local token from Electron."""
import os
from pathlib import Path

def main():
    if not os.getenv('ROADSCAN_API_KEY'):
        raise SystemExit('Missing desktop session token')
    data=Path(os.environ.get('ROADSCAN_DATA_DIR',str(Path.home()/'.roadscan'))).resolve()
    data.mkdir(parents=True,exist_ok=True)
    os.chdir(data)
    os.environ.setdefault('ROADSCAN_STORAGE',str(data/'private_uploads'))
    os.environ.setdefault('DATABASE_URL','sqlite:///'+str(data/'roadscan.db').replace('\\','/'))
    # The desktop process runs only on loopback and uses a random key per launch.
    import uvicorn
    uvicorn.run('roadscan.api:app',host='127.0.0.1',port=int(os.getenv('ROADSCAN_PORT','18743')),log_level='warning')

if __name__=='__main__':main()
