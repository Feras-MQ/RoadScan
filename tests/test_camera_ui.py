from pathlib import Path

HTML = (Path(__file__).resolve().parents[1] / "static" / "index.html").read_text(encoding='utf-8')


def test_camera_controls_and_mobile_fallback():
    for item in ('capture="environment"', 'cameraStart', 'cameraSwitch', 'cameraCapture', 'cameraStop', 'cameraVideo'):
        assert item in HTML


def test_camera_permissions_and_stream_cleanup():
    assert 'navigator.mediaDevices.getUserMedia' in HTML
    assert 'getTracks().forEach(track=>track.stop())' in HTML
    assert "window.addEventListener('pagehide'" in HTML
    assert 'video:{facingMode:{ideal:cameraFacing}}' in HTML


def test_camera_capture_used_for_upload_and_discardable():
    assert "capturedFile||document.getElementById('photo').files[0]" in HTML
    assert 'canvas.toBlob(' in HTML
    assert 'URL.revokeObjectURL(capturedUrl)' in HTML
    assert "document.getElementById('photo').addEventListener('change'" in HTML
