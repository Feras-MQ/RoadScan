"""Local Windows-friendly starter. Does not bypass authentication or download weights."""
import argparse
import os
import sys
import webbrowser
from pathlib import Path


def prepare(root: Path, username='supervisor', clipboard=None):
    """Create an admin only on first run, preserve existing accounts."""
    from .accounts import create_account_file
    account_file = root / 'private_accounts.json'
    if account_file.exists():
        return None, account_file
    token = create_account_file(str(account_file), username, 'admin')
    if clipboard:
        try:
            clipboard(token)
        except Exception:
            pass
    return token, account_file


def copy_windows_clipboard(value):
    if sys.platform != 'win32':
        return
    import subprocess
    # No shell and no secret in process arguments: pass via stdin.
    subprocess.run(['clip.exe'], input=value.encode('utf-16le'), check=True, timeout=5)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Start RoadScan locally with guided first-run authentication')
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error('Port must be between 1024 and 65535')
    root = Path(__file__).resolve().parent.parent
    os.chdir(root)
    try:
        token, account_file = prepare(root, clipboard=copy_windows_clipboard)
    except Exception as exc:
        print('Account setup failed:', exc, file=sys.stderr)
        return 1
    os.environ['ROADSCAN_ACCOUNTS_FILE'] = str(account_file)
    # Use only a locally installed, hash-verified checkpoint; never fetch weights.
    if not os.getenv('ROADSCAN_YOLO_WEIGHTS'):
        try:
            from .model_setup import configured_checkpoint
            checkpoint = configured_checkpoint(root)
            if checkpoint:
                os.environ['ROADSCAN_YOLO_WEIGHTS'] = checkpoint
                print('Installed YOLO checkpoint found; model will be checked at startup.', flush=True)
        except (ValueError, OSError) as exc:
            print('MODEL CONFIGURATION ERROR:', exc, file=sys.stderr, flush=True)
            return 1
    print('\n=== RoadScan Local Starter ===', flush=True)
    if token:
        print('FIRST RUN: Your administrator token (save privately):\n' + token, flush=True)
        print('On Windows the token was copied to your clipboard if available.', flush=True)
    else:
        print('Existing accounts preserved:', account_file, flush=True)
        print('Use your saved token. If lost, rotate it using roadscan.account_admin.', flush=True)
    print('Open the page, paste your token into Access token, then click Connect.', flush=True)
    print('AI detection requires your own trained D00/D10/D20/D40 checkpoint.', flush=True)
    print('Stop the server with Ctrl+C. Do not expose this starter to the internet.\n', flush=True)
    if not args.no_browser:
        import threading
        threading.Timer(2.0, lambda: webbrowser.open(f'http://127.0.0.1:{args.port}')).start()
    import uvicorn
    uvicorn.run('roadscan.api:app', host='127.0.0.1', port=args.port, reload=False)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
