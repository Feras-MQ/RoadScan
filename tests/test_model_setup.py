import hashlib
import json
from pathlib import Path
import pytest
from roadscan.model_setup import install, configured_checkpoint


def test_install_and_reopen(tmp_path):
    src = tmp_path / 'best.pt'
    src.write_bytes(b'fixture only, never loaded')
    root = tmp_path / 'app'
    out = install(src, root)
    assert out['sha256'] == hashlib.sha256(src.read_bytes()).hexdigest()
    assert Path(configured_checkpoint(root)).read_bytes() == src.read_bytes()


def test_refuses_overwrite(tmp_path):
    src = tmp_path / 'best.pt'; src.write_bytes(b'fake')
    install(src, tmp_path / 'app')
    with pytest.raises(FileExistsError):
        install(src, tmp_path / 'app')


def test_detects_tamper(tmp_path):
    src = tmp_path / 'best.pt'; src.write_bytes(b'fake')
    root = tmp_path / 'app'; install(src, root)
    (root / 'models' / 'roadscan_best.pt').write_bytes(b'changed')
    with pytest.raises(ValueError, match='hash changed'):
        configured_checkpoint(root)


def test_refuses_path_change(tmp_path):
    src = tmp_path / 'best.pt'; src.write_bytes(b'fake')
    root = tmp_path / 'app'; install(src, root)
    config = root / 'local_model.json'; data = json.loads(config.read_text())
    data['checkpoint'] = '../bad.pt'; config.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='inside'):
        configured_checkpoint(root)


def test_requires_checkpoint(tmp_path):
    assert configured_checkpoint(tmp_path) is None
    with pytest.raises(FileNotFoundError):
        install(tmp_path / 'missing.pt', tmp_path / 'app')
