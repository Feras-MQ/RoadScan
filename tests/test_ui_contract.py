from pathlib import Path

def test_review_ui_has_manual_editor_and_audit_controls():
    html=(Path(__file__).resolve().parents[1]/'static'/'index.html').read_text(encoding='utf-8')
    assert 'detectionsEditor' in html
    assert "JSON.parse(document.getElementById('detectionsEditor').value)" in html
    assert "'/sensitivity'" in html
    assert "'/audit'" in html
