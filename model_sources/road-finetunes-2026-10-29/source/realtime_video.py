# SPDX-License-Identifier: AGPL-3.0-only
# Scope: this team contribution; see the accompanying NOTICE.md.
"""Run the main YOLO26s on a video; --show opens a live window (press q to quit)."""
import argparse, time
from pathlib import Path
import cv2
from ultralytics import YOLO

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--weights", default="models/2_road_v1_yolo26s_1024_RECOMMENDED.pt")
ap.add_argument("--conf", type=float, default=0.25)
ap.add_argument("--imgsz", type=int, default=1024)
ap.add_argument("--show", action="store_true")
ap.add_argument("--out", default="video_frames/detected.mp4")
a = ap.parse_args()

model = YOLO(a.weights)
cap = cv2.VideoCapture(a.video)
fps = cap.get(cv2.CAP_PROP_FPS)
W, H = 1920, 1080  # 4K output would be huge; downscale for display/saving
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
out = cv2.VideoWriter(a.out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
counts, n, t0 = {}, 0, time.time()
while True:
    ok, frame = cap.read()
    if not ok:
        break
    r = model.predict(frame, imgsz=a.imgsz, conf=a.conf, iou=0.6, device=0, half=True, verbose=False)[0]
    for c in r.boxes.cls.tolist():
        counts[model.names[int(c)]] = counts.get(model.names[int(c)], 0) + 1
    img = cv2.resize(r.plot(line_width=3), (W, H))
    n += 1
    cv2.putText(img, f"{n / (time.time() - t0):.0f} FPS", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
    out.write(img)
    if a.show:
        cv2.imshow("RoadScan", cv2.resize(img, (1280, 720)))
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
out.release()
print(f"{n} frames, {n / (time.time() - t0):.1f} FPS processing (video is {fps:.0f} FPS)")
print("detections:", counts)
