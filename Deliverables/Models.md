# RoadScan model availability

All **19 unique model weights** are approved by the team for public release, including the previously restricted top five. **DINOv2 is published; the stock COCO initializer is available upstream.** Both downloads were anonymously fetched and their SHA-256 hashes verified on 28 October 2026. The 17 trained detector/classifier weights remain pending their specific source and license requirements.

- **[DINOv2 ViT-S/14 weight](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/b938bf1bc15c-dinov2_vits14_pretrain.pth)** — 88,283,115 bytes; download its [Apache-2.0 license and provenance](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/DINOv2-license-provenance.zip) and [checksums](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/SHA256SUMS.txt). This embedding backbone does not detect road-damage boxes.
- **[Official YOLO11n COCO initializer](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt)** — 5,613,764 bytes; subject to [Ultralytics terms](https://www.ultralytics.com/license). This general-purpose initializer was not trained by RoadScan and is not a road-damage detector.

For trained-model results and their limits, see the [all-model report](Model-Report.pdf). A clean public-download road-detection acceptance test remains pending an available road-trained checkpoint.

The [CSV inventory](public-model-inventory.csv) and [JSON inventory](public-model-inventory.json) record each proposed asset name, SHA-256, exact byte size, task, origin, availability and license conditions. They distinguish 16 road detectors, one four-label classifier, a stock COCO initializer and a DINOv2 embedding backbone. The classifier and embedding model are not substitutes for a box detector.

| Group | Release condition |
|---|---|
| 12 trained YOLO detectors | Assemble the applicable Ultralytics license/notices and corresponding training/source information; the team's contribution license is not yet declared |
| 4 RT-DETR detectors | Confirm the exact training implementation, initialization and applicable license/source packet |
| ResNet18 classifier | Confirm initialization and redistribution provenance |
| Stock COCO initializer | Official upstream download and original hash verified; no mirror uploaded |
| DINOv2 backbone | Published unchanged with Apache-2.0 license/provenance; anonymous download verified |

The combined weight size is **1,562,050,919 bytes**. Large files should be supplied as verified release assets rather than embedded in ordinary source commits. A release is not available until its download links and hashes have been checked.

The current full common-set benchmark is pending. Historical validation scores and filenames must not be used to invent a new top-five ranking; no `last` checkpoint or training history will be fabricated when it was not supplied.

For a trusted **road detector**, use **Settings → Your model library → Browse models → Use model** and verify **Active**. DINOv2 belongs to the embedding tools, not this detector import flow. Ask the maintainers through [GitHub Issues](https://github.com/Feras-MQ/RoadScan/issues) for support, provenance or licensing questions.

Sources: [Ultralytics licensing](https://www.ultralytics.com/license), [Ultralytics RT-DETR implementation](https://docs.ultralytics.com/models/rtdetr/), [original RT-DETR license](https://github.com/lyuwenyu/RT-DETR/blob/main/LICENSE), [DINOv2 license](https://github.com/facebookresearch/dinov2/blob/main/LICENSE), and [project notices](../THIRD_PARTY_NOTICES.md).
