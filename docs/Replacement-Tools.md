# Replacement tools — 24 October 2026, release 2026-10-24.2

These are newly implemented replacements, **not recovered copies of your teammate's source**. His original weights/results remain unchanged. A full new training run and real-road accuracy evaluation have not been performed.

## Use the new feature

1. Upload a photo with coordinates (use the location option on Overview).
2. Save at least one correctly placed damage box.
3. Open its review → **Same damage, another report?** → **Find nearby matches**.

The app extracts DINOv2 ViT-S/14 embeddings from damage crops, searches an exact FAISS index, and compares open reports within 50 m. It excludes the same report, resolved/duplicate reports, distant reports, and reports with a different location source. The first search computes embeddings; later requests reuse a private, content-and-checkpoint-keyed cache. The index is rebuilt from eligible cached vectors so closed reports cannot remain as stale index matches. Searches run on request, not for every live-camera frame; CPU contention can still slow preview during a search.

Similarity 0.80 is an **experimental, uncalibrated threshold**, not 80% accuracy. It is intentionally different from the teammate's simulated benchmark threshold because the replacement crop/preprocessing pipeline is not verified identical. Search requires coordinates and boxes; it never invents GPS or merges reports automatically. Limit: 100 nearby reports and 20 boxes per report per search. Match IDs can be located with Review queue search. Existing automatic dHash suggestions remain a separate lightweight feature and now exclude resolved reports too.

## Replacement source map

| Entry point | What it does |
|---|---|
| priority.py | Uses the exact app formula; exports each report's eight ±20% weight variations plus dataset ranking shifts and top-50 overlap |
| duplicate_finder.py | Runs the same DINOv2 / FAISS / GPS matcher on explicit local JSON records |
| accuracy_report.py | Evaluates a local YOLO checkpoint on a declared validation or test split; reports four damage classes separately from OTHER; only validation generates F1/F2 thresholds |
| roadscan/resnet_baseline.py | Evaluates or fine-tunes the supplied ResNet18 classifier; best epoch and thresholds use validation, final reporting uses test |
| roadscan/detector_train.py | Audits four-class local train/val data; trains with explicit seed/device and standard, no-augmentation or vertical-flip settings; reports validation metrics |
| runpod/run_all.py | Runs an explicit JSON experiment plan sequentially, recording logs and completion records; dry-run by default |
| roadscan/retrieval_eval.py | Existing pHash / ResNet18 / DINOv2 retrieval evaluator with Recall@1/5; use labelled damage-crop manifests for crop retrieval experiments |

## Running experiments

Start from `runpod/plan.example.json` and set actual local dataset/checkpoint paths. From the source directory:

`python runpod/run_all.py --plan runpod/plan.example.json --output experiments/runner`

This prints the planned jobs without training or allocating cloud resources. Add `--execute` only when the data, seeds, model initialization and outputs have been checked. It can run inside an already configured RunPod machine; it does not rent a GPU, download datasets with unknown licensing, or recover the teammate's exact historical run. CPU is the detector default; GPU options are available but were not tested on this laptop. ResNet uses `cuda` for a GPU; Ultralytics accepts its usual device identifiers.

Completed jobs can be reused only with unchanged plan, code and input fingerprints. A failed job is not silently overwritten or resumed mid-epoch: preserve/rename its partial output or choose new job output paths. Keep outputs outside dataset directories. Completion records are execution evidence, not proof that labels or dataset splits are correct; keep the produced results/weights with them.

Detector training layout: `ROOT/train/images`, `ROOT/train/labels`, `ROOT/val/images`, `ROOT/val/labels`; final test data stays outside this root. Class order is **0 D00, 1 D10, 2 D20, 3 D40**. External five-class labels must be remapped explicitly; do not interpret class 3 OTHER as pothole. The separate evaluator accepts a local YOLO YAML with the checkpoint's exact class order, including optional OTHER. Download scripts in dataset YAML are rejected. Exact train/val duplicates are rejected by the trainer; near-duplicate/group/country leakage still requires its own audit.

ResNet CSV: `image,split,D00,D10,D20,D40`, with 0/1 labels and `train`, `validation`, `test` split names. Paths are relative to the image root; exact cross-split duplicates are rejected. `--epochs 0` evaluates; positive epochs fine-tune an existing compatible four-output checkpoint. Resize, normalization and class order are recorded. This preprocessing is a documented replacement, not verified byte-for-byte reproduction of the teammate's missing transform code.

Priority JSON: a list of `{id,width,height,detections}` records; each detection has `{class_id,box:[x1,y1,x2,y2],confidence}` in original image pixels. Example: `python priority.py --input reports.json --output priority-results.json`.

Duplicate CLI query is one JSON record; gallery is a list. Fields: `id,status,gps:[latitude,longitude],location_source,image,detections`. Image paths must refer to your authorized local files. Pass `--query`, `--gallery`, `--checkpoint`, `--cache`, `--output`; radius defaults to 50 m. Set `PYTHONPATH` to include the source and its `third_party` directory, or use the detector-enabled Docker image where it is already configured.

## Evidence and limitations

216 backend tests and 18 frontend tests passed before final packaging checks. Real DINOv2 weights loaded; actual FAISS search matched identical synthetic crops at 11.1 m and rejected far/closed/different-source cases. This is software evidence, not field duplicate precision. The recorded fast request reused a previously computed embedding cache; it is not cold-start latency.

A synthetic one-epoch ResNet fine-tuning check exercised saved weights, validation thresholds and test reporting; detector validation/test evaluation and priority ranking also ran on synthetic inputs. Those synthetic weights and metrics are retained only in the working archive and are **not deployed or presented as project accuracy**. No full RDD retraining or real Saudi test evaluation occurred.

Gemini Flash-Lite (signed-out browser) reviewed four newly authored modules without private data. Defensive index/checkpoint checks were accepted; its suggestion to overwrite existing output directories was rejected to preserve results. This was not an Argon/Pro or Astra Ultra audit.

Official DINOv2 source is pinned to commit `7764ea0f912e53c92e82eb78a2a1631e92725fc8`; Apache-2.0 license is included under `third_party/dinov2`. The official pretrained backbone SHA-256 is `b938bf1bc15cd2ec0feacfe3a1bb553fe8ea9ca46a7e1d8d00217f29aef60cd9`. FAISS CPU is pinned to 1.15.1. The portable package includes the backbone; source-only builds download and verify it. This pretrained backbone is not a new RoadScan-trained model.

Remaining requirements: genuine Saudi test photos/labels and repeat pairs, calibrated duplicate threshold/ROC analysis, representative CPU latency, repaired split leakage, source data licenses/consent, privacy-redaction work, and final contributions/presentation/submission evidence. Replacement scripts provide a reproducible new workflow; they cannot prove the provenance of historical runs without their original data and source.
