# SPDX-License-Identifier: AGPL-3.0-only
# Scope: this team contribution; see the accompanying NOTICE.md.
"""Cut a road video into frames (every 0.2 s) with model pre-labels, ready to correct in label_tool.py.

    python extract_frames.py "my drive.mp4" drive3        # -> <frames>/drive3/images + labels
    cd labeled_road_data && python label_tool.py drive3

The key (drive3) must be new: it names the frames (drive3_00012.jpg) and finetune_road.py splits train/test per key.
"""
import argparse
import re
from pathlib import Path

import cv2
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
STEP_SEC = 0.2  # finetune_road.py assumes 5 frames per second (FPS_SAMPLED)
MAX_SIDE = 1920  # the labeled frames were 1920x1080; 4K adds nothing at imgsz 1024

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("key", help="short unique name for this video, letters/digits only")
ap.add_argument("--frames", type=Path, default=ROOT / "labeled_road_data" / "video_dataset")
ap.add_argument("--weights", default=str(ROOT / "models" / "2_road_v1_yolo26s_1024_RECOMMENDED.pt"))
a = ap.parse_args()
if not re.fullmatch(r"[A-Za-z0-9]+", a.key):
    raise SystemExit("key must be letters/digits only (no '_' or spaces)")
if list(a.frames.glob(f"*/images/{a.key}_*.jpg")):
    raise SystemExit(f"key '{a.key}' already used in {a.frames}; pick another")

out = a.frames / a.key
(out / "images").mkdir(parents=True, exist_ok=True)
(out / "labels").mkdir(parents=True, exist_ok=True)
model = YOLO(a.weights)
cap = cv2.VideoCapture(a.video)
n, fps = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), cap.get(cv2.CAP_PROP_FPS)
if n <= 0 or fps <= 0:
    raise SystemExit(f"cannot read {a.video}")
count = 0
for i in range(0, n, max(1, round(fps * STEP_SEC))):
    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
    ok, f = cap.read()
    if not ok:
        continue
    if max(f.shape[:2]) > MAX_SIDE:
        s = MAX_SIDE / max(f.shape[:2])  # keep aspect ratio (phone videos may be portrait)
        f = cv2.resize(f, (round(f.shape[1] * s), round(f.shape[0] * s)), interpolation=cv2.INTER_AREA)
    name = f"{a.key}_{i:05d}"
    cv2.imwrite(str(out / "images" / f"{name}.jpg"), f)
    r = model.predict(f, imgsz=1024, conf=0.35, iou=0.6, augment=True, verbose=False)[0]
    (out / "labels" / f"{name}.txt").write_text("".join(
        f"{int(c)} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n" for c, (x, y, w, h) in zip(r.boxes.cls.tolist(), r.boxes.xywhn.tolist())))
    count += 1
print(f"{count} frames -> {out}. Pre-labels are model guesses: review every frame in label_tool.py before training.")
