# RoadScan road fine-tune source

Sanitized source for the team's YOLO26s road fine-tunes; no weights or private data are bundled here. See [NOTICE.md](NOTICE.md) for the exact nine-file AGPL-3.0-only scope and [Source-Manifest.json](Source-Manifest.json) for original/published hashes.

## Contents

- `source/finetune_road.py` and `source/kaggle_finetune.ipynb`: current fine-tuning workflow; notebook pins Ultralytics 8.4.175.
- `source/history/record_of_first_run/`: historical v1 source/config evidence, not an exact-reproduction claim.
- `source/extract_frames.py`, `source/labeled_road_data/label_tool.py`, `source/realtime_video.py`: supplied preparation, annotation and video helpers.
- `source/results/`: saved A/B training configurations.
- `Model-Metadata.json`: four exact checkpoint identities; one existing main model and three new fine-tunes. Weights are not included or promoted.

This is a source release, not a self-contained training dataset or an instruction to retrain before using RoadScan. The training script expects external RDD images, private reviewed frames and split manifests; these are intentionally excluded. Resolve the sanitized TRAINING_ROOT paths before any separate training run. The video helper hardcodes CUDA and is not a CPU portability guarantee.

## Compatibility

All four checkpoints' class IDs are 0=D00, 1=D10, 2=D20, 3=OTHER, 4=D40; image size is 1024. RoadScan's existing name-based mapper passed these mappings and the prior four-class case. On 29 October each checkpoint also completed restricted loading and actual CPU1024 inference on one synthetic image and one supplied road image, sequentially in isolated containers. The three experimental library labels were verified in the browser on 30 October; the main selection was unchanged. These are compatibility checks, not accuracy, throughput or exact-training-reproduction evidence. See the [current audit and release conditions](../../Deliverables/Submission-Audit-2026-10-30.md).

## Evaluation limits

The package's 923 reviewed road frames reconstruct to 580 training and 343 selection frames. Saved A/B test lists match; no exact image-hash duplicate crosses the split, but seven video prefixes are shared and 69 boundaries place adjacent sampled frames on different sides. The road set selects checkpoints and best-F1 confidence thresholds, so its scores are not an untouched independent test. RDD lists contain 26,868 train / 5,758 val / 5,758 test names with no filename overlap; image-level or external-dataset exposure was not verified.

The v1 historical script requires no RDD score drop, but all saved epoch records drop; actual selection/export history is missing. The separate common big-test scoring script is also missing. Parent model filenames are consistent across records but lack historical hash binding. No independent accuracy or timing claim is made.

Collect a separate route/video/session test set; select checkpoints and thresholds on validation data; freeze settings before final evaluation. Preserve upstream terms and remaining original-main provenance questions separately from this narrow source grant.

## Checks

Five Python source files passed syntax parsing; notebook JSON and scoped license markers were checked. `SHA256SUMS.txt` hashes every other file in this folder. No private frames, labels, raw videos, private split lists, credentials or notebook outputs are included.
