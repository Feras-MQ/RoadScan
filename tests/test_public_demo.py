"""Public demo checks use disposable data only; they are not detector accuracy evidence."""
import hashlib
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from demo.seed_demo import MARKER, SEED_ID, seed


def test_seed_matches_public_workflow_and_api(tmp_path, monkeypatch):
    seed(tmp_path)
    from roadscan import api
    engine = create_engine("sqlite:///" + (tmp_path / "roadscan.db").as_posix(),
                           connect_args={"check_same_thread": False})
    api.BASE.metadata.create_all(engine)
    monkeypatch.setattr(api, "Session", sessionmaker(bind=engine))
    monkeypatch.setattr(api, "STORAGE", tmp_path / "private_uploads")
    monkeypatch.setattr(api, "init_db", lambda: None)
    monkeypatch.setenv("ROADSCAN_API_KEY", "synthetic-public-demo-test-only")
    for name in ("ROADSCAN_ACCOUNTS_FILE", "ROADSCAN_VIEWER_KEY", "ROADSCAN_REVIEWER_KEY"):
        monkeypatch.delenv(name, raising=False)
    headers = {"X-API-Key": "synthetic-public-demo-test-only"}
    try:
        with TestClient(api.app) as client:
            stats = client.get("/api/stats", headers=headers).json()
            assert stats["total"] == 14
            assert stats["by_location"] == {"recorded": 0, "simulated": 10, "none": 4}
            assert {k: v for k, v in stats["by_status"].items() if v} == {
                "Needs Review": 8, "Confirmed": 4, "Assigned": 1, "Resolved": 1}
            assert client.get("/api/reports/map?location=simulated", headers=headers).json()["total"] == 10
            assert client.get("/api/reports/map?location=recorded", headers=headers).json()["total"] == 0
            rows = client.get("/api/reports?size=100", headers=headers).json()["items"]
            for row in rows:
                assert row["source_metadata"]["synthetic_demo"] is True
                assert row["source_metadata"]["capture_location_known"] is False
                assert row["inference_state"] == "not_configured" and row["detections"] == []
                assert row["score"] is None and "SYNTHETIC PUBLIC DEMO" in row["note"]
                assert client.get(row["image_url"], headers=headers).status_code == 200
            row = client.get("/api/reports/public-demo-01", headers=headers).json()
            saved = client.patch("/api/reports/public-demo-01", headers=headers,
                                 json={"revision": row["revision"], "note": "My practice review",
                                       "status": "Confirmed", "action": "confirm"})
            assert saved.status_code == 200
    finally:
        engine.dispose()


def test_restart_preserves_edits_and_files_byte_for_byte(tmp_path):
    seed(tmp_path)
    with sqlite3.connect(tmp_path / "roadscan.db") as connection:
        connection.execute("UPDATE reports SET note='practice edit' WHERE id='public-demo-01'")
    (tmp_path / "my-extra-file.txt").write_text("keep me", encoding="utf-8")
    def hashes():
        return {p.relative_to(tmp_path): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in tmp_path.rglob("*") if p.is_file()}
    before = hashes()
    assert "preserved" in seed(tmp_path)
    assert hashes() == before


def test_refuses_existing_or_incomplete_workspace(tmp_path):
    protected = tmp_path / "existing"
    protected.mkdir()
    sentinel = protected / "roadscan.db"
    sentinel.write_bytes(b"private data must survive")
    with pytest.raises(ValueError, match="nonempty"):
        seed(protected)
    assert sentinel.read_bytes() == b"private data must survive"
    incomplete = tmp_path / "incomplete"
    incomplete.mkdir()
    (incomplete / MARKER).write_text(json.dumps({"seed_id": SEED_ID, "schema_version": 1}))
    with pytest.raises(ValueError, match="Incomplete"):
        seed(incomplete)
    assert not (incomplete / "roadscan.db").exists()


def test_refuses_root_directory():
    from pathlib import Path
    with pytest.raises(ValueError, match="dedicated"):
        seed(Path.cwd().anchor)
