# Team models and experiments — 24 October 2026

Feras Alyamani · Ahmed Salamah · Ahmed Alhejaili

## What was received and integrated

The supplied archive contains 203 entries, eight checkpoints, experiment CSVs, run settings, plots and split/cleaning audits. It contains **no Python training scripts or notebooks**. All original entries are preserved in `Models/RoadScan-Team-Results-2026-10-24.zip`; an import index adds checksum-bound metrics and the main model's validation thresholds. The untouched original is retained in the release archive.

Seven checkpoints are box detectors and appear in Settings. `baseline_resnet18.pt` is an image-level multi-label classifier, preserved for E1; it is intentionally not offered as a box detector. No retraining occurred during integration.

## How many images?

The supplied training narrative reports **26,869 RDD training images**, **5,758 validation**, and **5,758 test** images. The main YOLO26s run adds approximately **14,000 external training images**, so its training pool is approximately **41,000 images**, not an independently counted exact total. The raw dataset/manifests were not supplied. Ablations use their own run settings; the India-held-out run excludes India, so do not claim every model used 41,000.

The main run reports 120 epochs, best validation epoch 84, and 1024-pixel input. Extra sources include Rome potholes, HRP4K, SVRDD Beijing and web data. The supplied split audit reports near-duplicate leakage of 2.2% in validation and 2.4% in test; test performance may be optimistic. Check source licenses before redistribution.

## Detection results (supplied, not independently reproduced)

| Model | Evaluation split | mAP50 | mAP50–95 |
|---|---|---:|---:|
| YOLO26s Main, 1024 | RDD test | 63.04% | 33.01% |
| YOLO26s Size experiment, 640 | RDD test | 59.43% | 30.71% |
| YOLO26n Size experiment, 640 | RDD test | 55.99% | 28.03% |
| YOLO26s No augmentation, 640 | RDD test | 46.93% | 21.76% |
| YOLO26s Vertical flip, 640 | RDD test | 58.48% | 30.14% |
| YOLO26s Cleaned labels, 640 | RDD test | 60.05% | 30.73% |
| YOLO26s India held out, 640 | India test only | 8.86% | 3.77% |

mAP measures detection quality, not the percentage of images classified correctly. Main per-class AP50: D00 63.55%, D10 62.52%, D20 69.90%, D40 56.19%. Main external mAP50/mAP50–95: HRP4K 53.00/31.04%, Rome 35.07/14.49%, web 82.13/51.93%, SVRDD 67.63/38.85%; these are distinct test sets, not directly interchangeable accuracy claims.

E1 (image-presence evaluation, 5,758 images): ResNet18 any-damage F1 .893 / accuracy .869; main YOLO26s F1 .929 / accuracy .913. Per-class F1: ResNet .790/.751/.805/.639; detector .861/.805/.859/.762. E1 thresholds differ from box-detection thresholds.

E2: small beats nano on the supplied same-split detection metrics, while nano is faster in the local diagnostic. E3: standard augmentation beats no augmentation by 12.50 mAP50 points; vertical flips do not improve the standard run. Clean-label training marginally lowers validation mAP50–95 (.3403 vs .3421), so the main run retained original labels. E4: India-held-out mAP50 .0886 versus .3925 when India is included in the comparison model's training; domain shift is substantial.

E5 uses simulated duplicate observations and GPS: F0.5 is .851 for pHash+GPS, .975 for ResNet50+GPS, .980 for DINOv2+GPS, and .796 for DINOv2 without GPS. DINOv2+GPS reports precision .983, hard-repeat recovery .951, and new-report false merge .032 (without GPS .137). These are supplied experiment results, **not current app duplicate accuracy**; the app now offers a separate replacement DINOv2 crop search alongside dHash; its threshold is not yet calibrated. DINOv2 threshold .6529684 with 50 m candidates must never be applied to hash similarity.

## Calibration and selecting a model

Main thresholds: D00 .173, D10 .166, D20 .195, D40 .056; chosen on validation at 1024 pixels (F1 for cracks, F2 for potholes). The low pothole threshold favors recall and requires review. OTHER is excluded. Balanced/live mode uses reduced input sizes and has not been recalibrated. Other supplied detectors retain the app's default confidence until their own validated profiles are supplied.

Use **YOLO26s · Main · 1024 px** for detailed images; try **YOLO26n · Size experiment · 640 px** for a faster live preview. This is a speed/quality tradeoff, not proof that one model is best on your phone/drone footage. Model voting supports choosing an individual minority model; voting is slower and cannot guarantee correctness. Corrections enter an approved export, then separate training/evaluation; weights do not learn instantly.

## Local integration checks

216 backend tests passed, one optional test skipped; 18 frontend tests passed; TypeScript/Vite build passed. Seven checkpoints passed restricted loading, activation and actual CPU inference. Main thresholds are preserved in regular inference and isolated voting jobs. A synthetic report exercised upload, saved timing, human review, priority explanation and all eight sensitivity cases; English and Arabic UI checked. No real-image accuracy evaluation was rerun.

Three warm requests on one synthetic 960×640 image, Docker limited to 2 CPUs / 4 GiB: median model time nano640 57.89 ms, small640 122.38 ms, main Balanced640 124.74 ms, main Detail1024 298.94 ms. These are diagnostic model timings; not end-to-end camera FPS or representative field latency.

## Replacement implementation update

Read Replacement-Tools.md for the new training/evaluation runner, ResNet18 workflow, dataset-ranking sensitivity and DINOv2/FAISS/GPS app search. Original supplied training results remain unchanged; no full retraining or new real-road accuracy evaluation was performed.
