# SPDX-License-Identifier: AGPL-3.0-only
# Scope: this team contribution; see the accompanying NOTICE.md.
"""Fine-tune main_yolo26s_1024.pt on RDD + your hand-labeled video frames, keep it only if it is better.

    python finetune_video.py

Keeps the new model only if road-test mAP50 rises AND RDD val mAP50-95 stays >= the current model's.
"""
import json
import re
import shutil
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
VD = ROOT / "video_dataset"
MAIN = ROOT / "roadscan_results" / "weights" / "main_yolo26s_1024.pt"
OUT = ROOT / "roadscan_results" / "weights" / "main_yolo26s_1024_road.pt"
RDD_YAML = ROOT / "roadscan_results" / "yolo26s_finetune_full_rdd2022.yaml"
RDD_TRAIN = ROOT / "roadscan_results" / "data_audits" / "train_images_unique.txt"
RUN, RUNS = "yolo26s_road_finetune", ROOT / "roadscan_results" / "runs"
NAMES = {0: "D00_Longitudinal_Crack", 1: "D10_Transverse_Crack", 2: "D20_Alligator_Crack",
         3: "Other_Corruption", 4: "D40_Pothole"}
BLOCK_SEC, FPS_SAMPLED = 1, 5  # frames were sampled every 0.2 s
REPEAT = 10  # ~230 frames vs ~27k RDD images: repeat so they matter (augmentation varies each copy)


def split_frames():
    """Alternate 1-second blocks (3 train, 2 test) per video so every class lands in both sets."""
    train, test = [], []
    for video in ("mov", "wa"):
        frames = sorted(VD.glob(f"*/images/{video}_*.jpg"), key=lambda p: int(re.search(r"_(\d+)$", p.stem)[1]))
        for k, p in enumerate(frames):
            (test if (k // (BLOCK_SEC * FPS_SAMPLED)) % 5 >= 3 else train).append(p)
    return train, test


def write_yaml(name, train, val):
    path = VD / f"{name}.yaml"
    path.write_text(json.dumps({"train": train, "val": val, "nc": 5, "names": NAMES}), encoding="utf-8")
    return path


def score(weights, data, name):
    r = YOLO(str(weights)).val(data=str(data), split="val", imgsz=1024, batch=4, workers=0, device=0, conf=0.001,
                               iou=0.7, plots=False, verbose=False, project=str(RUNS / "evaluations"), name=name,
                               exist_ok=True)
    return {"map50": float(r.box.map50), "map50_95": float(r.box.map),
            "per_class_ap50": {NAMES[int(c)]: float(r.box.class_result(i)[2]) for i, c in enumerate(r.box.ap_class_index)}}


def main():
    train, test = split_frames()
    assert train and test and not set(train) & set(test)
    (VD / "split_train.txt").write_text("\n".join(map(str, train)) + "\n")
    (VD / "split_test.txt").write_text("\n".join(map(str, test)) + "\n")
    (VD / "split_train_x10.txt").write_text("\n".join(str(p) for p in train for _ in range(REPEAT)) + "\n")
    road = write_yaml("road_test", str(VD / "split_test.txt"), str(VD / "split_test.txt"))
    data = write_yaml("rdd_plus_road", [str(RDD_TRAIN), str(VD / "split_train_x10.txt")],
                      str(ROOT / "rdd2022_raw" / "RDD_SPLIT" / "val" / "images"))
    print(f"video frames: train {len(train)}, test {len(test)}", flush=True)

    YOLO(str(MAIN)).train(
        data=str(data), epochs=5, imgsz=1024, batch=6, workers=1, device=0, project=str(RUNS), name=RUN,
        exist_ok=True, save_period=1, plots=True, seed=42,
        # Gentle: frozen backbone + low LR; unfrozen lr0=1e-3 drifted RDD val 0.366 -> 0.350 (v2 run).
        freeze=10, optimizer="SGD", lr0=0.0005, lrf=0.1, warmup_epochs=0, cos_lr=True,
        # Rest matches the main run (runs/main_yolo26s_1024/args.yaml).
        mosaic=1.0, close_mosaic=2, mixup=0.1, scale=0.5, translate=0.1, degrees=0.0, fliplr=0.5,
        hsv_s=0.5, cls_pw=0.5, cls_remap=True, amp=True,
    )

    candidates = [MAIN, *sorted((RUNS / RUN / "weights").glob("epoch*.pt"))]
    results = []
    for i, ckpt in enumerate(candidates):
        res = {"checkpoint": str(ckpt), "road": score(ckpt, road, f"road_{i}"), "rdd": score(ckpt, RDD_YAML, f"rdd_{i}")}
        results.append(res)
        print(f"{ckpt.name:28s} road mAP50 {res['road']['map50']:.4f} | RDD val mAP50-95 {res['rdd']['map50_95']:.4f}",
              flush=True)
    (VD / "finetune_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    base = results[0]
    ok = [r for r in results[1:] if r["rdd"]["map50_95"] >= base["rdd"]["map50_95"]
          and r["road"]["map50"] > base["road"]["map50"]]
    if not ok:
        print("No checkpoint beat the current model on both road test and RDD val; keeping", MAIN)
        return
    best = max(ok, key=lambda r: r["road"]["map50"])
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite existing checkpoint: {OUT}")
    shutil.copy2(best["checkpoint"], OUT)
    print("Saved", OUT, "from", best["checkpoint"])


if __name__ == "__main__":
    main()
