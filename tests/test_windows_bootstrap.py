from pathlib import Path
from roadscan.windows_bootstrap import install_if_needed


def test_install_once_then_skip(tmp_path):
    (tmp_path / 'requirements.txt').write_text('fastapi\n')
    calls = []
    def runner(*args, **kwargs):
        calls.append((args, kwargs))
    assert install_if_needed(tmp_path, python='python.exe', runner=runner)
    assert not install_if_needed(tmp_path, python='python.exe', runner=runner)
    assert len(calls) == 1
    assert calls[0][0][0][:4] == ['python.exe', '-m', 'pip', 'install']


def test_reinstall_after_requirements_change(tmp_path):
    f = tmp_path / 'requirements.txt'
    f.write_text('fastapi\n')
    calls = []
    runner = lambda *a, **kw: calls.append(a)
    install_if_needed(tmp_path, python='python.exe', runner=runner)
    f.write_text('fastapi\nuvicorn\n')
    assert install_if_needed(tmp_path, python='python.exe', runner=runner)
    assert len(calls) == 2


def test_failed_install_does_not_write_marker(tmp_path):
    import subprocess
    import pytest
    (tmp_path / 'requirements.txt').write_text('bad-dep\n')
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0])
    with pytest.raises(subprocess.CalledProcessError):
        install_if_needed(tmp_path, python='python.exe', runner=fail)
    assert not (tmp_path / '.venv' / '.roadscan_requirements_sha256').exists()
