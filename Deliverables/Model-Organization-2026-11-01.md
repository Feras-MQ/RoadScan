# Model names and organization — 1 November 2026

The [current JSON](public-model-inventory.json) and [CSV](public-model-inventory.csv) contain **22 locally SHA256-verified identities**: 19 road detectors, one image classifier, one COCO initializer and one embedding backbone. The [peer supplement](peer-reported-models-2026-11-01.json) records **two additional reported identities**, separately and without claiming independent byte verification. Do not combine those scopes into a 24-model verified inventory.

## Recommended organization

This is a reversible documentation recommendation, not a change to the running selector or active model. Original model IDs, hashes, filenames, class maps and provenance remain unchanged. Display names below are proposed aliases only.

- **Default demo:** Main as the recommended default, plus Compact as a smaller alternative. No new device-speed claim is made.
- **Experimental:** Road v1, explicitly labelled experimental. Its placement is not a claim that it outperforms Main.
- **Baseline / Advanced comparisons:** original YOLO11n baseline and all three historical voting comparators. Preserve access to the exact identities for reproducibility and comparisons.
- **Support:** DINOv2 for visual matching; never present it as a road-damage detector.
- **Research archive:** retain every other unique research weight with source/configuration, results, checksums, notices and lineage. Archiving here means intended organization, not moving or deleting installed files. Keep original packages and their restoration/import mapping by full hash.

This organization is the joint recommendation of Dot and Ahmed's Claude, confirmed in repository PR 1, comment 6561418345, on 1 November 2026 at 17:31:50 UTC. The reviews initially proposed different third everyday options; the agreed plan uses two defaults with separate Experimental and Baseline / Advanced groups. Earlier review evidence is in comments 6561054223 and 6561265109. The agreement concerns organization and preservation, not a performance ranking or implemented library changes.

| Catalog key | Proposed display alias | Intended group |
|---|---|---|
| `2bb146ad53a3` | YOLO11n · Road baseline · 640 | Baseline / Advanced comparisons |
| `bda15131e5f6` | RT-DETR X · Early checkpoint · 640 · E1 | Research archive |
| `edb35d3cf7b1` | RT-DETR X · 640 · E50 | Research archive |
| `9e2a0484d6f4` | YOLO11m · 640 · E86 | Research archive |
| `9a13443ad7a3` | YOLOv8m · 640 · E97 | Research archive |
| `b636269a3035` | RT-DETR L · RDD2022 · 800 · E68 | Baseline / Advanced comparisons |
| `11602fd792d5` | RT-DETR · Setup benchmark · 640 · E1 | Research archive |
| `e1937609619f` | YOLO11s · RDD2022 · 800 · E85 | Baseline / Advanced comparisons |
| `4e14d23d45da` | YOLOv8m · RDD2022 · 800 · E21 | Baseline / Advanced comparisons |
| `0ebbc80d4a76` | YOLO11n · COCO initializer | Research archive |
| `31b518ed36ec` | YOLO26s · Standard training · 640 | Research archive |
| `1bb6724ee2d0` | YOLO26s · Cleaned labels · 640 | Research archive |
| `9f940caa9222` | Main · YOLO26s · 1024 | Default demo |
| `3be62681e3ec` | YOLO26n · Compact · 640 | Default demo |
| `3ef405bf22a9` | YOLO26s · No augmentation · 640 | Research archive |
| `63d2099e766f` | YOLO26s · Vertical flip · 640 | Research archive |
| `fa148e7109aa` | YOLO26s · India excluded · 640 | Research archive |
| `267c1eefc78d` | ResNet18 · Damage classifier · 512 | Research archive |
| `b938bf1bc15c` | DINOv2 · Visual matching backbone | Support |
| `78f5e2afb82d` | YOLO26s · Road v1 · 1024 · Experimental | Experimental |
| `00794102e39e` | YOLO26s · Road A · 1024 · Experimental | Research archive |
| `0caef4521c82` | YOLO26s · Road v2b · 1024 · Experimental | Research archive |

Catalog keys are the first 12 SHA256 characters, not app IDs. Imported detector IDs are full SHA256 values; the original baseline uses the special app ID `baseline`. Classifier, initializer and embedding artifacts are not detector-library choices. Full hashes, sizes, original filenames and actual release names are in the JSON/CSV.

## Additional peer evidence

| Reported key | Proposed alias | Reported bytes | Intended group |
|---|---|---:|---|
| `d66e7ddacc35` | RT-DETR L · Final saved checkpoint · E70 (peer-reported) |263,739,626|Research archive|
| `02ab48febc4e` | YOLOv8m · 183-labelled variant (peer-reported) |52,039,250|Research archive|

Full reported hashes and limitations are in the [peer supplement](peer-reported-models-2026-11-01.json). The first is reported as the same run as RT-DETR L E68, with embedded epoch 69 and 70 results rows of 200 planned; the stop reason is unknown. For the second, 183epochs is only a filename label, embedded epoch is -1, and training arguments, split and results remain unavailable. Neither has been independently fetched, hashed, loaded, promoted or published by this review.

## What the evidence supports

The 343 road images were reused for checkpoint, confidence and model selection; seven video groups overlap training/selection. Team RDD results also report near-duplicate leakage. Older validation scores, the reserved US baseline test, India-only evaluation, image classification and road-selection metrics are different measurements. They do not establish a fair universal ranking. Road v1's recorded selection/export history remains unresolved. See [fine-tune evidence](../model_sources/road-finetunes-2026-10-29/README.md), [trainer provenance](Trainer-Provenance-2026-10-31.md) and the dated [model report](Model-Report.md).

No unique checkpoint is recommended for irreversible deletion on this evidence, including the early RT-DETR X and setup weights. Redundant copies require exact occurrence/hash checks and preservation of a verified source; partial backups and synthetic test artifacts must not be counted as extra research models. This public guide intentionally contains no device-specific cleanup targets or report data. No cleanup was executed.

## Publication and restoration

Twelve weights are public release assets: eleven detectors and DINOv2. The COCO initializer has an official upstream link. Eight older detectors and ResNet18 remain metadata-only, with unresolved source/terms conditions listed individually in the [release matrix](Model-Release-Matrix-2026-10-30.json). Publication is not training reproducibility or acceptance testing.

For each identity, the current inventory binds the original/catalog filename to its full hash and, where public, actual download URL. Retain source packages and notices alongside archived weights. Restore/import a trusted detector by exact hash and preserve its original ID; importing does not itself select it. Consult [inference and reproducibility](Inference-and-Reproducibility.md) before activation.

The 1 November audit streamed existing local files and supplied ZIP entries without deserialization or inference. Public release digests matched those identities; anonymous HEAD checks returned 200 and expected lengths for 12 release weights and the initializer. Fresh remote weight bytes were not downloaded/rehashed in that pass. Current runtime selection, clean-machine acceptance and a common independent accuracy evaluation remain unverified.
