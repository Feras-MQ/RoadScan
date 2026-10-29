# SPDX-License-Identifier: AGPL-3.0-only
# Scope: this team contribution; see the accompanying NOTICE.md.
"""Fine-tune the RoadScan YOLO26s on RDD2022 + your hand-labeled road video frames (the recipe that gave road mAP50
0.358 -> 0.533). Settings are locked in RECIPE; read README_FINETUNE.md before changing anything.

    python finetune_road.py --rdd TRAINING_ROOT/RDD_SPLIT --check     # verify data only, no training
    python finetune_road.py --rdd TRAINING_ROOT/RDD_SPLIT             # train 5 epochs, score every epoch, save the best

--frames (default labeled_road_data/video_dataset) holds any number of folders like <name>/images/*.jpg + <name>/labels/*.txt +
<name>/reviewed.txt. Only frames listed in reviewed.txt (checked by a human in label_tool.py) are used.
"""
import argparse
import json
import re
from pathlib import Path

from ultralytics import YOLO
from ultralytics.utils.torch_utils import strip_optimizer

ROOT = Path(__file__).resolve().parent
NAMES = {0: "D00_Longitudinal_Crack", 1: "D10_Transverse_Crack", 2: "D20_Alligator_Crack",
         3: "Other_Corruption", 4: "D40_Pothole"}
FPS_SAMPLED = 5  # extract_frames.py samples every 0.2 s
VIDEO_COPIES = 2400  # ~9% of the 26,868 RDD train images; 240 frames x 10 in the run that worked
# Locked: every value here was tested. See README_FINETUNE.md "What failed" before touching any of them.
RECIPE = dict(
    epochs=5, imgsz=1024, seed=42, save_period=1,
    freeze=10, optimizer="SGD", lr0=0.0005, lrf=0.1, warmup_epochs=0, cos_lr=True,
    mosaic=1.0, close_mosaic=2, mixup=0.1, scale=0.5, translate=0.1, degrees=0.0, fliplr=0.5,
    hsv_s=0.5, cls_pw=0.5, cls_remap=True, amp=True,
)


def labeled_frames(frames_dir: Path) -> list[Path]:
    """Human-reviewed frames from every <folder>/images under frames_dir."""
    out = []
    for images in sorted(frames_dir.glob("*/images")):
        done = images.parent / "reviewed.txt"
        reviewed = set(done.read_text().split()) if done.exists() else set()
        out += [p for p in sorted(images.glob("*.jpg")) if p.stem in reviewed]
    return out


