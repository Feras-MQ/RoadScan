# RoadScan model report

28 October 2026 | Submission deadline: 31 October 2026


## RoadScan | Model report

All 19 model assets - evidence review dated 28 October 2026

Prepared for the 31 October 2026 submission. This report identifies every retained checkpoint, explains what each model does, and separates historical results from current software checks. It supplements the original project report; it does not replace or revise its experiments.

| Role | Count | Purpose |
| --- | --- | --- |
| Trained road detectors | 16 | 12 YOLO and 4 RT-DETR checkpoints locate damage with boxes. |
| ResNet18 classifier | 1 | Predicts image-level presence of four damage labels; no boxes. |
| Stock COCO YOLO11n | 1 | Official initialization checkpoint; not road-damage-trained. |
| DINOv2 ViT-S/14 | 1 | Official pretrained feature backbone for visual retrieval. |

### Evidence at a glance

The 19 distinct SHA-256 identities total 1,562,050,919 bytes (about 1.56 GB decimal). All assets are team-approved for public publication, including the formerly restricted top five. The unchanged DINOv2 weight is published with its license packet and checksum file; the 17 trained assets still have release conditions. Stock COCO uses its official upstream route. Check the live inventory for current downloads.

The full common-set benchmark has not started: 14 of 16 detectors completed 20-image preflights and zero completed the full evaluation. Historical baseline US test, teammate validation, YOLO26 RDD test and India-only results have different scopes. They do not establish a comparable ranking across all models.

### Class identities must follow the checkpoint

| Map | Index order | Interpretation |
| --- | --- | --- |
| Four-class detector | 0 D00; 1 D10; 2 D20; 3 D40 | Longitudinal, transverse, alligator cracks; potholes. |
| Five-class detector | 0 D00; 1 D10; 2 D20; 3 OTHER; 4 D40 | OTHER is an additional training label; pothole index changes. |

The YOLO26 supplied detection results average the four damage classes, excluding OTHER, although their checkpoints have five outputs. Imported validation averages must retain their original scope; the supplied index does not establish an identical class-averaging protocol for every model. Never treat class 3 as pothole in a five-class checkpoint.

