# RoadScan model availability

As of **1 November 2026**, the [JSON inventory](public-model-inventory.json) and [CSV inventory](public-model-inventory.csv) cover **22 locally SHA256-verified weights**, totalling **1,623,390,394 bytes**: 19 road detectors, one classifier, one stock COCO initializer and DINOv2. The three released Road fine-tunes are included. [Two additional peer-reported identities](peer-reported-models-2026-11-01.json) remain separately labelled and independently unverified.

**Twelve weights are mirrored publicly** (eleven road detectors and DINOv2), **one initializer** has an official upstream link, and **nine weights remain metadata-only**. The [release matrix](Model-Release-Matrix-2026-10-30.json) preserves per-model source, licensing and reproducibility conditions. A source-only Git checkout does not contain all weights; download URLs and exact release filenames are in the current inventory.

## Names and demo organization

Use the [complete naming and organization guide](Model-Organization-2026-11-01.md):

- **Default demo:** Main · YOLO26s · 1024 and YOLO26n · Compact · 640.
- **Experimental:** YOLO26s · Road v1 · 1024, with explicit selection-set limitations.
- **Baseline / Advanced comparisons:** original YOLO11n baseline, RT-DETR L E68, YOLO11s E85 and YOLOv8m 800 E21.
- **Support:** DINOv2 visual matching, outside the detector selector.
- **Research archive:** other unique weights with provenance and restoration mapping.

These are proposed display aliases and intended categories. No selector filtering, model activation, stable-ID rename, file move or deletion is implemented by this documentation. Main was selected in the last inspected historical configuration; the present runtime was not verified. This joint recommendation concerns organization and preservation, not a new performance ranking. The [organization guide](Model-Organization-2026-11-01.md) records the confirmed reviewer agreement.

## Distinguish the released road fine-tunes

| Proposed alias | Actual release filename | Full SHA256 |
|---|---|---|
| YOLO26s · Road v1 · 1024 · Experimental | `78f5e2afb82d-main_yolo26s_1024_road.pt` | `78f5e2afb82d5145f30de9957cb51f167241e377ed0b5775f71be1c5e80ac87d` |
| YOLO26s · Road A · 1024 · Experimental | `00794102e39e-main_yolo26s_1024_road_v2.pt` | `00794102e39e621f1268e31f43b3743daae17309b5eaf90feef1077f0bf0991b` |
| YOLO26s · Road v2b · 1024 · Experimental | `0caef4521c82-main_yolo26s_1024_road_v2b.pt` | `0caef4521c82a944cfe4b6e5022914eeabab9c69864967db17a9915f4fdc7500` |

Original package names and earlier proposed release names differ; identify each checkpoint by its full hash. Road A is the release filename containing `road_v2`, not Road v2b. Their presence in public downloads does not establish independent accuracy. Read [fine-tune provenance](../model_sources/road-finetunes-2026-10-29/README.md).

## Verification and limits

The 1 November audit streamed existing local weights and supplied archive entries without loading models. All 22 identities matched their recorded bytes and SHA256. GitHub release digests matched all 12 mirrored weights; anonymous HEAD requests for those 12 plus the official initializer returned 200 with expected lengths. Fresh remote weight bytes were not downloaded/rehashed in that pass; no new inference or clean-machine acceptance was performed.

For trusted road detectors, verify downloaded bytes against the inventory before importing. Import alone does not activate a model. Follow [inference and reproducibility](Inference-and-Reproducibility.md) for setup and validation. DINOv2 is an embedding backbone, ResNet18 is an image classifier, and the stock COCO initializer is not road-trained.

The 343 road images were used for checkpoint/confidence/model selection, with seven video groups shared with training. Supplied RDD results have reported near-duplicate leakage. There is no completed common independent evaluation supporting a universal ranking. Preserve the dated [model report](Model-Report.md) with [trainer evidence](Trainer-Provenance-2026-10-31.md); its historical 19-weight analysis does not cover every later checkpoint.

The current inventories preserve original 19 catalog keys and append three fine-tunes. Catalog keys are SHA prefixes, not app IDs. Earlier availability/eligibility fields are retained under explicitly dated `historical_inspection`; use current top-level status for downloads. Fine-tune metadata under `model_sources` remains a dated preparation record, not a current publication status. No unpublished weights or new redistribution grants accompany this documentation.
