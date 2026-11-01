"""Runs before any test module imports roadscan: tests must never touch the real workspace database or uploads."""
import os, tempfile
from pathlib import Path

_root = Path(tempfile.mkdtemp(prefix='roadscan-tests-'))
os.environ['DATABASE_URL'] = 'sqlite:///' + (_root / 'roadscan.db').as_posix()
os.environ['ROADSCAN_STORAGE'] = str(_root / 'uploads')