mAP50 is average precision at 0.50 intersection-over-union; mAP50-95 averages across stricter overlap thresholds. Neither is the percentage of photographs classified correctly. See the [metric guide](https://docs.ultralytics.com/guides/yolo-performance-metrics).

Asset identities, exact byte sizes and full 64-character hashes: [CSV inventory](public-model-inventory.csv), [JSON inventory](public-model-inventory.json). Class/configuration evidence: [detector map](detector-config-provenance-map.json).


## 01 | Training and checkpoint provenance

What the available records establish - and what they do not

### Original RoadScan baseline

| Model / SHA-256 prefix | Size | Configuration | Independent US test |
| --- | --- | --- | --- |
| YOLO11n baseline<br>2bb146ad53a3 | 5.54 MB | 4 classes / 640 px | mAP50 25.05%<br>mAP50-95 10.96% |

The baseline used 8,000 training images: 6,200 India and 1,800 China MotorBike. A separate 1,000-image Czech validation split selected the checkpoint; the reserved US test contained 1,000 images. Thus 9,000 is the combined training-plus-validation count, not 9,000 training images. The country plan and recovered bootstrap support these counts.

The recovery run selected epoch 27 and exported the best checkpoint after epoch 37; the configured maximum was 50 epochs with patience 10. The original archived best.pt asset and the inventoried baseline have the same full SHA-256, 2bb146ad53a3ddd149320aae3be67b2b1d50ccf0fdbc909edd749538055a2551. A genuine final last.pt was not found in the preserved original model archive; it must not be reconstructed or relabeled from best.pt.

Recovered evidence binds the run to the official COCO initializer 0ebbc80d4a76, Ultralytics 8.4.175, Torch 2.11.0+cu130 and Python 3.13.15. Recorded settings include 640-pixel input, batch 16, seed 20261010, deterministic training and AdamW. These describe the original run, not a new training run or the current CPU runtime.

Country separation and rejection of byte-identical cross-split images support the baseline held-out design. Missing sequence identifiers still limit near-duplicate assurance. The US test must remain separate from validation-based threshold or model selection.

### Supplied YOLO26 training narrative

The teammate narrative reports 26,869 RDD training images, 5,758 validation images and 5,758 test images. The main YOLO26s run adds approximately 14,000 external training images, giving approximately 41,000 training images for the main run only. This is a reported approximate count, not an independent recount. Ablations have their own settings and the India-held-out run excludes India.

Main-run records report 120 epochs, best validation epoch 84 and 1024-pixel input. Additional sources are Rome potholes, HRP4K, SVRDD Beijing and web images. Raw teammate training data/manifests and original training scripts/notebooks were not supplied. Reported near-duplicate leakage is 2.2% in validation and 2.4% in test, so results may be optimistic.

Original baseline notebook/bootstrap evidence was recovered; this does not fill the separate provenance gaps for teammate checkpoints. Missing framework versions, initializers or recipes remain unknown in the configuration map. Filename epoch labels are retained provenance labels, not independently verified training histories.

Sources: [detector configuration and provenance](detector-config-provenance-map.json); [team models and results](Team-Models-and-Results.md).


## 02 | Earlier supplied detector results

Eight imported checkpoints - validation evidence only

These are values from the supplied MODEL_INDEX.csv, preserved in the model inventory. RoadScan has not independently reproduced their validation evaluation. Training overlap, original validation membership and complete training recipes are not established. Four- and five-class groups are shown separately; table order is archival, not a ranking.

### Four-class validation group

| Checkpoint | SHA prefix | MB | Classes / px | mAP50 | mAP50-95 |
| --- | --- | --- | --- | --- | --- |
| RT-DETR X / Epoch 1 | bda15131e5f6 | 540.04 | 4 / 640 | 0.003% | 0.00% |
| RT-DETR X / Epoch 50 | edb35d3cf7b1 | 135.46 | 4 / 640 | 10.12% | 4.83% |
| YOLO11m / Epoch 86 | 9e2a0484d6f4 | 40.53 | 4 / 640 | 46.05% | 21.44% |
| YOLOv8m / Epoch 97 | 9a13443ad7a3 | 52.04 | 4 / 640 | 48.95% | 21.81% |
| RT-DETR / setup / Epoch 1 | 11602fd792d5 | 135.45 | 4 / 640 | 0.004% | 0.001% |

### Five-class validation group

| Checkpoint | SHA prefix | MB | Classes / px | mAP50 | mAP50-95 |
| --- | --- | --- | --- | --- | --- |
| RT-DETR L / RDD2022 / 800 px / Epoch 68 | b636269a3035 | 263.74 | 5 / 800 | 61.77% | 31.28% |
| YOLO11s / RDD2022 / 800 px / Epoch 85 | e1937609619f | 19.22 | 5 / 800 | 62.95% | 34.68% |
| YOLOv8m / RDD2022 / 800 px / Epoch 21 | 4e14d23d45da | 103.88 | 5 / 800 | 57.77% | 30.86% |

Size is the checkpoint file size in decimal megabytes, rounded to two decimals; full hashes and exact byte counts are in the [CSV inventory](public-model-inventory.csv). Checkpoint size is not parameter count or runtime RAM usage. Files can retain different optimizer or serialization contents, so size alone does not establish efficiency.

The Epoch 1 RT-DETR X and setup checkpoint have near-zero supplied validation scores. They remain in the inventory for traceability and are not silently discarded. The setup checkpoint is an RT-DETR detector despite its generic filename; it is distinct from RT-DETR X Epoch 1 by hash.

The five-class rows add OTHER at index 3 and move D40 to index 4. The supplied validation index does not prove that its reported means use precisely the YOLO26 four-damage-class averaging rule. Do not merge these values with the baseline independent US test or YOLO26 test results to select a universal winner.

Accuracy of an imported detector on unseen Saudi roads, or on a common set guaranteed unseen during its training, is still unknown. The [validation status](Validation-Status.md) records the remaining evaluation limits.


## 03 | YOLO26 detection experiments

Seven supplied detectors - four damage classes scored

The six RDD test rows below use supplied results.csv values. All seven checkpoints have five outputs, but supplied mAP scores cover D00, D10, D20 and D40 only; OTHER is excluded. The India-held-out row has its own evaluation domain and must remain separate.

### RDD test - supplied, not independently reproduced

| Checkpoint | SHA prefix | MB | Classes / px | mAP50 | mAP50-95 |
| --- | --- | --- | --- | --- | --- |
| YOLO26s / Main / 1024 px | 9f940caa9222 | 20.41 | 5 / 1024 | 63.04% | 33.01% |
| YOLO26s / Size experiment / 640 px | 31b518ed36ec | 20.32 | 5 / 640 | 59.43% | 30.71% |
| YOLO26n / Size experiment / 640 px | 3be62681e3ec | 5.46 | 5 / 640 | 55.99% | 28.03% |
| YOLO26s / No augmentation / 640 px | 3ef405bf22a9 | 20.32 | 5 / 640 | 46.93% | 21.76% |
| YOLO26s / Vertical flip / 640 px | 63d2099e766f | 20.32 | 5 / 640 | 58.48% | 30.14% |
| YOLO26s / Cleaned labels / 640 px | 1bb6724ee2d0 | 20.32 | 5 / 640 | 60.05% | 30.73% |

### India test only - domain-shift experiment

| Checkpoint | SHA prefix | MB | Classes / px | mAP50 | mAP50-95 |
| --- | --- | --- | --- | --- | --- |
| YOLO26s / India held out / 640 px | fa148e7109aa | 20.32 | 5 / 640 | 8.86% | 3.77% |

### What E2-E4 support within their supplied comparisons

E2 compares size/resolution: the small 640 model exceeds nano 640 on the supplied RDD detection metrics. E3 compares augmentation: standard small 640 exceeds no augmentation by 12.50 mAP50 percentage points; vertical flip does not improve the standard result. Cleaned-label validation mAP50-95 is 0.3403 versus 0.3421 for the original-label comparison, so the main run retained original labels. Those validation figures are not the test figures in the table.

E4 reports India-only mAP50 of 0.0886 for the India-held-out model versus 0.3925 when India is included in the comparison model training. This is evidence of domain shift under that experiment, not a forecast for Saudi conditions. The reported split leakage and absent raw manifests still limit confidence in transfer claims.

### Main-model detail and threshold scope

Main per-class AP50: D00 63.55%, D10 62.52%, D20 69.90%, D40 56.19%. Separate external mAP50/mAP50-95 results: HRP4K 53.00/31.04%, Rome 35.07/14.49%, web 82.13/51.93%, SVRDD 67.63/38.85%. Each is a distinct dataset; none is an interchangeable overall accuracy score.

Main thresholds D00 0.173, D10 0.166, D20 0.195 and D40 0.056 were selected on validation at 1024 pixels (F1 for cracks, F2 for potholes). Lower-resolution live modes have not been recalibrated. The low pothole threshold favors recall and needs human review. [Team experiment source](Team-Models-and-Results.md).


## 04 | Classification and duplicate retrieval

Three additional assets - different tasks, different metrics

| Asset | SHA prefix | MB | Role |
| --- | --- | --- | --- |
| ResNet18 / Image classifier | 267c1eefc78d | 44.79 | Four-label image classifier |
| YOLO11n | 0ebbc80d4a76 | 5.61 | Stock COCO initialization |
| DINOv2 ViT-S/14 / Official pretrained backbone | b938bf1bc15c | 88.28 | Pretrained visual embeddings |

### E1 - image-level damage presence

| Model | Any-damage F1 | Any-damage accuracy | Per-class F1: D00 / D10 / D20 / D40 |
| --- | --- | --- | --- |
| ResNet18 | 0.893 | 0.869 | 0.790 / 0.751 / 0.805 / 0.639 |
| Main YOLO26s | 0.929 | 0.913 | 0.861 / 0.805 / 0.859 / 0.762 |

The supplied E1 comparison uses 5,758 images and image-presence thresholds. Accuracy here measures the any-damage decision, not box localization. A classifier cannot supply road-damage boxes, and its F1 must not be inserted into a detector mAP ranking. ResNet18 remains available as the classification baseline; its exact initializer and training count are not independently established.

### E5 - simulated repeat observations with GPS

| Supplied duplicate method | F0.5 | Meaning |
| --- | --- | --- |
| pHash + GPS | 0.851 | Perceptual-hash comparison baseline |
| ResNet50 + GPS | 0.975 | Experiment method; not the inventoried ResNet18 asset |
| DINOv2 + GPS | 0.980 | Feature comparison with geographic candidate filtering |
| DINOv2 without GPS | 0.796 | Ablation of geographic filtering |

The supplied DINOv2+GPS experiment reports precision 0.983, hard-repeat recovery 0.951 and new-report false merge 0.032; the no-GPS false-merge rate is 0.137. These simulated observations do not measure current application duplicate accuracy. The E5 ResNet50 method is not a twentieth retained weight in this inventory.

The application offers a replacement DINOv2 damage-crop search with GPS candidate filtering alongside a separate lightweight dHash path. Its crop/preprocessing pipeline is not verified identical to E5 and its threshold is not calibrated on real repeat pairs. E5 threshold 0.6529684 with 50 m candidates must never be applied to hash similarity; a similarity score is not an accuracy percentage.

DINOv2 is an official pretrained backbone, not a model trained by RoadScan. Stock COCO YOLO11n initializes the road detector but has no road-damage test score here. Human review can approve examples for a separate training/evaluation/import cycle; it does not instantly update any model weights. [Supplied E1-E5 results](Team-Models-and-Results.md).


## 05 | Common-set and CPU evidence

Readiness diagnostics - no new accuracy ranking

The prepared common protocol uses 1,000 US RDD2022 images and four damage classes, with CPU inference at 640 pixels, batch 1 and two threads. It is independently held out for the original baseline only; imported training overlap is unknown. Fourteen detectors finished a 20-image preflight; zero full evaluations are complete. YOLO11s 800 (e1937609619f) and India-held-out YOLO26s (fa148e7109aa) have no completed preflight in this record.

| Detector / diagnostic at 640 px | SHA prefix | Mean warm time (ms) |
| --- | --- | --- |
| YOLO11n / Baseline | 2bb146ad53a3 | 176.7 |
| RT-DETR X / Epoch 1 | bda15131e5f6 | 1663.0 |
| RT-DETR X / Epoch 50 | edb35d3cf7b1 | 1517.3 |
| YOLO11m / Epoch 86 | 9e2a0484d6f4 | 506.5 |
| YOLOv8m / Epoch 97 | 9a13443ad7a3 | 518.0 |
| RT-DETR L / RDD2022 / 800 px / Epoch 68 | b636269a3035 | 815.4 |
| RT-DETR / setup / Epoch 1 | 11602fd792d5 | 1619.5 |
| YOLOv8m / RDD2022 / 800 px / Epoch 21 | 4e14d23d45da | 548.3 |
| YOLO26s / Size experiment / 640 px | 31b518ed36ec | 322.3 |
| YOLO26s / Cleaned labels / 640 px | 1bb6724ee2d0 | 240.1 |
| YOLO26s / Main / 1024 px | 9f940caa9222 | 179.5 |
| YOLO26n / Size experiment / 640 px | 3be62681e3ec | 82.6 |
| YOLO26s / No augmentation / 640 px | 3ef405bf22a9 | 219.0 |
| YOLO26s / Vertical flip / 640 px | 63d2099e766f | 176.9 |

Timing uses three warm-up images and ten timed images. It includes image decode, preprocessing, model forward and postprocessing; it excludes model loading and HTTP. The original preflights ran in a two-CPU, 3 GiB Linux container under host memory pressure. All timing rows used 640 pixels, including checkpoints whose names retain 800 or 1024 from their source configuration.

These short CPU diagnostics are not predictive hard real-time guarantees, representative field latency, camera FPS or end-to-end application latency. Differences between similarly sized YOLO26 variants can reflect the run conditions; do not interpret this table as a stable speed ranking. The preflight accuracy outputs are deliberately not presented as full-benchmark results.

Earlier application diagnostics used three warm requests on one synthetic image and a different resource budget: nano640 57.89 ms, small640 122.38 ms, main Balanced640 124.74 ms, main Detail1024 298.94 ms (median model time). Those figures are a separate experiment and must not be mixed with the table above. [Timing context](Team-Models-and-Results.md).


## 06 | Publication and application limits

Release authorization, asset terms and tested behavior are separate

All 19 original weights are authorized for publication; no ranking or top-five privacy restriction remains. The following asset-specific preparation status is dated 28 October 2026 and may change. Check the [live model inventory](public-model-inventory.json) and [model availability](Models.md) for current downloads and remaining conditions.

| Asset group | Release route / remaining condition |
| --- | --- |
| DINOv2 ViT-S/14 | Published unchanged at the [model-resources release](https://github.com/Feras-MQ/RoadScan/releases/tag/model-resources-2026-10-28), with Apache-2.0 license/attribution packet and SHA256SUMS. Anonymous download hashes verified. |
| Stock COCO YOLO11n | Official upstream link is eligible. A mirror needs the applicable AGPL notices and corresponding-source access. |
| RoadScan YOLO11n baseline | Original source evidence packet is assembled. Complete the scoped source terms and adjacent public corresponding-source access under applicable AGPL terms. |
| Other 11 trained YOLO detectors | Confirm initializer/implementation evidence and supply required corresponding source and notices. |
| Four trained RT-DETR detectors | Confirm actual implementation/version, initializer and exact artifact terms; compatible metadata alone does not establish Apache-only eligibility. |
| ResNet18 classifier | Establish actual initializer and pretrained-weight terms. A code-library license alone does not settle checkpoint terms. |

The absence of a repository-root LICENSE is not by itself a blanket prohibition on releasing a separately licensed asset. Existing asset terms, covered modifications, required notices and corresponding source still matter. Missing historical Git history is not a separate licensing ban; missing training provenance can still prevent the team from establishing the applicable terms. See the [AGPL text](https://raw.githubusercontent.com/ultralytics/ultralytics/v8.4.175/LICENSE) and [Ultralytics licensing policy](https://www.ultralytics.com/license).

### What the application evidence supports

Published validation records report 221 backend tests with one optional skip, 24 frontend tests, 67 browser checks, 19 fresh local lifecycle checks and two model fault checks. These are software evidence, not new model accuracy measurements. Isolated Linux x86-64 CPU checks passed; fresh public-clone acceptance with downloaded weights, Mac/ARM setup and drone hardware remain unverified.

Detection outputs remain reviewable predictions. Majority model voting is not ground truth; a reviewer may select a minority model. Priority is a configurable review aid, not calibrated physical severity. Human corrections produce candidate training examples, followed by a separate train/evaluate/import process; no automatic live learning is claimed.

No genuine labeled Saudi field test set or repeat-damage evaluation is complete. Low-resolution confidence thresholds, DINOv2 matching, representative camera latency and generalization need validation before operational claims. Read [Validation-Status.md](Validation-Status.md) and [Inference-and-Reproducibility.md](Inference-and-Reproducibility.md).


## 07 | Review trail and remaining work

Submission deadline: 31 October 2026

### Before making a stronger model claim

1. Freeze evaluation membership and label policy, preserve the US baseline holdout, and audit any imported training overlap. A common diagnostic set is not automatically an unseen test for every imported model.

2. Complete the full shared detector evaluation on suitable hardware with an identical four-class mapping, image size, threshold protocol and runtime. Publish per-class AP, precision/recall and measured conditions; keep classification and retrieval evaluations separate.

3. Collect and independently label Saudi road images and genuine repeat-damage pairs. Calibrate thresholds on validation only, then assess a held-out field set. Record geography, capture conditions and duplicate controls.

4. Measure warm and cold end-to-end camera/application latency and memory on presentation hardware. Verify each downloaded release asset by SHA-256 and complete a clean installation check. Preserve the current baseline while any later improvement is evaluated.

### Public evidence accompanying this report

| Reference | What it supports |
| --- | --- |
| [Model CSV](public-model-inventory.csv) / [JSON](public-model-inventory.json) | All 19 identities, full hashes, exact bytes, roles and asset-specific publication conditions. |
| [Detector map](detector-config-provenance-map.json) | All 16 detector class maps, original input sizes, available configurations and explicit provenance gaps. |
| [Team models and results](Team-Models-and-Results.md) | Reported data counts, supplied detection results, E1-E5, leakage, thresholds and prior CPU diagnostics. |
| [Validation status](Validation-Status.md) | Verified software behavior and unfinished model/field evaluation. |
| [Inference and reproducibility](Inference-and-Reproducibility.md) | Model import/runtime guidance and current reproducibility limits. |
| [Model availability](Models.md) | Current release/download status; consult alongside the live inventory. |

### Primary upstream references

[Ultralytics metric definitions](https://docs.ultralytics.com/guides/yolo-performance-metrics) explain detection measures. [Ultralytics licensing](https://www.ultralytics.com/license) and the [versioned AGPL text](https://raw.githubusercontent.com/ultralytics/ultralytics/v8.4.175/LICENSE) establish the relevant upstream framework terms. These sources do not independently verify RoadScan results.

The [original RT-DETR license](https://github.com/lyuwenyu/RT-DETR/blob/main/LICENSE) is Apache-2.0; this alone does not prove the provenance of an imported checkpoint. [Torchvision weight guidance](https://docs.pytorch.org/vision/stable/models.html#general-information-on-pre-trained-weights) distinguishes code licensing from pretrained-weight conditions. [DINOv2](https://github.com/facebookresearch/dinov2#license) states Apache-2.0 for its ordinary DINOv2 code and weights.

Report method: read existing inventories, experiment records and release preparation; verify cross-file identities and the baseline archive checksum; generate and inspect this document. No training, model loading, new inference, weight modification or new field measurement was performed for this report. Original project reports remain unchanged.
