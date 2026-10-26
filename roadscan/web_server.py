"""Docker / local web entrypoint; supports a prebuilt React UI."""
import os
from pathlib import Path

def main():
    import uvicorn
    uvicorn.run('roadscan.api:app',host=os.getenv('ROADSCAN_HOST','127.0.0.1'),port=int(os.getenv('ROADSCAN_PORT','8000')))

if __name__=='__main__':main()
