"""Offline-safe repeat startup: install requirements only when changed."""
import hashlib
import subprocess
import sys
from pathlib import Path


def requirements_fingerprint(root):
    return hashlib.sha256((Path(root) / 'requirements.txt').read_bytes()).hexdigest()


def install_if_needed(root, python=None, runner=subprocess.run):
    root = Path(root)
    python = str(python or sys.executable)
    marker = root / '.venv' / '.roadscan_requirements_sha256'
    digest = requirements_fingerprint(root)
    if marker.exists() and marker.read_text(encoding='ascii').strip() == digest:
        return False
    runner([python, '-m', 'pip', 'install', '-r', str(root / 'requirements.txt')], check=True, cwd=str(root))
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(digest + '\n', encoding='ascii')
    return True


def main():
    root = Path(__file__).resolve().parent.parent
    try:
        installed = install_if_needed(root)
    except (OSError, subprocess.CalledProcessError) as exc:
        print('Dependency setup failed:', exc, file=sys.stderr)
        return 1
    print('Dependencies installed.' if installed else 'Dependencies already installed; starting immediately.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
