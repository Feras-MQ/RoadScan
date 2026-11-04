"""Create a separate public workflow demo; never import or overwrite a real workspace."""
import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from roadscan.core import BASE, Audit, History, Report, phash
from roadscan.workflow import ACTIONS, validate_transition


SEED_ID = "roadscan-public-synthetic-demo-v1"
MARKER = "public-demo-v1.json"
ACTOR = "synthetic-demo-script"
# Staged public-road coordinates from the November 3 demo, not capture GPS.
# OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright
ROWS = [
    (24.4749137, 39.6053234, "Needs Review"),
    (24.4700231, 39.6017743, "Confirmed"),
    (24.4775266, 39.6110416, "Assigned"),
    (24.4765971, 39.6060646, "Needs Review"),
    (24.4770970, 39.6046631, "Needs Review"),
    (24.4695353, 39.6047120, "Confirmed"),
    (24.4671053, 39.6015531, "Resolved"),
    (24.4738255, 39.6064816, "Needs Review"),
    (None, None, "Needs Review"),
    (None, None, "Needs Review"),
    (None, None, "Confirmed"),
    (None, None, "Confirmed"),
    (24.4749137, 39.6053234, "Needs Review"),
    (24.4749137, 39.6053234, "Needs Review"),
]


def illustration(number):
    """Original procedural artwork with its qualification burned into the pixels."""
    image = Image.new("RGB", (960, 600), "#d6e6e1")
    draw = ImageDraw.Draw(image)
    draw.polygon([(310, 95), (650, 95), (940, 520), (20, 520)], fill="#525c62")
    draw.line([(480, 115), (480, 490)], fill="#e3c96a", width=9)
    offset = (number % 5) * 25
    draw.line([(230 + offset, 370), (280 + offset, 320), (310 + offset, 355),
               (350 + offset, 290), (375 + offset, 310)], fill="#24292d", width=7)
    draw.rectangle((0, 0, 959, 94), fill="#122c33")
    draw.rectangle((0, 520, 959, 599), fill="#122c33")
    font = ImageFont.load_default(size=25)
    small = ImageFont.load_default(size=20)
    draw.text((24, 18), f"SYNTHETIC PUBLIC DEMO / EXAMPLE {number:02d}", font=font, fill="white")
    draw.text((24, 54), "Illustration only. No camera capture or model inference.", font=small, fill="white")
    draw.text((24, 535), "Staged workflow status; no actual inspection or repair claimed.", font=small, fill="white")
    draw.text((24, 565), "Any map pin is SIMULATED, never this image's capture location.", font=small, fill="white")
    return image


def seed(data_dir):
    data_dir = Path(data_dir)
    if data_dir.is_symlink() or data_dir.resolve() == Path(data_dir.anchor):
        raise ValueError("Choose a dedicated empty demo directory, not a root or symlink.")
    data_dir.mkdir(parents=True, exist_ok=True)
    marker = data_dir / MARKER
    database = data_dir / "roadscan.db"
    storage = data_dir / "private_uploads"
    if marker.is_file():
        try:
            identity = json.loads(marker.read_text(encoding="utf-8"))
            if identity.get("seed_id") != SEED_ID or identity.get("schema_version") != 1:
                raise ValueError("Unrecognized demo marker.")
            if not database.is_file() or not storage.is_dir():
                raise ValueError("Demo database or image directory is missing.")
            with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as connection:
                connection.execute("SELECT id FROM reports LIMIT 1").fetchall()
        except (ValueError, AttributeError, sqlite3.Error) as exc:
            raise ValueError("Incomplete or invalid demo directory; nothing was overwritten.") from exc
        return "Existing public demo preserved; no reports or images changed."
    if any(data_dir.iterdir()):
        raise ValueError("Refusing to seed a nonempty, unmarked directory. Existing data is preserved.")

    # Atomic exclusive claim also prevents two initializers from seeding the same empty volume.
    lock = data_dir / ".seed-in-progress"
    lock.mkdir()
    storage.mkdir()
    engine = create_engine("sqlite:///" + database.resolve().as_posix())
    try:
        BASE.metadata.create_all(engine)
        with Session(engine) as session, session.begin():
            for index, (latitude, longitude, target) in enumerate(ROWS, start=1):
                rid = f"public-demo-{index:02d}"
                filename = rid + ".jpg"
                timestamp = datetime(2026, 11, 3, 12, tzinfo=timezone.utc) + timedelta(minutes=index)
                with illustration(index) as image:
                    image.save(storage / filename, "JPEG", quality=90)
                    image_hash = phash(image)
                note = (f"SYNTHETIC PUBLIC DEMO {index:02d} | Original procedural illustration; "
                        "no detector was run, and empty boxes do not establish absence of damage. "
                        "Scripted workflow status only: no actual inspection, dispatch or repair. "
                        + ("SIMULATED Madinah pin, not capture GPS. " if latitude is not None else "No location supplied. ")
                        + "Do not use these fixtures for model training or accuracy evaluation.")
                metadata = {
                    "synthetic_demo": True,
                    "seed_id": SEED_ID,
                    "capture_location_known": False,
                    "workflow_status_is_scripted": True,
                    "initial_prediction": {"state": "not_configured", "model_version": "not_configured",
                                           "detections": [], "reason": "Synthetic fixture; detector not run."},
                }
                report = Report(id=rid, image_ref=filename,
                                image_sha=hashlib.sha256((storage / filename).read_bytes()).hexdigest(),
                                image_phash=image_hash, created_at=timestamp, updated_at=timestamp,
                                status="Needs Review", source="synthetic_demo", source_metadata=json.dumps(metadata),
                                latitude=latitude, longitude=longitude,
                                location_source="simulated" if latitude is not None else "not_provided",
                                model_version="not_configured", inference_state="not_configured",
                                detections="[]", score=None, score_parts="{}", duplicates="[]", note=note)
                session.add(report)
                session.add(Audit(report_id=rid, actor=ACTOR, action="seed_demo", created_at=timestamp,
                                  details=json.dumps({"synthetic": True, "detector_run": False})))
                session.add(History(report_id=rid, to_status="Needs Review", actor=ACTOR, created_at=timestamp))
                stages = [] if target == "Needs Review" else ["Confirmed"]
                if target in {"Assigned", "Resolved"}:
                    stages.append(target)
                for stage in stages:
                    previous = report.status
                    validate_transition(previous, stage, ACTIONS[stage])
                    report.status = stage
                    report.reviewer = ACTOR
                    session.add(History(report_id=rid, from_status=previous, to_status=stage,
                                        actor=ACTOR, created_at=timestamp))
                    session.add(Audit(report_id=rid, actor=ACTOR, action=ACTIONS[stage], created_at=timestamp,
                                      details=json.dumps({"synthetic": True, "scripted_status_only": True})))
        marker.write_text(json.dumps({"seed_id": SEED_ID, "schema_version": 1, "initial_reports": 14,
                                      "simulated_pins": 10}, indent=2) + "\n", encoding="utf-8")
        lock.rmdir()
    finally:
        engine.dispose()
    return "Created 14 synthetic reports with 10 simulated Madinah pins; no detector predictions."


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, type=Path, help="Dedicated empty demo data directory")
    args = parser.parse_args(argv)
    try:
        print(seed(args.data_dir))
    except (ValueError, OSError) as exc:
        parser.exit(1, str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