def split_frames(frames: list[Path]) -> tuple[list[Path], list[Path]]:
    """Per video (file prefix before the last '_'), alternate 1-second blocks: 3 to train, 2 to test.
    Neighbouring frames are near-duplicates, so a random split would leak test frames into train."""
    videos: dict[str, list[Path]] = {}
    for p in frames:
        videos.setdefault(p.stem.rsplit("_", 1)[0], []).append(p)
    train, test = [], []
    for video, ps in sorted(videos.items()):
        ps.sort(key=lambda p: int(re.search(r"_(\d+)$", p.stem)[1]))
        for k, p in enumerate(ps):
            (test if (k // FPS_SAMPLED) % 5 >= 3 else train).append(p)
    assert not set(train) & set(test)
    return train, test


def rdd_lists(rdd: Path) -> tuple[list[str], Path]:
    """RDD train image paths from the saved split list, so train/val match the run that gave RDD val 0.366."""
    names = (ROOT / "rdd_split" / "train.txt").read_text().split()
    train = [str(rdd / "train" / "images" / n) for n in names]
    missing = [p for p in train if not Path(p).exists()]
    if missing:
        raise SystemExit(f"{len(missing)}/{len(train)} RDD train images missing, e.g. {missing[0]}")
    val = rdd / "val" / "images"
    want = set((ROOT / "rdd_split" / "val.txt").read_text().split())
    have = {p.name for p in val.glob("*.jpg")}
    if have != want:
        raise SystemExit(f"RDD val is not the original 5,758-image split ({len(have)} found); scores would not compare")
    return train, val


def score(weights, data, name):
    r = YOLO(str(weights)).val(data=str(data), split="val", imgsz=1024, batch=4, workers=0, conf=0.001, iou=0.7,
                               plots=False, verbose=False, project=str(ROOT / "runs" / "evaluations"), name=name,
                               exist_ok=True)
    return {"map50": float(r.box.map50), "map50_95": float(r.box.map),
            "per_class_ap50": {NAMES[int(c)]: float(r.box.class_result(i)[2]) for i, c in enumerate(r.box.ap_class_index)}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rdd", type=Path, required=True, help="RDD_SPLIT folder with train/ val/ (images + labels)")
    ap.add_argument("--frames", type=Path, default=ROOT / "labeled_road_data" / "video_dataset")
    ap.add_argument("--weights", type=Path, default=ROOT / "models" / "1_original_yolo26s_1024.pt",
                    help="start model; keep the MAIN model (README: why not the road model)")
    ap.add_argument("--out", type=Path, default=ROOT / "new_road_model.pt")
    ap.add_argument("--name", default="yolo26s_road_finetune_v2")
    ap.add_argument("--batch", type=int, default=6, help="6 fits 12 GB at imgsz 1024; lower it only for less VRAM")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--device", default="0")
    ap.add_argument("--max-rdd-drop", type=float, default=0.02,
                    help="accept a checkpoint only if RDD val mAP50-95 drops at most this much (v1 dropped 0.014)")
    ap.add_argument("--check", action="store_true", help="build and verify the data lists, then stop")
    a = ap.parse_args()
    if a.out.exists():
        raise SystemExit(f"Refusing to overwrite {a.out}; pass a new --out")

    rdd_train, rdd_val = rdd_lists(a.rdd)
    train, test = split_frames(labeled_frames(a.frames))
    if len(test) < 100:
        raise SystemExit(f"Only {len(test)} test frames; label more video first (label_tool.py)")
    repeat = max(1, round(VIDEO_COPIES / len(train)))
    work = ROOT / "runs" / a.name
    # Data lists live outside runs/<name>: multi-GPU (DDP) training deletes that folder before it starts.
    lists = ROOT / "lists" / a.name
    lists.mkdir(parents=True, exist_ok=True)
    (lists / "rdd_train.txt").write_text("\n".join(rdd_train) + "\n")
    (lists / "video_train.txt").write_text("\n".join(str(p) for p in train for _ in range(repeat)) + "\n")
    (lists / "video_test.txt").write_text("\n".join(map(str, test)) + "\n")
    data, road, rdd = lists / "data.yaml", lists / "road_test.yaml", lists / "rdd_val.yaml"
    for path, tr, va in ((data, [str(lists / "rdd_train.txt"), str(lists / "video_train.txt")], str(rdd_val)),
                         (road, str(lists / "video_test.txt"), str(lists / "video_test.txt")),
                         (rdd, str(rdd_val), str(rdd_val))):
        path.write_text(json.dumps({"train": tr, "val": va, "nc": 5, "names": NAMES}), encoding="utf-8")
    print(f"RDD train {len(rdd_train)} | video train {len(train)} x{repeat} | video test {len(test)}", flush=True)
    if a.check:
        return

    YOLO(str(a.weights)).train(data=str(data), batch=a.batch, workers=a.workers, device=a.device,
                               project=str(ROOT / "runs"), name=a.name, exist_ok=True, plots=True, **RECIPE)

    results = []
    for i, ckpt in enumerate([a.weights, *sorted((work / "weights").glob("epoch*.pt"))]):
        res = {"checkpoint": str(ckpt), "road": score(ckpt, road, f"{a.name}_road_{i}"),
               "rdd": score(ckpt, rdd, f"{a.name}_rdd_{i}")}
        results.append(res)
        print(f"{ckpt.name:28s} road mAP50 {res['road']['map50']:.4f} | RDD val mAP50-95 {res['rdd']['map50_95']:.4f}",
              flush=True)
    (work / "finetune_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    base = results[0]
    ok = [r for r in results[1:] if r["rdd"]["map50_95"] >= base["rdd"]["map50_95"] - a.max_rdd_drop
          and r["road"]["map50"] > base["road"]["map50"]]
    if not ok:
        print("No checkpoint improved the road score within the RDD limit; keeping", a.weights)
        return
    best = max(ok, key=lambda r: r["road"]["map50"])
    strip_optimizer(best["checkpoint"], s=str(a.out))  # drops optimizer state: 31 MB -> 20 MB, same model
    print("Saved", a.out, "from", best["checkpoint"])


if __name__ == "__main__":
    main()
