# RoadScan model availability

As of **31 October 2026**, the verified local inventory contains **22 unique weights**: 19 road detectors, one classifier, one stock COCO initializer and DINOv2. **Twelve weights are mirrored publicly (eleven road detectors and DINOv2), one initializer has an official upstream link, and nine weights are held individually.** Use the [current release matrix](Model-Release-Matrix-2026-10-30.md) for exact source, license and reproduction conditions; release permission is not proof of accuracy.

## Start with a road detector

- **[Main YOLO26s (1024)](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/9f940caa9222-main_yolo26s_1024.pt)** — 20,414,080 bytes; SHA256 `9f940caa92229f503eef1171010c13ee8fd74d7b69300e959357d6a8d14be434`.
- **[Original YOLO11n baseline](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/2bb146ad53a3-roadscan_baseline_best.pt)** — 5,536,234 bytes; SHA256 `2bb146ad53a3ddd149320aae3be67b2b1d50ccf0fdbc909edd749538055a2551`.

Verify downloaded bytes with `Get-FileHash -Algorithm SHA256 <path>` on Windows or `shasum -a 256 <path>` on macOS/Linux. Read the [Main/team source and notices](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Model-Source-2026-10-31.zip) or [baseline source packet](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Baseline-Source-AGPL-3.0.zip), then **Settings → Your model library → Browse models / drag file → Use model → verify Active**. Import alone does not activate weights.

For the supplied **experimental Road v1, Road A and Road v2b fine-tunes**, follow their individual download links and caveats in the [current matrix](Model-Release-Matrix-2026-10-30.md); use the full hash to distinguish them. Main remains the current local default. No universal best-model ranking or fresh-machine acceptance is claimed.

| Experimental choice | Original download | SHA256 |
|---|---|---|
| Road v1 (1024) | [road.pt](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/78f5e2afb82d-main_yolo26s_1024_road.pt) | `78f5e2afb82d5145f30de9957cb51f167241e377ed0b5775f71be1c5e80ac87d` |
| Road A (1024) | [road_v2.pt](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/00794102e39e-main_yolo26s_1024_road_v2.pt) | `00794102e39e621f1268e31f43b3743daae17309b5eaf90feef1077f0bf0991b` |
| Road v2b (1024) | [road_v2b.pt](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/0caef4521c82-main_yolo26s_1024_road_v2b.pt) | `0caef4521c82a944cfe4b6e5022914eeabab9c69864967db17a9915f4fdc7500` |

## Other tasks

- **[DINOv2 ViT-S/14 weight](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/b938bf1bc15c-dinov2_vits14_pretrain.pth)** — 88,283,115 bytes; download its [Apache-2.0 license and provenance](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/DINOv2-license-provenance.zip) and [checksums](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/SHA256SUMS.txt). This embedding backbone does not detect road-damage boxes.
- **[Official YOLO11n COCO initializer](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt)** — 5,613,764 bytes; subject to [Ultralytics terms](https://www.ultralytics.com/license). This general-purpose initializer was not trained by RoadScan and is not a road-damage detector.

For trained-model results and their limits, see the dated [all-model report](Model-Report.pdf) with the [31 October provenance update](Trainer-Provenance-2026-10-31.md). Road-trained checkpoints are now public; a clean-machine public-download installation test remains pending and must not be inferred from publication or local CPU smoke checks.

## Historical 19-weight inspection

The original [CSV inventory](public-model-inventory.csv) and [JSON inventory](public-model-inventory.json) describe the earlier 19-weight inspection: 16 road detectors, one classifier, a stock COCO initializer and DINOv2. Their original availability fields and the inspection conditions below are historical, superseded for current availability by the [22-weight matrix](Model-Release-Matrix-2026-10-30.json). The classifier and embedding model are not substitutes for a box detector.

| Historical group | Conditions recorded during the original inspection (see current matrix for resolution) |
|---|---|
| 12 trained YOLO detectors | Embedded AGPL-3.0 notices and Ultralytics metadata verified; complete corresponding source and scoped team-source terms |
| 4 RT-DETR detectors | Embedded AGPL-3.0 notices and serialized Ultralytics classes verified; complete original/custom training source and initializer provenance |
| ResNet18 classifier | Confirm initialization and redistribution provenance |
| Stock COCO initializer | Official upstream download and original hash verified; no mirror uploaded |
| DINOv2 backbone | Published unchanged with Apache-2.0 license/provenance; anonymous download verified |

Safe pickle-bytecode inspection identified explicit AGPL-3.0 notices in all 16 detectors, with saved framework versions 8.4.175, 8.4.177 or 8.4.178. These saved versions and initializer filename candidates do not prove the complete original training environment or absence of custom code. No model was executed for this inspection.

The **original 19-weight snapshot** totals **1,562,050,919 bytes**; this is not the current 22-weight total. Large files are supplied as release assets, separate from source commits. Published downloads and hashes were checked as recorded in the current matrix.

The current full common-set benchmark is pending. Historical validation scores and filenames must not be used to invent a new top-five ranking; no `last` checkpoint or training history will be fabricated when it was not supplied.

For a trusted **road detector**, use **Settings → Your model library → Browse models → Use model** and verify **Active**. DINOv2 belongs to the embedding tools, not this detector import flow. Ask the maintainers through [GitHub Issues](https://github.com/Feras-MQ/RoadScan/issues) for support, provenance or licensing questions.

Sources: [Ultralytics licensing](https://www.ultralytics.com/license), [Ultralytics RT-DETR implementation](https://docs.ultralytics.com/models/rtdetr/), [original RT-DETR license](https://github.com/lyuwenyu/RT-DETR/blob/main/LICENSE), [DINOv2 license](https://github.com/facebookresearch/dinov2/blob/main/LICENSE), and [project notices](../THIRD_PARTY_NOTICES.md).
