from pathlib import Path

def test_graphical_editor_contract():
    html=(Path(__file__).resolve().parents[1]/'static'/'index.html').read_text(encoding='utf-8')
    for token in ('drawCanvas','pointerdown','pointerup','drawUndo','drawClass','confidence:1','Save review'):
        assert token in html
